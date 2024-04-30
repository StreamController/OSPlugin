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

from loguru import logger as log

import pyclip

import threading
from time import sleep
import os
from PIL import Image

from .helper import keyboard_write

class WriteText(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.HAS_CONFIGURATION = True
        
    def on_ready(self):
        self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "keyboard.png"))

    def get_custom_config_area(self):
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True, vexpand=True, margin_top=5, margin_bottom=5, margin_start=5, margin_end=5)

        self.main_box.append(Gtk.Label(label="Text:", xalign=0, css_classes=["com_core447_OSPlugin-header"],
                                       margin_bottom=15))

        self.text_view = Gtk.TextView(editable=True, wrap_mode=Gtk.WrapMode.WORD_CHAR,
                                      hexpand=True, vexpand=True)
        self.main_box.append(self.text_view)
        self.buffer = self.text_view.get_buffer()

        self.load_defaults()

        self.buffer.connect("changed", self.on_change)
        
        return self.main_box
    
    def load_defaults(self):
        settings = self.get_settings()
        self.buffer.set_text(settings.get("text", ""))
    
    def on_change(self, buffer):
        settings = self.get_settings()
        settings["text"] = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
        self.set_settings(settings)

    def on_key_down(self) -> None:
        settings = self.get_settings()
        text = settings.get("text")
        if text is None:
            return
        
        if self.plugin_base.ui is None:
            self.show_error(1)
            return
        
        keyboard_write(self.plugin_base.ui, text)