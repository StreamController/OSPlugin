from GtkHelper.ComboRow import SimpleComboRowItem
from GtkHelper.GenerativeUI.ComboRow import ComboRow
from plugins.com_core447_OSPlugin.CPUTemperature import AUTO, convert_temp, get_cpu_temp, get_sensor_items, get_unit_items
from plugins.com_core447_OSPlugin.CPUUsage import get_cpu_percent, get_usage_method_items
from plugins.com_core447_OSPlugin.GraphBase import GraphBase
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.PluginBase import PluginBase

from PIL import Image

# The y-axis of a temperature graph, cpus report celsius so fahrenheit needs a taller axis
MAX_TEMP_C = 100
MAX_TEMP_F = 212

class CPU_Graph(GraphBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_configuration = False

        self.temp_available = True

        self.usage_method_row = ComboRow(
            action_core=self,
            var_name="usage_method",
            default_value="average",
            items=get_usage_method_items(),
            title="Usage Method",
            can_reset=False
        )

        self.unit_row = ComboRow(
            action_core=self,
            var_name="unit",
            default_value="C",
            items=get_unit_items(),
            title="Unit",
            can_reset=False,
            on_change=lambda *args: self.on_source_change()
        )

        self.sensor_row = ComboRow(
            action_core=self,
            var_name="sensor",
            default_value=AUTO,
            items=get_sensor_items(),
            title="Sensor",
            can_reset=False,
            on_change=lambda *args: self.on_source_change()
        )

        # Created last so its on_change always finds the rows it enables and disables
        self.graph_type_row = ComboRow(
            action_core=self,
            var_name="graph_type",
            default_value="usage",
            items=[SimpleComboRowItem("usage", "CPU Usage"),
                   SimpleComboRowItem("temp", "CPU Temperature")],
            title="Graph Type",
            can_reset=False,
            on_change=self.on_graph_type_change
        )

    def shows_temp(self) -> bool:
        return self.graph_type_row.get_value() == "temp"

    def on_graph_type_change(self, widget=None, new_item=None, old_item=None):
        self.update_row_sensitivity()

        old_value = old_item.get_value() if old_item is not None else None
        new_value = new_item.get_value() if new_item is not None else self.graph_type_row.get_value()

        # A history of percentages means nothing on a temperature axis and the other way around
        if old_value is not None and old_value != new_value:
            self.percentages.clear()

        if self.on_ready_called:
            self.show_graph()

    def on_source_change(self):
        # Readings of another sensor or in another unit cannot share a history either
        self.percentages.clear()

        if self.on_ready_called:
            self.show_graph()

    def update_row_sensitivity(self):
        shows_temp = self.shows_temp()
        self.unit_row.set_sensitive(shows_temp)
        self.sensor_row.set_sensitive(shows_temp)
        self.usage_method_row.set_sensitive(not shows_temp)

    def get_y_max(self) -> float:
        if not self.shows_temp():
            return 100
        return MAX_TEMP_F if self.unit_row.get_value() == "F" else MAX_TEMP_C

    def get_current_value(self) -> float:
        if not self.shows_temp():
            self.temp_available = True
            return get_cpu_percent(self.usage_method_row.get_value())

        temperature = get_cpu_temp(self.sensor_row.get_value())
        self.temp_available = temperature is not None
        if temperature is None:
            return 0.0

        return convert_temp(temperature, self.unit_row.get_value())

    def get_label_text(self) -> str:
        if not self.shows_temp():
            return super().get_label_text()

        if not self.temp_available:
            return "N/A"

        value = round(self.percentages[-1]) if self.percentages else 0
        return f"{value} °{self.unit_row.get_value()}"

    def on_tick(self):
        self.percentages.append(self.get_current_value())
        self.show_graph()
