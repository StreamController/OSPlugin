from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.PluginBase import PluginBase

# Import gtk modules
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gdk

import evdev

from evdev import ecodes
from selectors import DefaultSelector, EVENT_READ
from evdev import categorize, UInput

import threading
from time import sleep
import os
from PIL import Image

class Hotkey(ActionBase):
    ACTION_NAME = "Hotkey"
    CONTROLS_KEY_IMAGE = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.has_configuration = True
        
        self.pressed = False
        

    def on_ready(self):
        self.settings = self.get_settings()
        self.settings.setdefault("keys", [])
        self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "keyboard.png"))

    def get_config_rows(self) -> list:
        hotkey_row = HotkeyRow(self)

        self.delay_row = Adw.SpinRow.new_with_range(min=0, max=1, step=0.01)
        self.delay_row.set_title(self.plugin_base.lm.get("actions.hotkey.delay.title"))
        self.delay_row.set_subtitle(self.plugin_base.lm.get("actions.hotkey.delay.subtitle"))

        self.repeat_row = Adw.SwitchRow(title=self.plugin_base.lm.get("actions.hotkey.repeat.title"), subtitle=self.plugin_base.lm.get("actions.hotkey.repeat.subtitle"))
        self.hold_until_release = Adw.SwitchRow(title=self.plugin_base.lm.get("actions.hotkey.hold_until_release.title"), subtitle=self.plugin_base.lm.get("actions.hotkey.hold_until_release.subtitle"))

        self.load_config_values()

        self.delay_row.connect("changed", self.on_delay_changed)
        self.repeat_row.connect("notify::active", self.on_repeat_toggled)
        self.hold_until_release.connect("notify::active", self.on_hold_toggled)

        return [hotkey_row, self.delay_row, self.repeat_row, self.hold_until_release]
    
    def load_config_values(self):
        settings = self.get_settings()
        self.delay_row.set_value(settings.get("delay", 0.02))
        self.repeat_row.set_active(settings.get("repeat", False))
        if not self.repeat_row.get_active():
            self.hold_until_release.set_active(settings.get("hold_until_release", False))

    def on_delay_changed(self, spin_row):
        settings = self.get_settings()
        settings["delay"] = spin_row.get_value()
        self.set_settings(settings)

    def on_repeat_toggled(self, *args):
        settings = self.get_settings()
        settings["hold_until_release"] = False
        settings["repeat"] = self.repeat_row.get_active()
        self.set_settings(settings)

        self.hold_until_release.disconnect_by_func(self.on_hold_toggled)
        self.hold_until_release.set_active(False)
        self.hold_until_release.connect("notify::active", self.on_hold_toggled)

    def on_hold_toggled(self, *args):
        settings = self.get_settings()
        settings["repeat"] = False
        settings["hold_until_release"] = self.hold_until_release.get_active()
        self.set_settings(settings)

        self.repeat_row.disconnect_by_func(self.on_repeat_toggled)
        self.repeat_row.set_active(False)
        self.repeat_row.connect("notify::active", self.on_repeat_toggled)
    
    def on_key_down(self):
        self.pressed = True

        settings = self.get_settings()
        if settings.get("repeat", False):
            thread = threading.Thread(target=self.press_keys_in_loop, daemon=True, name="key_press")
            thread.start()
        elif settings.get("hold_until_release", False):
            self.press_down_keys()
        else:
            self.press_keys()




    def on_key_up(self):
        self.pressed = False

        settings = self.get_settings()
        if settings.get("hold_until_release", False):
            self.press_up_keys()


    def press_keys_in_loop(self):
        settings = self.get_settings()
        keys = settings.get("keys", [])
        delay = settings.get("delay", 0.02)
        repeat = settings.get("repeat", False)

        while self.pressed:
            for key in keys:
                self.plugin_base.ui.write(ecodes.EV_KEY, key[0], key[1])
                self.plugin_base.ui.syn()
                sleep(delay)

            if not repeat:
                break

    def press_keys(self):
        settings = self.get_settings()
        keys = settings.get("keys", [])
        delay = settings.get("delay", 0.02)

        for key in keys:
            self.plugin_base.ui.write(ecodes.EV_KEY, key[0], key[1])
            self.plugin_base.ui.syn()
            sleep(delay)

    def press_down_keys(self):
        settings = self.get_settings()
        keys = settings.get("keys", [])
        delay = settings.get("delay", 0.02)

        for key in keys:
            if key[1] == 1:
                self.plugin_base.ui.write(ecodes.EV_KEY, key[0], key[1])
                self.plugin_base.ui.syn()
                sleep(delay)

    def press_up_keys(self):
        settings = self.get_settings()
        keys = settings.get("keys", [])
        delay = settings.get("delay", 0.02)

        for key in keys:
            if key[1] == 0:
                self.plugin_base.ui.write(ecodes.EV_KEY, key[0], key[1])
                self.plugin_base.ui.syn()
                sleep(delay)

    def get_custom_config_area(self):
        if self.plugin_base.ui is not None:
            return
        
        return Gtk.Label(label="Missing permission. Please add <a href=\"https://github.com/streamcontroller/osplugin?tab=readme-ov-file#hotkeys--write-text\">this</a> udev rule", use_markup=True,
                         css_classes=["bold", "warning"])


