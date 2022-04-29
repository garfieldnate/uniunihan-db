try:
    import importlib.metadata as importlib_metadata
except ModuleNotFoundError:
    # https://github.com/microsoft/pyright/issues/656
    import importlib_metadata  # type: ignore

try:
    __version__ = importlib_metadata.version(__name__)
# happens during development or with `poetry install`'d module for some reason
except ModuleNotFoundError:
    __version__ = ""
