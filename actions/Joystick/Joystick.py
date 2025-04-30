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

class AxisItem(SimpleComboRowItem):
    def __init__(self, axis_name, axis_code, affects_mouse=False):
        display_name = axis_name
        if affects_mouse:
            display_name = f"{axis_name} ⚠️"
        super().__init__(axis_name, display_name)
        self.axis_code = axis_code
        self.affects_mouse = affects_mouse

class OperationItem(SimpleComboRowItem):
    def __init__(self, operation_name, operation_type):
        super().__init__(operation_name, operation_name)
        self.operation_type = operation_type

class Joystick(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.has_configuration = True
        self.joystick = None
        self.axis_items = [
            AxisItem("Left X (ABS_RZ)", e.ABS_RZ),
            AxisItem("Left Y (ABS_THROTTLE)", e.ABS_THROTTLE),
            AxisItem("Right X (ABS_RX)", e.ABS_RX),
            AxisItem("Right Y (ABS_RY)", e.ABS_RY),
            AxisItem("D-pad X", e.ABS_HAT0X),
            AxisItem("D-pad Y", e.ABS_HAT0Y),
            AxisItem("X Axis (ABS_X)", e.ABS_X, affects_mouse=True),
            AxisItem("Y Axis (ABS_Y)", e.ABS_Y, affects_mouse=True)
        ]
        
        self.operation_items = [
            OperationItem("Set Value", "set"),
            OperationItem("Add to Value", "add")
        ]

        # Create axis selection dropdown
        self.axis_row = ComboRow(
            action_core=self,
            var_name="axis",
            default_value=self.axis_items[0],
            items=self.axis_items,
            title=self.plugin_base.lm.get("actions.joystick.axis.title"),
            subtitle=self.plugin_base.lm.get("actions.joystick.axis.subtitle"),
            on_change=self.on_axis_change
        )
        
        # Create operation type dropdown
        self.operation_row = ComboRow(
            action_core=self,
            var_name="operation",
            default_value=self.operation_items[0],
            items=self.operation_items,
            title=self.plugin_base.lm.get("actions.joystick.operation.title"),
            subtitle=self.plugin_base.lm.get("actions.joystick.operation.subtitle"),
            on_change=self.on_operation_change
        )
        
        # Create value spin
        self.value_row = SpinRow(
            action_core=self,
            var_name="value",
            default_value=0,
            title=self.plugin_base.lm.get("actions.joystick.value.title"),
            subtitle=self.plugin_base.lm.get("actions.joystick.value.subtitle"),
            min=-32767,
            max=32767,
            step=100,
            digits=0
        )
        
        # Warning label for mouse-affecting axes
        self.warning_label = Gtk.Label(
            label="⚠️ Warning: Using this axis may affect mouse cursor position",
            halign=Gtk.Align.START,
            css_classes=["warning-text"]
        )
        self.warning_row = Adw.ActionRow()
        self.warning_row.set_child(self.warning_label)
        self.warning_row.set_visible(False)
        
        # Center button row
        self.center_row = Adw.ActionRow(
            title="Center Axis",
            subtitle="Reset the selected axis to center position"
        )
        
        center_button = Gtk.Button(label="Center", vexpand=True)
        center_button.connect("clicked", self.on_center_clicked)
        self.center_row.add_suffix(center_button)
        
        # Update UI based on current settings
        self.update_axis_range()
    
    def on_ready(self):
        self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "joystick.png"), size=0.8)
        
    
    def update_axis_range(self):
        """Update UI components based on current settings"""
        # Adjust the value range based on the selected axis
        axis_item = self.axis_row.get_selected_item()
        if axis_item:
            self.update_value_range_for_axis(axis_item.axis_code)
            self.warning_row.set_visible(hasattr(axis_item, 'affects_mouse') and axis_item.affects_mouse)
    
    def update_value_range_for_axis(self, axis_code):
        """Update value spinner range based on selected axis"""
        if axis_code in [e.ABS_HAT0X, e.ABS_HAT0Y]:
            self.value_row.min = -1
            self.value_row.max = 1
            self.value_row.step = 1
        else:
            self.value_row.min = -100
            self.value_row.max = 100
            self.value_row.step = 1
    
    def on_axis_change(self, widget, new_value, old_value):
        """Handle axis selection change"""
        if hasattr(new_value, 'axis_code'):
            self.update_value_range_for_axis(new_value.axis_code)
            self.warning_row.set_visible(hasattr(new_value, 'affects_mouse') and new_value.affects_mouse)
    
    def on_operation_change(self, widget, new_value, old_value):
        """Handle operation type change"""
        # You can adjust UI based on operation if needed
        pass
    
    def on_center_clicked(self, button):
        """Center the selected axis"""
        if not self.plugin_base.gamepad:
            return
            
        axis_item = self.axis_row.get_selected_item()
        if axis_item:
            self.plugin_base.gamepad.move_axis(axis_item.axis_code, 0)
            self.plugin_base.gamepad.save_axis_value(axis_item.axis_code, 0)
    
    def on_key_down(self) -> None:
        if not self.plugin_base.gamepad:
            print("failed to initialize joystick")
            return
        
        settings = self.get_settings()
        
        # Get the axis, operation and value
        axis_item = self.axis_row.get_selected_item()
        operation_item = self.operation_row.get_selected_item()
        percentage_value = int(settings.get("value", 0))  # Convert to integer
        
        try:
            axis_code = axis_item.axis_code
            operation = operation_item.operation_type
            
            # Convert percentage value to actual joystick value
            if axis_code in [e.ABS_HAT0X, e.ABS_HAT0Y]:
                value = percentage_value  # D-pad values are already -1, 0, 1
            else:
                # Convert from percentage (-100 to 100) to joystick value (-32767 to 32767)
                value = int((percentage_value / 100.0) * 32767)
            
            print(f"Axis: {axis_item.axis_code}, Operation: {operation_item.operation_type}, Percentage: {percentage_value}, Value: {value}")
            
            # Perform the joystick action
            if operation == "set":
                self.plugin_base.gamepad.move_axis(axis_code, value)
                # Save the new state (as percentage)
                self.plugin_base.gamepad.save_axis_value(axis_code, percentage_value)
            elif operation == "add":
                # For "add" operation, we need to implement a way to get current position
                # Since we can't directly read from the virtual joystick, we'll need to track state
                current_percentage = self.plugin_base.gamepad.get_last_axis_value(axis_code)
                new_percentage = current_percentage + percentage_value
                
                # Clamp values to appropriate range
                if axis_code in [e.ABS_HAT0X, e.ABS_HAT0Y]:
                    new_percentage = max(-1, min(1, new_percentage))
                    new_value = new_percentage
                else:
                    new_percentage = max(-100, min(100, new_percentage))
                    new_value = int((new_percentage / 100.0) * 32767)
                
                self.plugin_base.gamepad.move_axis(axis_code, int(new_value))  # Convert to integer
                self.plugin_base.gamepad.save_axis_value(axis_code, new_percentage)
                
        except Exception as ex:
            self.show_error(f"Failed to move joystick: {str(ex)}")
    
    def show_error(self, message):
        self.plugin_base.logger.error(message) 