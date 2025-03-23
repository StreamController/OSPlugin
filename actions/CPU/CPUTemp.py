from GtkHelper.ComboRow import SimpleComboRowItem
from GtkHelper.GenerativeUI.ComboRow import ComboRow
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

        self.unit_row = ComboRow(
            action_core=self,
            var_name="unit",
            default_value="C",
            items=[SimpleComboRowItem("C", "°C"), SimpleComboRowItem("F", "°F")],
            title="Unit",
            can_reset=False,
            on_change=lambda *args: self.update()
        )
    
    def on_ready(self):
        self.update()
        
    def on_tick(self):
        self.update()

    def celcius_to_fahrenheit(self, celsius):
        return celsius * 1.8 + 32

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

        unit_key = self.unit_row.get_value()
        temp = int(temperature)
        if unit_key == "F":
            temp = self.celcius_to_fahrenheit(temp)
        self.set_center_label(text=f"{round(temp)} °{unit_key}", font_size=18)