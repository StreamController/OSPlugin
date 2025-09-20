# Streamcontroller OS Plugin

streamcontroller official plugin to do OS Related actions

## Hotkeys & Write text

Hotkeys and write text actions require you are in the input group and you have the following udev rule

1. Add the udev rule
    ```bash
    sudo sh -c "echo 'ACTION!=\"remove\", KERNEL==\"uinput\", SUBSYSTEM==\"misc\", OPTIONS+=\"static_node=uinput\", TAG+=\"uaccess\", GROUP=\"input\", MODE=\"0660\"' > /etc/udev/rules.d/99-streamdeck-osplugin.rules"
    ```
2. Restart your computer to apply the changes
