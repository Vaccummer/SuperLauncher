import sys
from PySide2.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, 
    QTextEdit, QVBoxLayout, QLineEdit, QMenuBar, QAction
)
from PySide2.QtCore import QProcess, Qt, QByteArray, Signal
from PySide2.QtGui import QTextCursor, QKeyEvent

class TerminalWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = QProcess(self)
        self.init_ui()
        self.init_process()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 输出显示区域
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

        # 输入区域
        self.input = QLineEdit()
        self.input.returnPressed.connect(self.send_command)
        layout.addWidget(self.input)

    def init_process(self):
        # 启动系统默认终端（Windows 使用 cmd.exe）
        self.process.setProgram("cmd.exe" if sys.platform == "win32" else "bash")
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.readyReadStandardError.connect(self.read_error)
        self.process.start()
        
    def send_command(self):
        command = self.input.text() + "\n"
        self.process.write(command.encode())
        self.input.clear()
        self.append_text(f"\n$ {command.strip()}")  # 显示输入命令

    def read_output(self):
        data = self.process.readAllStandardOutput()
        self.append_text(bytes(data).decode("gbk" if sys.platform == "win32" else "utf-8"))

    def read_error(self):
        data = self.process.readAllStandardError()
        self.append_text(bytes(data).decode("gbk" if sys.platform == "win32" else "utf-8"))

    def append_text(self, text):
        self.output.moveCursor(QTextCursor.End)
        self.output.insertPlainText(text)
        self.output.moveCursor(QTextCursor.End)

class TerminalTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)
        self.add_new_tab()

    def add_new_tab(self):
        terminal = TerminalWidget()
        index = self.addTab(terminal, "Terminal")
        self.setCurrentIndex(index)

    def close_tab(self, index):
        widget = self.widget(index)
        if widget.process.state() == QProcess.Running:
            widget.process.terminate()
        widget.deleteLater()
        self.removeTab(index)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Terminal Emulator")
        self.setGeometry(100, 100, 800, 600)

        # 创建菜单栏
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        
        new_tab_action = QAction("New Tab", self)
        new_tab_action.triggered.connect(self.add_new_tab)
        file_menu.addAction(new_tab_action)

        # 主界面
        self.tab_widget = TerminalTabWidget()
        self.setCentralWidget(self.tab_widget)

    def add_new_tab(self):
        self.tab_widget.add_new_tab()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())