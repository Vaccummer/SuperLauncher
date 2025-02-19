import os
from types import UnionType
from PySide2.QtWidgets import QListWidget, QMainWindow, QWidget,QListWidgetItem,QPushButton, QHBoxLayout, QVBoxLayout, QLabel
from PySide2.QtGui import QFontMetrics, QIcon
from PySide2.QtCore import QSize, Qt
from functools import partial
from abc import abstractmethod
import asyncio
import asyncssh
from dataclasses import dataclass, fields
from copy import deepcopy
from typing import Literal, Union, Optional, TYPE_CHECKING
# local import
from ..ui.custom_widget import *
from ..tools.toolbox import *
from ..manager.paths_transfer import *
from ..worker import wrapped_worker as WW

from ..manager.task_manage import *
from .. import global_var as GV
from ..manager import exception_enum as EX

if TYPE_CHECKING:
    from Scripts import ControlLauncher
    from ..worker import worker_thread as WT

class AssItemType(Enum):
    Filename = "Filename"
    Foldername = "Foldername"
    App = "App"
    Error = "Error"
    Backspace = "Backspace"
    def __eq__(self, value: object) -> bool:
        return self.value == value
    def __str__(self) -> str:
        return self.value
    def __repr__(self) -> str:
        return self.value

@dataclass
class AssItemInfo:
    index:int=None
    title:Optional[str]=None
    path:Optional[str]=None
    type:AssItemType=None
    host:Optional[str]=None
    stat:Optional[os.stat_result]=None
    chname:Optional[str]=None
    group:Optional[str]=None
    app_id:Optional[int]=None

    def __ror__(self, value:"AssItemInfo") -> "AssItemInfo":
        if not isinstance(value, AssItemInfo):
            return self
        keys = [field.name for field in fields(self)]
        for key in keys:
            value_new = getattr(value, key)
            if value_new is not None:
                setattr(self, key, value_new)
        return self

class AssLineObject:
    def __init__(self, button:QPushButton, label:QLabel, item:QListWidgetItem):
        self.button = button
        self.label = label
        self.item = item

class AssMenuAction(Enum):
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
    def __eq__(self, value: object) -> bool:
        return self.value == value
    def __str__(self) -> str:
        return self.value
    def __repr__(self) -> str:
        return self.value
    
class Associate:
    def __init__(self, nums:int, 
                 app_info_d:dict[str, GV.LauncherAppInfo],
                 path_manager:TransferPathManager,):
        self.num = nums
        self.app_info_d = app_info_d
        self.manager:TransferPathManager = path_manager
    
    # To Associate subdirectory of certain path
    def ass_path(self, prompt_f:str)->list[AssItemInfo]:
        if not prompt_f:
            return []
        prompt_f_s = self.manager.check(prompt_f,)
        match prompt_f_s:
            case EX.PathNotExistsError():
                pass
            case os.stat_result() if stat.S_ISDIR(prompt_f_s.st_mode):
                dirs, stats = self.manager.listdir(prompt_f)
                rs = []
                for dir_i, stat_i in zip(dirs, stats):
                    if stat.S_ISDIR(stat_i.st_mode):
                        rs.append(AssItemInfo(title=dir_i, path=os.path.join(prompt_f, dir_i), type=AssItemType.Foldername, host=GV.HOST, stat=stat_i))
                    else:
                        rs.append(AssItemInfo(title=dir_i, path=os.path.join(prompt_f, dir_i), type=AssItemType.Filename, host=GV.HOST, stat=stat_i))
                return rs
            case os.stat_result() if not stat.S_ISDIR(prompt_f_s.st_mode):
                return []
            case _:
                title_f = prompt_f_s.__class__.__name__
                return [AssItemInfo(title=title_f, path="", type=AssItemType.Error, host=GV.HOST)]
        
        dir_n, base_n = os.path.split(prompt_f)
        dir_n_s = self.manager.check(dir_n)
        match dir_n_s:
            case os.stat_result() if stat.S_ISDIR(dir_n_s.st_mode):
                pass
            case os.stat_result() if not stat.S_ISDIR(dir_n_s.st_mode):
                return []
            case _:
                title_f = dir_n_s.__class__.__name__
                return [AssItemInfo(title=title_f, path="", type=AssItemType.Error, host=GV.HOST)]
        dirs_n2, stats_n2 = self.manager.listdir(dir_n)
        l1 = []
        l2 = []
        for dir_i, stat_i in zip(dirs_n2, stats_n2):
            if dir_i.startswith(base_n):
                if stat.S_ISDIR(stat_i.st_mode):
                    l1.append(AssItemInfo(title=dir_i, path=os.path.join(dir_n, dir_i), type=AssItemType.Foldername, host=GV.HOST, stat=stat_i))
                else:
                    l1.append(AssItemInfo(title=dir_i, path=os.path.join(dir_n, dir_i), type=AssItemType.Filename, host=GV.HOST, stat=stat_i))
            elif dir_i.lower().startswith(base_n.lower()):
                if stat.S_ISDIR(stat_i.st_mode):
                    l2.append(AssItemInfo(title=dir_i, path=os.path.join(dir_n, dir_i), type=AssItemType.Foldername, host=GV.HOST, stat=stat_i))
                else:
                    l2.append(AssItemInfo(title=dir_i, path=os.path.join(dir_n, dir_i), type=AssItemType.Filename, host=GV.HOST, stat=stat_i))
        return l1+l2

    # To associate a programme name of prompt
    def ass_name(self, prompt_f)->list[AssItemInfo]:
        if not prompt_f:
            return []
        name_l = []
        name_l2 = []
        chname_l = []
        name_l3 = []
        chname_l4 = []
        for name_i, app_i in self.app_info_d.items():
            chname_i = app_i.chname
            id_i = app_i.ID
            match name_i:
                case _ if name_i.startswith(prompt_f):
                    name_l.append(AssItemInfo(title=name_i, type=AssItemType.App, app_id=id_i, chname=chname_i, group=app_i.group, path=app_i.exe_path))
                case _ if chname_i and chname_i.startswith(prompt_f):
                    chname_l.append(AssItemInfo(title=chname_i, type=AssItemType.App, app_id=id_i, chname=chname_i, group=app_i.group, path=app_i.exe_path))
                case _ if name_i.lower().startswith(prompt_f.lower()):
                    name_l2.append(AssItemInfo(title=name_i, type=AssItemType.App, app_id=id_i, chname=chname_i, group=app_i.group, path=app_i.exe_path))
                case _ if prompt_f in name_i:
                    name_l3.append(AssItemInfo(title=name_i, type=AssItemType.App, app_id=id_i, chname=chname_i, group=app_i.group, path=app_i.exe_path))
                case _ if chname_i and prompt_f in chname_i:
                    chname_l4.append(AssItemInfo(title=chname_i, type=AssItemType.App, app_id=id_i, chname=chname_i, group=app_i.group, path=app_i.exe_path))

        total_l = name_l+chname_l+name_l2+name_l3+chname_l4
        return total_l
    
    def fill(self, prompt:str)->list[AssItemInfo]:
        if is_path(prompt):
            return self.fill_path(prompt)
        else:
            return self.fill_name(prompt)
        
    # Automatically complete PATH
    def fill_path(self, prompt_f:str)->Union[None, str]:
        # if prompt is a exsisting path
        name_type_l = self.ass_path(prompt_f)
        name_l = [i.title for i in name_type_l]
        if not name_l:
            return None
        path_check = self.manager.check(prompt_f)
        if not isinstance(path_check, os.stat_result):
            pass
        elif stat.S_ISDIR(path_check.st_mode):
            if len(name_l) == 1:
                return os.path.join(prompt_f, name_l[0])
            elif '/' in prompt_f and not prompt_f.endswith('/'):
                return prompt_f + '/'
            elif '\\' in prompt_f and not prompt_f.endswith('\\'):
                return prompt_f + '\\'
        else:
            return None
        dir_ni, base_ni = os.path.split(prompt_f)
        wait_l0 = [name_i for name_i in name_l if name_i.startswith(base_ni)]
        wait_l1 = [name_i for name_i in name_l if name_i.lower().startswith(base_ni.lower())]
        if len(wait_l0) == 1:
            return os.path.join(dir_ni, wait_l0[0])
        elif len(wait_l0+wait_l1) == 1:
            return os.path.join(dir_ni, wait_l1[0])
    
    # Automatically complete Name
    def fill_name(self, prompt_f:str) -> None|str:
        name_l = list(self.app_info_d.keys())
        id_l1 = [name_i for name_i in name_l if name_i.startswith(prompt_f)]
        if len(id_l1) == 1:
            return id_l1[0]
        elif len(id_l1) > 1:
            return None
        app_l = list(self.app_info_d.values())
        chname_l = [app_i.chname for app_i in app_l if app_i.chname and app_i.chname.startswith(prompt_f)]
        if len(chname_l) == 1:
            return chname_l[0]
        elif len(chname_l) > 1:
            return None
        id_l3 = [name_i for name_i in name_l if name_i.lower().startswith(prompt_f.lower())]
        if len(id_l3) == 1:
            return id_l3[0]
        else:
            return None

