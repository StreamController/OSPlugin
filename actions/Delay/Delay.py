from src.backend.DeckManagement.InputIdentifier import InputEvent
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.PluginBase import PluginBase

import time
import os

# Import gtk modules
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

class Delay(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.has_configuration = True
        
    def on_ready(self):
        self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "hourglass_empty-inv.png"), size=0.8)

    def get_config_rows(self) -> list:
        self.delay_row = Adw.SpinRow().new_with_range(min=0, max=60*60*24, step=0.1)
        self.delay_row.set_title(self.plugin_base.lm.get("delay.entry.title"))
        self.delay_row.set_subtitle(self.plugin_base.lm.get("delay.entry.subtitle"))

        # Load from config
        settings = self.get_settings()
        self.delay_row.set_value(settings.get("delay", 0))

        self.delay_row.connect("changed", self.on_delay_change)

        return [self.delay_row]
    
    def on_delay_change(self, *args):
        settings = self.get_settings()
        settings["delay"] = round(self.delay_row.get_value(), 1)
        self.set_settings(settings)

    def event_callback(self, event: InputEvent, data: dict = None):
        delay = self.get_settings().get("delay", 0)
        time.sleep(delay)