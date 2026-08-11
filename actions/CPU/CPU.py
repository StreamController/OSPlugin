from plugins.com_core447_OSPlugin.CPUUsage import get_cpu_percent, get_usage_method_items
from plugins.com_core447_OSPlugin.LabelPosition import create_position_row, set_positioned_label
from GtkHelper.GenerativeUI.ComboRow import ComboRow
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

class CPU(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_configuration = False

        self.usage_method_row = ComboRow(
            action_core=self,
            var_name="usage_method",
            default_value="average",
            items=get_usage_method_items(),
            title="Usage Method",
            can_reset=False,
            on_change=lambda *args: self.update()
        )

        self.position_row = create_position_row(self, on_change=lambda *args: self.update())

    def on_ready(self):
        self.update()

    def on_tick(self):
        self.update()

    def update(self):
        percent = round(get_cpu_percent(self.usage_method_row.get_value()))
        set_positioned_label(self, self.position_row, f"{percent}%", center_font_size=24)
