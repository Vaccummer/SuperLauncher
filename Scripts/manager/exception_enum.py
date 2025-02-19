class BaseException(Exception):
    def __init__(self, message:str):
        self.message = message
    def __str__(self):
        return self.message
    def __bool__(self):
        return False

class WrongHostError(BaseException):
    def __init__(self, message:str):
        super().__init__(message)


class PathNotExistsError(BaseException):
    def __init__(self, message:str):
        super().__init__(message)

class HostConnectError(BaseException):
    def __init__(self, message:str):
        super().__init__(message)

class PermissionError(BaseException):
    def __init__(self, message:str):
        super().__init__(message)
