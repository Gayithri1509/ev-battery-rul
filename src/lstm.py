import numpy as np
import pandas as pd
import torch
from torch import nn

from src.data import BATTERIES, add_targets, load_all
from src.features import build_features
from src.train import PARTIAL

WINDOW = 10  # how many recent cycles the model reads at once


def make_windows(a, w=WINDOW):
    """For each row, the last w rows of the SAME battery (first rows padded with row 0)."""
    padded = np.vstack([np.repeat(a[:1], w - 1, axis=0), a])
    return np.stack([padded[i : i + w] for i in range(len(a))])


class Net(nn.Module):
    def __init__(self, n_feat, hidden=32):
        super().__init__()
        self.lstm = nn.LSTM(n_feat, hidden, batch_first=True)
        self.head = nn.Linear(hidden, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.head(out[:, -1, :]).squeeze(-1)


def fit_predict(Xtr, ytr, Xte, seeds=(0, 1, 2), epochs=150):
    """Xtr, Xte: (n, WINDOW, n_feat). Returns the prediction averaged over seeds."""
    n_feat = Xtr.shape[2]
    med = np.nanmedian(Xtr.reshape(-1, n_feat), axis=0)  # fill gaps with TRAIN medians
    Xtr = np.where(np.isnan(Xtr), med, Xtr)
    Xte = np.where(np.isnan(Xte), med, Xte)
    mu = Xtr.reshape(-1, n_feat).mean(axis=0)
    sd = Xtr.reshape(-1, n_feat).std(axis=0) + 1e-8
    Xtr, Xte = (Xtr - mu) / sd, (Xte - mu) / sd
    ymu, ysd = ytr.mean(), ytr.std()

    xt = torch.tensor(Xtr, dtype=torch.float32)
    yt = torch.tensor((ytr - ymu) / ysd, dtype=torch.float32)
    xe = torch.tensor(Xte, dtype=torch.float32)

    preds = []
    for seed in seeds:
        torch.manual_seed(seed)
        net = Net(n_feat)
        opt = torch.optim.Adam(net.parameters(), lr=0.005, weight_decay=1e-4)
        loss_fn = nn.MSELoss()
        for _ in range(epochs):
            perm = torch.randperm(len(xt))
            for i in range(0, len(xt), 32):
                idx = perm[i : i + 32]
                opt.zero_grad()
                loss_fn(net(xt[idx]), yt[idx]).backward()
                opt.step()
        net.eval()
        with torch.no_grad():
            preds.append(net(xe).numpy())
    return np.mean(preds, axis=0) * ysd + ymu


def prepare(target, rule):
    df = add_targets(load_all(), rule=rule)
    X = build_features(df)
    X["cycle"] = df["cycle"]
    cols = PARTIAL + ["cycle"] if target == "rul" else PARTIAL
    if target == "rul":
        ok = (df["rul"].notna() & (df["rul"] >= 0)).to_numpy()  # B0007 drops out here
        y = df["rul"]
    else:
        ok = np.ones(len(df), dtype=bool)
        y = df["capacity"]
    df = df[ok].reset_index(drop=True)
    X = X.loc[ok, cols].reset_index(drop=True)
    return df, X, y[ok].to_numpy(dtype=float)


def run_lstm(target="rul", rule="first"):
    """Leave-one-battery-out with the LSTM. target is "rul" or "capacity"."""
    df, X, y = prepare(target, rule)
    name = "lstm | partial_curve" + ("+cycle" if target == "rul" else "")
    parts = {}
    for b in BATTERIES:
        m = (df["battery"] == b).to_numpy()
        if m.any():
            parts[b] = (make_windows(X[m].to_numpy(dtype=float)), y[m])

    rows = []
    for held_out in parts:
        train_b = [b for b in parts if b != held_out]
        Xtr = np.concatenate([parts[b][0] for b in train_b])
        ytr = np.concatenate([parts[b][1] for b in train_b])
        Xte, yte = parts[held_out]
        err = fit_predict(Xtr, ytr, Xte) - yte
        row = {
            "held_out": held_out,
            "model": name,
            "mae": np.abs(err).mean(),
            "rmse": np.sqrt((err ** 2).mean()),
        }
        if target == "rul":
            row.update(rule=rule, mae_cycles=row["mae"], mae_last30=np.abs(err[yte <= 30]).mean())
        rows.append(row)
    return pd.DataFrame(rows)


def show(res, value, title):
    t = res.pivot(index="model", columns="held_out", values=value)
    t["mean"] = t.mean(axis=1)
    print(f"\n{title}")
    print(t.round(3 if value == "mae" else 1).sort_values("mean"))


if __name__ == "__main__":
    cap = run_lstm("capacity")
    cap.to_csv("notebooks/results_lstm_capacity.csv", index=False)
    show(pd.concat([pd.read_csv("notebooks/results_capacity.csv"), cap]), "mae",
         "Capacity | MAE in Ah (lower is better)")

    rul = pd.concat([run_lstm("rul", "first"), run_lstm("rul", "permanent")])
    rul.to_csv("notebooks/results_lstm_rul.csv", index=False)
    base = pd.read_csv("notebooks/results_rul.csv")
    for rule in ["first", "permanent"]:
        both = pd.concat([base[base["rule"] == rule], rul[rul["rule"] == rule]])
        for metric in ["mae_cycles", "mae_last30"]:
            show(both, metric, f"RUL | EOL rule: {rule} | {metric} (lower is better)")