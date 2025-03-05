import pybit7z
from typing import Callable, Optional
from enum import Enum
from dataclasses import dataclass
import os
import shutil
import subprocess
import time
import stat


class ErrorCode(Enum):
    success = 0,
    FormatError = 1,
    InvalidArchivePath = 2,
    InvalidTaskType = 3,
    RarExcutableNotFound = 4,
    RarCompressError = 5,
    DstFileAlreadyExists = 6,
    DstDirAlreadyExists = 7,
    Terminated = 8,
    WrongPassword = 9,
    UnknownError = 10,
    InvalidZipTargetPath = 11,
    UnsupportedOperation = 12,

class TaskType(Enum):
    Compress = 0,
    Extract = 1,
    AddArchive = 2,

@dataclass
class ZipCallback:
    '''PyBit7z is just a wrapper of C++ bit7z library, not pure Python Implementation.
    So, don't use callback functions that include any UI elements.
    '''
    pg_cb:Callable[[int, int], None] = None
    filename_cb:Callable[[str], None] = None
    total_cb:Callable[[int], None] = None
    passwd_cb:Callable[[], str] = None

@dataclass
class ZipTask:
    src:list[str]|str
    dst:str
    task_type:TaskType
    password:Optional[str] = None
    makedir:bool=True
    overwrite:bool=False
    compress_level:int=3
    interval:float=1 # seconds
    threads:int=1

@dataclass
class ZipStateInfo:
    total_size:int = 1024
    current_size:int = 0
    current_file:str = ""

