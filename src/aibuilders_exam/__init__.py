"""Simple Jupyter notebook grading library and command-line tools."""
from __future__ import annotations

import sys

if sys.version_info >= (3, 8):
    from importlib import metadata
else:
    import importlib_metadata as metadata

__version__ = metadata.version("aibuilders-exam")
