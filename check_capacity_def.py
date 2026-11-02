import numpy as np

from src.data import load_all

df = load_all()


def ah(t, i, v, stop_v=None):
    """Charge delivered in Ah, optionally stopping when voltage first reaches stop_v."""
    t = np.asarray(t, float)
    i = np.abs(np.asarray(i, float))
    v = np.asarray(v, float)
    end = len(t)
    if stop_v is not None:
        k = np.where(v <= stop_v)[0]
        if len(k):
            end = k[0] + 1
    return np.sum(i[1:end] * np.diff(t[:end])) / 3600.0


df["ah_full"] = [ah(r.time, r.current, r.voltage) for r in df.itertuples()]
df["ah_to_2.7"] = [ah(r.time, r.current, r.voltage, 2.7) for r in df.itertuples()]
df["min_v"] = df["voltage"].apply(lambda a: float(np.min(a)))

for name, g in df.groupby("battery"):
    print(
        name,
        "| lowest voltage:", round(g["min_v"].min(), 2),
        "| error if full discharge:", round((g["ah_full"] - g["capacity"]).abs().mean(), 3),
        "| error if stopped at 2.7 V:", round((g["ah_to_2.7"] - g["capacity"]).abs().mean(), 3),
    )