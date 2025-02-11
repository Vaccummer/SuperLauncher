from typing import Literal, Union
import random
from PySide2.QtCore import QObject, Signal, Slot

from .. import global_var as GV
from .worker_backend import *
from dataclasses import dataclass
from enum import Enum


class TaskType(Enum):
    FILE = "file_operation"
    ZIP = "zip_operation"

@dataclass
class ZipTaskData:
    src:str
    dst:str
    thread_num:int=1
    password:str=''
    task:Literal['zip','unzip']=""


@dataclass
class FileTaskData:
    src:str
    src_type:Literal['Local', 'Remote']
    dst:str
    dst_type:Literal['Local', 'Remote']
    src_config:dict={}
    dst_config:dict={}


@dataclass
class TaskInfo:
    def __init__(self, task_type:TaskType, task_data:ZipTaskData|FileTaskData, ID:int=None):
        self.task_type = task_type
        self.task_data = task_data
        self.ID = ID
    


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

