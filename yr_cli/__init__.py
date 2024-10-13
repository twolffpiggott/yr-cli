__version__ = "0.0.2"

from importlib import resources


def get_icon_path(icon_name: str) -> str:
    with resources.path("yr_cli.icons", f"{icon_name}.png") as path:
        if not path.exists():
            raise FileNotFoundError(
                f"Icon file '{path}' not found in the package resources."
            )
        return str(path)
