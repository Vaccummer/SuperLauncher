from PySide2.QtWidgets import QApplication, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QApplication, QMainWindow, QComboBox, QVBoxLayout, QLabel
from PySide2.QtWidgets import QWidget, QTextEdit, QProgressBar, QToolButton, QPushButton, QFrame, QSystemTrayIcon, QMenu
from PySide2.QtWidgets import QVBoxLayout, QHBoxLayout, QFileDialog, QGraphicsBlurEffect, QScrollArea, QAction, QShortcut
from PySide2.QtCore import Qt, QEvent, QObject, Signal, QSize, Slot, QThread
from PySide2.QtCore import QTimer, QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup
from PySide2.QtGui import QPixmap, QPalette, QIcon, QFont, QScreen, QFontMetrics, QWindow, QKeySequence
from PySide2.QtGui import QPainter, QColor, QBrush, QPen, QLinearGradient, QTextCharFormat, QTextCursor
from Scripts2.toolbox import *
from am_store2.common_tools import *
from Scripts2.launcher_ori import *

class BaseLauncher(QMainWindow):
    MODE = "Launcher"
    HOST = 'Local'
    HOST_TYPE = "Local"
    def __init__(self, config:dict, app:QApplication):
        super().__init__()
        self.wkdir = os.getcwd()
        self.config = Config_Manager(wkdir=self.wkdir, 
                                     config=config, 
                                     mode_name=None,
                                     widget_name=None,
                                     obj_name=None,)
        self.app = app
        self._init_para()
        self.createTrayIcon()
        self._mainwindow_set()
    
    # For mouse control
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.isNearEdge(event.pos()):
                self.edge_drag = event.pos()
                self.original_geometry = self.geometry()
                event.accept()
            else:
                x, y, w, h = self.get_geometry(self.switch_button)
                if event.y() >y+h or event.x() > x+w:
                    self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                    event.accept()
        else:
            super().mousePressEvent(event)
    def mouseMoveEvent(self, event):
        if self.edge_drag:
            self.resizeWindow(event.pos())
        elif self.drag_position and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = None
            self.edge_drag = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    def isNearEdge(self, pos):
        x, y, w, h = self.get_geometry(self)
        return (
            pos.x() < self.edge_threshold or
            pos.x() > w - self.edge_threshold or
            pos.y() < self.edge_threshold or
            pos.y() > h - self.edge_threshold
        )
    def resizeWindow(self, pos):
        diff = pos - self.edge_drag
        if abs(diff.x()) > abs(diff.y()):
            new_width = max(self.original_geometry.width() + diff.x(), self.minimumWidth())
            self.setGeometry(self.original_geometry.x(), self.original_geometry.y(), new_width, self.original_geometry.height())
        else:
            new_height = max(self.original_geometry.height() + diff.y(), self.minimumHeight())
            self.setGeometry(self.original_geometry.x(), self.original_geometry.y(), self.original_geometry.width(), new_height)
        
    def closeEvent(self, event):
        # rewrite close event
        event.ignore()  # ignore the close event
        self.hide()  # hide the main window
        self.tray_icon.showMessage("Super Launcher", "Main Window is now hidden", QSystemTrayIcon.Information)
    
    def createTrayIcon(self):
        # create taskbar hide icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(self.config.get(None, "MainWindow", "taskbar_icon", "path")))
        self.tray_icon.setToolTip("Super Launcher")

        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        max_action = QAction("Maximum", self)
        max_action.triggered.connect(self.showMaximized)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.programm_exit)
        restart_action = QAction("Restart", self)
        restart_action.triggered.connect(lambda : self.restart_program(self.config.get(None, "Common", "script_path", None)))
        tray_menu = QMenu()

        tray_menu.addAction(show_action)
        tray_menu.addAction(max_action)
        tray_menu.addAction(restart_action)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.show)
        self.tray_icon.show()
    
    def _init_para(self):
        self.setMinimumSize(350, 350)
        # for mouse click enven judge
        self.drag_position = None
        self.edge_drag = None
        self.edge_threshold = 5

        # init state variable
        self.het = self.config.get("het", mode='Common', widget=None, obj="Size")
        self.gap = self.config.get("gap", mode='Common', widget=None, obj="Size")
        self.win_x = self.config.get("win_x", mode='Common', widget=None, obj="Size")
        self.win_y = self.config.get("win_y", mode='Common', widget=None, obj="Size")
        self.srh_r = self.config.get("srh_r", mode='Common', widget=None, obj="Size")
        self.edge_threshold = int(self.gap/3.5)

        self.ass_xlsx_path = self.config.get("settings_xlsx", "Launcher", widget="path", obj=None)
        self.ass_num = self.config.get("max_ass_num", "Common", None, None)
        self.ass_df = excel_to_df(self.ass_xlsx_path, region='A:D', sheet_name_f='all')
        # self.ass = Associate(self.config)
    
    def _mainwindow_set(self):
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("Super Launcher")
        self.setWindowIcon(QIcon(self.config.get(None, "MainWindow", "taskbar_icon", "path")))
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # 绘制带有圆角和渐变的窗口背景
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(113, 148, 139))
        gradient.setColorAt(1, QColor(162, 245, 224))
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 20, 20)
    
    def _load_data(self):
        self.launcher_data = LauncherPathManager(self.config)
        self.shortcut_data = ShortcutsPathManager(self.config)
        self.ssh_manager = self.up.ssh_manager
        
    @staticmethod
    def restart_program(script_path):
        os.system(f"python {script_path}")
    @staticmethod
    def programm_exit():
        ## programm exit
        QApplication.instance().quit()
    @staticmethod
    def get_geometry(window_f):
        geom_f = window_f.geometry()
        return[geom_f.x(), geom_f.y(), geom_f.width(), geom_f.height()]
