from PySide2.QtCore import QObject, Signal, Slot, QThread, QByteArray
from typing import Callable, Any, Literal
import time
from PIL import Image
from PySide2.QtCore import Signal, Slot, QObject, QThread
from typing import *
import os
import time
import asyncssh
import io
import asyncio
import io
from functools import partial

# local package
import backends as BK

# relative import 
from .config_ui import APixmap
from .TaskData import *
from .. import global_var as GV

ImageType = Image.Image

class FileWatcher(QThread):
    runtime_info = Signal(TaskRuntimeInfo)
    def __init__(self, drivers:list[str], filename:str, filepath:str):
        super().__init__()
        self.drivers = drivers
        self.worker = BK.FileWatcher(self.drivers)
        self.filename = filename
        self.filepath = filepath
        self.is_running = True

    def run(self):
        self.worker.initSet(self._cb, self.filename, self.filepath)
        self.worker.start()
        while self.is_running:
            time.sleep(0.1)

    def pause(self):
        self.worker.pause()

    def terminate(self):
        self.worker.terminate()
        self.is_running = False
        self.quit()

    def setWatch(self, filename:str, filepath:str):
        self.filename = filename
        self.filepath = filepath
        self.worker.setWatch(self.filename, self.filepath)

    def setDrivers(self, drivers:list[str]):
        self.drivers = drivers
        self.worker.setDrivers(self.drivers)

    def _cb(self, path:str):
        self.runtime_info.emit(TaskRuntimeInfo(ID='WatcherCustom', type='watcher', tracked_path=path))

class ZIPmanager(QThread):
    runtime_info = Signal(TaskRuntimeInfo)
    def __init__(self, task_f:TaskInfo):
        super().__init__()
        self.task_f:TaskInfo = task_f
        self.worker = BK.ZIPmanager()
        self.ID:int = task_f.ID
        self.progress_cb = partial(self._emitRuntimeInfo, ID=self.ID, type='progress')
        self.filename_cb = partial(self._emitRuntimeInfo, ID=self.ID, type='filename')
        self.done_cb = partial(self._emitRuntimeInfo, ID=self.ID, type='done')
        self.task_data:ZipTaskData = task_f.task_data

    def run(self):
        src = self.task_data.src
        dst = self.task_data.dst
        password = self.task_data.password
        interval = self.task_data.interval
        format = self.task_data.format

        match self.task_data.task:
            case ZipClass.ZIP:
                thread_num = self.task_data.thread_num
                code = self.worker.compress(ID=self.ID, srcs=src, output_path=dst, format=format, password=password, cb_per_interval=interval, threads=thread_num, file_cb=self.filename_cb, progress_cb=self.progress_cb)
                self.done_cb(code)
            case ZipClass.UNZIP:
                code = self.worker.decompress(ID=self.ID, src=src, output_dir=dst, format=format, password=password, cb_per_interval=interval, file_cb=self.filename_cb, progress_cb=self.progress_cb)
                self.done_cb(code)

    def terminate(self):
        self.worker.terminate(self.ID)

    def _emitRuntimeInfo(self, ID:int, type:Literal['filename', 'progress', 'done'], info:int|float|str):
        match type:
            case 'filename':
                self.runtime_info.emit(TaskRuntimeInfo(ID=ID, type=type, filename=info))
            case 'progress':
                self.runtime_info.emit(TaskRuntimeInfo(ID=ID, type=type, progress=info))

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

class FileTransfer(QThread):
    runtime_info = Signal(TaskRuntimeInfo)
    def __init__(self, task_f:FileTask):
        super().__init__()

