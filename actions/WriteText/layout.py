"""
Resolves characters into the key codes of the keyboard layout that is currently
active on the system.

uinput can only send hardware key codes - the compositor (Wayland) or the X
server turns those into characters using the active keyboard layout. Sending the
US QWERTY code of a character therefore types a different character on every
non-US layout (https://github.com/StreamController/OSPlugin/issues/11).

GTK already holds the exact keymap of the session: on Wayland the compositor
sends it over wl_keyboard.keymap, on X11 GDK reads it from the server. So
instead of guessing the layout we ask GDK which key and which modifiers produce
a given character, and send exactly those.
"""

import threading
import time

import gi
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, GLib

from loguru import logger as log

# X11/XKB key codes are evdev key codes offset by 8
XKB_KEYCODE_OFFSET = 8
MAX_XKB_KEYCODE = 256

# We cannot know which layout group the session currently has active, so we only
# ever trust the primary one
PRIMARY_GROUP = 0

# Which modifiers select which shift level, see the FOUR_LEVEL/EIGHT_LEVEL key
# types of xkeyboard-config. GDK reports levels zero based.
_LEVEL_MODIFIERS = {
    0: (),
    1: ("shift",),
    2: ("level3",),
    3: ("shift", "level3"),
    4: ("level5",),
    5: ("shift", "level5"),
    6: ("level3", "level5"),
    7: ("shift", "level3", "level5"),
}

# The keysyms a modifier can be bound to, in order of preference
_MODIFIER_KEYVALS = {
    "shift": (Gdk.KEY_Shift_L, Gdk.KEY_Shift_R),
    "level3": (Gdk.KEY_ISO_Level3_Shift, Gdk.KEY_Mode_switch),
    "level5": (Gdk.KEY_ISO_Level5_Shift,),
}

# Keymaps also bind their modifiers to key codes that no keyboard actually has
# (AltGr for example sits on both RightAlt and a placeholder key). Sending a key
# code a real keyboard can produce is the safer option.
_PREFERRED_MODIFIER_KEY_CODES = frozenset({
    29, 97,     # ctrl, left and right
    42, 54,     # shift, left and right
    56, 100,    # alt, left and right
    125, 126,   # meta, left and right
})

_MODIFIER_CANDIDATE_KEYVALS = frozenset(
    keyval for keyvals in _MODIFIER_KEYVALS.values() for keyval in keyvals
)

# Keypad and outer keys. Many keyboards don't have them and layouts usually
# offer the same character on the main key block as well, so they are only used
# when nothing else produces the character.
_SECONDARY_KEY_CODES = frozenset(
    {55, 86, 95, 96, 98, 101, 117, 118, 121, 179, 180}
    | set(range(71, 84))
)

# Layouts like the German one only reach some characters through a dead key.
# Pressing the dead key followed by space inserts the character itself.
_DEAD_KEY_CHARS = {
    "dead_grave": "`",
    "dead_acute": "´",
    "dead_circumflex": "^",
    "dead_tilde": "~",
    "dead_diaeresis": "\"",
    "dead_cedilla": "¸",
    "dead_macron": "¯",
    "dead_breve": "˘",
    "dead_abovedot": "˙",
    "dead_abovering": "°",
    "dead_doubleacute": "˝",
    "dead_caron": "ˇ",
    "dead_ogonek": "˛",
}


class LayoutTable:
    """
    A snapshot of the active keyboard layout.

    ``keystrokes`` maps a character to the sequence of steps that types it, each
    step being a tuple of (modifier key codes to hold, key code to tap). All key
    codes are evdev key codes.
    """

    def __init__(self, keystrokes: dict[str, list[tuple[tuple[int, ...], int]]],
                 labels: dict[int, str], shift_code: int | None):
        self.keystrokes = keystrokes
        self.labels = labels
        self.shift_code = shift_code

    def get_label(self, key_code: int) -> str | None:
        """The character a key is labelled with on the active layout, if it has one"""
        return self.labels.get(key_code)


