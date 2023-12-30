from src.backend.PluginManager.ActionBase import ActionBase
import globals as gl
from loguru import logger as log

import os
from PIL import Image, ImageEnhance

class DownKey(ActionBase):
    ACTION_NAME = "Volume Mixer Down Key"
    CONTROLS_KEY_IMAGE = True

    def __init__(self, deck_controller, page, coords):
        super().__init__(deck_controller, page, coords)
        self.PLUGIN_BASE.volume_actions.append(self)

        self.current_state = -1

        self.icon_path = os.path.join(self.PLUGIN_BASE.PATH, "assets", "volume_down.png")

    def on_tick(self):
        index = self.get_index()

        inputs = self.PLUGIN_BASE.pulse.sink_input_list()
        if index >= len(inputs):
            self.show_state(0)
        else:
            if self.can_go_lower():
                self.show_state(1)
            else:
                self.show_state(2)

    def can_go_lower(self) -> bool:
        index = self.get_index()
        inputs = self.PLUGIN_BASE.pulse.sink_input_list()
        if index >= len(inputs):
            return False
        current_vol = inputs[index].volume.value_flat
        if current_vol > 0:
            return True
        return False

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

        self.PLUGIN_BASE.pulse.volume_set_all_chans(obj=inputs[index], vol=max(0, volume))

    def get_index(self) -> int:
        start_index = self.PLUGIN_BASE.start_index
        own_index = self.coords[0]
        index = start_index + own_index - 1 # -1 because we want to ignore the first column containing the navigation keys
        return index
    
    def show_state(self, state: int) -> None:
        """
        0: No player
        1: Can go down
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
            self.set_bottom_label("Down", font_size=12)
            self.set_key(media_path=self.icon_path, margins=[10, 5, 10, 15])
            return
        elif state == 2:
            brightness = 0.65
            self.set_bottom_label("Min", font_size=12)

        # Set image with modified brightness
        image = Image.open(self.icon_path)
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(brightness)

        self.set_key(image=image, margins=[10, 5, 10, 15])