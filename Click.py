# Import StreamController modules
import time
from GtkHelper.ComboRow import SimpleComboRowItem
from GtkHelper.GenerativeUI.ComboRow import ComboRow
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

class Click(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_configuration = True

        self.button_row = ComboRow(
            action_core=self,
            var_name="button",
            default_value="left",
            items=[SimpleComboRowItem("left", "Left"), SimpleComboRowItem("middle", "Middle"), SimpleComboRowItem("right", "Right")],
            title="Button",
            can_reset=False
        )
        
    def on_ready(self) -> None:
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "click.png")
        self.set_media(media_path=icon_path, size=0.75)

    def on_key_down(self):
        if self.plugin_base.ui is None:
            self.show_error(1)
            return
        
        button = ecodes.BTN_LEFT
        if self.button_row.get_value() == "middle":
            button = ecodes.BTN_MIDDLE
        elif self.button_row.get_value() == "right":
            button = ecodes.BTN_RIGHT


        self.plugin_base.ui.write(ecodes.EV_KEY, button, 1)
        self.plugin_base.ui.syn()
        time.sleep(0.01)
        self.plugin_base.ui.write(ecodes.EV_KEY, button, 0)
        self.plugin_base.ui.syn()

    def get_custom_config_area(self):
        if self.plugin_base.ui is not None:
            return
        
        return Gtk.Label(label="Missing permission. Please add <a href=\"https://github.com/streamcontroller/osplugin?tab=readme-ov-file#hotkeys--write-text\">this</a> udev rule", use_markup=True,
                         css_classes=["bold", "warning"])