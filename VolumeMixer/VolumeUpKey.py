from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.PluginBase import PluginBase

import globals as gl
from loguru import logger as log

import os
from PIL import Image, ImageEnhance

class UpKey(ActionBase):
    def __init__(self, action_id: str, action_name: str,
                 deck_controller: "DeckController", page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
            deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)
        
        self.plugin_base.volume_actions.append(self)

        self.current_state = -1

        self.icon_path = os.path.join(self.plugin_base.PATH, "assets", "volume_up.png")

    def on_tick(self):
        index = self.get_index()

        inputs = self.plugin_base.pulse.sink_input_list()
        if index >= len(inputs):
            self.show_state(0)
        else:
            if self.can_go_higher():
                self.show_state(1)
            else:
                self.show_state(2)

    def can_go_higher(self) -> bool:
        index = self.get_index()
        inputs = self.plugin_base.pulse.sink_input_list()
        if index >= len(inputs):
            return False
        current_vol = inputs[index].volume.value_flat
        if current_vol < 1:
            return True
        return False

    def clear(self):
        if not self.showing_image:
            return
        self.set_key(image=None)

    def on_key_down(self):
        # Toggle mute
        inputs = self.plugin_base.pulse.sink_input_list()

        index = self.get_index()
        if index >= len(inputs):
            return
        
        volume = inputs[index].volume.value_flat
        volume += self.plugin_base.volume_increment

        self.plugin_base.pulse.volume_set_all_chans(obj=inputs[index], vol=min(1, volume))

    def get_index(self) -> int:
        start_index = self.plugin_base.start_index
        own_index = self.coords[0]
        index = start_index + own_index - 1 # -1 because we want to ignore the first column containing the navigation keys
        return index
    
    def show_state(self, state: int) -> None:
        """
        0: No player
        1: Can go up
        2: Greyed out
        """
        # Don't do anything if the state hasn't changed
        if state == self.current_state:
            return
        self.current_state = state
        
        brightness = 1
        if state == 0:
            brightness = 0.25
            self.set_bottom_label("No player", font_size=12)
        elif state == 1:
            self.set_bottom_label("Up", font_size=12)
            self.set_key(media_path=self.icon_path, margins=[10, 5, 10, 15])
            return
        elif state == 2:
            brightness = 0.65
            self.set_bottom_label("Max", font_size=12)

        # Set image with modified brightness
        image = Image.open(self.icon_path)
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(brightness)

        self.set_key(image=image, margins=[10, 5, 10, 15])