from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.PluginBase import PluginBase

import time

# Import gtk modules
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

class Delay(ActionBase):
    def __init__(self, action_id: str, action_name: str,
                 deck_controller: "DeckController", page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
            deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)

    def get_config_rows(self) -> list:
        self.delay_row = Adw.SpinRow().new_with_range(min=0, max=10, step=0.1)
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

    def on_key_down(self):
        delay = self.get_settings().get("delay", 0)
        time.sleep(delay)