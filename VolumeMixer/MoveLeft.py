from src.backend.PluginManager.ActionBase import ActionBase

import os
from PIL import Image, ImageEnhance

class MoveLeft(ActionBase):
    ACTION_NAME = "Volume Mixer Move Left"
    CONTROLS_KEY_IMAGE = True

    def __init__(self, deck_controller, page, coords):
        super().__init__(deck_controller, page, coords)

        self.current_state = -1

        self.icon_path = os.path.join(self.PLUGIN_BASE.PATH, "assets", "navigate_before.png")

    def on_ready(self):
        self.on_tick()

    def on_tick(self):
        number_of_players = len(self.PLUGIN_BASE.pulse.sink_input_list())
        player_columns = self.deck_controller.deck.key_layout()[1] -1 # -1 because we want to ignore the first column containing the navigation keys
        start_index = self.PLUGIN_BASE.start_index

        # Determine if we can go left
        if number_of_players - start_index - player_columns > -1: # -1 because we want the user to let the last column be empty
            # Show that we can go left
            self.show_state(1)
        else:
            # Show that we can't go left
            self.show_state(0)

    def on_key_down(self):
        self.on_tick()

        if self.current_state == 0:
            return
        # Change start_index
        self.PLUGIN_BASE.start_index += 1

        for action in self.PLUGIN_BASE.volume_actions:
            if action == self:
                continue
            action.on_tick()

    def show_state(self, state):
        """
        0: Greyed out
        1: Can go left
        """
        # Don't do anything if the state hasn't changed
        if self.current_state == state:
            return
        self.current_state = state
        if state == 0:
            image = Image.open(self.icon_path)
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(0.25)
            self.set_key(image=image)
        elif state == 1:
            self.set_key(media_path=self.icon_path)