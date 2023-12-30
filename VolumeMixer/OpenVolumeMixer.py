from src.backend.PluginManager.ActionBase import ActionBase
import globals as gl
from loguru import logger as log

import os
from PIL import Image

# Import gtk modules
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

class OpenVolumeMixer(ActionBase):
    ACTION_NAME = "Open Volume Mixer"
    CONTROLS_KEY_IMAGE = False

    def __init__(self, deck_controller, page, coords):
        super().__init__(deck_controller, page, coords)
        icon_path = os.path.join(self.PLUGIN_BASE.PATH, "assets", "equalizer.png")
        self.set_default_image(Image.open(icon_path))

    def on_ready(self):
        pass
        

    def on_key_down(self):
        # Reset position
        self.PLUGIN_BASE.start_index = 0

        page_path = os.path.join(self.PLUGIN_BASE.PATH, "VolumeMixer", "VolumeMixer.json")
        if not os.path.exists(page_path):
            log.error("Could not find volume mixer page. Consider reinstalling the plugin.")
            return
        page = gl.page_manager.get_page(path=page_path, deck_controller=self.deck_controller)
        if page is None:
            log.error("Could not create volume mixer page object. Consider reinstalling the plugin.")

        self.PLUGIN_BASE.original_page_path = self.deck_controller.active_page.json_path
        self.deck_controller.load_page(page)

    def get_config_rows(self) -> list:
        self.increments_row = Adw.SpinRow.new_with_range(min=0, max=100, step=5)
        self.increments_row.set_title("Increments (%):")

        # Load default
        settings = self.get_settings()
        self.increments_row.set_value(settings.get("increments", 10))
        self.PLUGIN_BASE.volume_increment = self.increments_row.get_value() / 100

        # Connect signal
        self.increments_row.connect("changed", self.on_increments_change)

        return [self.increments_row]
    
    def on_increments_change(self, row):
        settings = self.get_settings()
        settings["increments"] = row.get_value()
        self.PLUGIN_BASE.volume_increment = row.get_value() / 100
        self.set_settings(settings)