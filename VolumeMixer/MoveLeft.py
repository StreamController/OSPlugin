from src.backend.PluginManager.ActionBase import ActionBase

import os
from PIL import Image

class MoveLeft(ActionBase):
    ACTION_NAME = "Volume Mixer Move Left"
    CONTROLS_KEY_IMAGE = False

    def on_ready(self):
        icon_path = os.path.join(self.PLUGIN_BASE.PATH, "assets", "navigate_before.png")
        self.set_default_image(Image.open(icon_path))

    def on_key_down(self):
        # Toggle mute
        self.PLUGIN_BASE.start_index += 1

        for action in self.PLUGIN_BASE.volume_actions:
            action.on_tick()