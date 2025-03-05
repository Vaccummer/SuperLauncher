from PySide2.QtCore import QObject, Signal, Slot, QThread, QByteArray
from typing import Callable, Any, Literal, Optional
import atexit
import time
from PIL import Image
from PySide2.QtCore import Signal, Slot, QObject, QThread
from typing import *
import os
import time
from functools import partial

# local package
import backends as BK

# relative import 
from .wrapped_worker import *
from ..manager.config_ui import UIUpdater
from .task_data import *
from ..tools.toolbox import get_display_refresh_rate
from .. import global_var as GV
from .. import AM_ENUMS as AME
from .. import AM_DATACLASS as AMD

ImageType = Image.Image
runtime_info_type = AMD.task_manager.TaskRuntimeInfo

class FileWatcher(QThread):
    runtime_info = Signal(runtime_info_type)
    callback_info = Signal(list)
    stop_signal = Signal()
    def __init__(self, task_f:runtime_info_type):
        super().__init__()
        self.task_f = task_f
        self.task_data:AMD.task_manager.WatcherTask = task_f.task_data
        self.ID = task_f.ID
        self.drivers = self.task_data.drivers
        self.worker = Watcher(self.drivers)
        self.filename = self.task_data.filename
        self.filepath = self.task_data.filepath
        self.is_running = True
        self.stop_signal.connect(self.stop)
        self.src = ""
        self.src_hostname = ""

    def run(self):
        self.worker.initSet(self._callback, self.filename, self.filepath)
        self.worker.start()
        while self.is_running:
            time.sleep(0.1)
    
    def resume(self):
        self.worker.start()
    
    def pause(self):
        self.worker.pause()
    @Slot()
    def stop(self):
        self.worker.terminate()
        self.is_running = False

    def setWatch(self, filename:str, filepath:str):
        self.filename = filename
        self.filepath = filepath
        self.worker.setWatch(self.filename, self.filepath)

    def getDrivers(self)->list[str]:
        return self.drivers
    
    def setDrivers(self, drivers:list[str]):
        self.drivers = drivers
        self.worker.setDrivers(self.drivers)

    def setSrc(self, src:str, src_hostname:str):
        self.src = src
        self.src_hostname = src_hostname

    def _callback(self, filename:str):
        self.callback_info.emit([self.src_hostname, self.src, filename])

class ZIPmanager(QThread):
    runtime_info = Signal(runtime_info_type)
    stop_signal = Signal()
    def __init__(self, task_f:runtime_info_type):
        super().__init__()
        self.task_f:AMD.task_manager.TaskInfo = task_f
        self.worker = Zipper()
        self.ID:int = task_f.ID
        self.progress_cb = partial(self._emitRuntimeInfo, ID=self.ID, type='progress')
        self.filename_cb = partial(self._emitRuntimeInfo, ID=self.ID, type='filename')
        self.done_cb = partial(self._emitRuntimeInfo, ID=self.ID, type='done')
        self.task_data:AMD.task_manager.ZipTaskData = task_f.task_data
        self.stop_signal.connect(self.stop)

    def run(self):
        match self.task_data.task:
            case AME.task_manager.Zipper.ZipClass.ZIP:
                code = self.worker.compress(self.task_f, self.filename_cb, self.progress_cb)
            case AME.task_manager.Zipper.ZipClass.UNZIP:
                code = self.worker.decompress(self.task_f, self.filename_cb, self.progress_cb)
        if code == BK.ZipperErrorCode.InvalidZipPassword:
            passwd_f = input("Please input the password: ")
            if passwd_f is None:
                return code
            else:
                self.task_data.password = passwd_f
                return self.worker.compress(self.task_f, self.filename_cb, self.progress_cb)
        return code
    @Slot()
    def stop(self):
        self.worker.terminate(self.ID)

    def _emitRuntimeInfo(self, ID:int, type:Literal['filename', 'progress', 'done'], info:int|float|str):
        match type:
            case 'filename':
                self.runtime_info.emit(runtime_info_type(ID=ID, type=type, filename=info))
            case 'progress':
                self.runtime_info.emit(runtime_info_type(ID=ID, type=type, progress=info))
            case 'done':
                self.runtime_info.emit(runtime_info_type(ID=ID, type=type, done=info))

class ExplorerCopier(QThread):
    runtime_info = Signal(runtime_info_type)
    stop_signal = Signal()
    def __init__(self, task_f:AMD.task_manager.TaskInfo):
        super().__init__()
        self.task_f = task_f
        self.worker = Copier()
    
    def run(self):  
        self.worker.action(self.task_f.task_data.src, self.task_f.task_data.dst, self.task_f.task_data.task_type)
    
    def stop(self):
        pass

