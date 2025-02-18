from PySide2.QtCore import QObject, Signal, Slot, QThread, QByteArray
from typing import Callable, Any, Literal, Optional
from pynput import mouse
import time
from PIL import Image
from PySide2.QtCore import Signal, Slot, QObject, QThread
from typing import *
import os
import time
import io
from functools import partial
# local package
import backends as BK
# relative import 
from ..manager.config_ui import APixmap, UIUpdater
from .task_data import *
from .. import global_var as GV
from ..tools.toolbox import get_hard_drives

ImageType = Image.Image

class Watcher:
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, drivers:list[str]|None=None):
        if drivers is None:
            self.drivers = get_hard_drives()
        else:
            self.drivers = drivers
        self.watcher = BK.FileWatcher(self.drivers)
    
    def initSet(self, callback:Callable[[str], Any], filename:str, filepath:str)->None:
        self.watcher.initSet(callback, filename, filepath)

    def setDrivers(self, driver_l:list[str])->list[BK.WatcherErrorCode]:
        return self.watcher.setDrivers(driver_l)

    def setCallback(self, callback:Callable[[str], Any])->None:
        return self.watcher.setCallback(callback)

    def start(self)->None:
        return self.watcher.start()

    def pause(self)->None:
        return self.watcher.pause()

    def setWatch(self, filename:str, filepath:str)->None:
        return self.watcher.setWatch(filename, filepath)

    def terminate(self)->None:
        return self.watcher.terminate()

class Copier:
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.copier = BK.ExplorerAPI()
        self.copier.Init(BK.FileOperationSet(NoProgressUI=False, NoneUI=False, NoConfirmation=True, NoErrorUI=False, NoConfirmationForMakeDir=True, WarningIfPermanentDelete=False))

    def Config(self, set:BK.FileOperationSet)->None:
        self.copier.Config(set)

    def copy(self, src:str, dst:str)->BK.FileOperationResult:
        return self.copier.action(src, dst, BK.FileOperationType.COPY)
    
    def move(self, src:str, dst:str)->BK.FileOperationResult:
        return self.copier.action(src, dst, BK.FileOperationType.MOVE)
    
    def rm(self, path:str)->BK.FileOperationResult:
        return self.copier.rm(path)

    def action(self, src:str, dst:str, action:BK.FileOperationType)->BK.FileOperationResult:
        return self.copier.action(src, dst, action)

class Zipper:
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.zipper = BK.ZIPmanager()

    def compress(self, task_f:TaskInfo, file_cb:Callable[[str], None], progress_cb:Callable[[float], None])->BK.ZipperErrorCode:
        task_data:ZipTaskData = task_f.task_data
        code_f = self.zipper.compress(
            ID=task_f.ID,
            srcs=task_data.src,
            output_path=task_data.dst,
            format=task_data.format,
            password=task_data.password,
            cb_per_interval=task_data.interval,
            threads=task_data.thread_num,
            file_cb=file_cb,
            progress_cb=progress_cb
        )

    def decompress(self, task_f:TaskInfo, file_cb:Callable[[str], None], progress_cb:Callable[[float], None])->BK.ZipperErrorCode:
        task_data:ZipTaskData = task_f.task_data
        return self.zipper.decompress(
            ID=task_f.ID,
            src=task_data.src,
            output_dir=task_data.dst,
            format=task_data.format,
            password=task_data.password,
            cb_per_interval=task_data.interval,
            file_cb=file_cb,
            progress_cb=progress_cb)
    
    def getIDs(self)->list[int]:
        return self.zipper.getIDs()

    def terminate(self, ID_f:int)->BK.ZipperErrorCode:
        return self.zipper.terminate(ID_f)

class IconGet:
    extractor = BK.Worker()
    @classmethod
    def _Extract(cls, path:str, index:int=0):
        return cls.extractor.Extract(path, index)

    @classmethod
    def Extract(cls, path:str, index:int=0, output_format:ImageType|APixmap=APixmap)->ImageType|APixmap:
        out_data = cls._Extract(path, index)
        if output_format == APixmap:
            image_data = io.BytesIO(out_data).getvalue()
            pixmap = APixmap()
            pixmap.loadFromData(QByteArray(image_data))
            return pixmap
        else:
            image_f = Image.open(io.BytesIO(out_data))
            return image_f

class MouseListener:
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, on_move:Callable[[int, int], None], on_click:Callable[[int, int, mouse.Button, bool], None], on_scroll:Callable[[int, int, int, int], None]):
        self.listener = mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
    
    def launch(self)->None:
        self.listener.start()
        self.listener.join()
    
    def terminate(self)->None:
        self._instance = None
        self.listener.stop()
    
    
    
