import numpy as np
import pandas as pd
from scipy.io import loadmat
BATTERIES = ["B0005", "B0006", "B0007", "B0018"]

def load_battery(name, data_dir="data"):
    """Return the list of cycle entries for one battery, e.g. name="B0005"."""
    m = loadmat(f"{data_dir}/{name}.mat", struct_as_record=False, squeeze_me=True)
    return m[name].cycle


def load_discharges(name, data_dir="data"):
    """One row per discharge: battery, cycle, capacity + raw curves as arrays."""
    rows = []
    n = 0
    for entry in load_battery(name, data_dir):
        if entry.type == "discharge":
            rows.append({
                "battery": name,
                "cycle": n,
                "capacity": entry.data.Capacity,
                "voltage": entry.data.Voltage_measured,
                "current": entry.data.Current_measured,
                "temperature": entry.data.Temperature_measured,
                "time": entry.data.Time,
            })
            n += 1
    return pd.DataFrame(rows)

def load_all(names=BATTERIES, data_dir="data"):
    """Stack the discharge tables of all batteries into one table."""
    return pd.concat([load_discharges(n, data_dir) for n in names], ignore_index=True)
RATED_AH = 2.0
EOL_AH = 1.4


def eol_cycle(capacity, threshold=EOL_AH, rule="first"):
    """Cycle where life ends, or None if capacity never reaches the threshold.

    rule="first": first cycle at or below the threshold.
    rule="permanent": first cycle after the last time capacity was above it.
    """
    below = [i for i, x in enumerate(capacity) if x <= threshold]
    if not below:
        return None
    if rule == "first":
        return below[0]
    above = [i for i, x in enumerate(capacity) if x > threshold]
    if not above:
        return below[0]
    if above[-1] + 1 >= len(capacity):
        return None
    return above[-1] + 1


def add_targets(df, rule="first"):
    """Add soh, eol and rul columns. RUL = EOL cycle - current cycle."""
    df = df.copy()
    df["soh"] = df["capacity"] / RATED_AH
    eols = {}
    for name, g in df.groupby("battery"):
        e = eol_cycle(g.sort_values("cycle")["capacity"].tolist(), rule=rule)
        eols[name] = np.nan if e is None else e
    df["eol"] = df["battery"].map(eols)
    df["rul"] = df["eol"] - df["cycle"]
    return df