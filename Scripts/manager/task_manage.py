from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .paths_transfer import LauncherPathManager, ShortcutsPathManager, TransferPathManager
    from .config_ui import Config_Manager

from ..worker.worker_thread import *

ImageType = Image.Image

class ManagerGroup:
    def __init__(self, config:"Config_Manager", launcher:"LauncherPathManager", shortcut:"ShortcutsPathManager", transfer:"TransferPathManager", task:"TaskManager", event:"GlobalMouseListener"):
        self.config = config
        self.launcher = launcher
        self.shortcut = shortcut
        self.transfer = transfer
        self.task = task
        self.event = event

class TaskManager(QObject):
    task2run = Signal(TaskInfo)
    progress_update = Signal(TaskRuntimeInfo)
    filename_update = Signal(TaskRuntimeInfo)
    task_done = Signal(dict)

    def __init__(self) -> None:
        super().__init__()
        self._preload()

    def _preload(self):
        self.tasks:dict[int,TaskInfo] = {}
        self.threads:dict[int,QThread] = {}
        self.task2run.connect(self._run)
    
    def create_and_run_task(self, task_type:TaskType, task_data:ZipTaskData|FileTask|WatcherTask|None)->WokerThread:
        task = TaskInfo(task_type, task_data)
        task.ID = self.GetID()
        self.tasks[task.ID] = task
        return self._run(task)
    
    def GetID(self):
        for i in range(len(self.tasks), 999999999):
            if (self.tasks.get(i,None) is None) and (self.threads.get(i,None) is None):
                return i
        GV.logger.error(title="TaskIDError", message=f"No available ID")
        return None
    
    def _create_thread(self, task:TaskInfo)->WokerThread:
        if task.task_type == TaskType.FILE:
            if task.task_data.task_type in ['put', 'get']:
                thread_f = FileTransfer(task, self.default_sftp_config)
                thread_f.runtime_info.connect(self._runtime_info_process)
            elif task.task_data.task_type in [FileOperationType.COPY, FileOperationType.MOVE, FileOperationType.REMOVE]:
                thread_f = ExplorerCopier(task)
                thread_f.runtime_info.connect(self._runtime_info_process)
            else:
                raise ValueError(f"Invalid task_data.task_type: {task.task_data.task_type}")
        elif task.task_type == TaskType.ZIP:
            thread_f = ZIPmanager(task)
            thread_f.runtime_info.connect(self._runtime_info_process)
        elif task.task_type == TaskType.WATCHER:
            thread_f = FileWatcher(task)
        else:
            raise ValueError(f"Invalid task_info.task_type: {task.task_type}")
        return thread_f
    
    @Slot(TaskInfo)
    def _run(self, task:TaskInfo):
        thread_f = self._create_thread(task)
        self.threads[task.ID] = thread_f
        thread_f.start()
        return thread_f
    
    def _result_process(self, ID:int, result:TaskRuntimeInfo):
        error_f = result.error
        try:
            error_f = str(error_f)
        except:
            error_f = "UnknownError"
        message_f = result.error_msg if result.error_msg is not None else "Unknown error message"
        task_type = str(self.tasks[ID].task_type)
        GV.logger.error(title=error_f, message=f'Task {task_type} encounter error: {message_f}')

    @Slot(TaskRuntimeInfo)
    def _runtime_info_process(self, runtime_info:TaskRuntimeInfo):
        match runtime_info.type:
            case 'filename':
                self.filename_update.emit(runtime_info.filename)
            case 'progress':
                self.progress_update.emit(runtime_info.progress)
            case 'done':
                self._result_process(runtime_info.ID, runtime_info.done)
                self.tasks.pop(runtime_info.ID)
                self.threads.pop(runtime_info.ID)

    @Slot(int)
    def kill(self, ID:int):
        try:
            if self.threads.get(ID,None) is not None:
                self.threads[ID].stop()
                self.threads.pop(ID)
            else:
                GV.logger.warning(title="ThreadIDError", message=f"Thread {ID} not found")
            if self.tasks.get(ID,None) is not None:
                self.tasks.pop(ID)
            else:
                GV.logger.warning(title="TaskIDError", message=f"Task {ID} not found")
        except Exception as e:
            GV.logger.error(title="KillError", message=f"Error killing thread {ID}: {e}")

    def exit(self):
        for thread_i in self.threads.values():
            try:
                thread_i.stop()
                thread_i.wait()
                thread_i.quit()
            except Exception as e:
                GV.logger.error(title="CleanError", message=f"Error exiting thread: {e}")
        self.threads.clear()
        self.tasks.clear()

