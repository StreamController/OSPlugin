# Streamcontroller OS Plugin

streamcontroller official plugin to do OS Related actions

## Actions

- **CPU**: Displays the current CPU usage percentage on the button.
- **CPU Temperature**: Shows the current CPU temperature in Celsius or Fahrenheit.
- **CPU Graph**: Displays a real-time graph of CPU usage over time.
- **RAM**: Displays the current RAM usage percentage on the button.
- **RAM Graph**: Displays a real-time graph of RAM usage over time.
- **Hotkey**: Execute custom keyboard shortcuts with precise control over key press and release timing.
- **Hotkey from text**: Execute keyboard shortcuts using simple text notation (e.g., "ctrl+c").
- **Write Text**: Types out configured text automatically when the button is pressed.
- **Run Command**: Executes shell commands with options for displaying output and auto-running at intervals.
- **Easy Command**: Simple action to run a shell command when the button is pressed.
- **Launch**: Opens a selected application from your system's installed apps.
- **Open In Browser**: Opens a specified URL in your default web browser.
- **Click**: Simulates mouse clicks (left, middle, or right button).
- **Move XY**: Moves the mouse cursor to specific X and Y coordinates on the screen.
- **Delay**: Adds a configurable time delay between actions in a multi-action sequence.

## Hotkeys & Write text

Hotkeys and write text actions require you are in the input group and you have the following udev rule

1. Add the udev rule
    ```
    sudo sh -c "echo 'KERNEL==\"uinput\", SUBSYSTEM==\"misc\", OPTIONS+=\"static_node=uinput\", TAG+=\"uaccess\", GROUP=\"input\", MODE=\"0660\"' > /etc/udev/rules.d/99-streamdeck-osplugin.rules"
    ```
2. Create the input Group (if not already present):
    ```sh
    sudo groupadd input
    ```
3. Add yourself to the `input` group
    ```sh
    sudo usermod -aG input $USER
    ```
4. Restart your computer to apply the changes
