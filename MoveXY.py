# Import StreamController modules
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.PluginBase import PluginBase

# Import python modules
import os

# Import gtk modules - used for the config rows
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

from evdev import ecodes

class MoveXY(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_configuration = False
        
    def on_ready(self) -> None:
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "mouse.png")
        self.set_media(media_path=icon_path, size=0.75)

    def get_config_rows(self):
        self.x_row = Adw.SpinRow.new_with_range(min=0, max=25000, step=1)
        self.y_row = Adw.SpinRow.new_with_range(min=0, max=25000, step=1)

        self.x_row.set_title("X")
        self.y_row.set_title("Y")

        self.load_config_values()

        self.x_row.connect("changed", self.on_coords_changed)
        self.y_row.connect("changed", self.on_coords_changed)

        return [self.x_row, self.y_row]

    def load_config_values(self):
        settings = self.get_settings()
        self.x_row.set_value(int(settings.get("x", 0)))
        self.y_row.set_value(int(settings.get("y", 0)))

    def on_coords_changed(self, *args):
        settings = self.get_settings()
        settings["x"] = int(self.x_row.get_value())
        settings["y"] = int(self.y_row.get_value())
        self.set_settings(settings)

    def on_key_down(self):
        if self.plugin_base.ui is None:
            self.show_error(1)
            return
        settings = self.get_settings()
        x = settings.get("x", 0)
        y = settings.get("y", 0)
        # Move cursor to the top left corner
        self.plugin_base.ui.write(ecodes.EV_REL, ecodes.REL_X, -25000)
        self.plugin_base.ui.write(ecodes.EV_REL, ecodes.REL_Y, -25000)
        self.plugin_base.ui.syn()
        # Move cursor
        self.plugin_base.ui.write(ecodes.EV_REL, ecodes.REL_X, x)
        self.plugin_base.ui.write(ecodes.EV_REL, ecodes.REL_Y, y)
        self.plugin_base.ui.syn()

    def get_custom_config_area(self):
        if self.plugin_base.ui is not None:
            return
        
        return Gtk.Label(label="Missing permission. Please add <a href=\"https://github.com/streamcontroller/osplugin?tab=readme-ov-file#hotkeys--write-text\">this</a> udev rule", use_markup=True,
                         css_classes=["bold", "warning"])