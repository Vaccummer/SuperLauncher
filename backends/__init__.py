import os
import clr
import sys
path_script = os.path.abspath(__file__)
sys.path.append(os.path.join(os.path.dirname(path_script), "Zipper"))
path_dll = os.path.join(os.path.dirname(path_script), "IconGet", "IconExtractor.dll")
clr.AddReference(path_dll)
from IconExtractor import *
from .Zipper.ZIPmanager import *
from .Tracker.file_watcher import *
from .WinCopier.WinFile import *
