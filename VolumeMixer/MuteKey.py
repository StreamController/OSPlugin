from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.PluginBase import PluginBase

import globals as gl
from loguru import logger as log

import os

class MuteKey(ActionBase):
    def __init__(self, action_id: str, action_name: str,
                 deck_controller: "DeckController", page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
            deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)
        
        self.plugin_base.volume_actions.append(self)

    def on_tick(self):
        index = self.get_index()

        inputs = self.plugin_base.pulse.sink_input_list()
        if index < len(inputs):
            self.set_label(text=inputs[index].name, position="center", font_size=10)
        else:
            self.clear()

    def clear(self):
        self.set_label(text="no player", position="center", font_size=10)

    def on_key_down(self):
        # Toggle mute
        inputs = self.plugin_base.pulse.sink_input_list()

        index = self.get_index()
        if index >= len(inputs):
            return
        
        mute = inputs[index].mute == 0
        self.plugin_base.pulse.mute(obj=inputs[index], mute=mute)

    def get_index(self) -> int:
        start_index = self.plugin_base.start_index
        own_index = self.coords[0]
        index = start_index + own_index - 1 # -1 because we want to ignore the first column containing the navigation keys
        return index