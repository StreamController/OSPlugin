from plugins.dev_core447_OSPlugin.GraphBase import GraphBase
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.PluginBase import PluginBase

import psutil

from PIL import Image

class RAM_Graph(GraphBase):
    ACTION_NAME = "RAM Graph"
    CONTROLS_KEY_IMAGE = True

    def __init__(self, action_id: str, action_name: str,
                 deck_controller: "DeckController", page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
            deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)

    def on_tick(self):
        self.percentages.append(psutil.virtual_memory().percent)
        self.show_graph()