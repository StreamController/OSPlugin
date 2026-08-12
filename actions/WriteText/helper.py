"""
This code is from streamdeck-ui-gui: https://github.com/streamdeck-linux-gui/streamdeck-linux-gui
"""

from .mappings import _SUPPORTED_KEYS, _SPECIAL_KEYS, _OLD_NUMPAD_KEYS, _OLD_PYNPUT_KEYS, _MODIFIER_KEYS, _KEY_MAPPING, _SHIFT_KEY_MAPPING, _ALL_KEYS_DICT, _MASTER_DICT
from .layout import LayoutTable, layout

from evdev import InputDevice, UInput, list_devices
from evdev import ecodes as e

from loguru import logger as log
import time

def get_valid_key_names() -> list[str]:
    """Returns a list of valid key names."""
    key_names = [key for key in _SUPPORTED_KEYS]
    key_names.extend(_SPECIAL_KEYS.keys())
    key_names.extend(_OLD_NUMPAD_KEYS.keys())
    key_names.extend(_OLD_PYNPUT_KEYS.keys())
    key_names.extend(_MODIFIER_KEYS.keys())
    return sorted(key_names)

def check_caps_lock() -> bool:
    """Returns True if Caps Lock is on, False if it is off, and False if it cannot be determined."""
    devices = [InputDevice(path) for path in list_devices()]
    for device in devices:
        if device.capabilities().get(e.EV_LED):
            return e.LED_CAPSL in device.leds()
    return False

def get_keystrokes(table: LayoutTable | None, char: str) -> list[tuple[tuple[int, ...], int]] | None:
    """The key presses that type char, or None if the keyboard cannot reach it"""
    if table is not None:
        return table.keystrokes.get(char)

    # No layout to ask, assume the US one the mappings were written for
    keycode = _KEY_MAPPING.get(char)
    if keycode is None:
        return None
    modifier_codes = (e.KEY_LEFTSHIFT,) if char in _SHIFT_KEY_MAPPING else ()
    return [(modifier_codes, keycode)]


def _write_key(ui: UInput, modifier_codes: tuple[int, ...], keycode: int):
    for modifier_code in modifier_codes:
        ui.write(e.EV_KEY, modifier_code, 1)

    ui.write(e.EV_KEY, keycode, 1)
    ui.write(e.EV_KEY, keycode, 0)

    for modifier_code in reversed(modifier_codes):
        ui.write(e.EV_KEY, modifier_code, 0)

    # send keys
    ui.syn()


def _write_unicode(ui: UInput, char: str):
    """
    Last resort for characters the keyboard has no key for: the ctrl+shift+u
    sequence input methods listen for.
    """
    if not char.isprintable():
        log.warning(f"Unsupported character: {char}")
        return

    # hold shift + ctrl
    ui.write(e.EV_KEY, e.KEY_LEFTSHIFT, 1)
    ui.write(e.EV_KEY, e.KEY_LEFTCTRL, 1)

    # press 'U' to initiate unicode sequence
    ui.write(e.EV_KEY, e.KEY_U, 1)
    ui.write(e.EV_KEY, e.KEY_U, 0)

    # press unicode codepoint keys
    for hex_char in f"{ord(char):x}":
        keycode = _KEY_MAPPING[hex_char]
        ui.write(e.EV_KEY, keycode, 1)
        ui.write(e.EV_KEY, keycode, 0)

    # release shift + ctrl
    ui.write(e.EV_KEY, e.KEY_LEFTSHIFT, 0)
    ui.write(e.EV_KEY, e.KEY_LEFTCTRL, 0)

    # send keys
    ui.syn()


def keyboard_write(ui: UInput, text: str, delay: float = 0.01):
    caps_lock_is_on = check_caps_lock()
    table = layout.get_table()
    shift_code = table.shift_code if table is not None else e.KEY_LEFTSHIFT

    for char in text:
        keystrokes = get_keystrokes(table, char)

        if keystrokes is None:
            _write_unicode(ui, char)
            time.sleep(delay)
            continue

        # With caps lock on the keyboard hands out the other case of a letter,
        # so the shift we would use has to be flipped
        flip_shift = caps_lock_is_on and char.isalpha() and shift_code is not None

        for modifier_codes, keycode in keystrokes:
            if flip_shift:
                if shift_code in modifier_codes:
                    modifier_codes = tuple(code for code in modifier_codes if code != shift_code)
                else:
                    modifier_codes = modifier_codes + (shift_code,)

            _write_key(ui, modifier_codes, keycode)

        time.sleep(delay)

def parse_key_combination(key_combination: str) -> list[int]:
    keys = key_combination.lower().split('+')
    table = layout.get_table()
    parsed_keys = []
    for key in keys:
        mapped = _MASTER_DICT.get(key)

        # A few names in _SPECIAL_KEYS stand for a character
        char = key if len(key) == 1 else mapped if isinstance(mapped, str) and len(mapped) == 1 else None

        # Characters have to be looked up in the active layout - the key that
        # types "z" sits in a different place on every keyboard
        if char is not None:
            keystrokes = get_keystrokes(table, char)
            if keystrokes is not None and len(keystrokes) == 1:
                modifier_codes, keycode = keystrokes[0]
                parsed_keys.extend(modifier_codes)
                parsed_keys.append(keycode)
                continue

        if isinstance(mapped, int):
            parsed_keys.append(mapped)
        else:
            log.error(f"Unsupported key: {key}")
            # raise ValueError(f"Unsupported key: {key}")

    # Holding the same key twice would only confuse the receiving application
    return list(dict.fromkeys(parsed_keys))

# Function to press and release keys
def press_key_combination(ui: UInput, key_combination: str, delay: float = 0.01):
    keycodes = parse_key_combination(key_combination)
    
    # Press each key in the combination
    for keycode in keycodes:
        ui.write(e.EV_KEY, keycode, 1)  # Key down
    ui.syn()
    
    # Short delay between press and release
    time.sleep(delay)
    
    # Release each key in the combination
    for keycode in keycodes:
        ui.write(e.EV_KEY, keycode, 0)  # Key up
    ui.syn()

# text = "Hello, World!"
# from evdev import ecodes
# ui = UInput({ecodes.EV_KEY: range(0, 300),
            # ecodes.EV_REL: [ecodes.REL_X, ecodes.REL_Y]}, name="stream-controller-os-plugin")
# keyboard_write(ui, text)