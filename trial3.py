from typing import Literal
import os
import asyncssh
import asyncio
import time

async def _remote_transfer(src:str, dst:str):

    config_t = {
        'host':'172.28.14.64',
        'port':22,
        'username':'am',
        'password':'1984'
    }
    async with asyncssh.connect(**config_t) as conn:
        async with conn.start_sftp_client() as sftp:
            await sftp.put(src, dst, recurse=True, max_requests=2)
src = r'F:\Windows_Data\Desktop_File\voc2007.rar'
dst = r'/home/am/test23.rar'
size_f = os.path.getsize(src)
time_start = time.time()
asyncio.run(_remote_transfer(src, dst))
time_end = time.time()
speed = size_f / (time_end - time_start)/1024/1024
print(f'Speed: {speed:.2f} MB/s')
