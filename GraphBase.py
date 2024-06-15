from threading import Thread
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.PluginBase import PluginBase

import matplotlib.pyplot as plt
import matplotlib
from multiprocessing import Process, Queue
# Use different backend to prevent errors with running plt in different threads
matplotlib.use('agg')
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from PIL import Image
import io

# Import gtk
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gdk

# Import globals
import globals as gl

from src.Signals import Signals

class GraphBase(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.percentages: list[float] = []

        self.task_queue = Queue()
        self.result_queue = Queue()
        # self.process = Process(target=self.worker, args=(self.task_queue, self.result_queue), name="GraphBaseCreator")
        self.process = GraphCreator(task_queue=self.task_queue, result_queue=self.result_queue)
        self.process.start()

        gl.signal_manager.connect_signal(Signals.AppQuit, self.stop_process)

    def stop_process(self, *args):
        print("stop graph base")
        self.task_queue.put((None, None))

    def set_percentages_lenght(self, length: int):
        if len(self.percentages) > length:
            self.percentages = self.percentages[-length:]
        elif len(self.percentages) < length:
            for _ in range(length - len(self.percentages)):
                self.percentages.insert(0, 0)
        
        return self.percentages
    
    def get_graph(self) -> Image:
        ## Get vars
        settings = self.get_settings()
        time_period = settings.get("time-period", 15)
        self.set_percentages_lenght(time_period)

        self.task_queue.put((settings, self.percentages))

        img = self.result_queue.get()
        return img
    
    def show_graph(self):
        image = self.get_graph()
        if image is None:
            return
        self.set_media(image=image)

    def get_custom_config_area(self):
        return Gtk.Label(label=self.plugin_base.lm.get("actions.graph-base.memory-warning"), css_classes=["destructive-action"])
    
    def get_config_rows(self) -> list:
        self.line_color_row = ColorRow()
        self.line_color_row.color_label.set_label("Line Color:")

        self.fill_color = ColorRow()
        self.fill_color.color_label.set_label("Fill Color:")

        self.line_width_row = Adw.SpinRow.new_with_range(1, 30, 1)
        self.line_width_row.set_title("Line Width:")

        self.time_period_row = Adw.SpinRow.new_with_range(1, 60, 1)
        self.time_period_row.set_title("Time Period (s):")

        self.dynamic_scaling_row = Adw.SwitchRow(title="Dynamic Y-axis Scaling:")

        self.toggle_dynamic_scaling_on_press_row = Adw.SwitchRow(title="Toggle Dynamic Y-axis Scaling on Press:")


        ## Load defaults:
        settings = self.get_settings()

        self.fill_color.color_button.set_rgba(self.prepare_color(settings.get("fill-color", [255, 255, 255, 255])))
        self.line_color_row.color_button.set_rgba(self.prepare_color(settings.get("line-color", [255, 255, 255, 150])))

        self.line_width_row.set_value(settings.get("line-width", 5))
        self.time_period_row.set_value(settings.get("time-period", 15))

        self.dynamic_scaling_row.set_active(settings.get("dynamic-scaling", False))
        self.toggle_dynamic_scaling_on_press_row.set_active(settings.get("toggle-dynamic-scaling-on-press", False))


        ## Connect signals
        self.fill_color.color_button.connect("color-set", self.on_fill_color_change)
        self.line_color_row.color_button.connect("color-set", self.on_line_color_change)

        self.line_width_row.connect("changed", self.on_line_width_change)
        self.time_period_row.connect("changed", self.on_time_period_change)

        self.dynamic_scaling_row.connect("notify::active", self.on_dynamic_scaling_change)
        self.toggle_dynamic_scaling_on_press_row.connect("notify::active", self.on_dynamic_scaling_toggle_on_press_change)

        return [self.line_color_row, self.fill_color, self.line_width_row, self.time_period_row, self.dynamic_scaling_row, self.toggle_dynamic_scaling_on_press_row]
    
    def prepare_color(self, color_values: list[int]) -> Gdk.RGBA:
        if len(color_values) == 3:
            color_values.append(255)
        color = Gdk.RGBA()
        color.parse(f"rgba({color_values[0]}, {color_values[1]}, {color_values[2]}, {color_values[3]})")
        return color
    
    def on_fill_color_change(self, button):
        color = self.fill_color.color_button.get_rgba()
        green = round(color.green * 255)
        blue = round(color.blue * 255)
        red = round(color.red * 255)
        alpha = round(color.alpha * 255)
        settings = self.get_settings()
        settings["fill-color"] = [red, green, blue, alpha]
        self.set_settings(settings)
        self.show_graph()

    def on_line_color_change(self, button):
        color = self.line_color_row.color_button.get_rgba()
        green = round(color.green * 255)
        blue = round(color.blue * 255)
        red = round(color.red * 255)
        alpha = round(color.alpha * 255)
        settings = self.get_settings()
        settings["line-color"] = [red, green, blue, alpha]
        self.set_settings(settings)
        self.show_graph()

    def on_line_width_change(self, spin):
        settings = self.get_settings()
        settings["line-width"] = spin.get_value()
        self.set_settings(settings)
        self.show_graph()

    def on_time_period_change(self, spin):
        settings = self.get_settings()
        settings["time-period"] = int(spin.get_value())
        self.set_settings(settings)
        self.set_percentages_lenght(int(spin.get_value()))
        self.show_graph()

    def on_dynamic_scaling_change(self, switch, *args):
        settings = self.get_settings()
        settings["dynamic-scaling"] = switch.get_active()
        self.set_settings(settings)
        self.show_graph()

    def on_dynamic_scaling_toggle_on_press_change(self, switch, *args):
        settings = self.get_settings()
        settings["toggle-dynamic-scaling-on-press"] = switch.get_active()
        self.set_settings(settings)
        self.show_graph()

    def on_key_down(self):
        settings = self.get_settings()
        if not settings.get("toggle-dynamic-scaling-on-press", False):
            return
        settings["dynamic-scaling"] = not settings.get("dynamic-scaling", False)
        self.set_settings(settings)

        if hasattr(self, "dynamic_scaling_row"):
            self.dynamic_scaling_row.set_active(settings["dynamic-scaling"])

        self.show_graph()

    def on_removed_from_cache(self) -> None:
        self.task_queue.put((None, None))

class ColorRow(Adw.PreferencesRow):
    def __init__(self):
        super().__init__()

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True,
                                margin_top=10, margin_bottom=10, margin_start=15, margin_end=15)
        self.set_child(self.main_box)

        self.color_label = Gtk.Label(label="Color:", hexpand=True, xalign=0)
        self.main_box.append(self.color_label)

        self.color_button = Gtk.ColorButton(use_alpha=True)
        self.main_box.append(self.color_button)

