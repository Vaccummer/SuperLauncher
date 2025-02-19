from dataclasses import dataclass, fields
from typing import Literal, Any, Optional, Union
import os
from . import AM_ENUMS as AME

class AMDataClass:
    def __ror__(self, value:Any) -> Any:
        if type(value) != type(self):
            return self
        keys = [field.name for field in fields(self)]
        for key in keys:
            value_new = getattr(value, key)
            if value_new is not None:
                setattr(self, key, value_new)
        return self


class associate_list:
    @dataclass
    class AssItemInfo(AMDataClass):
        index:int=None
        title:Optional[str]=None
        path:Optional[str]=None
        type:AME.PyStyle.Launcher.associate_list.ItemType=None
        host:Optional[str]=None
        stat:Optional[os.stat_result]=None
        chname:Optional[str]=None
        group:Optional[str]=None
        app_id:Optional[int]=None

class task_manager:
    class CertainTaskData:
        class Zip:
            @dataclass
            class ZipTaskData(AMDataClass):
                ID:int
                src:str|list[str]
                dst:str
                task:AME.PyStyle.Manager.Zipper.ZipClass
                format:AME.PyStyle.Manager.Zipper.ZipFormat='zip'
                thread_num:int=1
                password:str=''
                interval:float=0.01
        class File:
            @dataclass
            class FileTaskData(AMDataClass):
                src:str
                dst:str
                stat_src:os.stat_result
                copier_type:Optional[AME.CStyle.Copier.Type]=None
                transfer_type:Optional[AME.PyStyle.Manager.Transfer.TaskHostType]=None
                total_size:int
    @dataclass
    class TaskInfo(AMDataClass):
        task_type:AME.PyStyle.Manager.TaskType
        task_data:Union["task_manager.CertainTaskData.Zip.ZipTaskData", "task_manager.CertainTaskData.File.FileTaskData", None]
        ID:Optional[int]=None
    
    @dataclass
    class TaskRuntimeInfo(AMDataClass):
        ID:int
        type:Literal['filename', 'progress', 'done', 'watcher', 'error']
        progress:float=None
        filename:str=None
        done:int=None
        tracked_path:str=None
