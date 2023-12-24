from plugins.dev_core447_OSPlugin.GraphBase import GraphBase

import psutil

from PIL import Image

class CPU_Graph(GraphBase):
    ACTION_NAME = "CPU Graph"
    CONTROLS_KEY_IMAGE = True

    def __init__(self, deck_controller, page, coords):
        super().__init__(deck_controller=deck_controller, page=page, coords=coords)

    def on_tick(self):
        self.percentages.append(psutil.cpu_percent())
        self.show_graph()