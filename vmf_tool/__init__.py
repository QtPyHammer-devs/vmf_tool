"""A library for interpreting & editing .vmf files"""

__all__ = ["solid", "parse", "vmf", "Vmf"]

from . import solid
from . import parse
from . import vmf


Vmf = vmf.Vmf
