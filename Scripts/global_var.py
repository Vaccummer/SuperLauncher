from enum import Enum
from typing import Literal,Callable
import time
import atexit
from PySide2.QtCore import QThread
from dataclasses import dataclass
from .ConsoleCustom.logger import get_logger
from .worker.task_data import TaskInfo
import backends as BK
MODE:str = "Launcher"
HOST:str = 'Local'
HOST_TYPE:str = "Local"
CONNECT:bool = True
CON_ERROR:str = ''
CLOSE_ACTION:list[Callable] = []
GEOMETRY:list[int] = [0, 0, 0, 0]
TASKS:list[TaskInfo] = []

UpdateSign = Literal[None, 'size', 'font', 'icon', 'config', 'height', 'margin', 'unpack', 'style']

logger = get_logger('runtime.log')


@dataclass
class FuncInfo():
    classname:str
    methodname:str
    filename:str
    linenum:int
    
@dataclass
class LaunchTask:
    name:str
    path:str
    type:Literal['file', 'dir']
    host:str

@dataclass
class FileOperation:
    operation:Literal['delete', 'copy', 'move','create']
    src:list|str
    dst:str
    src_host:str
    dst_host:str

    def __init__(self,operation:Literal['delete', 'copy', 'move','create']='', 
                 src:list|str='', dst:str='', src_host:str='', dst_host:str=''):
        self.operation = operation
        self.src = src
        self.dst = dst
        self.src_host = src_host
        self.dst_host = dst_host

@dataclass
class FileProcessProgressInfo:
    ID:str
    filename:str
    progress:float

@dataclass
class TransferInfo:
    ID:str
    src:str
    dst:str
    src_host:str
    dst_host:str
    size:int
    type_f:Literal['file', 'dir']

class ItemType(Enum):
    File = 'file'
    App = 'app'
    Folder = 'folder'
    Error = 'error'
    def __str__(self):
        return self.value

@dataclass
class IconQuery:
    type_f:Literal['file', 'app', "folder", "error"]|ItemType
    name:str
    chname:str=""
    group:str=None
    path:str=""
    host:str=""
    ID:int=None

@dataclass
class IconSaveRequest:
    type_f:Literal['file', 'app', "folder", 'exe']
    icon_path:str
    path:str=None
    host:str=None
    name:str=None
    group:str=None
    chname:str=None

@dataclass
class LauncherAppInfo:
    ID:int
    name:str
    chname:str
    group:str
    exe_path:str
    icon_path:str=""

    def deepcopy(self):
        return LauncherAppInfo(self.ID, self.name, self.chname, self.group, self.exe_path)

@dataclass
class IconSaveRequest:
    type_f:Literal['app', 'file', 'folder', 'exe']
    name:str
    group:str
    path:str
    host:str
    src:str



