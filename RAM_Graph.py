from plugins.dev_core447_OSPlugin.GraphBase import GraphBase

import psutil

from PIL import Image

class RAM_Graph(GraphBase):
    ACTION_NAME = "RAM Graph"
    CONTROLS_KEY_IMAGE = True

    def __init__(self, deck_controller, page, coords):
        super().__init__(deck_controller=deck_controller, page=page, coords=coords)

    def on_tick(self):
        self.percentages.append(psutil.virtual_memory().percent)
        self.set_percentages_lenght(15)

        self.set_key(image=self.get_graph())