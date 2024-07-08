# Import StreamController modules
import time
from GtkHelper.ItemListComboRow import ItemListComboRow, ItemListComboRowListItem
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
        
    def on_ready(self) -> None:
        icon_path = os.path.join(self.plugin_base.PATH, "assets", "click.png")
        self.set_media(media_path=icon_path, size=0.75)

    def on_key_down(self):
        if self.plugin_base.ui is None:
            self.show_error(1)
            return
        
        settings = self.get_settings()

        button = ecodes.BTN_LEFT
        if settings.get("button") == "middle":
            button = ecodes.BTN_MIDDLE
        elif settings.get("button") == "right":
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
    
    def get_config_rows(self):
        self.buttons = [ItemListComboRowListItem("left", "Left"), ItemListComboRowListItem("middle", "Middle"), ItemListComboRowListItem("right", "Right")]
        self.button_row = ItemListComboRow(self.buttons, title="Button")

        self.load_config_values()

        self.button_row.connect("notify::selected", self.on_receive_type_changed)

        return self.button_row,

    def load_config_values(self):
        settings = self.get_settings()
        self.button_row.set_selected_item_by_key(settings.get("button", "left"))

    def on_receive_type_changed(self, entry, *args):
        settings = self.get_settings()
        settings["button"] = entry.get_selected_item().key
        self.set_settings(settings)