class AMZipManagerBase:
    format_map = {
    ".zip":pybit7z.FormatZip,
    ".7z":pybit7z.FormatSevenZip,
    ".rar":pybit7z.FormatRar5,
    ".tar":pybit7z.FormatTar,
    ".wim":pybit7z.FormatWim,
    ".bz2":pybit7z.FormatBZip2,
    ".gz":pybit7z.FormatGZip,
    ".xz":pybit7z.FormatXz,
}

    def __init__(self, task:ZipTask, cb:ZipCallback):
        self.task = task
        self.cb = cb
        if isinstance(self.task.src, str):
            self.task.src = os.path.expanduser(os.path.abspath(self.task.src))
        else:
            self.task.src = [os.path.expanduser(os.path.abspath(i)) for i in self.task.src]
        self.task.dst = os.path.expanduser(os.path.abspath(self.task.dst))
        self.encoding = None
        self.state_info = ZipStateInfo()
        self.encoding_list = ['GBK', 'UTF-8', 'ANSI', "GB18030"]
        self.password = None
        self.is_running = True
        self.time_f = time.time()

    def _filename_cb(self, filename:str):
        self.state_info.current_file = str(filename)
        if self.cb.filename_cb is not None:
            self.cb.filename_cb(filename)

    def _total_cb(self, total:int):
        self.state_info.total_size = total
        if self.cb.total_cb is not None:
            self.cb.total_cb(total)
    
    def _passwd_cb(self)->str:
        if self.task.password is not None:
            return self.task.password
        if self.cb.passwd_cb is not None:
            self.task.password = self.cb.passwd_cb()
        else:
            self.task.password = ""
    
        return self.task.password

    def _pg_cb(self, size:int)->bool:
        time_f = time.time()
        self.state_info.current_size = size
        
        if time_f - self.time_f > self.task.interval:
            self.time_f = time_f
            if self.cb.pg_cb is not None:
                self.cb.pg_cb(size, self.state_info.total_size)
        return self.is_running

    def _rar_cb(self, filename:str):
        check_f = False
        for src_i in self.task.src:
            if src_i in filename:
                check_f = True
                break
        if not check_f:
            return
        names_f = filename.split(' ')
        for i in names_f:
            for src_i in self.task.src:
                if src_i in i:
                    print(i)
                    return
        self.state_info.current_file = i
        try:    
            size_tmp = os.path.getsize(i)
        except Exception as e:
            size_tmp = 0
        
        self.state_info.current_size += size_tmp
        
        if self.cb.filename_cb is not None:
            self.cb.filename_cb(i)
        
        if self.cb.pg_cb is not None:
            self.cb.pg_cb(self.state_info.current_size, self.state_info.total_size)
    
    def _try_encoding(self, char:str)->str:
        for i in self.encoding_list:
            try:
                char.decode(i)
                self.encoding = i
                return i
            except Exception as e:
                continue
        self.encoding = False

    def _rar_total_size(self):
        size_tmp = 0
        for i in self.task.src:
            if os.path.isdir(i):
                for root, dirs, files in os.walk(i):
                    for file in files:
                        size_tmp += os.path.getsize(os.path.join(root, file))
                    size_tmp += len(dirs)*4096
            else:
                size_tmp += os.path.getsize(i)
        return size_tmp
    
    def get_format(self)->pybit7z.BitInFormat|ErrorCode:
        '''
        Get the format of the archive.
        If the format is not supported, return ErrorCode.FormatError.
        "tar.gz", "tar.bz2", "tar.xz" are supported, but counducted in multiple steps.
        '''
        target_str = self.task.src if self.task.task_type == TaskType.Extract else self.task.dst
        ext_1 = os.path.splitext(target_str)[1]
        return self.format_map.get(ext_1, ErrorCode.FormatError)
    
    def compress_rar(self)->ErrorCode:
        '''
        Since Rar Compression is proprietary, we need to use the Rar executable to compress the files.
        We produce callback information by parsing the rar.exe output.
        So, we can't guarantee the accuracy of the callback information.
        '''
        if os.path.exists(self.task.dst) and self.task.task_type != TaskType.AddArchive:
            return ErrorCode.DstFileAlreadyExists

        if not os.path.exists(os.path.dirname(self.task.dst)):
            if self.task.makedir:
                os.makedirs(os.path.dirname(self.task.dst), exist_ok=True)
            else:
                return ErrorCode.InvalidArchivePath
        
        rar_path = shutil.which('rar.exe')
        
        if rar_path is None:
            return ErrorCode.RarExcutableNotFound
        
        self.state_info.total_size = self._rar_total_size()
        
        command_l = ['rar', 'a']
        if self.task.password is not None:
            command_l.append('-p' + self.task.password)
        command_l.append(f'-m{min(max(self.task.compress_level, 0), 5)}')
        command_l.append(f'{self.task.dst}')
        for i in self.task.src:
            command_l.append(f'{i}')
        process = subprocess.Popen(command_l, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while process.poll() is None:
            line = process.stdout.readline()
            if line:
                if not self.is_running:
                    process.terminate()
                    return ErrorCode.Terminated
                if self.encoding is None:
                    self._try_encoding(line)
                if self.encoding is False:
                    continue
                line_str = line.decode(self.encoding).strip()
                self._rar_cb(line_str)
        process.wait()
        if process.returncode != 0:
            return ErrorCode.RarCompressError
        return ErrorCode.success

    def cast_error(self, e:Exception)->ErrorCode:
        if "password" in str(e):
            return ErrorCode.WrongPassword
        elif "Operation aborted" in str(e):
            return ErrorCode.Terminated
        else:
            return ErrorCode.UnknownError
        
    def extract_work(self, format_f:pybit7z.BitInFormat)->ErrorCode:
        if not os.path.exists(self.task.src):
            return ErrorCode.InvalidArchivePath
        if not os.path.exists(self.task.dst):
            os.makedirs(self.task.dst, exist_ok=True)
        elif os.path.isdir(self.task.dst):
            if not self.task.overwrite:
                return ErrorCode.DstDirAlreadyExists
        
        try:
            with pybit7z.lib7zip_context() as lib:
                extractor = pybit7z.BitStringExtractor(lib, format_f)
                if self.task.password is not None:
                    extractor.set_password(self.task.password)
                extractor.set_file_callback(self._filename_cb)
                extractor.set_total_callback(self._total_cb)
                extractor.set_password_callback(self._passwd_cb)
                extractor.set_progress_callback(self._pg_cb)
                extractor.extract(self.task.src, self.task.dst)
        except Exception as e:
            return self.cast_error(e)

    def compress_work(self, format_f:pybit7z.BitInFormat)->ErrorCode:
        self.task.src = [i for i in self.task.src if os.path.exists(i)]
        if len(self.task.src) == 0:
            return ErrorCode.InvalidZipTargetPath
        
        if os.path.exists(self.task.dst):
            if not self.task.overwrite:
                return ErrorCode.DstFileAlreadyExists
            else:
                os.chmod(self.task.dst, stat.S_IWRITE)
                os.remove(self.task.dst)
        
        if not os.path.exists(os.path.dirname(self.task.dst)):
            if self.task.makedir:
                os.makedirs(os.path.dirname(self.task.dst), exist_ok=True)
            else:
                return ErrorCode.InvalidArchivePath
        try:
            with pybit7z.lib7zip_context() as lib:
                compressor = pybit7z.BitFileCompressor(lib, format_f)
                if self.task.password is not None:
                    compressor.set_password(self.task.password)
                '''
                TODO: file callback crashes in Compress Work but work in Extract Work.
                '''
                # compressor.set_file_callback(self._filename_cb)  
                compressor.set_threads_count(min(max(self.task.threads, 1), os.cpu_count()))
                compressor.set_total_callback(self._total_cb)
                compressor.set_progress_callback(self._pg_cb)
                compressor.compress(self.task.src, self.task.dst)
        except Exception as e:
            return self.cast_error(e)

class AMZipManager(AMZipManagerBase):
    def __init__(self, task:ZipTask, cb:ZipCallback):
        super().__init__(task, cb)

    def terminate(self):
        self.is_running = False

    def start_work(self) -> ErrorCode:
        '''
        Main Worker Function of the class.
        '''
        format_f = self.get_format()
        if isinstance(format_f, ErrorCode):
            return format_f
        if format_f == pybit7z.FormatRar5 and self.task.task_type !=TaskType.Extract:
            return self.compress_rar()
        
        match self.task.task_type:
            case TaskType.Extract:
                return self.extract_work(format_f)
            case TaskType.Compress:
                return self.compress_work(format_f)
            case TaskType.AddArchive:
                '''
                TODO: Add Archive Work
                '''
                return ErrorCode.UnsupportedOperation
            case _:
                return ErrorCode.InvalidTaskType
                