class Ass:
    class Info:
        __slots__ = ['index', 'text', 'type', 'path', 'host']
        def __init__(self, index:int,text:str,type:Literal['path','app'],path:str,host:str):
            self.index = index
            self.text = text
            self.type = type
            self.path = path
            self.host = host

class NameTagWidget(QWidget):
    def __init__(self, host_sd:atuple, basename_sd:atuple, host_font_f:atuple, basename_font_f:atuple, height_f:atuple):
        super().__init__()
        self.host_sd = host_sd
        self.basename_sd = basename_sd
        self.host_font_f = host_font_f
        self.basename_font_f = basename_font_f
        self.height_f = height_f
        if height_f is not None:
            UIUpdater.set(height_f, self.setFixedHeight, 'height')
        self._windowSet()
        self._initUI()
    
    def _windowSet(self):
        self.setWindowFlags(self.windowFlags()|Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setAttribute(Qt.WA_TranslucentBackground)  # 设置窗口属性为透明
    
    def _initUI(self):
        self.layout_0 = amlayoutH(align_v='c', spacing=1)
        self.host_label = NameTag(font=self.host_font_f, style_config=self.host_sd, height=self.height_f)
        self.basename_label = NameTag(font=self.basename_font_f, style_config=self.basename_sd, height=self.height_f)
        add_obj(self.host_label, self.basename_label, parent_f=self.layout_0)
        self.setLayout(self.layout_0)
        self.layout_0.setContentsMargins(0, 0, 0, 0)

    def setHost(self, host:str):
        self.host_label.setText(host)

    def setBasename(self, basename:str):
        self.basename_label.setText(basename)

    @Slot(list)
    def setPosition(self, pos:list[int]):
        if not self.isVisible():
            return
        self.setGeometry(pos[0], pos[1], self.width(), self.height())

class BasicAS(QListWidget):
    def focusNextPrevChild(self, next):
        return True
    def __init__(self, config:"Config_Manager", parent:"ControlLauncher",manager:"ManagerGroup"):
        super().__init__(parent)
        self.up = parent
        self.name = "associate_list"
        self.launcher_manager:LauncherPathManager = manager.launcher
        self.path_manager:TransferPathManager = manager.transfer
        self.task_manager:TaskManager = manager.task
        self.event_manager:GlobalMouseListener = manager.event
        self.config = config.deepcopy()
        self._loadAll()
    
    def startDrag(self, supportedActions: Qt.DropActions):
        item_f = self.currentItem()
        self.selected_item = item_f
        self.selected_label = self._itemLabel(item_f)
        self.is_dragging = True
        cwd_f = self.get_cwd()
        if cwd_f is None:
            return
        text_f = self._itemText(item_f)

        self.event_manager.resume('move')
        self.name_widget.setHost(GV.HOST)
        self.name_widget.setBasename(text_f)
        self.name_widget.adjustSize()
        self.name_widget.show()
        drag = QDrag(self)
        self.watcher.setSrc(os.path.join(cwd_f, text_f), GV.HOST)
        mime_data = QMimeData()
        if not os.path.exists(self.path_i):
            with open(self.path_i, 'a') as f:
                f.write("haha")
        mime_data.setUrls([QUrl.fromLocalFile(self.path_i)])
        drag.setMimeData(mime_data)
        drag.exec_(Qt.CopyAction)  
        self.name_widget.hide()
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls() or event.source() == self: 
            event.acceptProposedAction()  
    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasUrls()or event.source() == self:
            event.acceptProposedAction()
        else:
            event.ignore()
    def dropEvent(self, event: QDropEvent):
        mime_data = event.mimeData()
        if mime_data.hasUrls():  
            pos_f = event.pos()
            item_f = self.itemAt(pos_f)
            if item_f is None:
                return
            src = self.watcher.src
            cwd_f = self.get_cwd()
            hostname = self.watcher.src_hostname
            text_f = self._itemText(item_f)
            if text_f == "..":
                self._transfer(src=src, src_hostname=hostname, dst=os.path.dirname(cwd_f), dst_hostname=GV.HOST)
            else:
                dst = os.path.join(cwd_f, text_f)
                if not dst == cwd_f:
                    d_r = self.path_manager.check(dst, GV.HOST)
                    if d_r and stat.S_ISDIR(d_r.st_mode):
                        self._transfer(src=src, src_hostname=hostname, dst=dst, dst_hostname=GV.HOST)
            event.acceptProposedAction()

    @abstractmethod
    def _upload(self, src:str):
        pass
    
    def _loadAll(self):
        self.selected_item = None
        self.selected_label = None
        self.hover_label = None
        self.is_dragging = False
        self.pause_timer = QTimer(self)
        self.pause_timer.setSingleShot(True)
        self.pause_timer.setInterval(100)

        self.setAcceptDrops(True) 
        self.setDragEnabled(True) 
        self.setDropIndicatorShown(True)
        self.config.group_chose("Launcher", self.name)

        # load value
        pre = ['Launcher', self.name]
        self.extra_style_dict = {}
        self.max_item_maintain = UIUpdater.get(atuple(pre+['max_item_maintain']), 999)
        self.max_length = UIUpdater.get(atuple(pre+['max_length']), 600)
        self.max_app_num = UIUpdater.get(atuple(pre+['max_app_num']), 999)

        # load pointer
        ## style config
        self.pre = ['Launcher', self.name]
        self.button_config = atuple('Launcher', self.name,'style','button')
        self.label_config = atuple('Launcher', self.name, 'style', 'label')
        self.main_config = atuple('Launcher', self.name, 'style', 'main')
        self.item_config = atuple('Launcher', self.name, 'style', 'item')
        self.scroll_bar_config = atuple('Launcher', self.name, 'style', 'scroll_bar')
        self.font_a = atuple('Launcher', self.name, 'font', 'main')
        self.icon_proportion = atuple(self.pre+['style','button','icon_proportion'])
        self.item_height = atuple(self.pre+['style','main','item','height'])
        self.menu_style = atuple('Launcher', self.name, 'style', 'menu', 'main')
        self.menu_item_style = atuple('Launcher', self.name, 'style', 'menu', 'item_button')
        self.menu_font = atuple('Launcher', self.name, 'font', 'menu')
        self.host_sd = atuple('Launcher', self.name, 'style', 'ItemNameTag', 'Hostname')
        self.basename_sd = atuple('Launcher', self.name, 'style', 'ItemNameTag', 'Basename')
        self.tag_host_font = atuple('Launcher', self.name, 'font', 'tag_hostname')
        self.tag_basename_font = atuple('Launcher', self.name, 'font', 'tag_basename')

        ## size
        pre = ['Launcher', self.name, 'Size']
        self.button_height = self.item_height
        self.extra_width = atuple(pre+['extra_width'])
        self.max_width = atuple(pre+['max_width'])
        self.min_width = atuple(pre+['min_width'])
        self.menu_item_height = atuple(pre+['menu_item_height'])


        self.app_info_d:dict[int:GV.LauncherAppInfo] = self.launcher_manager.app_d
        self.ass = Associate(self.max_app_num, self.app_info_d, self.path_manager)
        self.config.group_chose(mode="Launcher", widget=self.name, obj=None)
        self.line_margin = atuple('Launcher', self.name, 'style', 'main', 'widget', 'line_margin')

        UIUpdater.set(self.font_a, self.setFont, 'font')
        style_d = atuple('Launcher', self.name, 'style', 'main')
        self.style_ctl = self.customStyle(style_d)
        spacing_f = atuple('Launcher', self.name, 'style', 'main', 'item', 'spacing')
        UIUpdater.set(spacing_f, self.setSpacing, 'spacing')

        self._loadPtr()
        default_path = os.path.abspath("./tmp/vaccummer_superlauncher_url_temp_file94138.txt")
        self.path_i = UIUpdater.get(atuple("Launcher", "associate_list", "path", "hook_file_path"), default_path)
        task_data = WatcherTask(get_hard_drives(), os.path.basename(self.path_i), self.path_i)
        self.watcher:WT.FileWatcher = self.task_manager.create_and_run_task(TaskType.WATCHER, task_data)
        self.watcher.callback_info.connect(self._hook_result_reciver)
        self.event_manager.mouse_press.connect(self._left_button_release)
        self.name_widget = NameTagWidget(host_sd=self.host_sd, basename_sd=self.basename_sd, host_font_f=self.tag_host_font, basename_font_f=self.tag_basename_font, height_f=self.item_height)
        self.name_widget.hide()
        self.event_manager.mouse_move.connect(self.name_widget.setPosition)
        self.event_manager.mouse_move.connect(self._set_hover_label)
    
    @Slot(list)
    def _hook_result_reciver(self, src_dst_l:list[str]):
        hostname, src, dst = src_dst_l
        if self.selected_item is not None:
            label_f = self._itemLabel(self.selected_item)
            label_f.setSelected(False)
        if os.path.basename(dst) == os.path.basename(self.path_i):
            WW.Copier().rm(dst)
        else:
            GV.logger.error(title="WatcherError", message=f'Watcher get an invalid tracked path: "{dst}"')
            return
        dst = os.path.dirname(dst)
        if not self.path_manager.check(src, hostname):
            GV.logger.warning(title="WatcherSrcNotExists", message="FileWatcher doses't has valid src")
            return
        self._transfer(src=src, src_hostname=hostname, dst=dst, dst_hostname='Local')

    @Slot(list)
    def _left_button_release(self, trace_info:list=None):
        if ((not trace_info) or((trace_info[2] == mouse.Button.left) and (trace_info[3] == False))):
            self.is_dragging = False
            if (self.selected_label is not None):
                self.selected_label.setSelected(False)
                self.selected_label = None
            if self.hover_label is not None:
                self.hover_label.setSelected(False)
                self.hover_label = None
    
    @Slot(list)
    def _set_hover_label(self, pos:list[int]):
        if not self.is_dragging:
            return
        item_f = self.itemAt(self.mapFromGlobal(QPoint(pos[0], pos[1])))
        if item_f == self.selected_item:
            if self.hover_label is not None:
                self.hover_label.setSelected(False)
            return
        if item_f is None:
            return
        if self.hover_label is not None:
            self.hover_label.setSelected(False)
        self.hover_label = self._itemLabel(item_f)
        self.hover_label.setBgColor("#216ECE")

    def _get_prompt(self)->str:
        return self.input_text

    def get_cwd(self)->str|None:
        prompt_f = self._get_prompt()
        if not is_path(prompt_f):
            return None
        if self.path_manager.check(prompt_f) is None:
            return os.path.dirname(prompt_f)
        else:
            return prompt_f

    def get_exe_path(self, name:str)->str:
        for value_i in self.path_dict.values():
            value_t =  value_i.get(name, None)
            if value_t is not None:
                return value_t
        return ''

    @abstractmethod
    def _transfer(self, src:str, src_hostname:str, dst:str, dst_hostname:str):
        pass
class UIAS(BasicAS):
    resize_info = Signal(list)
    def __init__(self, config:"Config_Manager", parent:"ControlLauncher",manager:"ManagerGroup"):  
        super().__init__(config, parent, manager)
        self._inititems()
        self.setFocusPolicy(Qt.NoFocus)

    @dynamic_load(type_f='style')
    def customStyle(self, style_d:dict, escape_sign:dict={}):
        # dynamic style set
        main_bg = Udata(atuple('widget', 'background'), 'transparent')
        main_border = Udata(atuple('widget', 'border'), 'none')
        main_radius = Udata(atuple('widget', 'border_radius'), 20)

        item_bg_colors = Udata(atuple('item', 'background_colors'), ['#F7F7F7', '#FFC300', '#FF5733'])
        item_border = Udata(atuple('item', 'border'), 'none')
        item_border_radius = Udata(atuple('item', 'border_radius'), 10)
        item_padding = Udata(atuple('item', 'padding'), [0, 0, 0, 0])
        item_margin = Udata(atuple('item', 'margin'), 0)
        item_height = Udata(atuple('item', 'height'), 60)
        item_spacing = Udata(atuple('item', 'spacing'), 5)

        bar_handle_colors = Udata(atuple('scroll_bar', 'background_colors'), ['#32CC99'])
        orbit_color = Udata(atuple('scroll_bar', 'orbit_color'), 'rgba(255, 255, 255, 50)')
        bar_radius = Udata(atuple('scroll_bar', 'border_radius'), 4)
        bar_width = Udata(atuple('scroll_bar', 'width'), 15)
        bar_margin = Udata(atuple('scroll_bar', 'margin'), 3)
        bar_min_height = Udata(atuple('scroll_bar', 'min_height'), 30)
        temp_d = {'QListWidget': {
                'background-color': main_bg,
                'border': main_border,
                'border-radius': main_radius,
            },
            'QListWidget::item': {
                'background-color': item_bg_colors[0],
                'border': item_border,
                'padding': item_padding,
                'margin': item_margin,
                'height': item_height,
                'border-top-left-radius': item_border_radius,
                'border-top-right-radius': item_border_radius,
                'border-bottom-left-radius': item_border_radius,
                'border-bottom-right-radius': item_border_radius,
            },
            'QListWidget::item:hover': {
                'background': item_bg_colors[1],
            },
            'QListWidget::item:selected': {
                'background': item_bg_colors[2],
            },
            'QScrollBar': {
                'background': orbit_color,
                'width': bar_width,
                'margin': bar_margin,
                'border-top-left-radius': bar_radius[0],
                'border-top-right-radius': bar_radius[1],
                'border-bottom-left-radius': bar_radius[2],
                'border-bottom-right-radius': bar_radius[3],
            },
            'QScrollBar::handle': {
                'background': bar_handle_colors[0],
                'border-radius': bar_radius,
                'min-height': bar_min_height,
            },
            'QScrollBar::handle:vertical:hover': {
                'background': bar_handle_colors[1],
            },
            'QScrollBar::handle:vertical:pressed': {
                'background': bar_handle_colors[2],
            },
            'QScrollBar::handle:horizontal': {
                'width': 0,
                'height': 0,
                'background': 'transparent',
            },
            "QScrollBar::add-line": {
                "background": 'transparent',
                "height": "0px",
                "subcontrol-position": "bottom",
                "subcontrol-origin": "margin",
            },
            "QScrollBar::sub-line": {
                "background": 'transparent',
                "height": "0px",
                "subcontrol-position": "top",
                "subcontrol-origin": "margin",
            },
            "QScrollBar::sub-page, QScrollBar::add-page": {
                "background": 'transparent',
            }
        }

        if not hasattr(self, 'style_dict'):
            self.style_dict = {}
        self.style_dict = process_style_dict(self.style_dict, temp_d, escape_sign, style_d)
        self.setStyleSheet(style_make(self.style_dict|self.extra_style_dict))
        label_resize_factor = UIUpdater.get(atuple('Launcher', self.name, 'style', 'label', 'resize_fractor'), 0.8)
        item_height = UIUpdater.get(atuple('Launcher', self.name, 'style', 'item', 'height'), 60)
        self.resize_info.emit([item_height, label_resize_factor])

    def _init_signle_item(self, button_size:atuple, index_f:int, label_font:atuple=None):
        label_font = self.font_a if label_font is None else label_font
        item_i = QListWidgetItem()
        item_i.setData(Qt.UserRole + 1, AssItemInfo(index=index_f))
        button_i = YohoPushButton(icon_i=None, style_config=self.button_config, icon_proportion=self.icon_proportion)
        button_i.setFixedSize(1.2*UIUpdater.get(button_size),UIUpdater.get(button_size))
        button_i.clicked.connect(partial(self._changeicon, index_i=index_f))

        label_i = AutoLabel(text="Default", font=label_font, style_config=self.label_config, height=button_size)
        # label_i = LabelAlikeButton(text_f="Default", style_config=self.label_config, font_f=label_font, height_f=button_size)
        label_i.setAlignment(Qt.AlignVCenter|Qt.AlignLeft)
        # label_i.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout_i = amlayoutH(align_v='l')
        UIUpdater.set(self.line_margin, layout_i.setContentsMargins, 'margin')
        layout_i.setSpacing(0)
        layout_i.addWidget(button_i)
        layout_i.addWidget(label_i)
        layout_i.addStretch()
        widget_i = QWidget()
        widget_i.setLayout(layout_i)
        self.addItem(item_i)
        self.setItemWidget(item_i, widget_i)
        height_f = UIUpdater.get(button_size, 60)
        item_i.setSizeHint(QSize(self.viewport().width(), height_f))
        return item_i, button_i, label_i

    def _init_special_item(self):
        self.s_item, self.s_button, self.s_label = self._init_signle_item(self.button_height, -1)
        self.s_item.setData(Qt.UserRole, AssItemInfo(title="..", type=AssItemType.Backspace))
        self.s_label.setText('..')
        self.s_button.force_antype = 'shake'
        self.s_item.setHidden(True)
        self.sort_reverse = False
        self.sort_list = ['type', 'name', 'time', 'size']
        self.sort_index = 0
        self.sort_method = self.sort_list[self.sort_index]
        self.sort_icons_d = atuple('Launcher', self.name, 'sort_method')
        self.sort_icons = {}
        UIUpdater.set(self.sort_icons_d, self._init_sort_icons, 'style')
        self.s_button.setIcon(self.sort_icons.get(self.sort_method, QIcon()))

    def _init_sort_icons(self, sort_config:dict[str:str], escape_sign:dict={}):
        for name_i in self.sort_list:
            self.sort_icons[name_i]  = QIcon(sort_config.get('path', {}).get(name_i, ''))
        self.fliter_sign = sort_config.get('fliter_sign', [])

    def _inititems(self):
        self.button_l:list[QPushButton] = []
        self.label_l:list[AutoLabel] = []
        self.item_l:list[QListWidgetItem] = []
        # init ".." item
        self._init_special_item()
        for i in range(self.max_app_num):
            item_i, button_i, label_i = self._init_signle_item(self.button_height, i)
            item_i.setHidden(True)
            self.item_l.append(item_i)
            self.button_l.append(button_i)
            self.label_l.append(label_i)
    
    def _itemIndex(self, item:QListWidgetItem)->int:
        return self._itemInfo(item).index
    
    def _itemInfo(self, item:QListWidgetItem)->AssItemInfo:
        return item.data(Qt.UserRole)
    
    def _itemText(self, item:QListWidgetItem)->str:
        index_f = self._itemIndex(item)
        if index_f == -1:
            return ".."
        return self._itemLabel(item).text()
    
    def _itemButton(self, item:QListWidgetItem) -> QPushButton:
        index_f = self._itemIndex(item)
        if index_f == -1:
            return self.s_button
        return self.button_l[index_f]
    
    def _itemLabel(self, item:QListWidgetItem) -> AutoLabel:
        index_f = self._itemIndex(item)
        if index_f == -1:
            return self.s_label
        return self.label_l[index_f]
    
    @Slot(list)
    def _resizeLabelButton(self, info_l:list):
        if hasattr(self, 'label_size_info_l'):
            if self.label_size_info_l == info_l:
                return
        else:
            self.label_size_info_l = info_l
        item_height, label_resize_factor = self.label_size_info_l
        for i in range(len(self.item_l)):
            self.label_l[i].setFixedHeight(int(item_height*label_resize_factor))
            self.button_l[i].setFixedSize(item_height, item_height)
class AssociateList(UIAS):
    text_set_signal = Signal(str)
    app_launch_signal = Signal(str)
    file_transfer_signal = Signal(dict)
    file_operation_signal = Signal(GV.FileOperation)
    launch_signal = Signal(GV.LaunchTask)
    def __init__(self, config:"Config_Manager", parent:"ControlLauncher",manager:"ManagerGroup"):  
        super().__init__(config, parent, manager)
        self.type = 'name'
        self.transfer_task = Signal(dict)
        self.raise_()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self._initMenu()
        self.customContextMenuRequested.connect(self.right_click)
        self.itemClicked.connect(self.left_click)
    
    def _getItemIcon(self, info:AssItemInfo)->AIcon:
        match info.type:
            case AssItemType.App:
                request = GV.IconQuery(type_f=GV.ItemType.App, name=info.title, path=info.path, group=info.group, ID=info.app_id)
                return AIcon(self.launcher_manager.get_app_icon(request))
            case AssItemType.Filename:
                request = GV.IconQuery(type_f=GV.ItemType.File, name=info.title,path=info.path, host=info.host)
                return AIcon(self.launcher_manager.get_file_icon(request))
            case AssItemType.Foldername:
                request = GV.IconQuery(type_f=GV.ItemType.Folder, name=info.title, path=info.path, host=info.host)
                return AIcon(self.launcher_manager.get_folder_icon(request))
            case AssItemType.Error:
                return AIcon(self.launcher_manager.error_icon)  
            case _:
                GV.logger.warning(f"Unknown item type: {info.type}")
                return AIcon(self.launcher_manager.default_file_icon)
    
    @Slot(str)
    def update_associated_words(self, text:str):
        self.input_text = text
        num_n = len(self.item_l)
        if is_path(text):
            self.type = 'path'
            sign_n = 'path'
            word_type_l:list[AssItemInfo] = self.word_sort(self.ass.ass_path(text))
        else:
            sign_n = 'name'
            word_type_l = self.ass.ass_name(text)
        match_num = len(word_type_l)
        if sign_n == 'path':
            self.s_item.setHidden(False)
        else:
            self.s_item.setHidden(True)
        if num_n< match_num:
            for iti in range(match_num-num_n):
                item_i, button_i, label_i = self._init_signle_item(self.button_height, index_f=len(self.item_l))
                self.item_l.append(item_i)
                self.button_l.append(button_i)
                self.label_l.append(label_i)
        num_t = len(self.item_l)
        for i in range(num_t):
            if i >= match_num:
                if i > self.max_item_maintain:
                    self.removeItemWidget(self.item_l[i])
                    self.item_l.pop(i)
                    self.button_l.pop(i)
                    self.label_l.pop(i)
                    del button_i
                    del label_i
                    del item_i
                else:
                    self.item_l[i].setHidden(True)
                continue
            self.item_l[i].setHidden(False)
            info_i = word_type_l[i]
            text_i = info_i.title
            self.label_l[i].setText(text_i)
            ori_data = self.item_l[i].data(Qt.UserRole+1)
            self.item_l[i].setData(Qt.UserRole+1, ori_data|info_i)
            icon_f = self._getItemIcon(info_i)
            self.button_l[i].setIcon(icon_f)

    def _tab_complete(self, current_text:str):
        return self.ass.fill(current_text)
    
    def left_click(self, item:QListWidgetItem):
        # if self.selected_item is not None:
        #     index_f = self._itemIndex(self.selected_item)
        #     self.label_l[index_f].setSelected(True)
        # self.selected_item = item
        index_f = self._itemIndex(item)
        item_text = self._itemText(item)
        prompt_f = self._get_prompt()
        if is_path(prompt_f):
            if not self.path_manager.check(prompt_f):
                prompt_f = os.path.dirname(prompt_f)
            if index_f == -1:
                path_n = os.path.dirname(prompt_f)
            else:
                path_n = os.path.join(prompt_f, item_text)
                if '/' in prompt_f:
                    path_n = path_n.replace('\\', '/')
            self.set_input_text(path_n)
        else:
            info_dict = item.data(Qt.UserRole)
            self.app_launch_signal.emit(info_dict)
            self.set_input_text('')
    
    def _initMenu(self):
        self.action_l = ['Launch','Delete', 'New', 'Assign Icon', 'Reverse', 'Download', 'Download(Ask dir)', 'Cursor', 'VS']
        self.context_menu = AutoMenu(main_style_d=self.menu_style, item_style_d=self.menu_item_style, 
                                actions=self.action_l, values=[],font=self.menu_font,height_f=self.menu_item_height 
                                )
        self.context_menu.action_signal.connect(self.menu_action_process)

    def right_click(self, pos):
        prompt_f = self._get_prompt() 
        if not is_path(prompt_f):
            return 
        item = self.itemAt(pos)
        if not item:
            return
        index_f = self._itemIndex(item)
        self.label_l[index_f].setSelected(True)
        self.labelSelected = self.label_l[index_f]
        ass_info:Ass.Info = item.data(Qt.UserRole)
        values = []
        for action_i in self.action_l:
            values.append({'action':action_i, 'info':ass_info})
        self.context_menu.value_l = values
        self.context_menu.action(1, pos, self.mapToGlobal(QPoint(0, 0)))

    @Slot(dict)
    def menu_action_process(self, action_dict:dict):
        self.labelSelected.setSelected(False)
        if not action_dict:
            return
        self.context_menu.hide()
        transfer_info = {}
        action_type = action_dict['action']
        ass_info:Ass.Info = action_dict['info']
        match action_type:
        # ['Open','Delete', 'New', 'Assign Icon', 'Reverse', 'Download', 'Download(Ask dir)']
            case 'Open':
                type_f = ass_info.type
                name_f = ass_info.text
                path_f = ass_info.path
                host_f = ass_info.host
                launch_task = GV.LaunchTask(type_f=type_f, name=name_f, path=path_f, host=host_f)
                self.launch_signal.emit(launch_task)
            case 'Delete':
                host_f = ass_info.host
                path_f = ass_info.path
                file_operation = GV.FileOperation(operation='delete', src=path_f, dst='', src_host=host_f, dst_host='')
                self.file_operation_signal.emit(file_operation)
            case 'New':
                host_f = ass_info.host
                # TODO: Implement TIP UI to ask user to type in the name of the new file
            case 'Assign Icon':
                self.assign_icon(ass_info)
            case 'Reverse':
                self.sort_reverse = not self.sort_reverse
                self.update_associated_words(self.input_text)
            case 'Download':
                src_host = ass_info.host
                src_path = ass_info.path
                dst = self.path_manager.default_download_path
                file_operation = GV.FileOperation(operation='copy', src=src_path, dst=dst, src_host=src_host, dst_host='Local')
                self.file_operation_signal.emit(file_operation)
            case 'Download(Ask dir)':
                dst = QFileDialog.getExistingDirectory(self, "Select Download Dir", self.path_manager.download_filedialog_root)    # wait for change
                if not dst:
                    return
                src = src_path
                src_host = ass_info.host
                file_operation = GV.FileOperation(operation='copy', src=src, dst=dst, src_host=src_host, dst_host='Local')
                self.file_operation_signal.emit(file_operation)
            case _:
                return

    def assign_icon(self, ass_info:Ass.Info):
        pass

    def _changeicon(self, index_i):
        if index_i == -1:
            self.change_sort_method()
            return
        app_name = self.label_l[index_i].text()
        app_i = self.launcher_manager.app_d.get(app_name, None)
        if app_i is None:
            warnings.warn(f"App {app_name} not found in LauncherPathManager!")
            return
        group_i = app_i.group
        if app_name == "..":
            self.change_sort_method(index_i)
        options = QFileDialog.Options()
        file_filter = "Icons (*.svg *.png *.jpg *.jpeg *.ico *.bmp)"
        file_path, _ = QFileDialog.getOpenFileName(self, "Select an Icon", self.launcher_manager.icon_cache_folder, file_filter)
        if not file_path:
            return  
        dst_path = self.launcher_manager.app_icon_save(app_name, group_i, file_path)
        self.button_l[index_i].setIcon(AIcon(dst_path))
        app_i.icon_path = dst_path

    def set_input_text(self, text:str):
        self.text_set_signal.emit(text)
        
    def change_sort_method(self):
        self.sort_index = (self.sort_index+1) % len(self.sort_list)
        self.sort_method = self.sort_list[self.sort_index]
        self.s_button.setIcon(self.sort_icons.get(self.sort_method, QIcon()))
        self.update_associated_words(self.input_text)

    def sort_fliter(self, input_l:list[AssItemInfo])->list[AssItemInfo]:
        tar_unfliterred = []
        tar_fliterred = []
        for item_i in input_l:
            flier_check = False
            for sign_i in self.fliter_sign:
                if not isinstance(item_i.title, str):
                    print(1)
                if item_i.title.startswith(sign_i):
                    flier_check = True
                    break
            if flier_check:
                tar_fliterred.append(item_i)
            else:
                tar_unfliterred.append(item_i)
        return tar_unfliterred+tar_fliterred

    def word_sort(self, input_l:list[AssItemInfo])->list[AssItemInfo]:
        match self.sort_method:
            case 'name':
                if self.sort_reverse:
                    input_l.sort(key=lambda x: x.title, reverse=True)
                else:
                    input_l.sort(key=lambda x: x.title)
                return self.sort_fliter(input_l)
            case 'type':
                tar_dir = []
                tar_file = []
                for item_i in input_l:
                    if item_i.type == AssItemType.Dir:
                        tar_dir.append(item_i)
                    else:
                        tar_file.append(item_i)
                tar_dir = self.sort_fliter(tar_dir)
                tar_file = self.sort_fliter(tar_file)
                if self.sort_reverse:
                    return tar_file+tar_dir
                else:
                    return tar_dir+tar_file
            case 'size':
                input_l.sort(key=lambda x: x.stat.st_size, reverse=self.sort_reverse)
                return self.sort_fliter(input_l)
            case 'time':
                input_l.sort(key=lambda x: x.stat.st_mtime, reverse=self.sort_reverse)
                return self.sort_fliter(input_l)
            case _:
                return self.sort_fliter(input_l)

    def _transfer(self, src:str, src_hostname:str, dst:str, dst_hostname:str):
        print(src, src_hostname, dst, dst_hostname)
        pass

class PathModeSwitch(CustomComboBox):
    def __init__(self, parent:QMainWindow, config:Config_Manager, path_manager:TransferPathManager) -> None:
        self.up = parent
        self.path_manager:TransferPathManager = path_manager
        self.name = "path_mode_switch"
        self.config = config.deepcopy()
        self._load()
        super().__init__(modes=self.mode_list, style_d=self.style_d, box_height=self.box_height, 
                         menu_font=self.menu_font, box_font=self.box_font, parent=parent)
        self.ForceRadius()
    def _load(self):
        self.hostd = self.path_manager.hostd
        self.mode_list = list(self.hostd.keys())
        self.pre = atuple('Launcher', self.name)
        self.style_d = atuple('Launcher', self.name, 'style')
        self.box_width = atuple('Launcher', self.name, 'Size', 'box_width')
        self.box_height = atuple('Launcher', self.name, 'Size', 'box_height')
        self.item_height = atuple('Launcher', self.name, 'Size', 'item_height')
        self.box_font = atuple('Launcher', self.name, 'font', 'box')
        self.menu_font = atuple('Launcher', self.name, 'font', 'menu')

    def setState(self, index_n:int):
        '''
        0: OK
        1: Connecting
        2: Error
        '''
        if not isinstance(index_n, int) and -1<index_n<3:
            return
        self.color_state = index_n
        self.box_w.color_state = index_n
        self.menu_w.color_state = index_n
        UIUpdater.action(self.style_d|atuple('box'), self.box_w.customStyle, 'box')
        UIUpdater.action(self.style_d|atuple('menu'), self.menu_w.customStyle, 'menu')
    def ForceRadius(self):
        self.box_w.extra_style_dict[atuple('QPushButton', 'border-top-right-radius')] = 0
        self.box_w.extra_style_dict[atuple('QPushButton', 'border-bottom-right-radius')] = 0
        self.box_w.setStyleSheet(style_make(self.box_w.style_dict|self.box_w.extra_style_dict))

class InputBox(AutoEdit):
    key_press = Signal(dict)
    def __init__(self, parent:QMainWindow, config:Config_Manager):
        self.up = parent
        self.name = "input_box"
        self.height_f = atuple('Launcher', self.name, 'Size', 'height')
        self.font_f = atuple('Launcher', self.name, 'font', 'main')
        self.config = config.deepcopy()
        self.style_d = atuple('Launcher', self.name, 'style')
        super().__init__(text='', font=self.font_f, style_d=self.style_d, height=self.height_f)
        self.custom_keys = [Qt.Key_Tab, Qt.Key_Return, Qt.Key_Enter, Qt.Key_Up, Qt.Key_Down]
    
    def event(self, event:QEvent):
        match event.type():
            case QEvent.DragEnter:
                mime_data = event.mimeData()
                if mime_data.hasUrls():  
                    event.acceptProposedAction()  
                    return True  
                else:
                    return super().event(event)  
            case QEvent.DragMove:  
                mime_data = event.mimeData()
                if mime_data.hasUrls():
                    event.acceptProposedAction()  
                    return True  
                else:
                    return super().event(event)  
            case QEvent.Drop:  
                mime_data = event.mimeData()
                if mime_data.hasUrls():  
                    urls = mime_data.urls()
                    paths = [url.toLocalFile() for url in urls]  
                    self.key_press.emit({'type':'file_drop', 'paths':paths, "text":self.text()})
                    event.acceptProposedAction()
                    return True  
            case QEvent.KeyPress:
                if event.key() in self.custom_keys:
                    self.key_press.emit({'type':'key_press', 'key':event.key(), "text":self.text()})
                    return True
                else:
                    return super().event(event)
            case _:
                return super().event(event)
    
    @Slot(str)
    def external_set_text(self, text:str):
        self.setText(text)

class SearchTogleButton(YohoPushButton):
    search_signal=Signal(dict) #{'url':str, 'sign':str}
    def __init__(self, parent, config:Config_Manager):
        self.up = parent
        self.name = "search_togle_button"
        config = config.deepcopy()
        icons = atuple('Launcher', self.name, 'icons')
        urls = atuple('Launcher', self.name, 'urls')
        sign = atuple('Launcher', self.name, 'sign')
        icon_proportion = atuple('Launcher', self.name, 'Size', 'icon_proportion')
        style_d = atuple('Launcher', self.name, 'style')

        self.url = config[urls][0]
        button_size = atuple('Launcher', self.name, 'Size', 'button_size')
        super().__init__(icon_i=config[icons][0], 
                         icon_proportion=icon_proportion,
                         style_config=style_d,
                        size_f=button_size,
                        parent=parent)
        UIUpdater.set(alist(icons, urls, sign), self._updateURL, alist())
        self.clicked.connect(self._click)
        self.show()
        self.raise_()
        # self._init_geometry(input_box_geometry)

    def _updateURL(self, icons:atuple, urls:atuple, sign:atuple):
        self.urls = urls
        self.icons = icons[:len(urls)]
        self.sign = sign
        if self.url in self.urls:
            return 
        else:
            self.url = urls[0]
            self.setIcon(QIcon(self.icons[0]))
        
    def wheelEvent(self, event):
        delta = event.angleDelta().y()  # 获取鼠标滚轮的增量
        index_n = self.urls.index(self.url)
        if delta > 0:
            index_n = (index_n+1) % len(self.urls)
        elif delta < 0: 
            index_n = (index_n+len(self.icons)-1) % len(self.icons)
        self.url = self.urls[index_n]
        self.setIcon(AIcon(self.icons[index_n]))

    def _click(self):
        self.search_signal.emit({'url':self.url, 'sign':self.sign})
    
    @Slot(dict)
    def _update_geometry(self, input_box_geometry:dict):
        rec:QRect = input_box_geometry['abs']
        x_n = rec.x()-GV.GEOMETRY[0]+rec.width()-self.width()
        y_n = rec.y()-GV.GEOMETRY[1]
        self.setGeometry(x_n, y_n, self.width(), self.height())

class ShortcutButton(QWidget):
    launch_signal = Signal(str)
    def __init__(self, parent: QMainWindow, config:Config_Manager, shortcuts_manager:ShortcutsPathManager) -> None:
        super().__init__(parent)
        self.manager:ShortcutsPathManager = shortcuts_manager
        self.ctrl_pressed = False
        self.name = "shortcut_obj"
        self.up = parent
        self.config = config.deepcopy().group_chose(mode="Launcher", widget=self.name)
        self.layout_0 = amlayoutV(align_h='c')
        self.setLayout(self.layout_0)
        self.layout_0.setContentsMargins(0, 0, 0, 0)
        self._initpara()
        self._initUI()
        self.refresh()
        #self.setFixedSize(*self.config.get(None, widget="Size", obj=self.name)[-2:], )

    def _initpara(self):
        self.v_num = self.config[atuple('Launcher', 'shortcut_obj', 'vertical_button_num')]
        self.h_num = self.config[atuple('Launcher', 'shortcut_obj', 'horizontal_button_num')]
        self.icon_proportion = atuple('Launcher', 'shortcut_obj', 'Size', 'icon_proportion')
        self.num_exp = self.v_num * self.h_num

        self.df = self.manager.df
        self.num_real = self.df.shape[0]
        self.buttonlabel_list = []
        pre = ['Launcher', self.name]
        self.size_i = atuple(pre+['Size', 'button_r'])
        self.name_label_width = atuple(pre+['Size', 'name_label_width'])

        self.font_i = atuple(pre+['font', 'button_title'])
        self.style_d = atuple(pre+['style', 'shortcut_button'])
        self.button_label_style = atuple(pre+['style', 'button_label'])
        
    def _launch(self):
        button = self.sender()
        path = button.property('path')
        self.launch_signal.emit(path)
        try:
            os.startfile(path)
        except Exception as e:
            print(e) 
    
    def _initUI(self):
        index_f = 0
        for v_i in range(self.v_num):
            layout_if = QHBoxLayout()
            layout_if.setAlignment(Qt.AlignCenter)
            for h_i in range(self.h_num):
                name = ""
                icon = self.config.get('default_button_icon', obj='path')
                path = ''
                layout_i = QVBoxLayout()
                button_i = YohoPushButton(icon_i=icon, style_config=self.style_d, size_f=self.size_i, an_time=150, icon_proportion=self.icon_proportion)
                button_i.setProperty('path', path)
                label_i = AutoLabel(text=name, font=self.font_i, style_config=self.button_label_style, width=self.name_label_width)
                button_i.clicked.connect(self._launch)
                self.buttonlabel_list.append((button_i, label_i))
                layout_i.addWidget(button_i)
                #layout_i.addWidget(label_i)
                layout_if.addLayout(layout_i)
                index_f += 1
            self.layout_0.addLayout(layout_if)                    

    def refresh(self):
        index_f = 0
        for v_i in range(self.v_num):
            for h_i in range(self.h_num):
                if index_f < self.num_real:
                    name, _, path = self.df.iloc[index_f, 0:3]
                    icon = self.manager.geticon(name)
                if isinstance(icon, atuple):
                    icon = self.config[icon]
                button_i, label_i = self.buttonlabel_list[index_f]
                button_i.setProperty('path', path)
                button_i.setIcon(QIcon(icon))
                label_i.setText(name)
                index_f += 1

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.ctrl_pressed = True
    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.ctrl_pressed = False
    def wheelEvent(self, event):
        if not self.ctrl_pressed:
            return
        # use wheel to resize the button
        if event.angleDelta().y() > 0:
            factor_i = 1.1
        else:
            factor_i = 0.9
        for button_i, label_i in self.buttonlabel_list:
            pix_size = label_i.font().pixelSize()
            label_i.font().setPixelSize(int(pix_size*factor_i))
            size_ori = button_i.size()
            button_i._resize([int(size_ori.width()*factor_i), int(size_ori.height()*factor_i)])

class TransferProgress(ProgressBar):
    def __init__(self, parent, max_value, height):
        self.up = parent
        super().__init__(parent, max_value, height)

class TransferInfo:
    def __init__(self, src:str, dst:str, src_host:str, dst_host:str, total_size:int):
        self.src = src
        self.dst = dst
        self.src_host = src_host
        self.dst_host = dst_host
        self.total_size = total_size
        random_num = random.randint(0, 1000000)
        self.ID = hash(tuple(src, dst, total_size, random_num))
        self.progress = 0

class ProgressWidget2(QWidget):
    def __init__(self, parent, config:Config_Manager, data:dict):
        self.up = parent
        super().__init__()
        self.data_l = []

    def _loadConfig(self):
        self.bar_height = atuple('Launcher', 'progress_widget', 'Size', 'bar_height')
        self.info_height = atuple('Launcher', 'progress_widget', 'Size', 'info_height')
        self.label_font = atuple('Launcher', 'progress_widget', 'font', 'label_font')
        self.src_label_bkg = atuple('Launcher', 'progress_widget', 'color', 'src_label_background')
        self.dst_label_bkg = atuple('Launcher', 'progress_widget', 'color', 'dst_label_background')
        self.arrow_icon = atuple('Launcher', 'progress_widget', 'path', 'arrow_icon')
        self.close_icon = atuple('Launcher', 'progress_widget', 'path', 'close_icon')

    def _initUI(self):
        # total layout
        self.layout_0 = amlayoutV()
        self.setLayout(self.layout_0)

        # left layout
        self.layout_up = amlayoutH()
        # right layout
        self.layout_down = amlayoutH()
        add_obj(self.layout_up, self.layout_down, parent_f=self.layout_0)

        self.bar = ProgressBar(self, self.data['max_value'], self.bar_height)
        self.progress_label = AutoLabel(self.progress, self.label_font)

        add_obj(self.bar, self.progress_label, parent_f=self.layout_up)

        self.label_src = AutoLabel(text=self.src, font=self.label_font, color=self.src_label_bkg, height=self.info_height)
        self.label_dst = AutoLabel(text=self.dst, font=self.label_font, color=self.dst_label_bkg, height=self.info_height)

        self.arrow = AutoLabel(text='',icon_f=self.arrow_icon, height=self.info_height)

        self.close_button = YohoPushButton(self.close_icon, self.info_height, "shake", an_time=90)
        self.close_button.clicked.connect(self._terminate)
        add_obj(self.label_src, self.arrow, self.label_dst, parent_f=self.layout_down)
        self.layout_down.addStretch(1)
        self.layout_down.addWidget(self.close_button)

    def update(self, size_transfered:int):
        self.size_transfered += size_transfered
        self.progress = self.size_transfered/self.total_task
        self.bar.setValue(self.progress)
        self.progress_label.setText(f"{self.progress:.2f}%")

    def _terminate(self):
        pass
    
    def add(self, data:TransferInfo):
        pass

class ProgressInfo(QWidget):
    def __init__(self, parent):
        self.up = parent
        super().__init__(parent)
        self.extra_style_dict = {}
        self.setWindowFlags(Qt.FramelessWindowHint)  
        # self.setAttribute(Qt.WA_StyledBackground, True)
        self._loadConfig()
        self._initLayout()
        self._initLabel()

    def _loadConfig(self):
        self.main_margin = atuple('Launcher', 'progress_widget', 'Size', 'toolwidget', 'main_margin')
        self.main_spacing = atuple('Launcher', 'progress_widget', 'Size', 'toolwidget', 'main_spacing')
        self.label_spacing = atuple('Launcher', 'progress_widget', 'Size', 'toolwidget', 'label_spacing')
        self.title_label_width = atuple('Launcher', 'progress_widget', 'Size', 'toolwidget', 'title_label_width')
        self.extra_width = atuple('Launcher', 'progress_widget', 'Size', 'toolwidget', 'extra_width')
        self.label_height = atuple('Launcher', 'progress_widget', 'Size', 'toolwidget', 'label_height')
        self.title_label_font = atuple('Launcher', 'progress_widget', 'font', 'title_label_font')
        self.info_label_font = atuple('Launcher', 'progress_widget', 'font', 'info_label_font')
        self.line_margin = atuple('Launcher', 'progress_widget', 'Size', 'toolwidget', 'line_margin')
        self.title_style_d = atuple('Launcher', 'progress_widget', 'style', 'tool_widget', 'title')
        self.info_style_d = atuple('Launcher', 'progress_widget', 'style', 'tool_widget', 'info')
        self.main_style_d = atuple('Launcher', 'progress_widget', 'style', 'tool_widget', 'main')
        self.extra_height = atuple('Launcher', 'progress_widget', 'Size', 'toolwidget', 'extra_height')
        UIUpdater.set(alist(self.label_height, self.label_spacing, self.extra_height), self._SetHeight)
        UIUpdater.set(self.extra_width, self._dynamicLoad, 'width')
        self.setMinimumWidth(self.extra_width+UIUpdater.config[self.title_label_width]+80)
        self.style_ctl = self.customStyle(self.main_style_d)

    @dynamic_load(type_f='style')
    def customStyle(self, style_d:dict, escape_sign:dict={}):
        bg_color = Udata(atuple('background'), '#F7F7F7')
        border = Udata(atuple('border'), 'none')
        border_radius = Udata(atuple('border-radius'), 10)

        if not hasattr(self, 'style_dict'):
            self.style_dict = {}
        
        temp_dict = {"QWidget":
                           {'background':bg_color,
                            'border':border,
                            'border-radius':border_radius,}
        }
        self.style_dict = process_style_dict(self.style_dict, temp_dict, escape_sign, style_d)
        self.setStyleSheet(style_make(self.style_dict|self.extra_style_dict))

    def _SetHeight(self, line_height, spacing, extra_height):
        height_t = 4*line_height+3*spacing+extra_height
        self.setFixedHeight(height_t)

    def _dynamicLoad(self, extra_width:int):
        self.extra_width = extra_width

    def _initLayout(self):
        self.layout_0 = amlayoutV(align_h='c')
        self.setLayout(self.layout_0)
        UIUpdater.set(self.main_margin, self.layout_0.setContentsMargins, type_f='margin')
        UIUpdater.set(self.main_spacing, self.layout_0.setSpacing)

        self.src_layout = amlayoutH(align_v='c')
        self.dst_layout = amlayoutH(align_v='c')
        self.size_layout = amlayoutH(align_v='c')
        self.progress_layout = amlayoutH(align_v='c')
        UIUpdater.set(self.label_spacing, self.src_layout.setSpacing)
        UIUpdater.set(self.label_spacing, self.dst_layout.setSpacing)
        UIUpdater.set(self.label_spacing, self.size_layout.setSpacing)
        UIUpdater.set(self.label_spacing, self.progress_layout.setSpacing)
        UIUpdater.set(self.line_margin, self.src_layout.setContentsMargins, type_f='margin')
        UIUpdater.set(self.line_margin, self.dst_layout.setContentsMargins, type_f='margin')
        UIUpdater.set(self.line_margin, self.size_layout.setContentsMargins, type_f='margin')
        UIUpdater.set(self.line_margin, self.progress_layout.setContentsMargins, type_f='margin')

        add_obj(self.src_layout, self.dst_layout, self.size_layout, self.progress_layout, parent_f=self.layout_0)

    def _initLabel(self):
        self.src_title = AutoLabel(text='Src', font=self.title_label_font, height=self.label_height, width=self.title_label_width, style_config=self.title_style_d)
        self.src_info = AutoLabel(text='', font=self.info_label_font, height=self.label_height, style_config=self.info_style_d)
        add_obj(self.src_title, self.src_info, parent_f=self.src_layout)

        self.dst_title = AutoLabel(text='Dst', font=self.title_label_font, height=self.label_height, width=self.title_label_width, style_config=self.title_style_d)
        self.dst_info = AutoLabel(text='', font=self.info_label_font, height=self.label_height, style_config=self.info_style_d)
        add_obj(self.dst_title, self.dst_info, parent_f=self.dst_layout)


        self.size_title = AutoLabel(text='Size', font=self.title_label_font, height=self.label_height, width=self.title_label_width,
                                    style_config=self.title_style_d)
        self.size_info = AutoLabel(text='', font=self.info_label_font, height=self.label_height, style_config=self.info_style_d)
        add_obj(self.size_title, self.size_info, parent_f=self.size_layout)

        self.progress_title = AutoLabel(text='Progress', font=self.title_label_font, height=self.label_height,
        width=self.title_label_width, style_config=self.title_style_d)
        self.progress_info = AutoLabel(text='', font=self.info_label_font, height=self.label_height, style_config=self.info_style_d)
        add_obj(self.progress_title, self.progress_info, parent_f=self.progress_layout)
    
    def format_size(self, size:int):
        if size < 1024:
            return f"{size}B"
        elif size < 1024*1024:
            return f"{size/1024:.2f}KB"
        elif size < 1024*1024*1024:
            return f"{size/1024/1024:.2f}MB"
        else:
            return f"{size/1024/1024/1024:.2f}GB"
        
    @Slot(dict)
    def change_info(self, info_d:TransferInfo):
        '''
        info_d:
            src: str
            src_host: str
            dst: str
            dst_host: str
            size: int (in bytes)
            progress: float (in percentage)
        '''
        src = info_d.src
        src_host = info_d.src_host
        dst = info_d.dst
        dst_host = info_d.dst_host
        size = info_d.total_size
        progress = info_d.progress
        src_str = f"{src_host}@{src}"
        dst_str = f"{dst_host}@{dst}"
        size_str = self.format_size(size)
        progress_str = f"{progress:.2f}%"
        width_t = max([QFontMetrics(self.src_info.font()).width(i) for i in [src_str, dst_str, size_str, progress_str]])
        self.src_info.setFixedWidth(width_t+self.extra_width)
        self.dst_info.setFixedWidth(width_t+self.extra_width)
        self.size_info.setFixedWidth(width_t+self.extra_width)
        self.progress_info.setFixedWidth(width_t+self.extra_width)
        if src_str != self.src_info.text():
            self.src_info.setText(src_str)
        if dst_str != self.dst_info.text():
            self.dst_info.setText(dst_str)
        if size_str != self.size_info.text():
            self.size_info.setText(size_str)
        if progress_str != self.progress_info.text():
            self.progress_info.setText(progress_str)
        self.setFixedWidth(width_t+self.extra_width+self.title_label_width)
    
    def SetProgress(self, progress:float):
        self.progress_info.setText(f"{progress:.2f}%")

class ProgressWidget(QWidget):
    update_signal = Signal(dict)
    kill_signal = Signal(int)
    add_signal = Signal(TransferInfo)
    def __init__(self, parent,):
        self.up = parent
        super().__init__(parent)
        self._loadConfig()
        self._initUI()
        UIUpdater.set(self.main_height, self.setFixedHeight)
        self.data_dict = {}
        self.tipTimer = QTimer(self)
        self.tipTimer.setSingleShot(True)
        self.tipTimer.timeout.connect(self._showTip)
        self.ID = None

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.RollIndex(-1)
        else:
            self.RollIndex(1)
    
    def _loadConfig(self):
        self.bar_height = atuple('Launcher', 'progress_widget', 'Size', 'bar_height')
        self.arrow_icon = atuple('Launcher', 'progress_widget', 'path', 'arrow_icon')
        self.close_icon = atuple('Launcher', 'progress_widget', 'path', 'close_icon')
        self.bar_style = atuple('Launcher', 'progress_widget', 'style', 'bar')
        self.icon_size = atuple('Launcher', 'progress_widget', 'Size', 'icon_size')
        self.icon_style = atuple('Launcher', 'progress_widget', 'style', 'close_button')
        self.main_style = atuple('Launcher', 'progress_widget', 'style', 'main')
        self.main_tip_style = atuple('Launcher', 'progress_widget', 'style', 'main_tip')
        self.main_height = atuple('Launcher', 'progress_widget', 'Size', 'widget_height')
        self.info_height = atuple('Launcher', 'progress_widget', 'Size', 'info_height')
    
    def _initUI(self):
        # total layout
        self.layout_0 = amlayoutH(align_v='c')
        self.layout_0.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout_0)

        self.bar = ProgressBar(parent=self, style_d=self.bar_style, max_value=100, height=self.bar_height)
        self.close_button = YohoPushButton(icon_i=self.close_icon, style_config=self.icon_style, size_f=self.icon_size)
        add_obj(self.bar, self.close_button, parent_f=self.layout_0)

        self.info_widget = ProgressInfo(self.up)
        self.info_widget.hide()

    def enterEvent(self, event):
        self.tipTimer.start(800)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.tipTimer.stop()
        self.info_widget.hide()
        super().leaveEvent(event)

    def _showTip(self):
        if not self.data_dict:
            return
        cursor_pos = QCursor.pos()
        #x_p, y_p = self.up.geometry().x(), self.up.geometry().y()
        x = cursor_pos.x()-self.up.geometry().x()+10
        y = cursor_pos.y()-self.up.geometry().y()+10

        w, h = self.info_widget.size().width(), self.info_widget.size().height()
        self.info_widget.setGeometry(x,y,w,h)
        self.info_widget.raise_()
        self.info_widget.show()
    
    def kill(self):
        ID_f = self.ID
        index_t = self.getIndex(ID_f)
        self.data_dict.pop(ID_f)
        if not self.data_dict:
            self.ID = None
        else:
            index_n = (index_t+len(self.data_dict))%len(self.data_dict)
            self.ID = list(self.data_dict.keys())[index_n]
            self.info_widget.change_info(self.data_dict[self.ID])
        self.kill_signal.emit(ID_f)

    def change_info(self, data:TransferInfo):
        self.info_widget.change_info(data)
        self.ID = data.ID
        self.bar.setValue(data.progress)

    def RollIndex(self, index_f:Literal[-1, 1]):
        if not self.data_dict:
            return
        index_n = self.getIndex(self.ID)
        index_n += index_f
        index_n = max(0, min(len(self.data_dict)-1, index_n))
        self.ID = list(self.data_dict.keys())[index_n]
        self.info_widget.change_info(self.data_dict[self.ID])

    def getIndex(self, ID):
        for index, data in enumerate(list(self.data_dict.keys())):
            if data == ID:
                return index
        warnings.warn(f"ID {ID} not found in data_l")
        return 0
    
    def getCurrentData(self):
        return self.data_dict[self.ID]
    
    def getCurrentID(self):
        return self.ID
    
    @Slot(int)
    def update(self, data_f:dict[Literal['ID', 'size']]):
        self.data_dict[data_f['ID']].progress += data_f['size']/self.data_dict[data_f['ID']].total_size
        if data_f['ID'] == self.ID:
            self.info_widget.SetProgress(copy.deepcopy(self.data_dict[data_f['ID']].progress))
            self.bar.setValue(copy.deepcopy(self.data_dict[data_f['ID']].progress))

    @Slot(TransferInfo)
    def add(self, data:TransferInfo):
        if not self.data_dict:
            self.data_dict[data.ID] = data
            self.ID = data.ID
            self.info_widget.change_info(data)
        else:
            self.data_dict[data.ID] = data

