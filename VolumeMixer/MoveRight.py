from src.backend.PluginManager.ActionBase import ActionBase

import os
from PIL import Image

class MoveRight(ActionBase):
    ACTION_NAME = "Volume Mixer Move Right"
    CONTROLS_KEY_IMAGE = False

    def on_ready(self):
        icon_path = os.path.join(self.PLUGIN_BASE.PATH, "assets", "navigate_next.png")
        self.set_default_image(Image.open(icon_path))

    def on_key_down(self):
        # Toggle mute
        self.PLUGIN_BASE.start_index = max(0, self.PLUGIN_BASE.start_index - 1)

        for action in self.PLUGIN_BASE.volume_actions:
            action.on_tick()