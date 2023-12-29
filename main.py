from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.PluginBase import PluginBase

# Import gtk modules
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

import sys
import os
import webbrowser
from loguru import logger as log
from PIL import Image, ImageEnhance
import math
import threading
import subprocess
import time
from evdev import ecodes as e
from evdev import UInput

from plugins.dev_core447_OSPlugin.Hotkey import Hotkey
from plugins.dev_core447_OSPlugin.Launch import Launch
from plugins.dev_core447_OSPlugin.CPU_Graph import CPU_Graph
from plugins.dev_core447_OSPlugin.RAM_Graph import RAM_Graph

## VolumeMixer
import pulsectl
from plugins.dev_core447_OSPlugin.VolumeMixer.OpenVolumeMixer import OpenVolumeMixer
from plugins.dev_core447_OSPlugin.VolumeMixer.ExitVolumeMixer import ExitVolumeMixer
from plugins.dev_core447_OSPlugin.VolumeMixer.MuteKey import MuteKey
from plugins.dev_core447_OSPlugin.VolumeMixer.VolumeUpKey import UpKey
from plugins.dev_core447_OSPlugin.VolumeMixer.VolumeDownKey import DownKey
from plugins.dev_core447_OSPlugin.VolumeMixer.MoveRight import MoveRight
from plugins.dev_core447_OSPlugin.VolumeMixer.MoveLeft import MoveLeft

# Add plugin to sys.paths
sys.path.append(os.path.dirname(__file__))

class RunCommand(ActionBase):
    ACTION_NAME = "Run Command"
    CONTROLS_KEY_IMAGE = False
    def __init__(self, deck_controller, page, coords):
        super().__init__(deck_controller=deck_controller, page=page, coords=coords)

        self.set_default_image(Image.open(os.path.join(self.PLUGIN_BASE.PATH, "assets", "terminal.png")))

    def on_key_down(self):
        command = self.get_settings().get("command", None)
        self.run_command(command)

    def get_config_rows(self):
        entry_row = Adw.EntryRow(title="Command:")

        # Load from config
        settings = self.get_settings()
        command = settings.setdefault("command", None)
        if command is None:
            command = ""
        entry_row.set_text(command)
        self.set_settings(settings)

        # Connect entry
        entry_row.connect("notify::text", self.on_change_command)

        return [entry_row]

    def on_change_command(self, entry, *args):
        settings = self.get_settings()
        settings["command"] = entry.get_text()
        self.set_settings(settings)

    def run_command(self, command):
        if command is None:
            return
        subprocess.Popen(command, shell=True, start_new_session=True)

class OpenInBrowser(ActionBase):
    ACTION_NAME = "Open In Browser"
    CONTROLS_KEY_IMAGE = False

    def __init__(self, deck_controller, page, coords):
        super().__init__(deck_controller=deck_controller, page=page, coords=coords)
        self.set_default_image(Image.open(os.path.join(self.PLUGIN_BASE.PATH, "assets", "web.png")))

    def on_key_down(self):
        url = self.get_settings().get("url", None)
        self.open_url(url)

    def get_config_rows(self):
        entry_row = Adw.EntryRow(title="URL:")
        new_window_toggle = Adw.SwitchRow(title="Open in new window")

        # Load from config
        settings = self.get_settings()
        url = settings.setdefault("url", None)
        if url is None:
            url = ""
        entry_row.set_text(url)
        new_window_toggle.set_active(settings.setdefault("new_window", False))
        self.set_settings(settings)

        # Connect entry
        entry_row.connect("notify::text", self.on_change_url)
        # Connect switch
        new_window_toggle.connect("notify::active", self.on_change_new_window)

        return [entry_row, new_window_toggle]

    def on_change_url(self, entry, *args):
        settings = self.get_settings()
        settings["url"] = entry.get_text()
        self.set_settings(settings)

    def on_change_new_window(self, switch, *args):
        settings = self.get_settings()
        settings["new_window"] = switch.get_active()
        self.set_settings(settings)

    def open_url(self, url):
        if url in [None, ""]:
            return
        new = 1 if self.get_settings().get("new_window", False) else 0
        webbrowser.open(url, new=new)


class Delay(ActionBase):
    ACTION_NAME = "Delay"
    CONTROLS_KEY_IMAGE = False
    def __init__(self, deck_controller, page, coords):
        super().__init__(deck_controller=deck_controller, page=page, coords=coords)

    def get_config_rows(self) -> list:
        self.delay_row = Adw.SpinRow().new_with_range(min=0, max=10, step=0.1)
        self.delay_row.set_title("Delay (s):")
        self.delay_row.set_subtitle("Delay the coming actions on this key")

        # Load from config
        settings = self.get_settings()
        self.delay_row.set_value(settings.get("delay", 0))

        self.delay_row.connect("changed", self.on_delay_change)

        return [self.delay_row]
    
    def on_delay_change(self, *args):
        settings = self.get_settings()
        settings["delay"] = round(self.delay_row.get_value(), 1)
        self.set_settings(settings)

    def on_key_down(self):
        delay = self.get_settings().get("delay", 0)
        time.sleep(delay)


class OSPlugin(PluginBase):
    def __init__(self):
        self.PLUGIN_NAME = "OS"
        self.GITHUB_REPO = "https://github.com/your-github-repo"
        super().__init__()
        self.init_vars()

        print(self.ACTIONS)
        self.add_action(RunCommand)
        self.add_action(OpenInBrowser)
        self.add_action(Hotkey)
        self.add_action(Delay)
        self.add_action(Launch)
        self.add_action(CPU_Graph)
        self.add_action(RAM_Graph)

        ## VolumeMixer
        self.add_action(OpenVolumeMixer)
        self.add_action(ExitVolumeMixer)
        self.add_action(MuteKey)
        self.add_action(UpKey)
        self.add_action(DownKey)
        self.add_action(MoveRight)
        self.add_action(MoveLeft)

        self.add_css_stylesheet(os.path.join(self.PATH, "style.css"))

        self.register_page(os.path.join(self.PATH, "VolumeMixer", "VolumeMixer.json"))

    def init_vars(self):
        self.ui = UInput({e.EV_KEY: range(0, 255)}, name="stream-controller")
        
        ## Volume Mixer #TODO: Add multi deck support
        self.original_page_path = None
        self.start_index = 0
        self.pulse = pulsectl.Pulse("stream-controller")
        self.volume_increment = 0.1
        self.volume_actions: list[ActionBase] = []