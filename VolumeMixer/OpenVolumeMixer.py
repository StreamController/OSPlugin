from src.backend.PluginManager.ActionBase import ActionBase
import globals as gl
from loguru import logger as log

import os
from PIL import Image

class OpenVolumeMixer(ActionBase):
    ACTION_NAME = "Open Volume Mixer"
    CONTROLS_KEY_IMAGE = False

    def on_ready(self):
        icon_path = os.path.join(self.PLUGIN_BASE.PATH, "assets", "equalizer.png")
        self.set_default_image(Image.open(icon_path))

    def on_key_down(self):
        page_path = os.path.join(self.PLUGIN_BASE.PATH, "VolumeMixer", "VolumeMixer.json")
        if not os.path.exists(page_path):
            log.error("Could not find volume mixer page. Consider reinstalling the plugin.")
            return
        page = gl.page_manager.get_page(path=page_path, deck_controller=self.deck_controller)
        if page is None:
            log.error("Could not create volume mixer page object. Consider reinstalling the plugin.")

        self.PLUGIN_BASE.original_page_path = self.deck_controller.active_page.json_path
        self.deck_controller.load_page(page)