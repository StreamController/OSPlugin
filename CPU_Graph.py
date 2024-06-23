from plugins.com_core447_OSPlugin.GraphBase import GraphBase
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.PluginBase import PluginBase

import psutil

from PIL import Image

class CPU_Graph(GraphBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_configuration = False

    def on_tick(self):
        self.percentages.append(psutil.cpu_percent())
        self.show_graph()