class GraphCreator(Process):
    def __init__(self, task_queue: Queue, result_queue: Queue):
        super().__init__(daemon=True, name="GraphCreator")
        self.task_queue = task_queue
        self.result_queue = result_queue

    def run(self):
        while True:
            settings, percentages = self.task_queue.get()
            if None in [settings, percentages]:
                break
            result = self.generate_graph(settings, percentages)
            self.result_queue.put(result)
        print("GraphCreator stopped")

    def generate_graph(self, settings: dict, percentages: list[float]):
        line_color = self.conv_color_to_plt(settings.get("line-color", [255, 255, 255, 255]))
        fill_color = self.conv_color_to_plt(settings.get("fill-color", [255, 255, 255, 150]))
        line_width = settings.get("line-width", 5)
        dynamic_scaling = settings.get("dynamic-scaling", False)

        # Create a new figure with a transparent background
        fig = plt.figure(figsize=(6, 6))
        fig.patch.set_alpha(0)
        fig.patch.set_facecolor('none')

        # Set the FigureCanvas to the backend
        canvas = FigureCanvas(fig)

        # Plot the data with a transparent background
        ax = plt.Axes(fig, [0., 0., 1., 1.])
        ax.set_axis_off()
        fig.add_axes(ax)

        ax.plot(percentages, color=line_color, linewidth=line_width)
        ax.fill_between(range(len(percentages)), percentages, color=fill_color[:3], alpha=fill_color[3])

        # Hide the spines
        for spine in ax.spines.values():
            spine.set_visible(False)

        # Turn off the axis and set margins to zero
        ax.margins(0)
        ax.axis('off')

        # Set the y-axis to range from 0 to 100
        if not dynamic_scaling:
            ax.set_ylim(0, 100)

        # Draw the canvas and retrieve the buffer
        canvas.draw()
        buf = io.BytesIO()
        canvas.print_png(buf)

        # Convert buffer to a Pillow Image
        buf.seek(0)
        img = Image.open(buf)

        # The Pillow Image now has a transparent background
        # img.show()  # If you want to display the image
        # img.save('plot.png')  # If you want to save the image

        plt.close()  # Close the plot to free resources

        # result_queue.put(img)
        return img

    def conv_color_to_plt(self, color: list[int]) -> list[float]:
        float_color: list[float] = []
        for c in color:
            float_color.append(c / 255)
        return float_color