from src.data import add_targets, load_all
from src.features import build_features

df = add_targets(load_all())
X = build_features(df)

print(X.shape)
print("missing values per column:")
print(X.isna().sum()[X.isna().sum() > 0])

dt = df["time"].apply(lambda a: float(a[-1]))
print("corr(total discharge time, capacity):", round(dt.corr(df["capacity"]), 4))

print(X.join(df["capacity"]).corr()["capacity"].drop("capacity").round(2).sort_values())