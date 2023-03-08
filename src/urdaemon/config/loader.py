import tomllib
import xdg_base_dirs as xdg


def load_config() -> dict:
    """Load the source configuration toml file."""
    # TODO: Support windows application paths?
    path = xdg.xdg_config_home() / "urdaemon" / "config.toml"
    if path.exists():
        with path.open("rb") as fp:
            config = tomllib.load(fp)
    else:
        config = {}
    return config
