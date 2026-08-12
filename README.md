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

### Troubleshooting

If the hotkey and write text actions don't do anything (or their config shows "Missing permission") even though you followed the steps above:

1. Check the permissions of the uinput device:
    ```sh
    ls -l /dev/uinput
    ```
    It should be owned by the `input` group and be group read- and writable (`crw-rw----`).
2. Make sure no other udev rule overrides the one above. Rules for `uinput` left behind by other Stream Deck tools are a common cause:
    ```sh
    grep -rl uinput /etc/udev/rules.d /usr/lib/udev/rules.d
    ```
    Remove the conflicting files and keep `99-streamdeck-osplugin.rules`.
3. Reload the rules and reboot:
    ```sh
    sudo udevadm control --reload-rules && sudo udevadm trigger
    ```
