from scipy.io import loadmat


def load_battery(name, data_dir="data"):
    """Return the list of cycle entries for one battery, e.g. name="B0005"."""
    m = loadmat(f"{data_dir}/{name}.mat", struct_as_record=False, squeeze_me=True)
    return m[name].cycle