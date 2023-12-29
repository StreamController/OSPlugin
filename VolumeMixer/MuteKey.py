from src.backend.PluginManager.ActionBase import ActionBase
import globals as gl
from loguru import logger as log

import os

class MuteKey(ActionBase):
    ACTION_NAME = "Volume Mixer Mute Key"
    CONTROLS_KEY_IMAGE = True

    def __init__(self, deck_controller, page, coords):
        super().__init__(deck_controller, page, coords)
        self.PLUGIN_BASE.volume_actions.append(self)

    def on_tick(self):
        index = self.get_index()

        inputs = self.PLUGIN_BASE.pulse.sink_input_list()
        if index < len(inputs):
            self.set_label(text=inputs[index].name, position="center", font_size=10)
        else:
            self.clear()

    def clear(self):
        self.set_label(text="no player", position="center", font_size=10)

    def on_key_down(self):
        # Toggle mute
        inputs = self.PLUGIN_BASE.pulse.sink_input_list()

        index = self.get_index()
        if index >= len(inputs):
            return
        
        mute = inputs[index].mute == 0
        self.PLUGIN_BASE.pulse.mute(obj=inputs[index], mute=mute)

    def get_index(self) -> int:
        start_index = self.PLUGIN_BASE.start_index
        own_index = self.coords[0]
        index = start_index + own_index - 1 # -1 because we want to ignore the first column containing the navigation keys
        return index