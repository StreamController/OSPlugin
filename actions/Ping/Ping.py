import os
import re
import subprocess
import threading

from loguru import logger as log

from GtkHelper.ComboRow import SimpleComboRowItem
from GtkHelper.GenerativeUI.ComboRow import ComboRow
from GtkHelper.GenerativeUI.EntryRow import EntryRow
from GtkHelper.GenerativeUI.SpinRow import SpinRow
from GtkHelper.GenerativeUI.SwitchRow import SwitchRow
from src.backend.PluginManager.ActionBase import ActionBase

# Matches "rtt min/avg/max/mdev = 7.206/8.237/9.269/1.031 ms" as well as busybox's "round-trip min/avg/max = ..."
RTT_REGEX = re.compile(r"min/avg/max[^=]*=\s*([\d.]+)/([\d.]+)/([\d.]+)")

REACHABLE_COLOR = [45, 130, 60, 255]
UNREACHABLE_COLOR = [150, 40, 40, 255]
NO_COLOR = [0, 0, 0, 0]


class Ping(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.has_configuration = True

        self.ping_timer: threading.Timer = None
        self.ping_lock = threading.Lock()

        self.host_row = EntryRow(
            action_core=self,
            var_name="host",
            default_value="",
            title=self.plugin_base.lm.get("actions.ping.host.title")
        )

        self.count_row = SpinRow(
            action_core=self,
            var_name="count",
            default_value=3,
            min=1, max=20, step=1, digits=0,
            title=self.plugin_base.lm.get("actions.ping.count.title"),
            subtitle=self.plugin_base.lm.get("actions.ping.count.subtitle")
        )

        self.timeout_row = SpinRow(
            action_core=self,
            var_name="timeout",
            default_value=2,
            min=1, max=60, step=1, digits=0,
            title=self.plugin_base.lm.get("actions.ping.timeout.title"),
            subtitle=self.plugin_base.lm.get("actions.ping.timeout.subtitle")
        )

        self.interval_row = SpinRow(
            action_core=self,
            var_name="interval",
            default_value=0,
            min=0, max=3600, step=10, digits=0,
            title=self.plugin_base.lm.get("actions.ping.interval.title"),
            subtitle=self.plugin_base.lm.get("actions.ping.interval.subtitle"),
            on_change=self.on_interval_changed
        )

        self.value_row = ComboRow(
            action_core=self,
            var_name="value",
            default_value="avg",
            items=[
                SimpleComboRowItem("avg", self.plugin_base.lm.get("actions.ping.value.avg")),
                SimpleComboRowItem("min", self.plugin_base.lm.get("actions.ping.value.min")),
                SimpleComboRowItem("max", self.plugin_base.lm.get("actions.ping.value.max"))
            ],
            title=self.plugin_base.lm.get("actions.ping.value.title")
        )

        self.color_row = SwitchRow(
            action_core=self,
            var_name="color_background",
            default_value=True,
            title=self.plugin_base.lm.get("actions.ping.color.title"),
            subtitle=self.plugin_base.lm.get("actions.ping.color.subtitle"),
            on_change=self.on_color_changed
        )

    def on_ready(self):
        self.start_timer()
        self.ping_threaded()

    def on_key_down(self):
        self.ping_threaded()

    def on_interval_changed(self, widget, new_value, old_value):
        self.start_timer()

    def on_color_changed(self, widget, new_value, old_value):
        if not new_value:
            self.set_background_color(NO_COLOR)

    def stop_timer(self):
        if self.ping_timer is not None:
            self.ping_timer.cancel()

    def start_timer(self):
        self.stop_timer()

        interval = self.interval_row.get_value()
        if interval <= 0:
            return

        self.ping_timer = threading.Timer(interval, self.on_timer)
        self.ping_timer.daemon = True
        self.ping_timer.name = "PingTimer"
        self.ping_timer.start()

    def on_timer(self):
        self.update()
        if self.get_is_present():
            self.start_timer()

    def ping_threaded(self):
        threading.Thread(target=self.update, daemon=True, name="Ping").start()

    def update(self):
        host = self.host_row.get_value()
        if host in (None, ""):
            return

        if not self.ping_lock.acquire(blocking=False):
            # A ping is already running
            return

        try:
            times = self.run_ping(host)
        finally:
            self.ping_lock.release()

        if times is None:
            self.set_center_label(self.plugin_base.lm.get("actions.ping.unreachable"))
            if self.color_row.get_value():
                self.set_background_color(UNREACHABLE_COLOR)
            return

        value = times[self.value_row.get_value()]
        self.set_center_label(f"{round(value)} ms" if value >= 10 else f"{round(value, 1)} ms")
        if self.color_row.get_value():
            self.set_background_color(REACHABLE_COLOR)

    def run_ping(self, host: str) -> dict[str, float]:
        """
        Returns the min, avg and max round trip times in ms or None if the host could not be reached
        """
        count = int(self.count_row.get_value())
        timeout = int(self.timeout_row.get_value())

        command = ["ping", "-n", "-q", "-c", str(count), "-W", str(timeout), host]
        if is_in_flatpak():
            # The runtime doesn't ship ping
            command = ["flatpak-spawn", "--host"] + command

        try:
            result = subprocess.run(command, capture_output=True, text=True,
                                    # C locale to keep the statistics line parsable
                                    env={**os.environ, "LC_ALL": "C"},
                                    timeout=count * timeout + 10)
        except Exception as e:
            log.error(e)
            return None

        if result.returncode != 0:
            return None

        match = RTT_REGEX.search(result.stdout)
        if match is None:
            return None

        return {
            "min": float(match.group(1)),
            "avg": float(match.group(2)),
            "max": float(match.group(3))
        }


def is_in_flatpak() -> bool:
    return os.path.isfile('/.flatpak-info')
