"""
This code is from streamdeck-ui-gui: https://github.com/streamdeck-linux-gui/streamdeck-linux-gui
"""

from .mappings import _SUPPORTED_KEYS, _SPECIAL_KEYS, _OLD_NUMPAD_KEYS, _OLD_PYNPUT_KEYS, _MODIFIER_KEYS, _KEY_MAPPING, _SHIFT_KEY_MAPPING

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

def keyboard_write(ui: UInput, text: str, delay: float = 0.01):
    caps_lock_is_on = check_caps_lock()
    for char in text:
        is_unicode = False
        unicode_bytes = char.encode("unicode_escape")
        # '\u' or '\U' for unicode, or '\x' for UTF-8
        if unicode_bytes[0] == 92 and unicode_bytes[1] in [85, 117, 120]:
            is_unicode = True

        if char in _KEY_MAPPING:
            keycode = _KEY_MAPPING[char]
            need_shift = False

            if char in _SHIFT_KEY_MAPPING:
                need_shift = True

            if char.isalpha() and caps_lock_is_on:
                need_shift = not need_shift

            if need_shift:
                ui.write(e.EV_KEY, e.KEY_LEFTSHIFT, 1)

            ui.write(e.EV_KEY, keycode, 1)
            ui.write(e.EV_KEY, keycode, 0)

            if need_shift:
                ui.write(e.EV_KEY, e.KEY_LEFTSHIFT, 0)

            # send keys
            ui.syn()
            time.sleep(delay)
        elif is_unicode:
            unicode_hex = hex(int(unicode_bytes[2:], 16))
            unicode_hex_keys = unicode_hex[2:]

            # hold shift + ctrl
            ui.write(e.EV_KEY, e.KEY_LEFTSHIFT, 1)
            ui.write(e.EV_KEY, e.KEY_LEFTCTRL, 1)

            # press 'U' to initiate unicode sequence
            ui.write(e.EV_KEY, e.KEY_U, 1)
            ui.write(e.EV_KEY, e.KEY_U, 0)

            # press unicode codepoint keys
            for hex_char in unicode_hex_keys:
                keycode = _KEY_MAPPING[hex_char]
                ui.write(e.EV_KEY, keycode, 1)
                ui.write(e.EV_KEY, keycode, 0)

            # release shift + ctrl
            ui.write(e.EV_KEY, e.KEY_LEFTSHIFT, 0)
            ui.write(e.EV_KEY, e.KEY_LEFTCTRL, 0)

            # send keys
            ui.syn()
        else:
            log.warning(f"Unsupported character: {char}")