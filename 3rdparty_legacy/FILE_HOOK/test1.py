from file_watcher import FileWatcher
from PySide2.QtCore import QObject, Signal, Slot,QThread
from PySide2.QtWidgets import QApplication
import threading
from PySide2.QtCore import QTimer, QCoreApplication
from PySide2.QtCore import QMetaObject, Qt,QTimer, QEventLoop
import time
import random
dict_f = {'haha':'preset'}

if __name__ == '__main__':
    app = QApplication([])
    def sleep(milliseconds):
        loop = QEventLoop()
        QTimer.singleShot(milliseconds, loop.quit)  # 定时器触发后退出事件循环
        loop.exec_()  # 进入事件循环，阻塞当前线程

    class The(QThread,QObject):
        change_flag = Signal(str)
        def __init__(self, parent):
            super().__init__(parent)
            self.value = ''
        def run(self):
            while True:
                value_t = dict_f.get('path', '')
                if value_t != self.value:
                    print('signal emit')
                    self.change_flag.emit(str(value_t))
                    self.value = value_t
                sleep(300)

    class Receiver(QObject):
        fileEvent = Signal(str)  # 定义一个信号，接受字符串参数
        def __init__(self):
            super().__init__()
            # self.thread1 = The(self)
            # self.thread1.change_flag.connect(self.handle_print)
            # self.thread1.start()
            self.fileEvent.connect(self.handle_print)

        @Slot(str)
        def handle_print(self, message):
            print(f"Received event")
            print(f"message: {message}"  )

    from functools import partial
    watcher = FileWatcher()
    rec = Receiver()
    index = 0

    def func_f(str_f:str):
        print(f"func_f received")
        global dict_f
        dict_f['path'] = str_f
        rec.fileEvent.emit(str_f)

    break_flag = False
    def func():
        try:
            index = 0
            while True:
                if index == 0:
                    watcher.start(['C:\\','D:\\'], 'hosts.am', 'D:\\Document\\Desktop\\hosts.am', func_f)
                    index = 1
                else:
                    time.sleep(0.5)
                    if break_flag:
                        break
        except Exception as e:
            print(f"Error: {e}")
        finally:
            # 停止监听
            watcher.stop()

    t = threading.Thread(target=func)
    t.start()
    app.exec_()

