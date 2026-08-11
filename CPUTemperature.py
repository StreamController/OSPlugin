from GtkHelper.ComboRow import SimpleComboRowItem

import psutil

# The units the temperature can be shown in, the sensors always report celsius
UNITS = ["C", "F"]

def get_unit_items() -> list[SimpleComboRowItem]:
    return [SimpleComboRowItem("C", "°C"), SimpleComboRowItem("F", "°F")]

def celcius_to_fahrenheit(celsius: float) -> float:
    return celsius * 1.8 + 32

# The sensor to read per chip, in order of preference. These are the package and control
# sensors that monitoring tools like btop show. The per core and per die sensors next to them
# (Core 0, Tccd1, ...) follow every boost of a single core, which swings by tens of degrees
# between two reads and is far too sporadic to put on a key.
PREFERRED_SENSORS = {
    "coretemp": ["Package id 0"],  # intel
    "k10temp": ["Tctl", "Tdie"],   # amd
}

# Picks the sensor above instead of a specific one
AUTO = "auto"

# Chips that only report cpu temperatures, so every sensor on them is one. Covers intel
# (coretemp), amd (k10temp, k8temp, the third party zenpower), arm boards (cpu_thermal) and the
# acpi thermal zone that laptops and virtual machines fall back to.
CPU_CHIPS = ["coretemp", "k10temp", "k8temp", "zenpower", "cpu_thermal", "acpitz"]

# Chips that mix cpu sensors with board ones only name them, like the "CPU" sensor of the
# embedded controller on asus boards or the "CPUTIN" one of super i/o chips
CPU_NAME = "cpu"

def is_cpu_sensor(chip: str, sensor) -> bool:
    if chip in CPU_CHIPS or CPU_NAME in chip.lower():
        return True

    return CPU_NAME in (sensor.label or "").lower()

def get_sensor_item(chip: str, index: int, sensor) -> SimpleComboRowItem:
    label = sensor.label or f"Sensor {index}"
    return SimpleComboRowItem(f"{chip}:{index}", f"{chip}: {label}")

def get_sensor_items() -> list[SimpleComboRowItem]:
    """The cpu sensors of this machine, to let the user pick one themselves."""

    temperatures = psutil.sensors_temperatures()

    items = [SimpleComboRowItem(AUTO, "Auto")]
    for chip, sensors in temperatures.items():
        for index, sensor in enumerate(sensors):
            if is_cpu_sensor(chip, sensor):
                items.append(get_sensor_item(chip, index, sensor))

    # Nothing on this machine is recognizable as a cpu sensor, offering all of them beats
    # offering none of them
    if len(items) == 1:
        for chip, sensors in temperatures.items():
            for index, sensor in enumerate(sensors):
                items.append(get_sensor_item(chip, index, sensor))

    return items

def get_auto_temp(temperatures: dict) -> float | None:
    for chip, labels in PREFERRED_SENSORS.items():
        sensors = temperatures.get(chip)
        if not sensors:
            continue

        for label in labels:
            for sensor in sensors:
                if sensor.label == label:
                    return sensor.current

        # Unknown sensor layout, the package sensor comes first on every chip we know of
        return sensors[0].current

    # Neither an intel nor an amd chip, take the first sensor that reads the cpu at all
    for chip, sensors in temperatures.items():
        for sensor in sensors:
            if is_cpu_sensor(chip, sensor):
                return sensor.current

    return None

def get_cpu_temp(sensor: str = AUTO) -> float | None:
    """
    Returns the temperature of the selected sensor in celsius, or None if it is not available.
    A sensor is stored as "chip:index", anything else falls back to the preferred sensor.
    """

    temperatures = psutil.sensors_temperatures()

    if sensor and sensor != AUTO:
        chip, _, index = sensor.rpartition(":")
        sensors = temperatures.get(chip, [])

        if index.isdigit() and int(index) < len(sensors):
            return sensors[int(index)].current

        # The picked sensor is gone, a missing reading is worse than a different one
    return get_auto_temp(temperatures)

def convert_temp(celsius: float, unit: str) -> float:
    if unit == "F":
        return celcius_to_fahrenheit(celsius)
    return celsius
