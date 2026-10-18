"""Python client for the Threadle CLI JSON interface."""

from .client import ThreadleStruct, configure, is_available, raw_cmd, session, start, stop

__version__ = "0.2.0"

__all__ = [
    "ThreadleStruct",
    "__version__",
    "configure",
    "is_available",
    "raw_cmd",
    "session",
    "start",
    "stop",
]
