import os
import clr
import sys
path_script = os.path.abspath(__file__)
path_f = os.path.join(os.path.dirname(path_script), "Zipper")
os.environ['PATH'] = path_f + os.pathsep + os.environ['PATH']
path_dll = os.path.join(os.path.dirname(path_script), "IconGet", "IconExtractor.dll")
clr.AddReference(path_dll)
import IconExtractor 
from .Zipper import ZIPmanager 
from .Tracker import file_watcher
from .WinCopier import WinFile
from .SFTPTransfer import client as SFTPClient