class HotkeyRow(Adw.PreferencesRow):
    def __init__(self, hotkey: Hotkey):
        super().__init__(title="Hotkey:")
        self.hotkey = hotkey
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True)
        self.set_child(self.main_box)

        self.hotkey_label = Gtk.Label(hexpand=True, label=hotkey.plugin_base.lm.get("actions.hotkey.label"), xalign=0, margin_start=12)
        self.main_box.append(self.hotkey_label)

        self.config_button = Gtk.Button(label="Config")
        self.main_box.append(self.config_button)
        self.config_button.connect("clicked", self.on_config)

    def on_config(self, button):
        recorder = HotkeyRecorder(self)
        recorder.present()


class HotkeyRecorder(Gtk.ApplicationWindow):
    def __init__(self, hotkey_row:HotkeyRow, *args, **kwargs):
        self.GTK_CODE_DIFFERENCE = 8
        super().__init__(*args, **kwargs)
        self.hotkey_row = hotkey_row

        self.all_keys = {}
        self.all_keys.update(evdev.ecodes.KEY)
        self.all_keys.update(evdev.ecodes.BTN)

        self.set_default_size(600, 300)
        self.set_title("Hotkey Recorder")

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, focus_on_click=True, focusable=True, can_focus=True)
        self.set_child(self.main_box)

        self.explain = Gtk.Label(label="Press keys to record...", margin_top=30)
        self.main_box.append(self.explain)

        self.scrolled_window = Gtk.ScrolledWindow()
        self.main_box.append(self.scrolled_window)

        self.scrolled_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True, vexpand=True)
        self.scrolled_window.set_child(self.scrolled_box)

        self.flow_box = Gtk.FlowBox(orientation=Gtk.Orientation.HORIZONTAL, selection_mode=Gtk.SelectionMode.NONE,
                                    vexpand=False)
        self.scrolled_box.append(self.flow_box)

        # Add vexpand box to bottom to fix stretching of flowbox children
        self.scrolled_box.append(Gtk.Box(vexpand=True))

        # Hearder bar
        self.header_bar = Gtk.HeaderBar()
        self.set_titlebar(self.header_bar)

        self.confirm_button = Gtk.Button(label=self.hotkey_row.hotkey.plugin_base.lm.get("actions.hotkey.recorder.confirm-text"), css_classes=["confirm-button"])
        self.confirm_button.connect("clicked", self.on_confirm)
        self.header_bar.pack_end(self.confirm_button)

        self.clear_button = Gtk.Button(label=self.hotkey_row.hotkey.plugin_base.lm.get("actions.hotkey.recorder.clear-text"), css_classes=["remove-button"])
        self.header_bar.pack_start(self.clear_button)
        self.clear_button.connect("clicked", self.on_clear)

        self.load_defaults()

        # Key Controller
        self.key_controller = Gtk.EventControllerKey()
        self.key_controller.connect("key-pressed", self.on_key_down)
        self.key_controller.connect("key-released", self.on_key_up)
        self.add_controller(self.key_controller)

        display = self.get_display()
        self.seat: Gdk.Seat = display.get_default_seat()
        # self.seat.grab(
            # self, Gdk.SeatCapabilities.KEYBOARD, False, None, None, None
        # )

        self.special_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True, vexpand=False,
                                   margin_start=10, margin_end=10, margin_top=10, margin_bottom=10)
        self.main_box.append(self.special_box)

        self.special_box.append(Gtk.Label(label="Special Keys:", margin_end=8))

        self.special_box_flow = Gtk.FlowBox(orientation=Gtk.Orientation.HORIZONTAL, selection_mode=Gtk.SelectionMode.NONE, hexpand=True)
        self.special_box.append(self.special_box_flow)

        special_keys = []
        for i in range(183, 195):
            special_keys.append(i)

        special_keys.append(ecodes.KEY_LEFTMETA)

        for i in special_keys:
            self.special_box_flow.append(SpecialKeyButton(self, self.all_keys[i], i))

        self.connect("destroy", self.on_destroy)

    def on_confirm(self, button):
        self.close()
        self.destroy()

    def on_destroy(self, *args):
        self.seat.ungrab()

    def on_key_down(self, controller, keyval, keycode, state):
        self.add_key(keycode, 1)

        # Notify app that key press was handled
        return True

    def on_key_up(self, controller, keyval, keycode, state):
        self.add_key(keycode, 0)
        
        # Notify app that key press was handled
        return True

    def add_key(self, key_code, state):
        key_code -= self.GTK_CODE_DIFFERENCE
        key_name = self.all_keys[key_code]
        self.flow_box.append(PressIndicator(key_name, state == 1, state == 0))
        self.hotkey_row.hotkey.settings["keys"].append([key_code, state])
        self.hotkey_row.hotkey.set_settings(self.hotkey_row.hotkey.settings)

    def load_defaults(self):
        for key in self.hotkey_row.hotkey.settings.get("keys", []):
            key_name = self.all_keys[key[0]]
            if isinstance(key_name, list):
                key_name = key_name[0]
            self.flow_box.append(PressIndicator(key_name, key[1] == 1, key[1] == 0))

    def on_clear(self, button):
        self.hotkey_row.hotkey.settings["keys"] = []
        self.hotkey_row.hotkey.set_settings(self.hotkey_row.hotkey.settings)

        # Clear ui
        while self.flow_box.get_first_child() is not None:
            self.flow_box.remove(self.flow_box.get_first_child())


