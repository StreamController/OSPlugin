from plugins.com_core447_OSPlugin.GraphBase import GraphBase
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.PluginBase import PluginBase

import psutil

from PIL import Image

class RAM_Graph(GraphBase):
    ACTION_NAME = "RAM Graph"
    CONTROLS_KEY_IMAGE = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_configuration = False

    def on_tick(self):
        self.percentages.append(psutil.virtual_memory().percent)
        self.show_graph()