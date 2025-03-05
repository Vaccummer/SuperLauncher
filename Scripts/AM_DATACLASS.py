from dataclasses import dataclass, fields
from typing import Literal, Any, Optional, Union, TYPE_CHECKING
import os


if TYPE_CHECKING:
    from PySide2.QtCore import QThread
    from .manager.config_ui import AIcon, Asize, APixmap
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
        type:"AME.associate_list.ItemType"=None
        host:Optional[str]=None
        stat:Optional[os.stat_result]=None
        chname:Optional[str]=None
        group:Optional[str]=None
        app_id:Optional[int]=None

class launcher_manager:
    @dataclass
    class IconQuery(AMDataClass):
        type_f:"AME.associate_list.ItemType"
        name:str
        chname:str=""
        group:str=None
        path:str=""
        host:str=""
        ID:int=None

    @dataclass
    class IconSaveRequest(AMDataClass):
        type_f:"AME.associate_list.ItemType"
        icon_path:str|AIcon|APixmap
        path:str=None
        host:str=None
        name:str=None
        group:str=None
        chname:str=None
    

class task_manager:
    @dataclass
    class ZipTaskData(AMDataClass):
        ID:int
        src:str|list[str]
        dst:str
        task:"AME.task_manager.Zipper.ZipClass" 
        format:"AME.task_manager.Zipper.ZipFormat"
        thread_num:int=1
        password:str=''
        interval:float=0.01
    
    @dataclass
    class FileTaskData(AMDataClass):
        src:str
        dst:str
        stat_src:os.stat_result
        copier_type:Optional[AME.CStyle.Copier.Type]=None
        transfer_type:Optional[AME.PyStyle.Manager.Transfer.TaskHostType]=None
        total_size:int
    
    @dataclass
    class WatcherTask(AMDataClass):
        drivers:list[str]
        filename:str
        filepath:str

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

    @dataclass
    class LaunchTask(AMDataClass):
        name:str
        path:str
        type:Literal['file', 'dir']
        host:str
        ID:Optional[int]=None

    @dataclass
    class ThreadInfo(AMDataClass):
        ID:str
        task:"task_manager.TaskInfo"
        thread:"QThread"
    
    @dataclass
    class FuncInfo(AMDataClass):
        classname:str
        methodname:str
        filename:str
        linenum:int
        