class FileTransfer(QThread):
    runtime_info = Signal(runtime_info_type)
    stop_signal = Signal()
    def __init__(self, task_f:AMD.task_manager.TaskInfo, sftp_config:Optional[BK.TransferConfig]=None):
        super().__init__()
        self.task_f = task_f
        self.task_data:AMD.task_manager.FileTaskData = task_f.task_data
        self.sftp_config = sftp_config 
        self.stop_sign = False

    def run(self):
        self._remote_transfer(self.task_f.type_f)

    def _remote_transfer(self, type_f:Literal['put', 'get']):
        self.task_config = BK.TransferConfig() if self.task_config is None else self.task_config
        assert isinstance(self.sftp_config, BK.TransferConfig)
        self.worker = BK.SFTPClient(self.sftp_config, self.task_config, self._progress_cb, self._error_cb)
        try:
            self.worker.transfer(self.task_data.src, self.task_data.dst, type_f)
            self.runtime_info.emit(runtime_info_type(ID=self.ID, type='done', done=AME.task_manager.Transfer.ErrorType.Normal))
        except Exception as e:
            if str(e) == 'Canceled':
                self.runtime_info.emit(runtime_info_type(ID=self.ID, type='done', done=AME.task_manager.Transfer.ErrorType.Canceled))
            else:
                self._error_cb(e)

    def _progress_cb(self, src:str, dst:str, size:int):
        if self.stop_sign:
            raise Exception('Canceled')
        self.runtime_info.emit(runtime_info_type(ID=self.ID, type='progress', progress=size/self.total_size))
    
    def _error_cb(self, error:Any):
        try:
            msg = str(error)
        except:
            msg = 'Unknown Error Info'
        self.runtime_info.emit(runtime_info_type(ID=self.ID, type='error', error=error, error_msg=msg))

    @Slot()
    def stop(self) -> None:
        self.stop_sign = True

    def config(self, config:BK.TransferConfig):
        self.task_config = config

class GlobalMouseListener(QThread):
    '''
    mouse_press: list[pos_x, pos_y, button, is_press]
    mouse_move: list[pos_x, pos_y]
    mouse_scroll: list[pos_x, pos_y, delta_x, delta_y]
    '''
    mouse_press = Signal(list)
    mouse_move = Signal(list)
    mouse_scroll = Signal(list)
    def __init__(self):
        super().__init__()
        self.listener = MouseListener(self._on_move, self._on_click, self._on_scroll)
        self.mouse_press_state = []
        self.mouse_move_state = []
        self.mouse_scroll_state = []
        self.press_listening:bool = True
        self.move_listening:bool = True
        self.scroll_listening:bool = True
        self.listener_time = time.time()
        self.listener_time_delta = 1/get_display_refresh_rate()

    def pause(self, type:Literal['press', 'move', 'scroll', None]):
        match type:
            case 'press':
                self.press_listening = False
            case 'move':
                self.move_listening = False
            case 'scroll':
                self.scroll_listening = False
            case None:
                self.press_listening = False
                self.move_listening = False
                self.scroll_listening = False
    
    def resume(self, type:Literal['press', 'move', 'scroll', None]):
        match type:
            case 'press':
                self.press_listening = True
            case 'move':
                self.move_listening = True
            case 'scroll':
                self.scroll_listening = True
            case None:
                self.press_listening = True
                self.move_listening = True
                self.scroll_listening = True
                
    def run(self):
        self.listener.launch()
    
    def stop(self):
        self.listener.terminate()
    
    def _on_move(self, x:int, y:int):
        if self.move_listening:
            time_n = time.time()
            if time_n - self.listener_time > self.listener_time_delta:
                self.mouse_move.emit([x, y])
                self.listener_time = time_n
    
    def _on_click(self, x:int, y:int, button:mouse.Button, is_press:bool):
        if self.press_listening:
            time_n = time.time()
            if time_n - self.listener_time > self.listener_time_delta:
                self.mouse_press.emit([x, y, button, is_press])
                self.listener_time = time_n
    
    def _on_scroll(self, x:int, y:int, delta_x:int, delta_y:int):
        if self.scroll_listening:
            time_n = time.time()
            if time_n - self.listener_time > self.listener_time_delta:
                self.mouse_scroll.emit([x, y, delta_x, delta_y])
                self.listener_time = time_n
    
WokerThread = Union[FileWatcher, ZIPmanager, ExplorerCopier, FileTransfer]