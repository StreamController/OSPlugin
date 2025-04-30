#!/usr/bin/env python3

"""
Joystick emulation module using evdev
"""

from evdev import UInput, ecodes as e, AbsInfo
import time
import math

class VirtualJoystick:
    def __init__(self, name="virtual-joystick-streamcontroller", system_ui=None):
        # Define capabilities for a typical joystick with proper AbsInfo objects
        # Specifically not including ABS_X and ABS_Y to avoid mouse movement
        # Instead use ABS_RZ and ABS_THROTTLE for additional axes
        capabilities = {
            e.EV_KEY: [e.BTN_A, e.BTN_B, e.BTN_X, e.BTN_Y, 
                       e.BTN_TL, e.BTN_TR, e.BTN_TL2, e.BTN_TR2, 
                       e.BTN_SELECT, e.BTN_START, e.BTN_MODE,
                       e.BTN_THUMBL, e.BTN_THUMBR],
            e.EV_ABS: [
                # Alternative axes that don't affect mouse
                (e.ABS_RZ, AbsInfo(value=0, min=-32767, max=32767, fuzz=0, flat=0, resolution=0)),
                (e.ABS_THROTTLE, AbsInfo(value=0, min=-32767, max=32767, fuzz=0, flat=0, resolution=0)),
                # Standard gamepad axes
                (e.ABS_RX, AbsInfo(value=0, min=-32767, max=32767, fuzz=0, flat=0, resolution=0)),
                (e.ABS_RY, AbsInfo(value=0, min=-32767, max=32767, fuzz=0, flat=0, resolution=0)),
                (e.ABS_HAT0X, AbsInfo(value=0, min=-1, max=1, fuzz=0, flat=0, resolution=0)),
                (e.ABS_HAT0Y, AbsInfo(value=0, min=-1, max=1, fuzz=0, flat=0, resolution=0)),
                # Include original X/Y axes for completeness but not recommended
                (e.ABS_X, AbsInfo(value=0, min=-32767, max=32767, fuzz=0, flat=0, resolution=0)),
                (e.ABS_Y, AbsInfo(value=0, min=-32767, max=32767, fuzz=0, flat=0, resolution=0)),
            ]
        }

        self.axis_values: dict = {}
        
        # Create the UInput device
        print()
        self.ui = system_ui if system_ui else UInput(capabilities, name=name, phys="virtual-gamepad")
        self.system_ui = system_ui
        print(f"Created virtual joystick: {name}")

        self.center_all()
    
    def move_axis(self, axis, value):
        """Move an axis to a specific value."""
        # Map potentially problematic axes to alternative axes if system_ui not provided
        if not self.system_ui and axis == e.ABS_X:
            print(f"Warning: ABS_X (0) may affect mouse, consider using ABS_RZ (5) instead")
            # Optionally use an alternative axis that doesn't affect mouse
            # axis = e.ABS_RZ  # Uncomment to automatically redirect
        
        if not self.system_ui and axis == e.ABS_Y:
            print(f"Warning: ABS_Y (1) may affect mouse, consider using ABS_THROTTLE (6) instead")
            # Optionally use an alternative axis that doesn't affect mouse
            # axis = e.ABS_THROTTLE  # Uncomment to automatically redirect
        
        self.ui.write(e.EV_ABS, axis, value)
        self.ui.syn()
    
    def press_button(self, button, duration=0.1):
        """Press a button for a specified duration."""
        self.ui.write(e.EV_KEY, button, 1)  # Button down
        self.ui.syn()
        time.sleep(duration)
        self.ui.write(e.EV_KEY, button, 0)  # Button up
        self.ui.syn()
    
    def move_dpad(self, x, y):
        """Move the D-pad (hat) in a direction (-1, 0, 1 for each axis)."""
        self.ui.write(e.EV_ABS, e.ABS_HAT0X, x)  # -1 left, 0 center, 1 right
        self.ui.write(e.EV_ABS, e.ABS_HAT0Y, y)  # -1 up, 0 center, 1 down
        self.ui.syn()
    
    def circle_movement(self, duration=5, steps=100):
        """Move the left stick in a circle pattern."""
        print(f"Moving left stick in a circle for {duration} seconds...")
        start_time = time.time()
        
        while time.time() - start_time < duration:
            progress = (time.time() - start_time) / duration
            angle = progress * 2 * math.pi
            
            # Calculate X and Y coordinates on the circle
            x = int(32767 * math.cos(angle))
            y = int(32767 * math.sin(angle))
            
            # Use alternative axes that don't affect mouse
            self.move_axis(e.ABS_RZ, x)
            self.move_axis(e.ABS_THROTTLE, y)
            
            time.sleep(duration / steps)
    
    def center_all(self):
        """Center all joystick axes."""
        # Center all axes
        for axis in [e.ABS_X, e.ABS_Y, e.ABS_RX, e.ABS_RY, e.ABS_RZ, e.ABS_THROTTLE]:
            self.move_axis(axis, 0)
        self.move_dpad(0, 0)
    
    def close(self):
        """Close the joystick device."""
        if hasattr(self, 'ui') and not self.system_ui:
            self.ui.close()

    def get_last_axis_value(self, axis_code):
        return self.axis_values.get(axis_code, 0)
    
    def save_axis_value(self, axis_code, value):
        self.axis_values[axis_code] = value

if __name__ == "__main__":
    joystick = VirtualJoystick()
    input()
    while True:
        joystick.circle_movement(10)
        joystick.center_all()
        time.sleep(1)