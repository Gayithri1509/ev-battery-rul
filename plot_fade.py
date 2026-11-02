import matplotlib.pyplot as plt

from src.data import BATTERIES, load_all

df = load_all()

fig, ax = plt.subplots(figsize=(9, 5))
for name in BATTERIES:
    d = df[df["battery"] == name]
    ax.plot(d["cycle"], d["capacity"], label=name)
ax.axhline(1.4, color="red", linestyle="--", label="EOL 1.4 Ah")
ax.axhline(2.0, color="gray", linestyle=":", label="Rated 2.0 Ah")
ax.set_xlabel("Discharge cycle")
ax.set_ylabel("Capacity (Ah)")
ax.set_title("Capacity fade, NASA batteries")
ax.legend()
fig.savefig("notebooks/capacity_fade.png", dpi=150)

print(df.groupby("battery")["capacity"].agg(["count", "first", "min", "max", "last"]))
plt.show()