import os
from pickle import NONE
from types import UnionType
from matplotlib.pyplot import disconnect
import wexpect
import subprocess
import threading
from typing import Optional, Callable, Sequence, Any
import shutil
import re
from enum import Enum
from dataclasses import dataclass, fields

class ScpErrorCode(Enum):
    Sucess = 0
    SrcDeny = 7
    DstDeny = 8
    PathInvalid = 9
    PasswordInvalid = 10
    ConnectionError = 11
    Unknown = 12

@dataclass
class ScpHostConfig:
    host:str
    username:str
    password:str
    port:int

@dataclass
class ScpTask:
    src:str
    src_host_config:ScpHostConfig|None
    dst:str
    dst_host_config:ScpHostConfig|None
    total_size:int

    def __ror__(self, value: Any) -> "ScpTask":
        if type(value) != type(self):
            return self
        keys = [field.name for field in fields(self)]
        for key in keys:
            value_new = getattr(value, key)
            if value_new is not None:
                setattr(self, key, value_new)
        return self

class ScpClient:
    '''
    SCP Client implemented using cmd and scp.exe
    No gurantee to function properly on non-Windows platforms and even on windows
    please pre-check the validity of src, dst
    progress_cb: (size_n, total_size, percent)
    filename_cb: (filename)
    done_cb: (error_code)
    '''
    def __init__(self, task_f:ScpTask,
                 progress_cb:Callable[[str, int], None], 
                 filename_cb:Callable[[str], None], 
                 done_cb:Callable[[str], ScpErrorCode], 
                 exec_path:str=None):
        if exec_path is not None and os.path.exists(str(exec_path)):
            self.exec_path = str(exec_path)
        else:
            self.exec_path = shutil.which("scp.exe")
        self.progress_cb = progress_cb
        self.filename_cb = filename_cb
        self.done_cb = done_cb
        self.task_f = task_f
    
    def _UriEncode(self, path_f:str)->str:
        return path_f.replace("\\", "/").replace(" ", "%20").replace("#","%23").replace("?","%3F")
    
    def _FormatPath(self, task_f:ScpTask, is_src:bool)->str:
        config_f = task_f.src_host_config if is_src else task_f.dst_host_config
        src_f = self._UriEncode(task_f.src if is_src else task_f.dst)
        if config_f is None:
            return src_f
        return f"scp://{config_f.username}@{config_f.host}:{config_f.port}/{src_f}"
    
    def _produce_cmd(self, task_f:ScpTask|None=None)->str:
        "scp.exe -r  scp://am@172.28.14.64:22//home/am/a.rar scp://am@172.28.14.64:22//home/am/casdasd.rar scp://am@172.28.14.64:22//home/am/c.rar scp://am@192.168.31.46:45/c:/Users/am"
        if task_f is None:
            task_f = self.task_f
        cmd_f = []
        cmd_f.append(f'"{self.exec_path}"')
        cmd_f.append("-r")
        cmd_f.append(self._FormatPath(task_f, True))
        cmd_f.append(self._FormatPath(task_f, False))
        return " ".join(cmd_f)
    
    def _produce_pattern(self, task_f:ScpTask|None=None)->dict[str, str]:
        if task_f is None:
            task_f = self.task_f
        patterns = []
        s_p = re.escape(f"{task_f.src_host_config.username}@{task_f.src_host_config.host}'s password:")
        s_p = f"^{s_p}.+$"
        d_p = re.escape(f"{task_f.dst_host_config.username}@{task_f.dst_host_config.host}'s password:")
        d_p = f"^{d_p}.+$"
        progress_pattern = r"^([\u4e00-\u9fff\w\s\-\.\/@#]+?)\s+(\d+%)?\s+(\d+[KMGTkmgt]?[Bb])?\s+(\d+\.?\d*[KMGTkmgt]?[Bb]/[Ss])?\s+(\d{2}:\d{2})?\s*(ETA)?$"

        wrong_passwd_pattern = re.escape("Permission denied, please try again.")

        src_deny_ori = re.escape(f"{task_f.src_host_config.username}@{task_f.src_host_config.host}: Permission denied")
        src_permission_denied_pattern = f"^{src_deny_ori}.+$"

        dst_deny_ori = re.escape(f"{task_f.dst_host_config.username}@{task_f.dst_host_config.host}: Permission denied")
        dst_permission_denied_pattern = f"^{dst_deny_ori}.+$"

        path_invalid_ori = re.escape("No such file or directory")
        path_invalid_pattern = f"^.+{path_invalid_ori}$"

        disconnect_pattern = r".*Connection\s+closed.*"

        return {
            'SrcPassword':s_p,
            'DstPassword':d_p,
            'Progress':progress_pattern,
            'WrongPasswd':wrong_passwd_pattern,
            'SrcDeny':src_permission_denied_pattern,
            'DstDeny':dst_permission_denied_pattern,
            'PathInvalid':path_invalid_pattern,
            "Disconnect":disconnect_pattern,
            'EOF':wexpect.EOF,
            "Unknown":r".+"
        }

    def _format_size(self, size_f:str)->int|None:
        if size_f.lower().endswith("kb"):
            return int(size_f[:-2]) * 1024
        elif size_f.lower().endswith("mb"):
            return int(size_f[:-2]) * 1024 * 1024
        elif size_f.lower().endswith("gb"):
            return int(size_f[:-2]) * 1024 * 1024 * 1024
        elif size_f.lower().endswith("tb"):
            return int(size_f[:-2]) * 1024 * 1024 * 1024 * 1024
        elif size_f.lower().endswith("b"):
            return int(size_f[:-1])
        else:
            return None
    
    def _handle_progress(self, str_f:str, pattern_f:str):
        match_f = re.match(pattern_f, str_f)
        if not match_f:
            return
        filename = match_f.group(1).strip()
        size_f = match_f.group(3)
        if filename is None or size_f is None:
            return
        size = self._format_size(size_f)
        if size is None:
            return
        if filename != self.now_filename:
            self.filename_cb(filename)
            self.now_filename = filename
        self.progress_cb(filename, size)

    def run(self):
        self.error_code = ScpErrorCode.Sucess
        self.now_host = None
        self.now_filename = None
        cmd_str = self._produce_cmd()
        print(cmd_str)
        self.child = wexpect.spawn(cmd_str)
        pattern_dict = self._produce_pattern()
        choices = list(pattern_dict.keys())
        patterns = list(pattern_dict.values())
        while True:
            index_f = self.child.expect(patterns)
            choice_i = choices[index_f]
            str_f = self.child.after
            match choice_i:
                case 'Progress':
                    self._handle_progress(str_f, pattern_dict['Progress'])
                case 'WrongPasswd':
                    self.error_code = ScpErrorCode.PasswordInvalid
                    break
                case 'SrcPassword':
                    PASSWORD = self.task_f.src_host_config.password
                    self.child.sendline(PASSWORD)
                case 'DstPassword':
                    PASSWORD = self.task_f.dst_host_config.password
                    self.child.sendline(PASSWORD)
                case 'EOF':
                    break
                case 'SrcDeny':
                    self.error_code = ScpErrorCode.SrcDeny
                    break
                case 'DstDeny':
                    self.error_code = ScpErrorCode.DstDeny
                    break
                case 'PathInvalid':
                    self.error_code = ScpErrorCode.PathInvalid
                    break
                case "Disconnect":
                    self.error_code = ScpErrorCode.ConnectionError
        self.child.terminate()
        self.done_cb(self.error_code)
    
    def stop(self):
        self.child.terminate()
    
if __name__ == "__main__":
    def progress_cb(filename:str, size:int):
        print(f"{filename}: {size}")
    def filename_cb(filename:str):
        print(f"filename: {filename}")
    def done_cb(error_code:ScpErrorCode):
        print(f"error_code: {error_code}")

    src_config = ScpHostConfig(host="172.28.14.64", username="am", password="1984", port=22)
    dst_config = ScpHostConfig(host="192.168.31.46", username="am", password="1984", port=45)
    task_f = ScpTask(
        src="/mnt/f/Windows_Data/Desktop_File/抖音下载1.8",
        src_host_config=src_config,
        dst="c:/Users/am",
        dst_host_config=dst_config,
        total_size=1000000000
    )
    scp_client = ScpClient(task_f, progress_cb, filename_cb, done_cb)
    scp_client.run()


