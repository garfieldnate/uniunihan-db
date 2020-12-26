try:
    import importlib.metadata as importlib_metadata
except ModuleNotFoundError:
    import importlib_metadata  # type: ignore # https://github.com/python/mypy/issues/1153

try:
    __version__ = importlib_metadata.version(__name__)
except ModuleNotFoundError:  # happens during development or with `poetry install`'d module for some reason
    __version__ = ""
