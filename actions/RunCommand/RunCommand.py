import os
import subprocess

# Import gtk modules
import gi
from src.backend.PluginManager.ActionBase import ActionBase

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw


class RunCommand(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.has_configuration = True

    def on_ready(self):
        self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "terminal.png"))

    def on_key_down(self):
        settings = self.get_settings()

        result = self.run_command(settings.get("command", None))
        if settings.get("display_output", False):
            self.set_center_label(result)

    def get_config_rows(self):
        entry_row = Adw.EntryRow(title=self.plugin_base.lm.get("run.entry.title"))
        self.display_output_switch = Adw.SwitchRow(
            title=self.plugin_base.lm.get("run.display-output.title"),
            subtitle=self.plugin_base.lm.get("run.display-output.subtitle"))
        self.detached_switch = Adw.SwitchRow(title=self.plugin_base.lm.get("run.detached.title"),
                                             subtitle=self.plugin_base.lm.get(
                                                 "run.detached.subtitle"))

        # Load from config
        settings = self.get_settings()
        command = settings.setdefault("command", None)
        self.set_settings(settings)

        if command is None:
            command = ""
        entry_row.set_text(command)

        self.display_output_switch.set_active(settings.get("display_output", False))
        self.detached_switch.set_active(settings.get("detached", False))

        # Connect entry
        entry_row.connect("notify::text", self.on_change_command)
        self.display_output_switch.connect("notify::active", self.on_display_output_changed)
        self.detached_switch.connect("notify::active", self.on_detached_changed)

        return [entry_row, self.display_output_switch, self.detached_switch]

    def on_change_command(self, entry, _):
        settings = self.get_settings()
        settings["command"] = entry.get_text()
        self.set_settings(settings)

    def on_display_output_changed(self, switch, _):
        settings = self.get_settings()
        settings["display_output"] = switch.get_active()
        if switch.get_active():
            # can't display output AND run detached
            self.detached_switch.set_active(False)
        else:
            # remove possibly present label
            self.set_center_label(None)
        self.set_settings(settings)

    def on_detached_changed(self, switch, _):
        settings = self.get_settings()
        settings["detached"] = switch.get_active()
        if switch.get_active():
            # can't run detached AND display output
            self.display_output_switch.set_active(False)
        self.set_settings(settings)

    def run_command(self, command):
        if command is None:
            return

        if self.is_in_flatpak():
            command = "flatpak-spawn --host " + command

        if self.get_settings().get("detached", False):
            subprocess.Popen(command, shell=True, start_new_session=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=os.path.expanduser("~"))  # If cwd is not set in the flatpak /app/bin/StreamController cannot be found
            return ""

        result = subprocess.Popen(command, shell=True, start_new_session=True, text=True, stdout=subprocess.PIPE, cwd=os.path.expanduser("~"))  # If cwd is not set in the flatpak /app/bin/StreamController cannot be found

        result.wait()
        return result.communicate()[0].rstrip()

    def is_in_flatpak(self) -> bool:
        return os.path.isfile('/.flatpak-info')