class SpecialKeyButton(Gtk.Box):
    def __init__(self, recorder: HotkeyRecorder, key_name:str, key_code:int):
        """
        Why not use a Gtk.Button? Because the button doesn't support separate press and release event handling
        """
        super().__init__(css_classes=["com_core447_OSPlugin-SpecialKeyButton"])

        self.label = Gtk.Label(label=key_name, css_classes=["bold"])
        self.append(self.label)

        self.recorder = recorder
        self.key_name = key_name
        self.key_code = key_code

        self.gesture_ctrl = Gtk.GestureClick()

        self.gesture_ctrl.connect("pressed", self.on_press)
        self.gesture_ctrl.connect("released", self.on_release)

        self.add_controller(self.gesture_ctrl)

    def on_press(self, button, *args):
        print(f"Pressed: {self.key_name}")
        self.recorder.add_key(self.key_code + self.recorder.GTK_CODE_DIFFERENCE, 1)
        # self.recorder.add_key(self.key_code + self.recorder.GTK_CODE_DIFFERENCE, 0)

    def on_release(self, button, *args):
        print(f"Released: {self.key_name}")
        self.recorder.add_key(self.key_code + self.recorder.GTK_CODE_DIFFERENCE, 0)


class PressIndicator(Gtk.FlowBoxChild):
    def __init__(self, key_name:str, down:bool = False, up:bool = False):
        super().__init__(hexpand=False, vexpand=False, height_request=20, width_request=20)

        self.key_name = key_name
        self.up = up
        self.down = down

        self.build()

    def build(self):
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=False, vexpand=False)
        self.set_child(self.main_box)
        
        self.top_box = Gtk.Box(height_request=25, width_request=20, hexpand=False, halign=Gtk.Align.CENTER)
        self.main_box.append(self.top_box)

        self.top_icon = Gtk.Image(margin_top=0, margin_bottom=0).new_from_icon_name("pan-up")
        self.top_icon.set_visible(self.up)
        self.top_icon.set_halign(Gtk.Align.CENTER)
        self.top_box.append(self.top_icon)

        self.label = Gtk.Label(label=self.key_name, hexpand=False, css_classes=["hotkey-editor-key-label"],
                               margin_top=0, margin_bottom=0)
        self.main_box.append(self.label)

        self.bottom_box = Gtk.Box(height_request=25, width_request=20, hexpand=False, halign=Gtk.Align.CENTER)
        self.main_box.append(self.bottom_box)

        self.bottom_icon = Gtk.Image(margin_top=0, margin_bottom=0).new_from_icon_name("pan-down")
        self.bottom_icon.set_visible(self.down)
        self.bottom_icon.set_halign(Gtk.Align.CENTER)
        self.bottom_box.append(self.bottom_icon)