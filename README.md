# Streamcontroller OS Plugin

streamcontroller official plugin to do OS Related actions

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
