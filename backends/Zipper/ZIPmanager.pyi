from typing import Callable
from enum import Enum

class ZipperErrorCode(Enum):
    success = 0,
    FilterNotSpecified = -1,
    FormatFeatureNotSupported = -2,
    IndicesNotSpecified = -3,
    InvalidArchivePath = -4,
    InvalidOutputBufferSize = -5,
    InvalidCompressionMethod = -6,
    InvalidDictionarySize = -7,
    InvalidIndex = -8,
    InvalidWordSize = -9,
    ItemIsAFolder = -10,
    ItemMarkedAsDeleted = -11,
    NoMatchingItems = -12,
    NoMatchingSignature = -13,
    NonEmptyOutputBuffer = -14,
    NullOutputBuffer = -15,
    RequestedWrongVariantType = -16,
    UnsupportedOperation = -17,
    UnsupportedVariantType = -18,
    WrongUpdateMode = -19,
    InvalidZipPassword = -20,
    UnknownError = -21,
    IDNotExist = -22,

class ZIPmanager:
    def __init__(self):
        pass
    
    def compress(self, ID: int, srcs: list[str], output_path: str, format: str, password: str, cb_per_interval: float, threads: int, file_cb: Callable[[str], None], progress_cb: Callable[[float], None])->ZipperErrorCode:
        pass

    def decompress(self, ID:int, src:str, output_dir:str, format:str, password:str, cb_per_interval:float, file_cb: Callable[[str], None], progress_cb:Callable[[float], None])->ZipperErrorCode:
        pass

    def getIDs(self)->list[int]:
        pass

    def terminate(self, ID_f:int)->ZipperErrorCode:
        pass
