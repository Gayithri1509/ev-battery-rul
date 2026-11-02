from src.data import BATTERIES, load_all

df = load_all()
for name in BATTERIES:
    c = df[df["battery"] == name]["capacity"].tolist()
    below = [i for i, x in enumerate(c) if x <= 1.4]
    if not below:
        print(name, "never reaches 1.4 Ah")
        continue
    first = below[0]
    back_above = [i for i in range(first, len(c)) if c[i] > 1.4]
    print(name, "first <=1.4 at", first, "| back above 1.4 at", back_above,
          "| max after first:", round(max(c[first:]), 3))