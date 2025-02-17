from typing import Callable, Any
from enum import Enum

class WatcherErrorCode(Enum):
    Success = 0,
    AlreadyWatching = -1,
    CannotSupervise = -2,
    NotInWatchList = -3,
    UnknowAddWatchError = -4,
    UnknowRemoveWatchError = -5,
    UnknowError = -6,

class FileWatcher:
    def __init__(self, drivers: list[str]):
        ...

    def initSet(self, callback:Callable[[str], Any], filename:str, filepath:str)->None:
        ...

    def setDrivers(self, driver_l:list[str])->list[WatcherErrorCode]:
        ...

    def setCallback(self, callback:Callable[[str], Any])->None:
        ...

    def start(self)->None:
        ...

    def pause(self)->None:
        ...

    def setWatch(self, filename:str, filepath:str)->None:
        ...

    def terminate(self)->None:
        ...



