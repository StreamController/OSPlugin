import multiprocessing
import os
import subprocess
import threading

# Import gtk modules
import gi
from src.backend.PluginManager.ActionBase import ActionBase

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk


class RunCommand(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.has_configuration = True

        self.auto_run_timer: threading.Timer = None

    def on_ready(self):
        self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "terminal.png"))
        self.start_timer()

    def stop_timer(self):
        if self.auto_run_timer is not None:
            self.auto_run_timer.cancel()

    def start_timer(self):
        self.stop_timer()
        settings = self.get_settings()
        if settings.get("auto_run", 0) <= 0:
            return
        self.auto_run_timer = threading.Timer(settings.get("auto_run", 0), self.execute, args=(True,))
        self.auto_run_timer.setDaemon(True)
        self.auto_run_timer.setName("AutoRunTimer")
        self.auto_run_timer.start()

    def on_key_down(self):
        self.execute()

    def execute(self, restart_timer: bool = False):
        self.stop_timer()
        settings = self.get_settings()

        result = self.run_command(settings.get("command", None))
        if settings.get("display_output", False):
            self.set_center_label(result)

        if restart_timer:
            self.start_timer()

    def get_config_rows(self):
        entry_row = Adw.EntryRow(title=self.plugin_base.lm.get("run.entry.title"))
        self.display_output_switch = Adw.SwitchRow(
            title=self.plugin_base.lm.get("run.display-output.title"),
            subtitle=self.plugin_base.lm.get("run.display-output.subtitle"))
        self.detached_switch = Adw.SwitchRow(title=self.plugin_base.lm.get("run.detached.title"),
                                             subtitle=self.plugin_base.lm.get(
                                                 "run.detached.subtitle"))
        
        self.auto_run_row = Adw.SpinRow.new_with_range(0, 60, 0.1)
        self.auto_run_row.set_title("Auto run every (s)")
        self.auto_run_row.set_subtitle("Auto run command automatically (0 to disable)")

        # Load from config
        settings = self.get_settings()
        command = settings.setdefault("command", None)
        self.set_settings(settings)

        if command is None:
            command = ""
        entry_row.set_text(command)

        self.display_output_switch.set_active(settings.get("display_output", False))
        self.detached_switch.set_active(settings.get("detached", False))
        self.auto_run_row.set_value(settings.get("auto_run", 0))

        # Connect entry
        entry_row.connect("notify::text", self.on_change_command)
        self.display_output_switch.connect("notify::active", self.on_display_output_changed)
        self.detached_switch.connect("notify::active", self.on_detached_changed)
        self.auto_run_row.connect("changed", self.on_auto_run_changed)

        return [entry_row, self.display_output_switch, self.detached_switch, self.auto_run_row]
    
    def on_auto_run_changed(self, spin):
        settings = self.get_settings()
        settings["auto_run"] = round(spin.get_value(), 1)
        self.set_settings(settings)
        self.start_timer()

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
            self.set_center_label("")
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

        if is_in_flatpak():
            command = "flatpak-spawn --host " + command

        if self.get_settings().get("detached", False):
            p = multiprocessing.Process(target=subprocess.Popen, args=[command], kwargs={"shell": True, "start_new_session": True, "stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL, "cwd": os.path.expanduser("~")})
            p.start()
            return ""

        result = subprocess.Popen(command, shell=True, start_new_session=True, text=True, stdout=subprocess.PIPE, cwd=os.path.expanduser("~"))  # If cwd is not set in the flatpak /app/bin/StreamController cannot be found

        result.wait()
        return result.communicate()[0].rstrip()


def is_in_flatpak() -> bool:
    return os.path.isfile('/.flatpak-info')
