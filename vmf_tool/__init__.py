"""A library for interpreting & editing .vmf files"""

__all__ = ["solid", "vmf", "Vmf"]

# TODO: from . import entity
from . import solid
from . import vmf


Vmf = vmf.Vmf

# TODO: load /update defaults & other config info from a supplied game_dir
