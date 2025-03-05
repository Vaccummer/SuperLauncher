from typing import Literal, Union, Any
import random
import os
from PySide2.QtCore import QObject, Signal, Slot
from dataclasses import dataclass
from enum import Enum
from typing import Callable
import time
# relative import
from .. import global_var as GV
from backends import FileOperationType
from backends.SFTPTransfer.client import SFTPConfig
zipformat = Literal['zip', '7z', 'bz2', 'tar', 'gz', 'xz', 'gz']

