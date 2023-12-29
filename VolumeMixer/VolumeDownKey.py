from src.backend.PluginManager.ActionBase import ActionBase
import globals as gl
from loguru import logger as log

import os
from PIL import Image

class DownKey(ActionBase):
    ACTION_NAME = "Volume Mixer Down Key"
    CONTROLS_KEY_IMAGE = False

    def __init__(self, deck_controller, page, coords):
        super().__init__(deck_controller, page, coords)
        self.PLUGIN_BASE.volume_actions.append(self)

        self.showing_image = False
        self.icon_path = os.path.join(self.PLUGIN_BASE.PATH, "assets", "volume_down.png")

    def on_tick(self):
        index = self.get_index()

        inputs = self.PLUGIN_BASE.pulse.sink_input_list()
        if index < len(inputs):
            if not self.showing_image:
                self.set_key(media_path=self.icon_path)
                self.showing_image = True

        else:
            self.clear()

    def clear(self):
        if not self.showing_image:
            return
        self.set_key(image=None)

    def on_key_down(self):
        # Toggle mute
        inputs = self.PLUGIN_BASE.pulse.sink_input_list()

        index = self.get_index()
        if index >= len(inputs):
            return
        
        volume = inputs[index].volume.value_flat
        volume -= self.PLUGIN_BASE.volume_increment

        self.PLUGIN_BASE.pulse.volume_set_all_chans(obj=inputs[index], vol=min(1, volume))

    def get_index(self) -> int:
        start_index = self.PLUGIN_BASE.start_index
        own_index = self.coords[0]
        index = start_index + own_index - 1 # -1 because we want to ignore the first column containing the navigation keys
        return index