class ProgressWidgetManager(QStackedWidget):
    def __init__(self, parent:QWidget, config:Config_Manager):
        super().__init__(parent)
        self.name = 'progress_widget'
        self.up = parent
        self.config = config.deepcopy().group_chose(mode="Launcher", widget=self.name)
    
    def _load(self):
        self.bar_height = self.config.get('bar_height', obj='Size')
        self.info_height = self.config.get('info_height', obj='Size')

        self.label_font = self.config.get('label_font', obj='font')

        self.srclabel_bkglabel_bkg = self.config.get('src_label_background', obj='color')
        self.dstlabel_bkg = self.config.get('dst_label_background', obj='color')

        self.arrow_icon = QIcon(self.config.get('arrow_icon', obj='path'))
        self.close_icon = QIcon(self.config.get('close_icon', obj='path'))

    def _add_widget(self, data:dict):
        widget = ProgressWidget(self.up, self.config, data)
        self.addWidget(widget)
        return widget

class AsBACKup:
    def _upload(self, src:Union[str, list]):
        prompt_text = self._get_prompt()
        if not is_path(prompt_text):
            return
        if not self.path_manager.check(prompt_text):
            prompt_text = os.path.dirname(prompt_text)
        if not self.path_manager.isdir(prompt_text):
            return
        if isinstance(src, str):
            src = [src]
        src = [i for i in src if os.path.exists(i)]
        if src:
            self._transfer_preprocess({'src':src, 'dst':prompt_text, 'task_type':'upload',
                                    'host':GV.HOST, 'host_type':self.path_manager.host_type})
    
    def _download(self, item, ask_save_dir:bool):
        if ask_save_dir:
            dir_path = QFileDialog.getExistingDirectory(self, "Choose a directory to save the file", self.filelog_default_path)
            if not dir_path:
                return
        else:
            dir_path = self.download_dir
        item_text = self._itemText(item)
        prompt_f = self._get_prompt()
        if not self.path_manager.check(prompt_f):
            prompt_f = os.path.dirname(prompt_f)
        src = os.path.join(prompt_f, item_text)
        if os.path.isdir(dir_path) and self.path_manager.check(src):
            file_type = 'dir' if self.path_manager.isdir(src) else 'file'
            self._transfer_preprocess({'src':[src], 'dst':dir_path, 'task_type':'download', 
                                     'host':self.up.HOST, 'host_type':self.path_manager.host_type})

    def _transfer_preprocess(self, tasks:dict):
        task_tupe_list = [] # [(src, dst, size), ...]
        type_t = tasks['task_type']
        host = tasks['host']
        host_type = tasks['host_type']
        if type_t == 'upload' or host_type != 'Remote':
            # src in upload task is a list of local directories or files
            # dst is a Local or Remote directory
            for src_i in tasks['src']:
                if os.path.isdir(src_i):
                    for dirpath, dirnames, filenames in os.walk(src_i):
                        for filename_i in filenames:
                            src = os.path.join(dirpath, filename_i)
                            dst = os.path.join(tasks['dst'], os.path.relpath(dirpath, src_i), filename_i)
                            size_f = os.path.getsize(src)
                            task_tupe_list.append((src, dst, size_f))
                else:
                    size_f = os.path.getsize(src_i)
                    task_tupe_list.append((src_i, os.path.join(tasks['dst'], os.path.basename(src_i)), size_f))
        else:
            for src_i in tasks['src']:
                for relpath, filename, file_path, size_i in self.path_manager.walk(src_i):
                    dst = os.path.join(tasks['dst'], relpath, filename)
                    task_tupe_list.append((file_path, dst, size_i))
        self.transfer_task.emit({'tasks':task_tupe_list, 'task_type':type_t, 'host':host, host_type:host_type})


    def _local_transfer(self, src:str, dst:str):
        return
        bar = self.up.download_progress_bar
        if os.path.isfile(src):
            size_f = os.path.getsize(src)
            asyncio.run(self.copy_directory([(src, dst, size_f)], bar))
        elif os.path.isdir(src):
            tasks_f = self.src_dst_parsing(src, dst, 'local')
            size_f = sum([i[2] for i in tasks_f])
            asyncio.run(self.copy_directory(tasks_f, bar))
        else:
            return

    def _remote_transfer(self, src:str, dst:str, type_f:Literal['put', 'get']):
        bar = self.up.download_progress_bar
        if type_f == "put":
            tasks = self.src_dst_parsing(src, dst, 'local', 'remote')
            size_a = sum([i[2] for i in tasks])
            asyncio.run(self.transfer_multiple_files(tasks, type_f))
        else:
            tasks = self.src_dst_parsing(src, dst, 'remote', 'local')
            size_a = sum([i[2] for i in tasks])
            asyncio.run(self.transfer_multiple_files(tasks, type_f))

    def src_dst_parsing(self, src:str, dst:str, src_type:Literal['local', 'remote'], dst_type:Literal['local', 'remote'])->list:
        copy_paths = []  
        if src_type == 'local':
            for dirpath, dirnames, filenames in os.walk(src):
                relative_path = os.path.relpath(dirpath, src)
                target_dir = os.path.join(dst, relative_path)  
                if dst_type == 'local':
                    if not os.path.exists(target_dir):
                        os.makedirs(target_dir)
                else:
                    try:
                        self.remote_server.mkdir(target_dir)
                    except Exception as e:
                        pass
                for filename in filenames:
                    src_file = os.path.join(dirpath, filename)  
                    dst_file = os.path.join(target_dir, filename)  
                    file_size = os.path.getsize(src_file)
                    copy_paths.append((src_file, dst_file, file_size))
        else:
            walk_out = self.remote_server.walk(src)
            if not walk_out:
                return []
            for relpath, type, size_f in walk_out:
                if type == 'directory':
                    target_dir = os.path.join(dst, relpath)
                    os.makedirs(target_dir, exist_ok=True)
                else:
                    src_file = os.path.join(src, relpath)
                    dst_file = os.path.join(dst, os.path.basename(src), relpath)
                    copy_paths.append((src_file, dst_file, size_f))
        return copy_paths
     
    async def copy_directory(self, task_i:tuple, bar:QProgressBar):
        tasks = []  
        for src_i, dst_i, size_i in task_i:
            chunck_size = self.cal_chunck_size(size_i, hosttype='local')
            # tasks.append(copy_file_chunk(src_i, dst_i, chunck_size, bar))
        await asyncio.gather(*tasks) 
    
    def progress_handler(self, current, total):
        print(f"上传进度：{current}/{total} bytes ({(current / total) * 100:.2f}%)")
    
    async def transfer_single_file(self, src, dst, size_f, sftp, type_f:Literal['get', 'put']):
        block_size = self.cal_chunck_size(size_f)
        if type_f == 'get':
            await sftp.get(src, dst, progress_handler=self.progress_handler, block_size= block_size)
        else:
            await sftp.put(src, dst, progress_handler=self.progress_handler, block_size= block_size)

    async def transfer_multiple_files(self, tasks:List[tuple[str, str]], type_f:Literal['get', 'put']):
        host_d = self.remote_server.host
        try:
            async with asyncssh.connect(host_d['HostName'], 
                                        username=host_d.get('User', os.getlogin()), 
                                        password=host_d.get(('Password', '')),
                                        port=int(self.host.get('port', 22))) as conn:
                async with conn.start_sftp_client() as sftp:
                    tasks = []  
                    for src, dst, size_f in tasks:
                        tasks.append(self.transfer_single_file(src, dst, sftp, type_f))
                    await asyncio.gather(*tasks)
                    return True
        except Exception as e:
            print(f"文件传输失败: {e}")
            return False

