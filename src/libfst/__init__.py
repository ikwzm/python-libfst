__version__     = "0.0.2"
__author__      = "Ichiro Kawazome"
__copyright__   = "Copyright (c) 2026 Ichiro Kawazome"
__license__     = "BSD 2-Clause"
__email__       = "ichiro_k@ca2-so-net.ne.jp"
__description__ = "GTKWave FST Package"

from .       import Enum
from .       import hier
from .reader import Reader
from .writer import Writer

__all__ = [
    "Enum",
    "hier",
    "Reader",
    "Writer",
]
