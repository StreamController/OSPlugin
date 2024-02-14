from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.PluginBase import PluginBase

import os
from PIL import Image, ImageEnhance

class MoveLeft(ActionBase):
    def __init__(self, action_id: str, action_name: str,
                 deck_controller: "DeckController", page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
            deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)

        self.current_state = -1

        self.icon_path = os.path.join(self.plugin_base.PATH, "assets", "navigate_before.png")

    def on_ready(self):
        self.on_tick()

    def on_tick(self):
        number_of_players = len(self.plugin_base.pulse.sink_input_list())
        player_columns = self.deck_controller.deck.key_layout()[1] -1 # -1 because we want to ignore the first column containing the navigation keys
        start_index = self.plugin_base.start_index

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
        self.plugin_base.start_index += 1

        for action in self.plugin_base.volume_actions:
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