def _build_table() -> LayoutTable | None:
    display = Gdk.Display.get_default()
    if display is None:
        return None

    # char/dead key char -> (is_secondary, level, key code), lowest sorts best
    direct: dict[str, tuple[bool, int, int]] = {}
    dead: dict[str, tuple[bool, int, int]] = {}
    labels: dict[int, str] = {}
    modifier_codes: dict[int, list[int]] = {}

    for xkb_code in range(XKB_KEYCODE_OFFSET, MAX_XKB_KEYCODE):
        found, keys, keyvals = display.map_keycode(xkb_code)
        if not found:
            continue

        key_code = xkb_code - XKB_KEYCODE_OFFSET
        for key, keyval in zip(keys, keyvals):
            # Modifiers are bound once for the whole keymap, not per group
            if keyval in _MODIFIER_CANDIDATE_KEYVALS:
                modifier_codes.setdefault(keyval, []).append(key_code)

            if key.group != PRIMARY_GROUP:
                continue

            is_secondary = key_code in _SECONDARY_KEY_CODES
            name = Gdk.keyval_name(keyval) or ""
            candidate = (is_secondary, key.level, key_code)

            if name in _DEAD_KEY_CHARS:
                char = _DEAD_KEY_CHARS[name]
                if char not in dead or candidate < dead[char]:
                    dead[char] = candidate
                continue

            unicode_value = Gdk.keyval_to_unicode(keyval)
            if unicode_value == 0:
                continue

            char = chr(unicode_value)
            if char not in direct or candidate < direct[char]:
                direct[char] = candidate
            if key.level == 0 and char.strip() and char.isprintable():
                labels.setdefault(key_code, char.upper())

    modifiers: dict[str, int] = {}
    for modifier, candidates in _MODIFIER_KEYVALS.items():
        for keyval in candidates:
            key_codes = modifier_codes.get(keyval)
            if not key_codes:
                continue
            preferred = [code for code in key_codes if code in _PREFERRED_MODIFIER_KEY_CODES]
            modifiers[modifier] = preferred[0] if preferred else key_codes[0]
            break

    keystrokes: dict[str, list[tuple[tuple[int, ...], int]]] = {}
    for char, (_, level, key_code) in direct.items():
        step = _resolve_step(level, key_code, modifiers)
        if step is not None:
            keystrokes[char] = [step]

    space = keystrokes.get(" ")
    if space is not None:
        for char, (_, level, key_code) in dead.items():
            if char in keystrokes:
                continue
            step = _resolve_step(level, key_code, modifiers)
            if step is not None:
                keystrokes[char] = [step, space[0]]

    # A new line is entered with Return, not with the Linefeed key some keymaps
    # still carry
    if "\r" in keystrokes:
        keystrokes["\n"] = keystrokes["\r"]

    if not keystrokes:
        return None

    return LayoutTable(keystrokes, labels, modifiers.get("shift"))


def _resolve_step(level: int, key_code: int,
                  modifiers: dict[str, int]) -> tuple[tuple[int, ...], int] | None:
    needed = _LEVEL_MODIFIERS.get(level)
    if needed is None:
        return None

    modifier_codes = []
    for modifier in needed:
        if modifier not in modifiers:
            # The layout uses a modifier that is not bound to any key
            return None
        modifier_codes.append(modifiers[modifier])

    return tuple(modifier_codes), key_code


class LayoutKeymap:
    # The keymap changes when the user switches layouts, so the snapshot is only
    # reused for long enough to cover a single write
    CACHE_TTL = 0.5
    # Building has to happen on the main thread, don't block a tick thread for
    # longer than this if the main loop is busy
    BUILD_TIMEOUT = 0.5

    def __init__(self):
        self._lock = threading.Lock()
        self._table: LayoutTable | None = None
        self._built_at: float = 0.0

    def get_table(self) -> LayoutTable | None:
        with self._lock:
            if self._table is not None and time.monotonic() - self._built_at < self.CACHE_TTL:
                return self._table

        table = self._build()
        with self._lock:
            if table is not None:
                self._table = table
                self._built_at = time.monotonic()
            # Fall back to the last known layout if the rebuild didn't work out
            return self._table

    def _build(self) -> LayoutTable | None:
        if threading.current_thread() is threading.main_thread():
            return self._build_safely()

        result: dict[str, LayoutTable | None] = {}
        done = threading.Event()

        def build():
            try:
                result["table"] = self._build_safely()
            finally:
                done.set()
            return GLib.SOURCE_REMOVE

        GLib.idle_add(build)

        if not done.wait(self.BUILD_TIMEOUT):
            log.warning("Timed out reading the keyboard layout from the main thread")
            return None
        return result.get("table")

    def _build_safely(self) -> LayoutTable | None:
        try:
            return _build_table()
        except Exception as error:
            log.error(f"Could not read the keyboard layout: {error}")
            return None


layout = LayoutKeymap()
