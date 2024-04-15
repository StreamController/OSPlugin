from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.ActionHolder import ActionHolder

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
from evdev import ecodes
from evdev import UInput

from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page

from plugins.com_core447_OSPlugin.Hotkey import Hotkey
from plugins.com_core447_OSPlugin.Launch import Launch
from plugins.com_core447_OSPlugin.actions.RunCommand.RunCommand import RunCommand
from plugins.com_core447_OSPlugin.actions.OpenInBrowser.OpenInBrowser import OpenInBrowser
from plugins.com_core447_OSPlugin.actions.Delay.Delay import Delay
from plugins.com_core447_OSPlugin.CPU_Graph import CPU_Graph
from plugins.com_core447_OSPlugin.RAM_Graph import RAM_Graph
from .MoveXY import MoveXY
from .Click import Click
from .actions.CPU.CPU import CPU
from .actions.RAM.RAM import RAM
from .actions.WriteText.WriteText import WriteText

# Add plugin to sys.paths
sys.path.append(os.path.dirname(__file__))


class OSPlugin(PluginBase):
    def __init__(self):
        self.PLUGIN_NAME = "OS"
        self.GITHUB_REPO = "https://github.com/your-github-repo"
        super().__init__()
        self.ui = None
        self.init_vars()

        self.run_command_holder = ActionHolder(
            plugin_base=self,
            action_base=RunCommand,
            action_id="com_core447_OSPlugin::RunCommand",
            action_name=self.lm.get("actions.run-command.name")
        )
        self.add_action_holder(self.run_command_holder)

        self.open_in_browser_holder = ActionHolder(
            plugin_base=self,
            action_base=OpenInBrowser,
            action_id="com_core447_OSPlugin::OpenInBrowser",
            action_name=self.lm.get("actions.open-in-browser.name")
        )
        # self.add_action_holder(self.open_in_browser_holder) #FIXME: Not working in flatpak right now

        self.hotkey_holder = ActionHolder(
            plugin_base=self,
            action_base=Hotkey,
            action_id="com_core447_OSPlugin::Hotkey",
            action_name=self.lm.get("actions.hotkey.name")
        )
        if self.ui is not None:
            self.add_action_holder(self.hotkey_holder)

        self.delay_holder = ActionHolder(
            plugin_base=self,
            action_base=Delay,
            action_id="com_core447_OSPlugin::Delay",
            action_name=self.lm.get("actions.delay.name")
        )
        self.add_action_holder(self.delay_holder)

        self.launch_holder = ActionHolder(
            plugin_base=self,
            action_base=Launch,
            action_id="com_core447_OSPlugin::Launch",
            action_name=self.lm.get("actions.launch.name")
        )
        # Deactived because of problems in flatpak and app gathering
        # self.add_action_holder(self.launch_holder)

        self.cpu_graph_holder = ActionHolder(
            plugin_base=self,
            action_base=CPU_Graph,
            action_id="com_core447_OSPlugin::CPU_Graph",
            action_name=self.lm.get("actions.cpu-graph.name")
        )
        self.add_action_holder(self.cpu_graph_holder) #FIXME: too unstable

        self.ram_graph_holder = ActionHolder(
            plugin_base=self,
            action_base=RAM_Graph,
            action_id="com_core447_OSPlugin::RAM_Graph",
            action_name=self.lm.get("actions.ram-graph.name")
        )
        self.add_action_holder(self.ram_graph_holder) #FIXME: too unstable

        self.move_xy_holder = ActionHolder(
            plugin_base=self,
            action_base=MoveXY,
            action_id="com_core447_OSPlugin::MoveXY",
            action_name=self.lm.get("actions.move-xy.name")
        )
        self.add_action_holder(self.move_xy_holder)

        self.click_holder = ActionHolder(
            plugin_base=self,
            action_base=Click,
            action_id="com_core447_OSPlugin::Click",
            action_name=self.lm.get("actions.click.name")
        )
        self.add_action_holder(self.click_holder)

        self.cpu_holder = ActionHolder(
            plugin_base=self,
            action_base=CPU,
            action_id="com_core447_OSPlugin::CPU",
            action_name=self.lm.get("actions.cpu.name")
        )
        self.add_action_holder(self.cpu_holder)

        self.ram_holder = ActionHolder(
            plugin_base=self,
            action_base=RAM,
            action_id="com_core447_OSPlugin::RAM",
            action_name=self.lm.get("actions.ram.name")
        )
        self.add_action_holder(self.ram_holder)

        self.write_text_holder = ActionHolder(
            plugin_base=self,
            action_base=WriteText,
            action_id="com_core447_OSPlugin::WriteText",
            action_name=self.lm.get("actions.write-text.name")
        )
        if self.ui is not None:
            self.add_action_holder(self.write_text_holder)

        # Register plugin
        self.register(
            plugin_name=self.lm.get("plugin.name"),
            github_repo="https://github.com/StreamController/OSPlugin",
            plugin_version="1.0.0",
            app_version="1.0.0-alpha"
        )


        self.add_css_stylesheet(os.path.join(self.PATH, "style.css"))

    def init_vars(self):
        self.lm = self.locale_manager
        self.lm.set_to_os_default()

        self.ui = None
        try:
            self.ui = UInput({ecodes.EV_KEY: range(0, 300),
                         ecodes.EV_REL: [ecodes.REL_X, ecodes.REL_Y]}, name="stream-controller-os-plugin")
        except Exception as e:
            log.error(e)