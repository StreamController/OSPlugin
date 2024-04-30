# Import StreamController modules
import time
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.PluginBase import PluginBase

# Import python modules
import os

# Import gtk modules - used for the config rows
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

from evdev import ecodes

class Click(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def on_ready(self) -> None:
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "click.png")
        self.set_media(media_path=icon_path, size=0.75)

    def on_key_down(self):
        if self.plugin_base.ui is None:
            self.show_error(1)
            return
        self.plugin_base.ui.write(ecodes.EV_KEY, ecodes.BTN_LEFT, 1)
        self.plugin_base.ui.syn()
        time.sleep(0.01)
        self.plugin_base.ui.write(ecodes.EV_KEY, ecodes.BTN_LEFT, 0)
        self.plugin_base.ui.syn()