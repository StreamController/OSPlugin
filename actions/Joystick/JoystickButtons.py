from src.backend.PluginManager.ActionBase import ActionBase
import os
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

from evdev import UInput, ecodes as e

from .joy import VirtualJoystick
from GtkHelper.GenerativeUI.ComboRow import ComboRow
from GtkHelper.GenerativeUI.SpinRow import SpinRow
from GtkHelper.GenerativeUI.SwitchRow import SwitchRow
from GtkHelper.ComboRow import BaseComboRowItem, SimpleComboRowItem

class ButtonItem(SimpleComboRowItem):
    def __init__(self, button_name, button_code):
        super().__init__(button_name, button_name)
        self.button_code = button_code

class ActionTypeItem(SimpleComboRowItem):
    def __init__(self, action_name, action_type):
        super().__init__(action_name, action_name)
        self.action_type = action_type

class JoystickButtons(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.has_configuration = True
        self.button_items = [
            ButtonItem("A Button", e.BTN_A),
            ButtonItem("B Button", e.BTN_B),
            ButtonItem("X Button", e.BTN_X),
            ButtonItem("Y Button", e.BTN_Y),
            ButtonItem("Left Bumper", e.BTN_TL),
            ButtonItem("Right Bumper", e.BTN_TR),
            ButtonItem("Left Trigger", e.BTN_TL2),
            ButtonItem("Right Trigger", e.BTN_TR2),
            ButtonItem("Select Button", e.BTN_SELECT),
            ButtonItem("Start Button", e.BTN_START),
            ButtonItem("Home/Guide", e.BTN_MODE),
            ButtonItem("Left Stick Click", e.BTN_THUMBL),
            ButtonItem("Right Stick Click", e.BTN_THUMBR)
        ]
        
        self.action_type_items = [
            ActionTypeItem("Press and Release", "press_release"),
            ActionTypeItem("Press", "press"),
            ActionTypeItem("Release", "release"),
            ActionTypeItem("Toggle", "toggle")
        ]

        # Create button selection dropdown
        self.button_row = ComboRow(
            action_core=self,
            var_name="button",
            default_value=self.button_items[0],
            items=self.button_items,
            title=self.plugin_base.lm.get("actions.joystick-buttons.button.title"),
            subtitle=self.plugin_base.lm.get("actions.joystick-buttons.button.subtitle")
        )
        
        # Create action type dropdown
        self.action_type_row = ComboRow(
            action_core=self,
            var_name="action_type",
            default_value=self.action_type_items[0],
            items=self.action_type_items,
            title=self.plugin_base.lm.get("actions.joystick-buttons.action-type.title"),
            subtitle=self.plugin_base.lm.get("actions.joystick-buttons.action-type.subtitle")
        )
        
        # Duration setting for press and release
        self.duration_row = SpinRow(
            action_core=self,
            var_name="duration",
            default_value=0.1,
            title=self.plugin_base.lm.get("actions.joystick-buttons.duration.title"),
            subtitle=self.plugin_base.lm.get("actions.joystick-buttons.duration.subtitle"),
            min=0.01,
            max=2.0,
            step=0.01,
            digits=2
        )
        
        # Update UI based on selected action type
        self.action_type_row.on_change = self.on_action_type_change
        self.update_ui_visibility()
    
    def on_ready(self):
        self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "controller.png"), size=0.8)
        
    def update_ui_visibility(self):
        """Update UI components visibility based on action type"""
        action_type_item = self.action_type_row.get_selected_item()
        if action_type_item:
            # Only show duration for press_release mode
            show_duration = action_type_item.action_type == "press_release"
            self.duration_row.widget.set_visible(show_duration)
    
    def on_action_type_change(self, widget, new_value, old_value):
        """Handle action type selection change"""
        self.update_ui_visibility()
    
    def on_key_down(self) -> None:
        if not self.plugin_base.gamepad:
            print("Failed to initialize joystick")
            return
        
        settings = self.get_settings()
        
        # Get button and action type
        button_item = self.button_row.get_selected_item()
        action_type_item = self.action_type_row.get_selected_item()
        
        try:
            button_code = button_item.button_code
            action_type = action_type_item.action_type
            
            # Perform button action based on selected type
            if action_type == "press_release":
                duration = float(settings.get("duration", 0.1))
                print(f"Press and release button {button_item.get_value()} for {duration}s")
                self.plugin_base.gamepad.press_button(button_code, duration)
            
            elif action_type == "press":
                print(f"Press button {button_item.get_value()}")
                self.plugin_base.gamepad.ui.write(e.EV_KEY, button_code, 1)  # Button down
                self.plugin_base.gamepad.ui.syn()
            
            elif action_type == "release":
                print(f"Release button {button_item.get_value()}")
                self.plugin_base.gamepad.ui.write(e.EV_KEY, button_code, 0)  # Button up
                self.plugin_base.gamepad.ui.syn()
            
            elif action_type == "toggle":
                # Get current state from settings
                current_state = self.get_button_state(button_code)
                new_state = 1 if current_state == 0 else 0
                
                print(f"Toggle button {button_item.get_value()} to {new_state}")
                self.plugin_base.gamepad.ui.write(e.EV_KEY, button_code, new_state)
                self.plugin_base.gamepad.ui.syn()
                
                # Save the new state
                self.save_button_state(button_code, new_state)
                
        except Exception as ex:
            self.show_error(f"Failed to press joystick button: {str(ex)}")
    
    def get_button_state(self, button_code):
        """Get the current state of a button for toggle mode"""
        settings = self.get_settings()
        button_states = settings.get("button_states", {})
        return int(button_states.get(str(button_code), 0))
    
    def save_button_state(self, button_code, state):
        """Save the current state of a button for toggle mode"""
        settings = self.get_settings()
        if "button_states" not in settings:
            settings["button_states"] = {}
        settings["button_states"][str(button_code)] = state
        self.set_settings(settings)
    
    def show_error(self, message):
        self.plugin_base.logger.error(message) 