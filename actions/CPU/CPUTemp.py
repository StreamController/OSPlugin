from GtkHelper.ItemListComboRow import ItemListComboRow, ItemListComboRowListItem
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.PluginBase import PluginBase

import time
import os
import psutil

# Import gtk modules
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

class CPUTemp(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_configuration = False
    
    def on_ready(self):
        self.update()
        
    def on_tick(self):
        self.update()

    def get_config_rows(self):
        self.unit_row_entries = [
            ItemListComboRowListItem("C", "°C"),
            ItemListComboRowListItem("F", "°F"),
        ]
        self.unit_row = ItemListComboRow(items=self.unit_row_entries)
        self.unit_row.set_title("Temperature unit")

        self.load_configs()

        self.unit_row.connect("notify::selected", self.on_unit_changed)

        return [self.unit_row]

    def load_configs(self):
        settings = self.get_settings()

        fahrenheit = settings.get("unit", "C") == "F"
        self.unit_row.set_selected_item_by_key("F" if fahrenheit else "C")

    def on_unit_changed(self, widget, *args):
        settings = self.get_settings()
        settings["unit"] = widget.get_selected_item().key
        self.set_settings(settings)

        self.update()

    def update(self):
        temperature = psutil.sensors_temperatures()
        # intel cpu
        if "coretemp" in temperature:
            temperature = temperature.get("coretemp")[0].current
        # amd cpu
        elif "k10temp" in temperature:
            temperature = temperature.get("k10temp")
            if len(temperature) > 1:
                # zen chips and newer, Tccd1
                temperature = temperature[1].current
            else:
                # amd chips before zen, or if only Tctl is returned
                temperature = temperature[0].current
        else:
            self.set_center_label(text="N/A", font_size=18)
            return

        settings = self.get_settings()
        unit_key = settings.get("unit", "C")
        self.set_center_label(text=f"{int(temperature)} °{unit_key}", font_size=18)