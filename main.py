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
from evdev import ecodes as e
from evdev import UInput

from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page

from plugins.dev_core447_OSPlugin.Hotkey import Hotkey
from plugins.dev_core447_OSPlugin.Launch import Launch
from plugins.dev_core447_OSPlugin.actions.RunCommand.RunCommand import RunCommand
from plugins.dev_core447_OSPlugin.actions.OpenInBrowser.OpenInBrowser import OpenInBrowser
from plugins.dev_core447_OSPlugin.actions.Delay.Delay import Delay
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








class OSPlugin(PluginBase):
    def __init__(self):
        self.PLUGIN_NAME = "OS"
        self.GITHUB_REPO = "https://github.com/your-github-repo"
        super().__init__()
        self.init_vars()

        self.run_command_holder = ActionHolder(
            plugin_base=self,
            action_base=RunCommand,
            action_id="dev_core447_OSPlugin::RunCommand",
            action_name=self.lm.get("actions.run-command.name")
        )
        self.add_action_holder(self.run_command_holder)

        self.open_in_browser_holder = ActionHolder(
            plugin_base=self,
            action_base=OpenInBrowser,
            action_id="dev_core447_OSPlugin::OpenInBrowser",
            action_name=self.lm.get("actions.open-in-browser.name")
        )
        self.add_action_holder(self.open_in_browser_holder)

        self.hotkey_holder = ActionHolder(
            plugin_base=self,
            action_base=Hotkey,
            action_id="dev_core447_OSPlugin::Hotkey",
            action_name=self.lm.get("actions.hotkey.name")
        )
        self.add_action_holder(self.hotkey_holder)

        self.delay_holder = ActionHolder(
            plugin_base=self,
            action_base=Delay,
            action_id="dev_core447_OSPlugin::Delay",
            action_name=self.lm.get("actions.delay.name")
        )
        self.add_action_holder(self.delay_holder)

        self.launch_holder = ActionHolder(
            plugin_base=self,
            action_base=Launch,
            action_id="dev_core447_OSPlugin::Launch",
            action_name=self.lm.get("actions.launch.name")
        )
        # Deactived because of problems in flatpak and app gathering
        # self.add_action_holder(self.launch_holder)

        self.cpu_graph_holder = ActionHolder(
            plugin_base=self,
            action_base=CPU_Graph,
            action_id="dev_core447_OSPlugin::CPU_Graph",
            action_name=self.lm.get("actions.cpu-graph.name")
        )
        self.add_action_holder(self.cpu_graph_holder)

        self.ram_graph_holder = ActionHolder(
            plugin_base=self,
            action_base=RAM_Graph,
            action_id="dev_core447_OSPlugin::RAM_Graph",
            action_name=self.lm.get("actions.ram-graph.name")
        )
        self.add_action_holder(self.ram_graph_holder)

        ## VolumeMixer
        self.open_volume_mixer_holder = ActionHolder(
            plugin_base=self,
            action_base=OpenVolumeMixer,
            action_id="dev_core447_OSPlugin::VM_Open",
            action_name=self.lm.get("actions.open-volume-mixer.name")
        )
        self.add_action_holder(self.open_volume_mixer_holder)

        self.exit_volume_mixer_holder = ActionHolder(
            plugin_base=self,
            action_base=ExitVolumeMixer,
            action_id="dev_core447_OSPlugin::VM_Exit",
            action_name=self.lm.get("actions.exit-volume-mixer.name")
        )
        self.add_action_holder(self.exit_volume_mixer_holder)

        self.mute_key_holder = ActionHolder(
            plugin_base=self,
            action_base=MuteKey,
            action_id="dev_core447_OSPlugin::VM_VolumeMute",
            action_name=self.lm.get("actions.mute-key.name")
        )
        self.add_action_holder(self.mute_key_holder)

        self.up_key_holder = ActionHolder(
            plugin_base=self,
            action_base=UpKey,
            action_id="dev_core447_OSPlugin::VM_VolumeUp",
            action_name=self.lm.get("actions.up-key.name")
        )
        self.add_action_holder(self.up_key_holder)

        self.down_key_holder = ActionHolder(
            plugin_base=self,
            action_base=DownKey,
            action_id="dev_core447_OSPlugin::VM_VolumeDown",
            action_name=self.lm.get("actions.down-key.name")
        )
        self.add_action_holder(self.down_key_holder)

        self.move_right_holder = ActionHolder(
            plugin_base=self,
            action_base=MoveRight,
            action_id="dev_core447_OSPlugin::VM_MoveRight",
            action_name=self.lm.get("actions.move-right.name")
        )
        self.add_action_holder(self.move_right_holder)

        self.move_left_holder = ActionHolder(
            plugin_base=self,
            action_base=MoveLeft,
            action_id="dev_core447_OSPlugin::VM_MoveLeft",
            action_name=self.lm.get("actions.move-left.name")
        )
        self.add_action_holder(self.move_left_holder)

        # Register plugin
        self.register(
            plugin_name=self.lm.get("plugin.name"),
            github_repo="https://github.com/Core447/OSPlugin",
            plugin_version="0.1",
            app_version="0.1.1-alpha"
        )


        self.add_css_stylesheet(os.path.join(self.PATH, "style.css"))

        self.register_page(os.path.join(self.PATH, "VolumeMixer", "VolumeMixer.json"))

        

    def init_vars(self):
        self.lm = self.locale_manager
        self.lm.set_to_os_default()

        self.ui = UInput({e.EV_KEY: range(0, 255)}, name="stream-controller")
        
        ## Volume Mixer #TODO: Add multi deck support
        self.original_page_path = None
        self.start_index = 0
        self.pulse = pulsectl.Pulse("stream-controller", threading_lock=True)
        self.volume_increment = 0.1
        self.volume_actions: list[ActionBase] = []