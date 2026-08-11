from plugins.com_core447_OSPlugin.LabelPosition import create_position_row, set_positioned_label
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.PluginBase import PluginBase

import time
import os
import psutil

# Import gtk modules
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

class RAM(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_configuration = False

        self.position_row = create_position_row(self, on_change=lambda *args: self.update())

    def on_ready(self):
        self.update()

    def on_tick(self):
        self.update()

    def update(self):
        percent = round(psutil.virtual_memory().percent)
        set_positioned_label(self, self.position_row, f"{percent}%", center_font_size=24)