class FileTransfer2(QThread):
    runtime_info = Signal(TaskRuntimeInfo)
    class SingleTask:
        __slots__ = ['src', 'dst', 'src_host', 'dst_host', 'size', 'type_f']
        def __init__(self, src:str, dst:str, src_host:str, dst_host:str, size:int, type_f:Literal['file', 'dir']):
            self.src = src
            self.dst = dst
            self.src_host = src_host
            self.dst_host = dst_host
            self.size = size
            self.type_f = type_f

    def __init__(self, task_f:TaskInfo):
        super().__init__()
        self.task = task_f
        self.ID = task_f.ID
        self.task_data:FileTaskData = task_f.task_data
        self.total_size = task_f.task_data.total_size
        self.close_sign = False

    def _size_add(self, src_path:str, dst_path:str, size_i:int, size_t:int):
        if src_path == self.src_path:
            self.size_n  = self.size_n - self.size_i + size_i
            self.size_i = size_i
        else:
            self.size_n += size_i
            self.src_path = src_path
            self.size_i = size_i
            info_n = TaskRuntimeInfo(ID=self.ID, type='filename', filename=dst_path)
            self.runtime_info.emit(info_n)
            
        info_i = TaskRuntimeInfo(ID=self.ID, type='progress', progress=self.size_n/self.total_size)
        self.runtime_info.emit(info_i)
        if self.close_sign:
            info_ext = TaskRuntimeInfo(ID=self.ID, type='done', done=TransferError.Canceled)
            self.runtime_info.emit(info_ext)

    def close(self):
        self.close_sign = True

    def run(self):
        src_host = self.task_data.src_type
        dst_host = self.task_data.dst_type
        if src_host == 'Remote':
            try:
                self.remote_transfer(type_f='get')
                code = TransferError.Normal
            except Exception as e:
                match e:
                    case asyncssh.PermissionDenied:
                        code = TransferError.PermissionDenied
                    case _:
                        code = TransferError.UnknownError
            finally:
                self.runtime_info.emit(TaskRuntimeInfo(ID=self.ID, type='done', done=code))
                return
        elif dst_host == 'Remote':
            try:
                self.remote_transfer(type_f='put')
                code = TransferError.Normal
            except Exception as e:
                match e:
                    case asyncssh.PermissionDenied:
                        code = TransferError.PermissionDenied
                    case _:
                        code = TransferError.UnknownError
            finally:
                self.runtime_info.emit(TaskRuntimeInfo(ID=self.ID, type='done', done=code))
                return

        try:
            asyncio.run(self._transfer())
            self.runtime_info.emit(TaskRuntimeInfo(ID=self.ID, type='done', done=TransferError.Normal))
        except Exception as e:
            GV.logger.warning(f"Transfer encounters error: {e}")
            self.runtime_info.emit(TaskRuntimeInfo(ID=self.ID, type='done', done=TransferError.UnknownError))

    def remote_transfer(self, type_f:Literal['put', 'get']='put', password:str=None):
        asyncio.run(self._remote_transfer(type_f, password))

    async def _remote_transfer(self, type_f:Literal['put', 'get'], password:str=None):
        if type_f == 'get':
            config = self.task_data.src_config
        elif type_f == 'put':
            config = self.task_data.dst_config
        
        if not config:
            GV.logger.warning(f"Tranfer task {self.task_f.ID} has no host config")
            return

        config_t = {
            'host':config['HostName'],
            'port':config.get('port', 22),
            'username':config.get('User', os.getlogin()),
            'password':password if password is not None else ""
        }

        async with asyncssh.connect(**config_t) as conn:
            async with conn.start_sftp_client() as sftp:
                if type_f == 'put':
                    await sftp.put(self.task_f.src, self.task_f.dst, recurse=True, progress_handler=self._size_add, max_requests=2)
                elif type_f == 'get':
                    await sftp.get(self.task_f.src, self.task_f.dst, recurse=True, progress_handler=self._size_add, max_requests=2)

    # def _load_task(self, src:str, dst:str)->list[SingleTask]:
    #     if not os.path.exists(src):
    #         return []
    #     elif os.path.isfile(src):
    #         dst_n = path_join(dst, os.path.basename(src))
    #         return [FileTransfer.SingleTask(src, dst_n, self.manager.hostname_n, self.manager.hostname_n, os.path.getsize(src), 'file')]
    #     task_f = []
    #     path_lt = glob(os.path.join(src, '*'), recursive=True)
    #     for path_i in path_lt:
    #         if os.path.isfile(path_i):
    #             task_f.append(LocalTransfer.TaskInfo(path_i, path_join(dst, os.path.basename(path_i)), os.path.getsize(path_i), 'file'))
    #         elif not os.listdir(path_i):
    #             path_join(dst, os.path.basename(path_i))
            
    async def _transfer(self):
        for i in range(0,len(self.task_data.src_dst_stat_list),self.task_data.thread_num):
            task_f_i = self.task_data.src_dst_stat_list[i:i+self.task_data.thread_num]
            task_l = []
            for task_i in task_f_i:
                task_l.append(self.copy_with_progress(task_i[0], task_i[1], task_i[2].st_size))
            await asyncio.gather(*task_l)
            if self.close_sign:
                return
            
    async def copy_with_progress(self, src:str, dst:str, total_size:int):
        copied_size = 0
        with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
            while chunk := fsrc.read(int(self.task_data.local_chunk_size)):  
                fdst.write(chunk)
                copied_size += len(chunk)
                self._size_add(src, dst, copied_size, total_size)
                if self.close_sign:
                    return
