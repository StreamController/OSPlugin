from GtkHelper.ComboRow import SimpleComboRowItem
from GtkHelper.GenerativeUI.ComboRow import ComboRow

# The label rows an action can write its value to, plus the option to not show one at all
POSITIONS = ["top", "center", "bottom"]
OFF = "off"

def get_position_items(include_off: bool = False) -> list[SimpleComboRowItem]:
    items = []
    if include_off:
        items.append(SimpleComboRowItem(OFF, "Off"))

    items.append(SimpleComboRowItem("top", "Top"))
    items.append(SimpleComboRowItem("center", "Center"))
    items.append(SimpleComboRowItem("bottom", "Bottom"))

    return items

def create_position_row(action_core, on_change: callable = None, default_value: str = "center",
                        include_off: bool = False, title: str = "Label Position") -> ComboRow:
    return ComboRow(
        action_core=action_core,
        var_name="label_position",
        default_value=default_value,
        items=get_position_items(include_off),
        title=title,
        can_reset=False,
        on_change=on_change
    )

def set_positioned_label(action_core, position_row: ComboRow, text: str,
                         center_font_size: int = 18, side_font_size: int = 15,
                         fallback: str = "center"):
    """
    Writes text to the label row the user selected and clears the other rows, so the value does
    not stay behind after a position change. The side rows get a smaller font than the center one
    because they are a lot shorter.
    """

    # The generative ui fires its on_change before the action is ready
    if not action_core.on_ready_called:
        return

    position = position_row.get_value()
    if position not in POSITIONS + [OFF]:
        position = fallback

    for other in POSITIONS:
        if other != position:
            action_core.set_label(text="", position=other)

    if position == OFF:
        return

    font_size = center_font_size if position == "center" else side_font_size
    action_core.set_label(text=text, position=position, font_size=font_size)
