from importlib.resources import files


def load_dashboard() -> str:
    return files("aap.assets").joinpath("dashboard.html").read_text()
