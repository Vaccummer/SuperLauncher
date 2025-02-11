from typing import Callable
class ZIPmanager:
    '''
    error code:
    -7: manual cancel
    -1: unknown error
    0: success
    2: src path not exist
    9: wrong password
    '''
    def __init__(self):
        pass
    
    def compress(self, srcs: list[str], output_path: str, format: str, password: str, pg_cb: Callable[[int], bool], filename_cb: Callable[[str], None], interval: int, threads: int)->int:
        pass

    def decompress(self, src: str, output_dir: str, format: str, password: str, pg_cb: Callable[[int], bool], filename_cb: Callable[[str], None], interval: int, threads: int)->int:
        pass
