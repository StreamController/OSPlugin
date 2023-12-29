from src.backend.PluginManager.ActionBase import ActionBase
import globals as gl
from loguru import logger as log

import os
from PIL import Image

class ExitVolumeMixer(ActionBase):
    ACTION_NAME = "Exit Volume Mixer"
    CONTROLS_KEY_IMAGE = False

    def on_ready(self):
        icon_path = os.path.join(self.PLUGIN_BASE.PATH, "assets", "back.png")
        self.set_default_image(Image.open(icon_path))

    def on_key_down(self):
        page_path = self.PLUGIN_BASE.original_page_path
        if page_path is None:
            log.warning("No original page path to return to.")
            return
        if not os.path.exists(page_path):
            log.error("Could not find original page - cannot exit volume mixer.")
            return
        page = gl.page_manager.get_page(path=page_path, deck_controller=self.deck_controller)
        if page is None:
            log.error("Could not create original page - cannot exit volume mixer.")

        self.PLUGIN_BASE.original_page_path = None
        self.deck_controller.load_page(page)