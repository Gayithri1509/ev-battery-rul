import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.data import BATTERIES, add_targets, load_all
from src.features import build_features

# early part of the curve only: does not depend on the cutoff voltage
PARTIAL = ["t_to_3.8", "t_to_3.6", "t_to_3.4", "dq_4.0_3.8", "dq_3.8_3.6", "dq_3.6_3.4"]


def lobo_capacity():
    """Leave-one-battery-out: predict capacity (Ah) of the held-out battery."""
    df = add_targets(load_all())
    X = build_features(df)
    X["cycle"] = df["cycle"]
    y = df["capacity"]
    sets = {
        "all_features": [c for c in X.columns if c != "cycle"],
        "partial_curve": PARTIAL,
    }

    rows = []
    for held_out in BATTERIES:
        train = (df["battery"] != held_out).to_numpy()
        test = ~train
        ytr, yte = y[train], y[test].to_numpy()

        preds = {
            "naive_mean": np.full(test.sum(), ytr.mean()),
            "linear_cycle_only": LinearRegression()
            .fit(X.loc[train, ["cycle"]], ytr)
            .predict(X.loc[test, ["cycle"]]),
        }
        for s, cols in sets.items():
            lin = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LinearRegression())
            lin.fit(X.loc[train, cols], ytr)
            preds[f"linear | {s}"] = lin.predict(X.loc[test, cols])

            gbm = LGBMRegressor(
                n_estimators=300, learning_rate=0.05, num_leaves=15,
                min_child_samples=10, random_state=0, verbose=-1,
            )
            gbm.fit(X.loc[train, cols], ytr)
            preds[f"lightgbm | {s}"] = gbm.predict(X.loc[test, cols])

        for model, p in preds.items():
            err = p - yte
            rows.append({
                "held_out": held_out,
                "model": model,
                "mae": np.abs(err).mean(),
                "rmse": np.sqrt((err ** 2).mean()),
            })
    return pd.DataFrame(rows)


def lobo_rul(rule="first"):
    """Leave-one-battery-out RUL in cycles. Only cycles before EOL are used."""
    df = add_targets(load_all(), rule=rule)
    X = build_features(df)
    X["cycle"] = df["cycle"]
    ok = (df["rul"].notna() & (df["rul"] >= 0)).to_numpy()  # B0007 drops out here
    df, X = df[ok], X[ok]
    y = df["rul"]
    sets = {
        "all_features+cycle": list(X.columns),
        "partial_curve+cycle": PARTIAL + ["cycle"],
    }

    rows = []
    for held_out in [b for b in BATTERIES if b != "B0007"]:
        train = (df["battery"] != held_out).to_numpy()
        test = ~train
        ytr, yte = y[train], y[test].to_numpy()
        mean_eol = df.loc[train].groupby("battery")["eol"].first().mean()

        preds = {
            "naive_mean_eol_minus_cycle": np.clip(
                mean_eol - X.loc[test, "cycle"].to_numpy(), 0, None
            ),
            "linear_cycle_only": LinearRegression()
            .fit(X.loc[train, ["cycle"]], ytr)
            .predict(X.loc[test, ["cycle"]]),
        }
        for s, cols in sets.items():
            lin = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LinearRegression())
            lin.fit(X.loc[train, cols], ytr)
            preds[f"linear | {s}"] = lin.predict(X.loc[test, cols])

            gbm = LGBMRegressor(
                n_estimators=300, learning_rate=0.05, num_leaves=15,
                min_child_samples=10, random_state=0, verbose=-1,
            )
            gbm.fit(X.loc[train, cols], ytr)
            preds[f"lightgbm | {s}"] = gbm.predict(X.loc[test, cols])

        late = yte <= 30  # the last 30 cycles before EOL matter most
        for model, p in preds.items():
            err = p - yte
            rows.append({
                "rule": rule,
                "held_out": held_out,
                "model": model,
                "mae_cycles": np.abs(err).mean(),
                "mae_last30": np.abs(err[late]).mean(),
            })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    res = lobo_capacity()
    res.to_csv("notebooks/results_capacity.csv", index=False)

    out = pd.concat([lobo_rul("first"), lobo_rul("permanent")])
    out.to_csv("notebooks/results_rul.csv", index=False)
    for rule in ["first", "permanent"]:
        for metric in ["mae_cycles", "mae_last30"]:
            t = out[out["rule"] == rule].pivot(index="model", columns="held_out", values=metric)
            t["mean"] = t.mean(axis=1)
            print(f"\nRUL | EOL rule: {rule} | {metric} (lower is better)")
            print(t.round(1).sort_values("mean"))