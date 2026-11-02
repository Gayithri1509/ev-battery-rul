import numpy as np
import pandas as pd

V_LEVELS = [4.0, 3.8, 3.6, 3.4, 3.2, 3.0]


def _at_voltage(v, level):
    """Index of the first sample at or below `level` volts, or None."""
    idx = np.where(v <= level)[0]
    return int(idx[0]) if len(idx) else None


def cycle_features(time, voltage, current, temperature):
    """Clues from one discharge curve. Total discharge time is left out on purpose."""
    t = np.asarray(time, dtype=float)
    v = np.asarray(voltage, dtype=float)
    i = np.abs(np.asarray(current, dtype=float))
    temp = np.asarray(temperature, dtype=float)

    # charge delivered so far, in Ah (simple sum of current x time step)
    q = np.concatenate([[0.0], np.cumsum(i[1:] * np.diff(t))]) / 3600.0

    feat = {}
    q_at, t_at = {}, {}
    for lvl in V_LEVELS:
        k = _at_voltage(v, lvl)
        q_at[lvl] = q[k] if k is not None else np.nan
        t_at[lvl] = t[k] if k is not None else np.nan
    for lvl in V_LEVELS[1:]:
        feat[f"t_to_{lvl}"] = t_at[lvl]
    for hi, lo in zip(V_LEVELS[:-1], V_LEVELS[1:]):
        feat[f"dq_{hi}_{lo}"] = q_at[lo] - q_at[hi]

    feat["v_mean"] = v.mean()
    feat["v_std"] = v.std()
    feat["i_mean"] = i.mean()
    feat["temp_mean"] = temp.mean()
    feat["temp_max"] = temp.max()
    feat["temp_rise"] = temp.max() - temp[0]
    return feat


def build_features(df):
    """One row of features per discharge row of the table from load_all()."""
    rows = [
        cycle_features(r.time, r.voltage, r.current, r.temperature)
        for r in df.itertuples()
    ]
    return pd.DataFrame(rows, index=df.index)