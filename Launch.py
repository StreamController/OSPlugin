from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.PluginBase import PluginBase

# Import gtk modules
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw


import glob
import configparser
import os
import subprocess


class Launch(ActionBase):
    def __init__(self, *args, **kwargs):
        self.has_configuration = False
        super().__init__(*args, **kwargs)

    def get_installed_apps(self):
        apps = {}
        desktop_files = glob.glob("/usr/share/applications/*.desktop")
        desktop_files += glob.glob(os.path.expanduser("~/.local/share/applications/*.desktop"))

        for desktop_file in desktop_files:
            config = configparser.ConfigParser(interpolation=None)
            config.read(desktop_file)
            try:
                # 'Desktop Entry' is a standard group name in .desktop files
                entry = config['Desktop Entry']
                # 'Name' is a standard key in .desktop files, represents the app name
                # 'Exec' is a standard key in .desktop files, represents the executable path
                apps[entry.get('Name')] = entry.get('Exec')
            except KeyError:
                continue

        return apps
    
    def get_exec_path_by_name(self, name):
        return self.get_installed_apps().get(name)
    
    def get_name_by_exec_path(self, exec_path):
        for name, path in self.apps.items():
            if path == exec_path:
                return name
    
    def get_config_rows(self) -> list:
        self.app_model = Gtk.StringList()
        self.app_selector = Adw.ComboRow(model=self.app_model, title="App:")
        self.app_selector.set_enable_search(True) #TODO: Implements

        self.update_app_selector()
        self.load_config_defaults()

        self.app_selector.connect("notify::selected-item", self.on_change_app)

        return [self.app_selector]

    def on_change_app(self, *args):
        app = self.app_selector.get_selected_item()
        path = self.get_exec_path_by_name(app.get_string())

        settings = self.get_settings()
        settings["app_path"] = path
        self.set_settings(settings)

    def update_app_selector(self):
        # Clear the model
        for i in range(self.app_model.get_n_items()):
            self.app_model.remove(0)

        for app in self.get_installed_apps():
            self.app_model.append(app)

        self.app_model.append("None")

    def load_config_defaults(self):
        settings = self.get_settings()
        app_path = settings.get("app_path")
        if settings is not None:
            app_path = settings.setdefault("app_path", None)


        for i in range(self.app_model.get_n_items()):
            item = self.app_model.get_item(i).get_string()
            if self.get_exec_path_by_name(item) == app_path:
                self.app_selector.set_selected(i)
                return
            
    def on_key_down(self):
        settings = self.get_settings()
        app_path = settings.get("app_path")
        if app_path is not None:
            subprocess.Popen([app_path], start_new_session=True)