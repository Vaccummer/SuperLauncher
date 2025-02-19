import backends as BK
from enum import Enum

class AMEnum(Enum):
    def __eq__(self, other):
        return self.value == other
    def __str__(self):
        return str(self.value)
    def __repr__(self):
        return str(self.value)
    
class CStyle:
    class Zipper:
        ErrorCodes = BK.ZIPmanager.ZipperErrorCode
    class Copier:
        Operation = BK.WinFile.FileOperationResult
        Result = BK.WinFile.FileOperationResult
        Set = BK.WinFile.FileOperationSet
        Type = BK.WinFile.FileOperationType
    class Watcher:
        ErrorCode = BK.file_watcher.WatcherErrorCode
    class Extractor:
        class ErrorType(AMEnum):
            No256Icon = BK.IconExtractor.No256Icon
            FileNotExists = BK.IconExtractor.FileNotExists
            ErrorLoad = BK.IconExtractor.ErrorLoad
            UnkownError = BK.IconExtractor.UnkownError

class associate_list:
    class ItemType(AMEnum):
        Filename = "Filename"
        Foldername = "Foldername"
        App = "App"
        Error = "Error"
        Backspace = "Backspace"
    class MenuAction(AMEnum):
        Launch = "Launch"
        Delete = "Delete"
        Copy = "Copy"
        Cut = "Cut"
        Paste = "Paste"
        Remame = "Remame"
        New = "New"
        Download = "Download"
        DownloadAskDir = "Download(Ask Dir)"
        Cursor = "Cursor"
        VSCode = "VSCode"
        PowerShell = "PowerShell"
        CMD = "CMD"
        PowerShellAdmin = "PowerShellAdmin"
        CMDAdmin = "CMDAdmin"

class task_manager:
    class TaskType(AMEnum):
        FILE = "FileOperation"
        ZIP = "ZipOperation"
        WATCHER = "Watcher"
        MOUSE_LISTENER = "MouseListener"
    class Transfer:
        class ErrorType(AMEnum):
            Normal = 0
            PermissionDenied = -1
            ConnectionError = -2
            UnknownError = -3
            Canceled = -4
        class TaskHostType(AMEnum):
            Remote2Local = "Remote2Local"
            Local2Remote = "Local2Remote"
            Remote2Remote = "Remote2Remote"
            Local2Local = "Local2Local"             
    class Zipper:
        class ZipClass(AMEnum):
            ZIP = "zip"
            UNZIP = "unzip"
        class ZipFormat(AMEnum):
            ZIP = "zip"
            RAR = "rar"
            TAR = "tar"
            GZIP = "gzip"
            BZIP2 = "bzip2"
            XZ = "xz"














