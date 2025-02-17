import os
import clr
import sys
path_script = os.path.abspath(__file__)
path_f = os.path.join(os.path.dirname(path_script), "Zipper")
os.environ['PATH'] = path_f + os.pathsep + os.environ['PATH']
print(path_f)
sys.path.append(path_f)
path_dll = os.path.join(os.path.dirname(path_script), "IconGet", "IconExtractor.dll")
clr.AddReference(path_dll)
from IconExtractor import *
from .Zipper.ZIPmanager import *
from .Tracker.file_watcher import *
from .WinCopier.WinFile import *
from .SFTPTransfer.client import *
