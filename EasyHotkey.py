from .actions.WriteText.helper import press_key_combination
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


class EasyHotkey(ActionBase):
    ACTION_NAME = "Hotkey from text"
    CONTROLS_KEY_IMAGE = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def on_ready(self):
        self.settings = self.get_settings()
        self.settings.setdefault("hotkey", "")
        self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "keyboard.png"))

    def get_config_rows(self) -> list:
        self.hotkey_row = Adw.EntryRow(title="Hotkey")

        self.delay_row = Adw.SpinRow.new_with_range(min=0, max=1, step=0.01)
        self.delay_row.set_title(self.plugin_base.lm.get("actions.hotkey.delay.title"))
        self.delay_row.set_subtitle(self.plugin_base.lm.get("actions.hotkey.delay.subtitle"))

        self.load_config_values()

        self.hotkey_row.connect("changed", self.on_hotkey_changed)
        self.delay_row.connect("changed", self.on_delay_changed)

        return [self.hotkey_row, self.delay_row]
    
    def on_hotkey_changed(self, entry_row):
        settings = self.get_settings()
        settings["hotkey"] = entry_row.get_text()
        self.set_settings(settings)
    
    def load_config_values(self):
        settings = self.get_settings()
        self.hotkey_row.set_text(settings.get("hotkey", "") or "")
        self.delay_row.set_value(settings.get("delay", 0.02))

    def on_delay_changed(self, spin_row):
        settings = self.get_settings()
        settings["delay"] = spin_row.get_value()
        self.set_settings(settings)

    def on_key_down(self):
        settings = self.get_settings()
        hotkey = settings.get("hotkey")
        if hotkey in [None, ""]:
            return
        press_key_combination(ui=self.plugin_base.ui, key_combination=hotkey, delay=settings.get("delay", 0.02))