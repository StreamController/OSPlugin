import multiprocessing
import os
import subprocess
import threading

# Import gtk modules
import gi
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.DeckManagement.InputIdentifier import Input, InputEvent, InputIdentifier

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk


class EasyCommand(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.has_configuration = True

        self.auto_run_timer: threading.Timer = None

        self.registered_down: bool = False # Temporary workaround for an issue in the app causing the action to get the short_up event if it's on the same key, but different page as a "change page" action that triggers the change #TODO

    def on_ready(self):
        self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "terminal.png"))

    def get_config_rows(self):
        entry_row = Adw.EntryRow(title=self.plugin_base.lm.get("run.entry.title"))

        # Load from config
        settings = self.get_settings()
        command = settings.setdefault("command", None)
        self.set_settings(settings)

        entry_row.set_text(command or "")

        # Connect entry
        entry_row.connect("notify::text", self.on_change_command)

        return [entry_row]

    def on_change_command(self, entry, _):
        settings = self.get_settings()
        settings["command"] = entry.get_text()
        self.set_settings(settings)

    def on_key_down(self):
        settings = self.get_settings()
        command = settings.get("command", None)
        if command is not None:
            self.run_command(command)

    def run_command(self, command):
        if command is None:
            return

        if is_in_flatpak():
            command = "flatpak-spawn --host " + command

        p = multiprocessing.Process(target=subprocess.Popen, args=[command], kwargs={"shell": True, "start_new_session": True, "stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL, "cwd": os.path.expanduser("~")})
        p.start()
        return ""


def is_in_flatpak() -> bool:
    return os.path.isfile('/.flatpak-info')
