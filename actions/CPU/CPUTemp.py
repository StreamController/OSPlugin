from GtkHelper.GenerativeUI.ComboRow import ComboRow
from plugins.com_core447_OSPlugin.CPUTemperature import AUTO, convert_temp, get_cpu_temp, get_sensor_items, get_unit_items
from plugins.com_core447_OSPlugin.LabelPosition import create_position_row, set_positioned_label
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.PluginBase import PluginBase

import time
import os

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
            items=get_unit_items(),
            title="Unit",
            can_reset=False,
            on_change=lambda *args: self.update()
        )

        self.sensor_row = ComboRow(
            action_core=self,
            var_name="sensor",
            default_value=AUTO,
            items=get_sensor_items(),
            title="Sensor",
            can_reset=False,
            on_change=lambda *args: self.update()
        )

        self.position_row = create_position_row(self, on_change=lambda *args: self.update())

    def on_ready(self):
        self.update()

    def on_tick(self):
        self.update()

    def update(self):
        temperature = get_cpu_temp(self.sensor_row.get_value())
        if temperature is None:
            set_positioned_label(self, self.position_row, "N/A")
            return

        unit_key = self.unit_row.get_value()
        temp = convert_temp(int(temperature), unit_key)
        set_positioned_label(self, self.position_row, f"{round(temp)} °{unit_key}")
