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
    def __init__(self, action_id: str, action_name: str,
                 deck_controller: "DeckController", page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
            deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)

        self.set_default_image(Image.open(os.path.join(self.plugin_base.PATH, "assets", "terminal.png")))

    def on_key_down(self):
        command = self.get_settings().get("command", None)
        self.run_command(command)

    def get_config_rows(self):
        entry_row = Adw.EntryRow(title=self.plugin_base.lm.get("run.entry.title"))

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
        
        if self.is_in_flatpak():
            command = "flatpak-spawn --host " + command

        subprocess.Popen(command, shell=True, start_new_session=True)

    def is_in_flatpak(self) -> bool:
        return os.path.isfile('/.flatpak-info')