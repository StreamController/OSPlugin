from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.PluginBase import PluginBase

import os
from PIL import Image
import webbrowser

# Import gtk modules
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

class OpenInBrowser(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.has_configuration = True
        
    def on_ready(self):
        self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "web.png"))

    def on_key_down(self):
        url = self.get_settings().get("url", None)
        self.open_url(url)

    def get_config_rows(self):
        entry_row = Adw.EntryRow(title=self.plugin_base.lm.get("open-browser.url.title"))
        new_window_toggle = Adw.SwitchRow(title=self.plugin_base.lm.get("open-browser.new-window"))

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

        return [entry_row]

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
        
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        new = 1 if self.get_settings().get("new_window", False) else 0
        #FIXME: New window not working in flatpak
        webbrowser.open(url, new=new)