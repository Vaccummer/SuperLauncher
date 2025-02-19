import sys
import os
import pyte
from pyte.screens import Char
from PySide2.QtCore import Qt, QProcess
from PySide2.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget,
                             QVBoxLayout, QPushButton, QPlainTextEdit, QLineEdit)
from PySide2.QtGui import QColor, QTextCursor, QFont, QTextCharFormat

class TerminalDisplay(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QPlainTextEdit {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 14px;
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: none;
            }
        """)
        self.setReadOnly(True)
        self.columns, self.rows = 120, 30
        self.screen = pyte.Screen(self.columns, self.rows)
        self.stream = pyte.ByteStream(self.screen)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)

    def write(self, data):
        try:
            self.stream.feed(data)
            self._update_screen()
        except Exception as e:
            print(f"Decode error: {repr(e)}")

    def _update_screen(self):
        cursor = self.textCursor()
        cursor.select(QTextCursor.Document)
        cursor.removeSelectedText()
        
        default_bg = QColor("#1E1E1E")
        default_fg = QColor("#D4D4D4")
        
        for y in range(self.screen.lines):
            line = self.screen.display[y] if y < len(self.screen.display) else []
            for x in range(self.screen.columns):
                # 修复字符对象处理
                if x < len(line):
                    char = line[x]
                    if not isinstance(char, Char):
                        char = Char(data=char, fg="default", bg="default")
                else:
                    char = Char(" ")
                
                fmt = QTextCharFormat()
                fmt.setForeground(self._get_color(char.fg, default_fg))
                fmt.setBackground(self._get_color(char.bg, default_bg))
                cursor.setCharFormat(fmt)
                cursor.insertText(char.data)
            cursor.insertText("\n")
        self.ensureCursorVisible()

    def _get_color(self, color, default):
        color_map = {
            "default": default,
            "black": QColor("#000000"),
            "red": QColor("#CD3131"),
            "green": QColor("#0DBC79"),
            "yellow": QColor("#E5E510"),
            "blue": QColor("#2472C8"),
            "magenta": QColor("#BC3FBC"),
            "cyan": QColor("#11A8CD"),
            "white": QColor("#E5E5E5"),
        }
        return color_map.get(str(color).lower(), default)

class TerminalTab(QWidget):
    def __init__(self):
        super().__init__()
        self.process = QProcess()
        self.init_ui()
        self.start_shell()
        
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.readyReadStandardError.connect(self.read_error)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.display = TerminalDisplay()
        layout.addWidget(self.display)
        
        self.input_edit = QLineEdit()
        self.input_edit.setStyleSheet("""
            QLineEdit {
                font-family: 'Consolas';
                font-size: 14px;
                background-color: #252526;
                color: #D4D4D4;
                border: 1px solid #3F3F46;
                padding: 5px;
            }
        """)
        self.input_edit.returnPressed.connect(self.execute_command)
        layout.addWidget(self.input_edit)

    def start_shell(self):
        if os.name == 'nt':
            self.process.setProgram("cmd.exe")
            self.process.setArguments(["/k", "chcp 65001"])
        else:
            self.process.setProgram("bash")
            self.process.setArguments(["-i"])
            
        env = QProcess.systemEnvironment()
        env.append("TERM=xterm-256color")
        self.process.setEnvironment(env)
        self.process.start()

    def execute_command(self):
        command = self.input_edit.text()
        if command:
            self.process.write(command.encode() + b"\r\n")
            self.input_edit.clear()

    def read_output(self):
        data = self.process.readAllStandardOutput().data()
        self.display.write(data)

    def read_error(self):
        data = self.process.readAllStandardError().data()
        self.display.write(data)

class AdvancedTerminal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tab_count = 1
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Terminal v6.0")
        self.setGeometry(100, 100, 800, 600)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: 0; }
            QTabBar::tab {
                background: #333333;
                color: white;
                padding: 8px;
                min-width: 120px;
            }
            QTabBar::tab:selected { background: #1E1E1E; }
        """)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        
        self.add_tab_btn = QPushButton("+")
        self.add_tab_btn.setFixedSize(30, 30)
        self.add_tab_btn.clicked.connect(self.add_new_tab)
        self.tab_widget.setCornerWidget(self.add_tab_btn)
        
        self.setCentralWidget(self.tab_widget)
        self.add_new_tab()

    def add_new_tab(self):
        tab = TerminalTab()
        self.tab_widget.addTab(tab, f"Terminal {self.tab_count}")
        self.tab_count += 1

    def close_tab(self, index):
        widget = self.tab_widget.widget(index)
        widget.process.terminate()
        widget.deleteLater()
        self.tab_widget.removeTab(index)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Consolas", 12))
    
    # 忽略PNG警告
    os.environ["QT_LOGGING_RULES"] = "qt.libpng.warning=false"
    
    if os.name == 'nt':
        os.environ["PYTHONIOENCODING"] = "utf-8"
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    
    window = AdvancedTerminal()
    window.show()
    sys.exit(app.exec_())
