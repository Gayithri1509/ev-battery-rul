from src.data import add_targets, load_all

df = load_all()
for rule in ["first", "permanent"]:
    t = add_targets(df, rule=rule)
    print(rule, t.groupby("battery")["eol"].first().to_dict())

t = add_targets(df)
print(t.groupby("battery")["soh"].agg(["first", "min"]).round(3))
print(t[t["battery"] == "B0005"][["cycle", "capacity", "soh", "rul"]].iloc[[0, 50, 124, 167]])