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

class TransferError(Enum):
    Normal = 0
    PermissionDenied = -1
    ConnectionError = -2
    UnknownError = -3
    Canceled = -4

    def __eq__(self, other):
        return self.value == other

class ZipClass(Enum):
    ZIP = "zip"
    UNZIP = "unzip"

    def __eq__(self, other):
        return self.value == other

    def __str__(self):
        return self.value

class TaskType(Enum):
    FILE = "FileOperation"
    ZIP = "ZipOperation"
    WATCHER = "Watcher"
    MOUSE_LISTENER = "MouseListener"

    def __eq__(self, other):
        return self.value == other
    
    def __str__(self):
        return self.value
 
@dataclass
class ZipTaskData:
    ID:int
    src:str|list[str]
    dst:str
    task:ZipClass
    format:zipformat='zip'
    thread_num:int=1
    password:str=''
    interval:float=0.01
    
@dataclass
class FileTask:
    src:str
    dst:str
    stat_local:os.stat_result
    task_type:Literal['put', 'get', FileOperationType.COPY, FileOperationType.MOVE, FileOperationType.REMOVE]
    total_size:int
    host_config:SFTPConfig=None

@dataclass
class WatcherTask:
    drivers:list[str]
    filename:str
    filepath:str

@dataclass
class TaskRuntimeInfo:
    ID:int
    type:Literal['filename', 'progress', 'done', 'watcher', 'error']
    progress:float=None
    filename:str=None
    done:int=None
    tracked_path:str=None
    error:Any=None
    error_msg:str=None

@dataclass
class TaskInfo:
    def __init__(self, task_type:TaskType, task_data:ZipTaskData|FileTask|WatcherTask|None, ID:int=None):
        super().__init__()
        self.task_type = task_type
        self.task_data = task_data
        self.ID = ID
        self.progress:float = None
        self.filename:str = None
        self.done:int = None
        self.start_time:float = time.time()
    
class TaskManager(QObject):
    task2add = Signal(TaskInfo)
    progress_emit = Signal(dict)
    progress_update = Signal(dict)
    task_done = Signal(dict)

    def __init__(self) -> None:
        pass

    def _load(self):
        self.tasks:dict[int,TaskInfo] = {}

        self.task2add.connect(self.add)

    @Slot(TaskInfo)
    def add(self, task:TaskInfo):
        id_f = random.randint(999999999)
        while self.tasks.get(id_f,None) is not None:
            id_f = random.randint(999999999)
        task.ID = id_f
        self.tasks[id_f] = task
        self._launch(task)
    
    def _launch(self, task:TaskInfo):
        pass

# def update_progress(task_f:TaskInfo, progress:float)->None:
#     task_f.progress = progress

# def update_filename(task_f:TaskInfo, filename:str)->None:
#     task_f.filename = filename

# def update_done(task_f:TaskInfo, done:int)->None:
#     task_f.done = done


