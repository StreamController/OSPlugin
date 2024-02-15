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

from evdev import ecodes as e
from selectors import DefaultSelector, EVENT_READ
from evdev import categorize, UInput

import threading
from time import sleep

class Hotkey(ActionBase):
    ACTION_NAME = "Hotkey"
    CONTROLS_KEY_IMAGE = False

    def __init__(self, action_id: str, action_name: str,
                 deck_controller: "DeckController", page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
            deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)
    def on_ready(self):
        self.settings = self.get_settings()
        self.settings.setdefault("keys", [])

    def get_config_rows(self) -> list:
        hotkey_row = HotkeyRow(self)

        return [hotkey_row]
    
    def on_key_down(self):
        for key in self.settings.get("keys", []):
            self.plugin_base.ui.write(e.EV_KEY, key[0], key[1])
            self.plugin_base.ui.syn()



class HotkeyRow(Adw.PreferencesRow):
    def __init__(self, hotkey: Hotkey):
        super().__init__(title="Hotkey:")
        self.hotkey = hotkey
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True)
        self.set_child(self.main_box)

        self.hotkey_label = Gtk.Label(hexpand=True)
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

        self.confirm_button = Gtk.Button(label="Confirm", css_classes=["confirm-button"])
        self.confirm_button.connect("clicked", self.on_confirm)
        self.header_bar.pack_end(self.confirm_button)

        self.clear_button = Gtk.Button(label="Clear", css_classes=["remove-button"])
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