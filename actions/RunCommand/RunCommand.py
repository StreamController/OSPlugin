from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.PluginBase import PluginBase

import os
from PIL import Image
import subprocess

# Import gtk modules
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

class RunCommand(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.HAS_CONFIGURATION = True

    def on_ready(self):
        self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "terminal.png"))

    def on_key_down(self):
        settings = self.get_settings()

        result = self.run_command(settings.get("command", None))
        if settings.get("display_output", False):
            self.set_center_label(result)

    def get_config_rows(self):
        entry_row = Adw.EntryRow(title=self.plugin_base.lm.get("run.entry.title"))
        self.display_output_switch = Adw.SwitchRow(title=self.plugin_base.lm.get("run.display-output.title"),
                                                   subtitle=self.plugin_base.lm.get("run.display-output.subtitle"))

        # Load from config
        settings = self.get_settings()
        command = settings.setdefault("command", None)
        if command is None:
            command = ""
        entry_row.set_text(command)

        self.display_output_switch.set_active(settings.get("display_output", False))
        self.set_settings(settings)

        # Connect entry
        entry_row.connect("notify::text", self.on_change_command)
        self.display_output_switch.connect("notify::active", self.on_display_output_changed)

        return [entry_row, self.display_output_switch]

    def on_change_command(self, entry, *args):
        settings = self.get_settings()
        settings["command"] = entry.get_text()
        self.set_settings(settings)

    def on_display_output_changed(self, switch, *args):
        settings = self.get_settings()
        settings["display_output"] = switch.get_active()
        if not switch.get_active():
            self.set_center_label(None)
        self.set_settings(settings)

    def run_command(self, command):
        if command is None:
            return
        
        if self.is_in_flatpak():
            command = "flatpak-spawn --host " + command

        result = subprocess.Popen(command, shell=True, start_new_session=True, text=True, stdout=subprocess.PIPE, cwd=os.path.expanduser("~")) # If cwd is not set in the flatpak /app/bin/StreamController cannot be found
        result.wait()
        return result.communicate()[0].rstrip()
        if result.stdout is None:
            return
        return result.stdout.strip()

    def is_in_flatpak(self) -> bool:
        return os.path.isfile('/.flatpak-info')