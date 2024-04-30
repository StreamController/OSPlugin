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
    
    def on_ready(self):
        self.update()
        
    def on_tick(self):
        self.update()

    def update(self):
        percent = round(psutil.virtual_memory().percent)
        self.set_center_label(text=f"{percent}%", font_size=24)