# Streamcontroller OS Plugin

streamcontroller official plugin to do OS Related actions

## Hotkeys & Write text

Hotkeys and write text actions require you are in the input group and you have the following udev rules

```
KERNEL=="uinput", SUBSYSTEM=="misc", OPTIONS+="static_node=uinput", TAG+="uaccess", GROUP="input", MODE="0660"
```
