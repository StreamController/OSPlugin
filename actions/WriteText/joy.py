#!/usr/bin/env python3

"""
Joystick emulation script using evdev
"""

from evdev import UInput, ecodes as e, AbsInfo
import time
import math

class VirtualJoystick:
    def __init__(self, name="virtual-joystick-nnice"):
        # Define capabilities for a typical joystick with proper AbsInfo objects
        capabilities = {
            e.EV_KEY: [e.BTN_A, e.BTN_B, e.BTN_X, e.BTN_Y],
            e.EV_ABS: [
                (e.ABS_X, AbsInfo(value=0, min=-32767, max=32767, fuzz=0, flat=0, resolution=0)),
                (e.ABS_Y, AbsInfo(value=0, min=-32767, max=32767, fuzz=0, flat=0, resolution=0)),
                (e.ABS_RX, AbsInfo(value=0, min=-32767, max=32767, fuzz=0, flat=0, resolution=0)),
                (e.ABS_RY, AbsInfo(value=0, min=-32767, max=32767, fuzz=0, flat=0, resolution=0)),
                (e.ABS_HAT0X, AbsInfo(value=0, min=-1, max=1, fuzz=0, flat=0, resolution=0)),
                (e.ABS_HAT0Y, AbsInfo(value=0, min=-1, max=1, fuzz=0, flat=0, resolution=0)),
            ]
        }
        
        # Create the UInput device
        self.ui = UInput(capabilities, name=name)
        print(f"Created virtual joystick: {name}")
    
    def move_axis(self, axis, value):
        """Move an axis to a specific value."""
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
            
            # Move the joystick
            self.move_axis(e.ABS_X, x)
            self.move_axis(e.ABS_Y, y)
            
            time.sleep(duration / steps)
    
    def demo(self, duration=10):
        """Run a demo of joystick capabilities."""
        print("Starting joystick demo...")
        
        # Press some buttons
        print("Testing buttons...")
        for button in [e.BTN_A, e.BTN_B, e.BTN_X, e.BTN_Y]:
            self.press_button(button, 0.2)
            time.sleep(0.1)
        
        # Move axes
        print("Testing D-pad...")
        directions = [(0, -1), (1, 0), (0, 1), (-1, 0), (0, 0)]  # Up, Right, Down, Left, Center
        for x, y in directions:
            self.move_dpad(x, y)
            time.sleep(0.5)
        
        # Run circular pattern on left stick
        self.circle_movement(duration=3)
        
        # Center all axes
        print("Centering all axes...")
        self.move_axis(e.ABS_X, 0)
        self.move_axis(e.ABS_Y, 0)
        self.move_axis(e.ABS_RX, 0)
        self.move_axis(e.ABS_RY, 0)
        self.move_dpad(0, 0)
        
        print("Demo completed!")

# Test the virtual joystick if this script is run directly
if __name__ == "__main__":
    try:
        joystick = VirtualJoystick()
        # joystick.demo()
        input("Press Enter to start")
        joystick.move_axis(1, 32767)
        print("Joystick will remain active. Press Ctrl+C to exit.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting joystick emulation...")
    finally:
        if 'joystick' in locals():
            joystick.ui.close()
