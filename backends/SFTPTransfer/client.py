import asyncssh
import asyncio
from dataclasses import dataclass
from typing import Callable, Literal

@dataclass
class SFTPConfig:
    host:str
    port:int
    username:str
    password:str

@dataclass
class TransferConfig:
    block_size:int = -1
    max_requests:int = 2
    preserve:bool = True


class SFTPClient:
    def __init__(self, Sftpconfig:SFTPConfig, taskConfig:TransferConfig, pg_cb:Callable[[str, str, int], None], err_cb:Callable[[str, str, int], None]):
        self.sftp_config = Sftpconfig
        self.task_config = taskConfig
        self.pg_cb = pg_cb
        self.err_cb = err_cb
    
    async def _transfer(self, src:str, dst:str, task_type:Literal['put', 'get']):
        with asyncssh.connect(**self.sftp_config) as conn:
            with conn.start_sftp_client() as sftp:
                if task_type == 'put':
                    await sftp.put(src, dst, recurse=True, progress_handler=self.pg_cb, max_requests=self.task_config.max_requests, block_size=self.task_config.block_size, error_handler=self.err_cb, preserve=self.task_config.preserve)
                elif task_type == 'get':
                    await sftp.get(src, dst, recurse=True, progress_handler=self.pg_cb, max_requests=self.task_config.max_requests, block_size=self.task_config.block_size, error_handler=self.err_cb, preserve=self.task_config.preserve)
    
    def transfer(self, src:str, dst:str, task_type:Literal['put', 'get']):
        asyncio.run(self._transfer(src, dst, task_type))







