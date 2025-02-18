import os
import sys
from toolbox import *
from Scripts.manager.paths_transfer import *
from PySide2.QtWidgets import QListWidget, QMainWindow, QWidget,QListWidgetItem,QPushButton, QHBoxLayout, QVBoxLayout, QLabel
from PySide2.QtGui import QFontMetrics, QIcon
from PySide2.QtCore import QSize, Qt
from .ui.custom_widget import *
from functools import partial
import shutil
import pandas
import pathlib
import aiofiles
import asyncio
import asyncssh
from typing import List, Literal, Union, OrderedDict

async def copy_file_chunk(src:str, dst:str, chunk_size:int, bar:QProgressBar):
    async with aiofiles.open(src, 'rb') as fsrc, aiofiles.open(dst, 'wb') as fdst:
        while True:
            chunk = await fsrc.read(chunk_size)
            if not chunk:
                break  
            await fdst.write(chunk)
            # update progress bar here 

class Associate:
    def __init__(self, nums:int, 
                 program_info_df:Dict[str, pandas.DataFrame],
                 path_manager:PathManager,):
        self.num = nums
        self.df = program_info_df
        self._load()
        self.pathid:PathManager = path_manager
    
    def _load(self):
        self.names = []
        self.ch_names = []
        self.exe_path = []
        self.groups = []
        for group, df_i in self.df.items():
            self.names.extend(df_i['Name'].to_list())
            self.ch_names.extend(df_i['Chinese Name'].to_list())
            self.exe_path.extend(df_i['EXE Path'].to_list())
            self.groups.extend([group]*len(df_i))
    
    # To Associate subdirectory of certain path
    def ass_path(self, prompt_f):
        if not prompt_f:
            return [], []
        prompt_f_s = self.pathid.check(prompt_f,)
        if prompt_f_s is None:
            pass
        elif stat.S_ISDIR(prompt_f_s.st_mode):
            return self.pathid.listdir(prompt_f)
        else:
            return [], []
        dir_n, base_n = os.path.split(prompt_f)
        dir_n_s = self.pathid.check(dir_n)
        if dir_n_s is None:
            return [], []
        if stat.S_ISDIR(dir_n_s.st_mode):
            names_l, stat_l = self.pathid.listdir(dir_n)
        else:
            return [], []
        names_l_t = []
        for name_i, stat_i in zip(names_l, stat_l):
            if base_n.lower() in name_i.lower():
                base_index = (name_i.lower()).index(base_n.lower())
                names_l_t.append((name_i, stat_i, base_index))
        names_l_1 = sorted(names_l_t, key=lambda x: x[2])
        names_t = [i[0] for i in names_l_1]
        type_t = [i[1] for i in names_l_1]
        return names_t, type_t

    # To associate a programme name of prompt
    def ass_name(self, prompt_f)->Tuple[List[str], List[Literal['app']]]:
        if not prompt_f:
            return [], []
        output_name = sorted([name_i for name_i in self.names if prompt_f.lower() in name_i.lower()], key=lambda s: (s.lower().index(prompt_f.lower()))/len(s))
        output_chname = sorted([ch_name_i for ch_name_i in self.ch_names if prompt_f.lower() in ch_name_i.lower()], key=lambda s: (s.lower().index(prompt_f.lower()))/len(s))
        output_chname_t = [i for i in output_chname if self.names[self.ch_names.index(i)] not in output_name]
        names_t = rm_dp_list_elem(output_name+output_chname_t, reverse=False)[0:self.num]
        return names_t, ['app']*len(names_t)
    
    # To associate programmes with multiple prompts
    def multi_pro_name(self, prompt_list_f):
        output_0 = list_overlap([self.name(prompt_if)[0] for prompt_if in prompt_list_f])
        output_1 = [self.names[(self.ch_names).index(ch_name_i)] for ch_name_i in list_overlap([self.name(prompt_if)[1] for prompt_if in prompt_list_f])]
        out_t = (output_0+output_1)[0:self.num]
        return out_t, ['app']*len(out_t)
    
    def ass_get(self, prompt:str):
        if is_path(prompt):
            return self.ass_path(prompt)
        else:
            if ";" in prompt:
                return self.multi_pro_name(prompt.split(';'))
            return self.ass_name(prompt)
    
    def fill(self, prompt:str)->Tuple[List[str], List[os.stat_result]]:
        if is_path(prompt):
            return self.fill_path(prompt)
        else:
            return self.fill_name(prompt)
        
    # Automatically complete PATH
    def fill_path(self, prompt_f:str)->Union[None, str]:
        # if prompt is a exsisting path
        name_l, stat_l = self.ass_path(prompt_f)
        if not name_l:
            return None
        path_check = self.pathid.check(prompt_f)
        if path_check is None:
            pass
        elif stat.S_ISDIR(path_check.st_mode):
            if len(name_l) == 1:
                return os.path.join(prompt_f, name_l[0])
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
    def fill_name(self, prompt_f:str) -> Union[None, str]:
        output_0 = [name_i for name_i in self.names if name_i.startswith(prompt_f)]
        output_1 = [name_i for name_i in self.names if name_i.lower().startswith(prompt_f.lower())]
        output_2 = [ch_name_i for ch_name_i in self.ch_names if ch_name_i.startswith(prompt_f)]
        if len(output_0) == 1:
            return output_0[0]
        elif len(output_1+output_1) == 1:
            return output_1[0]
        elif len(output_2) == 1:
            return self.names[self.ch_names.index(output_2[0])]

class BasicAS(QListWidget, QObject):
    def __init__(self, config:Config_Manager, parent:Union[QMainWindow, QWidget],manager:LauncherPathManager):
        super().__init__(parent)
        self.up = parent
        self.name = "associate_list"
        self.config = config.deepcopy()
        self.setAcceptDrops(True)  # 接受放置事件
        self.setDragEnabled(True)  # 启用拖动事件
        self.config.group_chose("Launcher", self.name)
        self.launcher_manager = manager
        self._loadconfig(self.config)
        # UIUpdater.set(self.config, self._loadconfig, type_f='config')
        self._load()
        
    def focusNextPrevChild(self, next):
        return True
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():  # 检查是否有文件 URL
            event.acceptProposedAction()  # 接受拖入
        else:
            super().dragEnterEvent(event)
    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)
    def dropEvent(self, event: QDropEvent):
        mime_data = event.mimeData()
        if mime_data.hasUrls():  # 如果拖放的内容是文件
            urls = mime_data.urls()
            paths = [url.toLocalFile() for url in urls]  # 获取文件路径
            self._upload(paths)
            event.acceptProposedAction()  # 接受拖放
        else:
            super().dropEvent(event)
    
    @abstractmethod
    def _upload(self, src:str):
        pass
    
    def _loadconfig(self, config:Config_Manager):
        # dynamic load
        pre = ['Launcher', self.name]
        self.num = config[atuple(pre+['max_exe_num'])]
        self.max_num = config[atuple(pre+['max_dir_num'])]
        self.max_length = config[atuple(pre+['max_length'])]

        pre = ['Launcher', self.name, 'path']
        self.download_dir = config[atuple(pre+['download_save_dir'])]
        self.filelog_default_path = config[atuple(pre+['filelog_default_path'])]
        self.exe_icon_getter = config[atuple(pre+['exe_icon_getter'])]
        self.file_icon_getter = config[atuple(pre+['file_icon_getter'])]
        
    def _load(self):
        # static load
        self.pre = atuple('Launcher', self.name)
        self.button_config = atuple('Launcher', self.name,'style','button')
        self.label_config = atuple('Launcher', self.name, 'style', 'label')
        self.main_config = atuple('Launcher', self.name, 'style', 'main')
        self.item_config = atuple('Launcher', self.name, 'style', 'item')
        self.scroll_bar_config = atuple('Launcher', self.name, 'style', 'scroll_bar')
        self.font_a = atuple('Launcher', self.name, 'font', 'main')

        # size
        pre = ['Launcher', self.name, 'Size']
        self.item_height = atuple(pre+['item_height'])
        self.button_height = atuple(pre+['button_height'])
        self.extra_width = atuple(pre+['extra_width'])
        self.max_width = atuple(pre+['max_width'])
        self.min_width = atuple(pre+['min_width'])

        self.launcher_df = self.launcher_manager.df
        self.path_manager:PathManager = self.up.path_manager
        self.ass = Associate(self.max_num, self.launcher_df, self.path_manager)
        self.config.group_chose(mode="Launcher", widget=self.name, obj=None)

        self._load_default_icons()

    def _load_default_icons(self) -> dict:
        self.file_icon_folder = self.config.get('file_icon_folder', mode="Launcher", widget=self.name, obj="path")
        
        self.file_icon_d = {}
        for name_i in os.listdir(self.file_icon_folder):
            name, ext = os.path.splitext(name_i)
            self.file_icon_d[name] = QIcon(os.path.join(self.file_icon_folder, name_i))
        
        pre = ["Launcher", self.name, "path"]
        default_folder_icon = atuple(pre+['default_folder_icon'])
        default_file_icon = atuple(pre+['default_file_icon'])
        default_back_icon = atuple(pre+['default_back_icon'])
        self.default_icon_d = {'dir':default_folder_icon, 'file':default_file_icon, 'back':default_back_icon}

    def cal_chunck_size(self, size_f:int, hosttype:Literal['local', 'remote'])->int:
        if hosttype == 'local':
            return min(max(self.local_min_chunck, size_f//48), self.local_max_chunck)
        else:
            return min(max(self.remote_min_chunck, size_f//48), self.remote_max_chunck)
    
    def _geticon(self, name:str, sign:Literal['name', "path"], stat_f:os.stat_result)->QIcon:
        match sign:
            case "name":
                return self.launcher_manager.get_icon(name)
            case _:
                if isinstance(stat_f, str) and stat_f == 'back':
                    return self.default_icon_d.get('back', self.default_icon_d.get('dir',''))
                elif stat.S_ISDIR(stat_f.st_mode):
                    return self.default_icon_d['dir']
                else:
                    for key, value in self.file_icon_d.items():
                        if name.endswith(f'.{key}'):
                            return value
                    return self.default_icon_d['file']
                  
    def _changeicon(self, index_i):
        app_name = self.label_l[index_i].text
        options = QFileDialog.Options()
        file_filter = "SVG Files (*.svg);;ICO Files (*.ico);;PNG Files (*.png)"
        file_path, _ = QFileDialog.getOpenFileName(self, f"Choose '{app_name}' icon", "", file_filter, options=options)

        if not file_path:
            return
        file_type = os.path.splitext(file_path)[-1]
        dst = os.path.join(os.path.basename(self.ass_icon_list[0]), app_name+file_type)
        path = glob(os.path.join(os.path.basename(self.ass_icon_list[0]), app_name+".*"))
        for path_i in path:
            os.remove(path_i)
        shutil.copy2(file_path, dst)
        self.button_l[index_i].setIcon(QIcon(dst))
    
    def _get_prompt(self)->str:
        return self.up.input_box.text()
class UIAS(BasicAS):
    def __init__(self, config:Config_Manager, parent:Union[QMainWindow, QWidget],manager:LauncherPathManager):  
        super().__init__(config, parent, manager)
        UIUpdater.set(self.font_a, self.setFont, 'font')
        UIUpdater.set(alist(self.main_config, self.item_config, self.scroll_bar_config), self.customStyle)
        self._inititems()
        self.setFocusPolicy(Qt.NoFocus)

    def customStyle(self, main_config:dict, item_config:dict, bar_config:dict):
        # dynamic style set
        main_bg = main_config.get('background', 'transparent')
        main_border = main_config.get('border', 'none')
        main_radius = main_config.get('border_radius', 20)


        item_bg_colors = enlarge_list(item_config.get('background_colors', ['#F7F7F7']),3)
        item_border = item_config.get('border', 'none')
        item_border_radius = item_config.get('border_radius', 10)
        item_padding = item_config.get('padding', [10,5,5,5])
        height_f = item_config.get('height', 50)

        bar_handle_colors = enlarge_list(bar_config.get('background_colors', ['#32CC99']),3)
        orbit_color = bar_config.get('orbit_color', '#F7F7F7')
        bar_radius = bar_config.get('border_radius', 7)
        bar_width = bar_config.get('width', 15)
        bar_height = bar_config.get('height', 30)

        self.style_d = {
            'QListWidget': {
                'border': main_border,
            },
            'QListView': {
                'background': main_bg,
                'border': main_border,
                'border-radius': main_radius,
            },
            'QListView::item': {
                'border': item_border,
                "padding": f"{item_padding[2]}px {item_padding[1]}px {item_padding[3]}px {item_padding[0]}px",
                'background-color': item_bg_colors[0],
                'border-radius': f"{item_border_radius}px",
                'height': f"{height_f}px",
            },
            'QListView::item:hover': {
                'background-color': item_bg_colors[1],
            },
            'QListView::item:selected': {
                'background-color': item_bg_colors[2],
            },
            'QListWidget QScrollBar:vertical': {
                'background': orbit_color,
                'width': f"{bar_width}px",
                'margin': '3px',
                'border-radius': f"{bar_radius}px",
            },
            'QListWidget QScrollBar::handle': {
                'background': bar_handle_colors[0],
                'min-height': f"{bar_height}px",
                'border-radius': f"{bar_radius}px",
            },
            'QListWidget QScrollBar::handle::hover': {
                'background': bar_handle_colors[1],
            },
            'QListWidget QScrollBar::handle::selected': {
                'background': bar_handle_colors[2],
            },
            "QListWidget QScrollBar::add-line,QListWidget QScrollBar::sub-line":{
                'background': 'none',
                'height': '0px',
            },
            "QListWidget QScrollBar::add-page,QListWidget QScrollBar::sub-page":{
                'background': 'none',

            }
        }
        self.style_sheet = style_make(self.style_d)
        self.setStyleSheet(self.style_sheet)
        self.setSpacing(1)  # 设置 item 之间的间距为 10 像素
        self.setAttribute(Qt.WA_TranslucentBackground) 

    def _init_signle_item(self, button_size:atuple, index_f:int, label_font:atuple=None):
        label_font = self.font_a if label_font is None else label_font
        item_i = QListWidgetItem()
        item_i.setData(Qt.UserRole, int(index_f))
        button_i = YohoPushButton(icon_i=self.default_icon_d['dir'], style_config=self.button_config, size_f=button_size)
        label_i = AutoLabel(text="Default", font=label_font, style_config=self.label_config)
        label_i.setAlignment(Qt.AlignLeft)
        UIUpdater.set(button_size, label_i.setFixedHeight)
        layout_i = amlayoutH(align_v='l')
        layout_i.setContentsMargins(0,0,0,0)
        layout_i.addWidget(button_i)
        layout_i.addWidget(label_i)
        widget_i = QWidget()
        widget_i.setLayout(layout_i)
        self.addItem(item_i)
        self.setItemWidget(item_i, widget_i)
        return item_i, button_i, label_i

    def _inititems(self):
        self.button_l = []
        self.label_l = []
        self.item_l = []
        for i in range(self.max_num):
            item_i, button_i, label_i = self._init_signle_item(self.button_height, i)
            item_i.setHidden(True)
            self.item_l.append(item_i)
            self.button_l.append(button_i)
            self.label_l.append(label_i)
            button_i.clicked.connect(partial(self._changeicon, index_i=i))

    def _get_item_text(self, item:QListWidgetItem)->str:
        index_f = item.data(Qt.UserRole)
        return self.label_l[index_f].text()
    
    def _getbutton(self, item:QListWidgetItem) -> QPushButton:
        index_f = item.data(Qt.UserRole)
        return self.button_l[index_f]
class AssociateList(UIAS):
    transfer_task = Signal(dict)
    def __init__(self, config:Config_Manager, parent:Union[QMainWindow, QWidget],manager:LauncherPathManager):  
        super().__init__(config, parent, manager)
        self.raise_()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.right_click)
        self.itemClicked.connect(self.left_click)
    
    def update_associated_words(self, text:str):
        if is_path(text):
            sign_n = 'path'
            matching_words, type_l = self.ass.ass_path(text)
            matching_words.insert(0, '..')
            type_l.insert(0, 'back')
        else:
            sign_n = 'name'
            matching_words, type_l = self.ass.ass_name(text)
        num_n = len(self.item_l)
        match_num = len(matching_words)
        if  num_n< match_num:
            for iti in range(match_num-num_n):
                item_i, button_i, label_i = self._init_signle_item(self.button_height, index_f=len(self.item_l))
                self.item_l.append(item_i)
                self.button_l.append(button_i)
                self.label_l.append(label_i)
        num_t = len(self.item_l)
        for i in range(num_t):
            if i >= len(matching_words):
                self.item_l[i].setHidden(True)
                continue
            self.item_l[i].setHidden(False)
            text_i = matching_words[i]
            icon_i = self._geticon(text_i, sign_n, type_l[i])
            self.label_l[i].setText(text_i)
            self.button_l[i].setIcon(AIcon(icon_i))

        # font_metrics = QFontMetrics(self.font())
        # b_h = self.config[self.button_height]
        # e_w = self.config[self.extra_width]
        # extra_size = b_h + e_w
        # if matching_words:
        #     max_len = max(13, max([len(i) for i in matching_words]))
        #     extra_size = int(e_w*max_len)
        #     width_f = max([font_metrics.boundingRect(' '+word).width() + extra_size for word in matching_words])
        # else:
        #     extra_size = int(self.extra_width*13)
        #     width_f = font_metrics.boundingRect("RemoteDesktop").width() + extra_size
    
    def _tab_complete(self, current_text:str):
        return self.ass.fill(current_text)
    
    def left_click(self, item):
        item_text = self._get_item_text(item)
        prompt_f = self._get_prompt()
        if is_path(prompt_f):
            if not self.path_manager.check(prompt_f):
                prompt_f = os.path.dirname(prompt_f)
            if item_text != '..':
                path_n = os.path.join(prompt_f, item_text)
                if '/' in prompt_f:
                    path_n = path_n.replace('\\', '/')
            else:
                path_n = os.path.dirname(prompt_f)
            self.up.input_box.setText(path_n)
        item.setSelected(False)
    
    def right_click(self, pos):
        prompt_f = self._get_prompt() 
        if not is_path(prompt_f):
            return 
        item = self.itemAt(pos)
        context_menu = QMenu(self)
        down_action = QAction('Downdload', self)
        downdir_action = QAction('Download to DIR', self)
        change_icon_action = QAction("Change Default Icon")
        down_action.triggered.connect(lambda: self._download(item, ask_save_dir=True))
        downdir_action.triggered.connect(lambda: self._download(item, ask_save_dir=False))
        change_icon_action.triggered.connect(lambda: self._cg_default_icon(item))
        context_menu.addAction(down_action)
        context_menu.addAction(downdir_action)
        context_menu.addAction(change_icon_action)
        context_menu.exec_(self.mapToGlobal(pos))

    def _transfer_trigger(self):
        pass

    def _cg_default_icon(self, item):
        pass


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
                                    'host':self.up.HOST, 'host_type':self.path_manager.host_type})
    
    def _download(self, item, ask_save_dir:bool):
        if ask_save_dir:
            dir_path = QFileDialog.getExistingDirectory(self, "Choose a directory to save the file", self.filelog_default_path)
            if not dir_path:
                return
        else:
            dir_path = self.download_dir
        item_text = self._get_item_text(item)
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
            tasks.append(copy_file_chunk(src_i, dst_i, chunck_size, bar))
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

class SwitchButton2(QComboBox):
    def __init__(self, parent: QMainWindow, config:Config_Manager) -> None:
        super().__init__(parent)
        self.up = parent
        self.name = "switch_button"
        self.config = config.deepcopy()
        self.config.group_chose(mode="MainWindow", widget=self.name)
        self.mode_list = self.config.get("mode_list", mode="Common", widget=None, obj=None)
        self.currentIndexChanged.connect(self._index_change)  
        self.font_f = atuple('MainWindow', self.name, 'font')
        self.height_f = atuple('MainWindow', self.name, 'Size', 'height')
        self.style_config = atuple('MainWindow', self.name, 'style')
        UIUpdater.set(self.style_config, self.customStyle)
        UIUpdater.set(alist(self.font_f, self.height_f), self._loadconfig, 
                      alist('font', None))
        self._initUI()

    def customStyle(self, config:dict):
        box_config:dict = config.get('box', {})
        menu_config:dict = config.get('menu', {})
        b_bg = box_config.get('background', 'rgba(255, 255, 255, 50)')
        b_font_color = box_config.get('font_color', '#F7F7F7')
        b_border = box_config.get('border', 'none')
        b_radius = box_config.get('border_radius', 10)
        b_padding = box_config.get('padding', [5,0,5,5])

        m_font_color = menu_config.get('font_color', '#F7F7F7')
        m_bg = menu_config.get('background', '#9DCDC8FF')
        m_hover_bg = menu_config.get('line_hover_background', '#4CC1B5')
        m_hover_font_color = menu_config.get('hover_font_color', 'black')

        self.style_d = {
            "QComboBox": {
                "background": b_bg,
                "color": b_font_color,
                "border": b_border,
                "border-radius": f"{b_radius}px",
                "padding": f"{b_padding[2]}px {b_padding[1]}px {b_padding[3]}px {b_padding[0]}px"
            },
            "QComboBox::drop-down": {
                "border": "none"
            },
            "QComboBox QAbstractItemView": {
                "padding": f"{b_padding[2]}px {b_padding[1]}px {b_padding[3]}px {b_padding[0]}px",
                'border': 'none',
                "background-color": m_bg,
                "color": m_font_color,
                "selection-background-color": m_hover_bg,
                "selection-color": m_hover_font_color
            },
            "QComboBox QAbstractItemView::item": {
                            "border": "none",
                            "border-style": "none",
                            "outline": "none",
                            "box-shadow": "none"
                        },
            "QComboBox QAbstractItemView::item:hover": {
                "border": "none",
                "border-style": "none",
                "outline": "none",
                "box-shadow": "none",
                "background-color": m_hover_bg,
                "color": m_hover_font_color
            },
            "QComboBox QAbstractItemView::item:selected": {
                "border": "none", 
                "border-style": "none",
                "outline": "none",
                "box-shadow": "none",
                "background-color": m_hover_bg,
                "color": m_hover_font_color
            }
        }
        self.style_sheet = style_make(self.style_d)
        self.setStyleSheet(self.style_sheet)

    def _loadconfig(self, font_f, height_f):
        self.setFixedHeight(height_f)
        self.setFont(font_f)

    def _initUI(self):
        for model_if in self.mode_list:
            self.addItem(model_if)
        self.setCurrentIndex(0)

        font_metrics = QFontMetrics(self.font())
        min_length = font_metrics.boundingRect('Local').width() + 30  
        length_t = font_metrics.boundingRect(self.mode_list[0]).width() + 30
        length_t = max(length_t, min_length)
        self.setFixedWidth(length_t)
    
    def _index_change(self):
        mode_n = self.currentText()
        font_metrics = QFontMetrics(self.font())
        min_length = font_metrics.boundingRect('Local').width() + 30  
        w_f = max(font_metrics.boundingRect(mode_n).width() + 30  ,min_length)  
        self.setFixedWidth(w_f)

class SwitchButton(CustomComboBox):
    def __init__(self, parent: QMainWindow, config:Config_Manager) -> None:
        self.name = "switch_button"
        self._load()
        super().__init__(modes=self.modes, style_d=self.style_d, parent=parent,
                         box_height=self.box_h, item_height=self.item_h,font_f=self.font_f)
            

    def _index_change(self):
        mode_n = self.currentText()
        font_metrics = QFontMetrics(self.font())
        min_length = font_metrics.boundingRect('Local').width() + 30  
        w_f = max(font_metrics.boundingRect(mode_n).width() + 30  ,min_length)  
        self.setFixedWidth(w_f)

    def _load(self):
        self.pre = atuple('MainWindow', self.name)
        self.font_f = atuple('MainWindow', self.name, 'font')
        self.box_h = atuple('MainWindow', self.name, 'Size', 'box_height')
        self.item_h = atuple('MainWindow', self.name, 'Size', 'item_height')
        self.style_d = atuple('MainWindow', self.name, 'style')
        self.modes = self.config[atuple('Common', 'mode_list')]

class PathModeSwitch(QComboBox):
    def __init__(self, parent:QMainWindow, config:Config_Manager) -> None:
        super().__init__(parent)
        self.up = parent
        self.name = "path_mode_switch"
        self.config = config.deepcopy()
        self.config.group_chose(mode="Launcher", widget=self.name, obj=None)
        self.height_f = atuple('Launcher', self.name, 'Size', 'height')
        self.font_f = atuple('Launcher', self.name, 'font', 'main')
        self._load()
        self._initUI()
        UIUpdater.set(alist(self.height_f, self.font_f), self._loadconfig, alist(None, 'font'))
        self.currentIndexChanged.connect(self._index_change)
        self._index_change()
    
    def _loadconfig(self, height_f, font_f):
        self.setFixedHeight(height_f)
        self.setFont(font_f)
    
    def _load(self):
        self.path_manager:PathManager = self.up.path_manager
        self.hostd = self.path_manager.hostd
        self.mode_list = list(self.hostd.keys())
        self.pre = atuple('Launcher', self.name)
    
    def _initUI(self):
        for model_if in self.mode_list:
            self.addItem(model_if)
        self.setCurrentIndex(0)
        font_metrics = QFontMetrics(self.font())
        w_f = font_metrics.boundingRect(self.mode_list[0]).width() + 60  
        self.setFixedWidth(w_f)
        UIUpdater.set(self.pre|atuple('style'), self.customStyle)   
    
    def customStyle(self, config):
        box_config = config.get('box', {})
        menu_config = config.get('menu', {})
        b_bg = box_config.get('normal_background', 'rgba(255, 255, 255, 50)')
        b_font_color = box_config.get('font_color', '#F7F7F7')
        b_border = box_config.get('border', 'none')
        b_radius = box_config.get('border_radius', 10)
        b_padding = box_config.get('padding', [5,0,5,5])

        m_font_color = menu_config.get('font_color', '#F7F7F7')
        m_bg = menu_config.get('background', '#9DCDC8FF')
        m_hover_bg = menu_config.get('line_hover_background', '#4CC1B5')
        m_hover_font_color = menu_config.get('hover_font_color', 'black')
        self.box_style_dict = {
            'QComboBox':{
                'background': b_bg,
                'color': b_font_color,
                'border': b_border,
                'border-radius': f"{b_radius}px",
                "padding": f"{b_padding[2]}px {b_padding[1]}px {b_padding[3]}px {b_padding[0]}px", 
            },
            "QComboBox::drop-down":{
                'border': 'none'
            },
            }
        self.menu_style_dict = {
            'QComboBox QAbstractItemView':{
                'background-color': m_bg,
                'color': m_font_color,
                'selection-background-color': m_hover_bg,
                'selection-color': m_hover_font_color
            }
        }
        self.style_sheet_0 = style_make(self.box_style_dict)
        self.style_sheet_1 = style_make(self.menu_style_dict)
        self.setStyleSheet(self.style_sheet_0+'\n'+self.style_sheet_1)

    def _index_change(self):
        mode_n = self.currentText()
        font_metrics = QFontMetrics(self.font())
        min_length = font_metrics.boundingRect(self.mode_list[0]).width() + 60  
        w_f = max(font_metrics.boundingRect(mode_n).width() + 60  ,min_length)
        self.setFixedWidth(w_f)
    
    def _change_color(self, state_f:Literal['normal', 'error', 'warn']):
        color = self.config[self.pre|atuple('style', 'box', f'{state_f}_color')]
        if not color:
            color = "rgba(255, 255, 255, 50)" 
        self.box_style_dict['QComboBox']['background'] = color
        self.style_sheet_0 = style_make(self.box_style_dict)
        self.setStyleSheet(self.style_sheet_0+'\n'+self.style_sheet_1)

class TopButton(QWidget, QObject):
    button_click = Signal(str)  # Literal['minimum', 'maximum', 'close']
    def __init__(self, parent: QMainWindow, config:Config_Manager) -> None:
        super().__init__(parent)
        self.name = "top_button"
        self.up = parent
        self.config = config.deepcopy()
        self.config.group_chose(mode="MainWindow", widget=self.name)
        self.geom = atuple('MainWindow', self.name, 'Size', 'widget_height')
        UIUpdater.set(self.geom, self.setFixedHeight)
        self.max_state = False
        
    def _initbuttons(self):
        self.pre = atuple('MainWindow', self.name)
        size_i = atuple('MainWindow', self.name, 'Size', 'button_size')
        pre = ['MainWindow', self.name, 'path']
        self.max_path = atuple(pre+['maximum'])
        self.min_path = atuple(pre+['minimum'])
        self.middle_path = atuple(pre+['middle'])
        self.close_path = atuple(pre+['close'])
        self.entry_path = atuple(pre+['entry'])
        style_f = self.pre|atuple('style')

        self.max_button = YohoPushButton(icon_i=self.max_path, style_config=style_f, size_f=size_i)
        self.max_button.clicked.connect(lambda: self._b_click('maximum'))
        self.min_button = YohoPushButton(icon_i=self.min_path, style_config=style_f, size_f=size_i)
        self.min_button.clicked.connect(lambda: self._b_click('minimum'))
        self.close_button = YohoPushButton(icon_i=self.close_path, style_config=style_f, size_f=size_i)
        self.close_button.clicked.connect(lambda: self._b_click('close'))

        self.enty_button = YohoPushButton(icon_i=self.entry_path, style_config=style_f, size_f=size_i)
        self.enty_button.clicked.connect(lambda: self._b_click('entry'))

        return [self.enty_button, self.min_button, self.max_button, self.close_button]

    def _b_click(self, sign:Literal['minimum', 'maximum', 'close', 'entry']):
        self.button_click.emit(sign)

    @Slot(str)
    def _isMax(self, state:bool):
        if state:
            self.max_button.setIcon(self.max_path)
        else:
            self.max_button.setIcon(self.middle_path)

class InputBox(AutoEdit):   
    key_press = Signal(dict)
    def __init__(self, parent:QMainWindow, config:Config_Manager):
        self.up = parent
        self.name = "input_box"
        self.height_f = atuple('Launcher', self.name, 'Size', 'height')
        self.font_f = atuple('Launcher', self.name, 'font', 'main')
        self.style_config = atuple('Launcher', self.name, 'style')
        super().__init__(text='', font=self.font_f, style_d=self.style_config, height=self.height_f)
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
    
class SearchTogleButton(YohoPushButton):
    search_signal=Signal(dict) #{'url':str, 'sign':str}
    def __init__(self, parent, config:Config_Manager):
        self.up = parent
        self.name = "search_togle_button"
        config = config.deepcopy()
        icons = atuple('Launcher', self.name, 'icons')
        urls = atuple('Launcher', self.name, 'urls')
        sign = atuple('Launcher', self.name, 'sign')
        size = atuple('Launcher', self.name, 'Size', 'button_size')
        style_d = atuple('Launcher', self.name, 'style')

        self.url = config[urls][0]
        button_size = atuple('Launcher', self.name, 'Size', 'button_size')
        super().__init__(icon_i=config[icons][0], 
                         style_config=style_d,
                        size_f=button_size)
        UIUpdater.set(alist(icons, urls, sign), self._updateURL, alist())
        self.clicked.connect(self._click)
    
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

class ShortcutButton(QWidget):
    launch_signal = Signal(str)
    def __init__(self, parent: QMainWindow, config:Config_Manager) -> None:
        super().__init__(parent)
        self.ctrl_pressed = False
        self.name = "shortcut_obj"
        self.up = parent
        self.config = config.deepcopy().group_chose(mode="Launcher", widget=self.name)
        self.layout_0 = QVBoxLayout()
        self.setLayout(self.layout_0)
        self._initpara()
        self._initUI()
        self.refresh()
        #self.setFixedSize(*self.config.get(None, widget="Size", obj=self.name)[-2:], )

    def _initpara(self):
        self.manager:ShortcutsPathManager = self.up.shortcut_data
        self.v_num = self.config[atuple('Launcher', 'shortcut_obj', 'vertical_button_num')]
        self.h_num = self.config[atuple('Launcher', 'shortcut_obj', 'horizontal_button_num')]
        self.icon_proportion = atuple('Launcher', 'shortcut_obj', 'Size', 'icon_proportion')
        self.num_exp = self.v_num * self.h_num

        self.df = self.manager.df
        self.num_real = self.df.shape[0]
        self.buttonlabel_list = []
        pre = ['Launcher', self.name]
        self.size_i = atuple(pre+['Size', 'button_r'])

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
                label_i = AutoLabel(text=name, font=self.font_i, style_config=self.button_label_style)
                button_i.clicked.connect(self._launch)
                self.buttonlabel_list.append((button_i, label_i))
                layout_i.addWidget(button_i)
                layout_i.addWidget(label_i)
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

class UIShortcutSetting(QWidget):
    def __init__(self, parent:QMainWindow, config:Config_Manager):
        super().__init__()
        self.up = parent
        self.name = 'shortcut_obj'
        self.config = config.deepcopy().group_chose(mode="Launcher", widget=self.name)
        self._initpara()
        self._windowset()
        self._initUI()
    
    def _windowset(self):
        self.drag_position = None
        self.edge_drag = None
        self.edge_threshold = 20
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("Shortcut Setting")
        UIUpdater.set(atuple('Launcher','shortcut_obj','path','taskbar_icon'), self.setWindowIcon,type_f='icon')
        # For mouse control
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.isNearEdge(event.pos()):
                self.edge_drag = event.pos()
                self.original_geometry = self.geometry()
                event.accept()
            else:
                # x, y, w, h = self.get_geometry(self)
                # if event.y() >y+h or event.x() > x+w:
                if True:
                    self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                    event.accept()
        else:
            super().mousePressEvent(event)
    def mouseMoveEvent(self, event):
        # if self.edge_drag:
        #     self.resizeWindow(event.pos())
        if self.drag_position and event.buttons() == Qt.LeftButton:
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
            pos.x() > w - self.edge_threshold or
            pos.y() > h - self.edge_threshold
        )
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
    @staticmethod
    def get_geometry(window_f):
        geom_f = window_f.geometry()
        return[geom_f.x(), geom_f.y(), geom_f.width(), geom_f.height()]
    
    def _set_w(self, obj, size:List[Union[int,bool]]):
        if size[0]:
            obj.setMinimumWidth(size[0])
        if size[1]:
            obj.setMaximumWidth(size[1])
    
    def _initpara(self):
        # init other para
        self.title_i = atuple('Launcher', self.name, 'name', 'window_title')
        self.v_num = self.config.get('vertical_button_num', mode="Launcher", obj=None)
        self.h_num = self.config.get('horizontal_button_num', mode="Launcher", obj=None)
        self.num_t = int(self.v_num*self.h_num)
        self.objs = []
        self.option_button = []
        self.line_height = atuple('Launcher', self.name, 'Size', 'line_height')
        self.colname_margin = atuple('Launcher', self.name, 'Size', 'colname_margin')
        pre = ['Launcher', self.name, 'font']
        self.window_title_font = atuple(pre+['window_title'])
        self.coordinate_label_font = atuple(pre+['coordinate_label'])
        self.app_name_label_font = atuple(pre+['app_name_label'])
        self.exe_lineedit_font = atuple(pre+['exe_lineedit'])
        self.option_button_font = atuple(pre+['option_button'])
        self.title_style = atuple('Launcher', self.name, 'style', 'setting_title')
        self.col_style = atuple('Launcher', self.name, 'style', 'column_label')
        self.cor_style = atuple('Launcher', self.name, 'style', 'coordinate_label')
        self.icon_button_style = atuple('Launcher', self.name, 'style', 'icon_button')
        self.app_name_edit_style = atuple('Launcher', self.name, 'style', 'app_name_edit')
        self.exe_lineedit_style = atuple('Launcher', self.name, 'style', 'exe_lineedit')
        self.tooltip_style = atuple('Launcher', self.name, 'style', 'exe_tip')
        self.search_button_style = atuple('Launcher', self.name, 'style', 'folder_search_button')
        # init path
        pre = ['Launcher', self.name, 'path']
        self.manager:ShortcutsPathManager = self.up.shortcut_data
        self.df = self.manager.df
        self.taskbar_icon = atuple(pre+['taskbar_icon'])
        self.button_icons = atuple(pre+['button_icons'])
        self.default_app_icon = atuple(pre+['default_app_icon'])
        self.default_folder_icon = atuple(pre+['default_folder_icon'])

        self.col_coordinate_icon = atuple(pre+['col_coordinate_icon'])
        self.col_name_icon = atuple(pre+['col_name_icon'])
        self.col_icon_icon = atuple(pre+['col_icon_icon'])
        self.col_path_icon = atuple(pre+['col_path_icon'])
        self.col_search_icon = atuple(pre+['col_search_icon'])

        # size para
        pre = ['Launcher', self.name, 'Size']
        self.title_height = atuple(pre+['title_height'])
        self.col_label_height = atuple(pre+['col_label_height'])
        for i in range(5):
            setattr(self, f"colwidth_{i}", atuple(pre+[f'colwidth_{i}']))
    
    def showWin(self):
        up_geom = self.up.geometry()
        x, y, w, h = up_geom.x(), up_geom.y(), up_geom.width(), up_geom.height()
        w_1, h_1 = self.config[atuple('Launcher', self.name, 'Size', 'setting_window_size')]
        x_t = x + w//2 - w_1//2
        y_t = y + h//2 - h_1//2
        self.setGeometry(x_t, y_t, w_1, h_1)
        self.show()
        self.raise_()
    
    def _initUI(self):
        ## UI set
        self.layout_0 = QVBoxLayout()
        self._init_title()
        self._init_colname()
        self._init_obj()
        self._init_action_button()
        self.setLayout(self.layout_0)

    def _init_title(self):
        title_label = AutoLabel(text=self.title_i, font=self.window_title_font, style_config=self.title_style, height=self.title_height)
        title_label.setAlignment(Qt.AlignCenter)
        self.layout_0.addWidget(title_label)
    
    def _init_colname(self):
        self.layout_col = QHBoxLayout()
        UIUpdater.set(self.colname_margin,self.layout_col.setContentsMargins,'margin')
        self.config.group_chose(obj="name")

        col_names_size = {'coordinate':self.colwidth_0, 
                          'name':self.colwidth_1, 
                          'icon':self.colwidth_2, 
                          'path':999, 
                          'search':self.colwidth_4}
        
        for name_i, size_i in col_names_size.items():
            icon_f = getattr(self, f"col_{name_i}_icon")
            if name_i != 'path':
                col_label = AutoLabel(text='', font=self.app_name_label_font, style_config=self.col_style, 
                                      icon_f=icon_f,height=self.col_label_height, width=size_i)
            else:
                col_label = AutoLabel(text='', font=self.app_name_label_font, style_config=self.col_style,
                                      icon_f=icon_f,height=self.col_label_height)
            # self._set_w(col_label, size_i)
            col_label.setAlignment(Qt.AlignCenter)
            self.layout_col.addWidget(col_label)
        
        self.layout_0.addLayout(self.layout_col)
    
    def _get_obj(self, index:int):
        if index < self.df.shape[0]:
            name_if = self.df.iloc[index, 0]
            icon_if = self.manager.geticon(name_if)
            exe_f = self.df.iloc[index, 2]
        else:
            name_if = ''
            icon_if = self.default_app_icon
            exe_f = ''
        output = []
        # coordinate define
        coordinate_name = f"({(index+1)%self.h_num},{(index+1)//self.h_num+1})"
        
        cor_label = AutoLabel(text=coordinate_name, font=self.coordinate_label_font,style_config=self.cor_style, 
                              width=self.colwidth_0, height=self.line_height)
        output.append(cor_label)

        icon_button = YohoPushButton(icon_i=icon_if, style_config=self.icon_button_style, size_f=self.line_height)
        icon_button.setProperty('path', '')
        output.append(icon_button)
        
        name_if = name_if if isinstance(name_if, str) else ''
        name_edit =AutoEdit(text=name_if, font=self.app_name_label_font, style_d=self.app_name_edit_style,
                            height=self.line_height, width=self.colwidth_2)
        output.append(name_edit)

        exe_edit = ExePathLine(style_d=self.exe_lineedit_style, height_f=self.line_height, 
                               place_holder=exe_f, font=self.exe_lineedit_font,tooltip_style=self.tooltip_style)
        output.append(exe_edit)
        
        folder_button = YohoPushButton(icon_i=self.default_folder_icon, style_config=self.search_button_style,
                                       size_f=self.line_height)
        output.append(folder_button)
        return output

    def _init_obj(self):
        obj_layout = QVBoxLayout()
        num_t = int(self.v_num*self.h_num)
        for i_f in range(num_t):
            layout_h = QHBoxLayout()
            col_label, icon_button, name_edit,  exe_edit, folder_button = self._get_obj(i_f)
            self.objs.append({"index":i_f, "col_label":col_label, "name_edit":name_edit, 
                              "icon_button":icon_button, "exe_edit":exe_edit, "folder_button":folder_button})
            icon_button.clicked.connect(partial(self._icon_change, index_f=i_f))
            #exe_edit.textChanged.connect(partial(self._check_path_validity, index_f=i_f))
            folder_button.clicked.connect(partial(self._exe_search, index_f=i_f))
            for i in [col_label, icon_button, name_edit, exe_edit, folder_button]:
                layout_h.addWidget(i)
            obj_layout.addLayout(layout_h)

        # Create a scroll area and add the content layout to it
        scroll_content = QWidget()  # Create a widget to contain the layout
        scroll_content.setLayout(obj_layout)
        
        frame = QFrame()  # Create a frame to contain the scroll area
        frame_layout = QVBoxLayout()
        frame_layout.addWidget(scroll_content)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame.setLayout(frame_layout)
        frame.setObjectName("OuterFrame")
        frame.setStyleSheet('''QFrame#OuterFrame {
                            background: transparent;
                            border-radius: 10px;
                            border: 1px solid gray;
                            background-color: transparent;
                        }''')  # Set border to the frame
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(frame)  # Set the frame as the widget of the scroll area
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("background: transparent; border: none;")  # Set background to transparent and no border to the scroll area
        self.layout_0.addWidget(scroll_area)
        
        # Customize scrollbar style
        scroll_bar = scroll_area.verticalScrollBar()
        scroll_bar.setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 20px;
                margin: 5px;
                
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 25);
                min-height: 20px;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical:hover {
                background: #737373;
            }
            QScrollBar::add-line:vertical {
                background: transparent;
                height: 0px;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
            }
            QScrollBar::sub-line:vertical {
                background: transparent;
                height: 0px;
                subcontrol-position: top;
                subcontrol-origin: margin;
            }
            QScrollBar::sub-page:vertical, QScrollBar::add-page:vertical {
            background: transparent; 
            }
        """)

    def _init_action_button(self):
        button_layout = QHBoxLayout()
        self.config.group_chose("Launcher", "shortcut_obj", "color")
        launcher_button = ColorfulButton("Launcher",
                                         [self.config[('launcher0')],
                                         self.config[('launcher1')],
                                         self.config[('launcher2')],],
                                         self.option_button_font, 
                                         self.line_height)
        launcher_button.setProperty('sign', 'launcher')
        launcher_button.clicked.connect(self._confirm_action)
        shortcut_button = ColorfulButton("Shortcut",
                                         [self.config['shortcut0'],
                                         self.config['shortcut1'],
                                         self.config['shortcut2']],
                                         self.option_button_font, 
                                         self.line_height)
        shortcut_button.setProperty('sign', 'shortcut')
        shortcut_button.clicked.connect(self._confirm_action)
        confirm_button = ColorfulButton("Confirm", 
                                        [self.config['confirm0'],
                                        self.config['confirm1'],
                                        self.config['confirm2']],
                                        self.option_button_font, 
                                        self.line_height
                                        )
        confirm_button.setProperty('sign', True)
        confirm_button.clicked.connect(self._confirm_action)

        cancel_button = ColorfulButton("Cancel",
                                       [self.config['cancel0'],
                                       self.config['cancel1'],
                                       self.config['cancel2']],
                                       self.option_button_font,
                                       self.line_height)
        cancel_button.setProperty('sign', False)
        cancel_button.clicked.connect(self._confirm_action)

        self.option_button.extend([launcher_button, shortcut_button, confirm_button, cancel_button])
        button_layout.addWidget(launcher_button)
        button_layout.addWidget(shortcut_button)
        button_layout.addWidget(confirm_button)
        button_layout.addWidget(cancel_button)
        self.layout_0.addLayout(button_layout)
class ShortcutSetting(UIShortcutSetting):
    def __init__(self, parent:QMainWindow, config:Config_Manager):
        super().__init__(parent, config)
        self.up = parent
        self.name = 'shortcut_obj'
        self.config = config.deepcopy().group_chose(mode="Launcher", widget='shortcut_obj')
        self.layout_0 = QVBoxLayout()
    
    def _check_path_validity(self, index_f:int):
        line_edit:QLineEdit = self.objs[index_f]['exe_edit']
        text_f = line_edit.text()
        if os.path.exists(text_f) or (not text_f):
            line_edit.setStyleSheet("border: 1px solid grey; background-color: transparent;")  # 路径不存在，变红
        elif os.path.isabs(text_f):
            line_edit.setStyleSheet("border: 3px solid #F0F411; background-color: transparent;")  # 路径不存在，变红
        else:
            line_edit.setStyleSheet("border: 3px solid #EE1515; background-color: transparent;")  # 路径存在，变黄
    
    def _icon_change(self, index_f:int):
        name = self.objs[index_f]['name_edit'].text()
        options = QFileDialog.Options()
        file_filter = "SVG Files (*.svg);;ICO Files (*.ico)"
        dir_f = ''
        file_path, _ = QFileDialog.getOpenFileName(self, f"Choose '{name}' icon", dir_f, file_filter, options=options)
        if not file_path:
            return
        self.objs[index_f]['icon_button'].setIcon(QIcon(file_path))
        self.objs[index_f]['icon_button'].setProperty('path', file_path)
        return
        _, format_f = os.path.splitext(file_path)
        icon_path_ori = self.df.iloc[index_f, 1]
        icon_dir_ori = os.path.basename(icon_path_ori)
        name = self.objs[index_f]['name_edit'].text()
        dir_f = icon_dir_ori if os.path.exists(icon_dir_ori) else ""
        icon_dir = self.config.get("button_icons_dir", mode="Launcher", widget="shortcut_obj", obj="path")
        dst = os.path.join(icon_dir, name+format_f)
        if os.path.exists(icon_path_ori):
            os.remove(icon_path_ori)
        if os.path.exit(dst):
            os.remove(dst)
        shutil.copy2(file_path, dst)
        self.df.iloc[index_f, 1] = dst
        self.objs[index_f]['icon_button'].setIcon(QIcon(dst))

    def _exe_search(self, index_f:int):
        exe_path_ori = self.df.iloc[index_f, 2]
        exe_dir_ori = os.path.dirname(exe_path_ori)
        name = self.objs[index_f]['name_edit'].text()
        dir_f = exe_dir_ori if os.path.exists(exe_dir_ori) else ""
        options = QFileDialog.Options()
        file_filter = "All Files (*);;Folders"
        file_path, _ = QFileDialog.getOpenFileName(self, f"Choose '{name}' launch file", dir_f, file_filter, options=options)
        if file_path:
            self.objs[index_f]['exe_edit'].setText(path_format(file_path))
    
    def _read_data(self):
        self.df = self.df.reset_index(drop=True)
        for i in range(self.num_t):
            name = self.objs[i]['name_edit'].text()
            exe_path = self.objs[i]['exe_edit'].text()
            icon_button = self.objs[i]['icon_button']
            if not name:
                continue
            if icon_button.property('path'):
                ext = os.path.splitext(icon_button.property('path'))[1]
                dst = os.path.join(self.button_icons, name+ext)
                if os.path.exists(dst):
                    os.remove(dst)
                shutil.copy2(icon_button.property('path'), dst)
                self.df.loc[i, 'Icon_Path'] = dst
            self.df.loc[i, 'EXE_Path'] = exe_path
            self.df.loc[i,'Display_Name'] = name
            
    def _confirm_action(self):
        button_t = self.sender()
        sign_f = button_t.property('sign')
        match sign_f:
            case "launcher":
                launcher_set = self.config.get('settings_xlsx', widget=None, obj='path')
                os.startfile(launcher_set)
                return
            case "shortcut":
                shortcut_set = self.config.get('setting_xlsx', widget='shortcut_obj', obj='path')
                os.startfile(shortcut_set)
                return 
            case False:
                self.close()
                return
            case True:
                pass
            case _:
                warnings.warn(f"ShorcutSetting._confirm_action recive illegal para {sign_f}")
                return
        
        self.hide()
        self._read_data()
        self.manager.save()
        self.up.shortcut_button.refresh()
        self.close()


class Terminal(QTextEdit):
    def __init__(self, config:Config_Manager, parent:QMainWindow):
        super().__init__(parent)
        self.name = 'Terminal'
        self.config=config.deepcopy()
        self.config.group_chose(mode='Terminal', widget=None)
        self._setstyle()
    def _setstyle(self):
        self.setReadOnly(True)
        self.setFont(self.config.get('main', obj="font"))
        
        self.main_style_sheet = f'''
            QTextEdit {{
                color: {self.config.get('text', obj='color')};
                background-color: {self.config.get('background', obj='color')};
                border: 0px solid #1E1F22;
                border-radius: 20px}}
        '''
        self.setStyleSheet(self.main_style_sheet)
        self.bar_style = f'''
        QScrollBar:vertical {{
            background: transparent;
            width: 10px;
            margin: 0px;
        }}

        QScrollBar::handle:vertical {{
            background: {self.config.get('scroll_bar', obj='color')} ;
            min-height: 20px;
            border-radius: 5px;
        }}

        QScrollBar::sub-line:vertical,
        QScrollBar::add-line:vertical,
        QScrollBar::sub-page:vertical,
        QScrollBar::add-page:vertical {{
            background: none;
            }}
        '''
        self.verticalScrollBar().setStyleSheet(self.bar_style)
    
    def add_text(self, text_f:str, color:str):
        pass
    
    def add_command(self, text_f:str):
        pass
    
    def add_error(self, text_f:str):
        pass

class TransferProgress(ProgressBar):
    def __init__(self, parent, max_value, height):
        self.up = parent
        super().__init__(parent, max_value, height)

class ProgressWidget(QWidget):
    def __init__(self, parent, config:Config_Manager, data:dict):
        self.up = parent
        super().__init__()
        self.size_transfered = 0
        self.progress = 0
        self.data = data
        self.total_task = data['total_size']
        self.src = data['src']
        self.dst = data['dst']

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

    def _update(self, size_transfered:int):
        self.size_transfered += size_transfered
        self.progress = self.size_transfered/self.total_task
        self.bar.setValue(self.progress)
        self.progress_label.setText(f"{self.progress:.2f}%")

    def _terminate(self):
        pass

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
   
class ExePathLine(AutoEdit):
    def __init__(self, style_d, tooltip_style, height_f:int, place_holder:str,font:QFont,):
        super().__init__(text='', font=font, style_d=style_d, height=height_f)
        self.setPlaceholderText(place_holder)
        self.place_holder = place_holder

        UIUpdater.set(style_d, self._loadColor)
        UIUpdater.set(tooltip_style, self._customTooltip)
        self.textChanged.connect(self._text_change)
    
    def _loadColor(self, style_d:atuple):
        self.background_color = style_d['background']
        self.warning_color = style_d['background_warning']
        self.error_color = style_d['background_error']

    def _customTooltip(self, tooltip_style:dict):
        self.setToolTip(self.place_holder)
        fm = tooltip_style.get('font_family', 'Consolas')
        size_f = tooltip_style.get('font_pt', 20)
        pd = tooltip_style.get('padding', [10,0,5,5])
        
        self.toolstyle_d = {
            'QToolTip':{
                'background-color': tooltip_style.get('background', '#FFFFFF'),
                'color': tooltip_style.get('color', '#161616'),
                'font': f'{size_f}pt "{fm}"',
                'border': tooltip_style.get('border', 'none'),
                'border-radius': f"{tooltip_style.get('border-radius', 10)}px",
                "padding": f"{pd[2]}px {pd[1]}px {pd[3]}px {pd[0]}px", 
                'opacity': tooltip_style.get('opacity', 100),
        }
        }
        self.tool_style = style_make(self.toolstyle_d)
        style_t = self.style_n + '\n' + self.tool_style
        self.setStyleSheet(style_t)

    def _text_change(self, text):
        self.setToolTip(text)
        if os.path.exists(text) or (not text):
            color_n = self.background_color
        elif os.path.isabs(text):
            color_n = self.warning_color
        else:
            color_n = self.error_color
        self.style_dict['QLineEdit']['background-color'] = color_n
        self.style_n = style_make(self.style_dict)
        style_t = self.style_n + '\n' + self.tool_style
        self.setStyleSheet(style_t)

class NameEdit(AutoEdit):
    def __init__(self, text_f:str,style_d,font:QFont, height:int,
                 ):
        super().__init__(text=text_f, font=font, height=height, style_d=style_d)
        self.style_d = style_d
    
    def _setStlye(self, sign_f:bool=True):
        style_dict = UIUpdater.config[self.style_d]
        if not style_dict:
            style_dict = {}
        if sign_f:
            self.style_dict['QLineEdit']['background-color'] = style_dict.get('background', '#F7F7F7')
        else:
            self.style_dict['QLineEdit']['background-color'] = style_dict.get('background_error', '#FF5733')
        self.style_n = style_make(self.style_dict)
        self.setStyleSheet(self.style_n)

class SheetControl(QTabBar):
    tab_operation = Signal(dict)
    def __init__(self, parent:QWidget, font_f:QFont, style_main:dict, style_menu:dict):
        super().__init__(parent)
        self.up = parent
        self.pre = ['Launcher', 'shortcut_obj', 'path']
        UIUpdater.set(font_f, self.setFont, 'font')
        UIUpdater.set(style_main, self.customStyle)
        self.setMovable(True) 
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)
        self.setElideMode(Qt.ElideNone)
        self.tabMoved.connect(self.move_tab)
    
    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.win_move(0)
        else:
            self.win_move(1)
        event.accept()
    
    def win_move(self, index):
        scroll_buttons = self.findChildren(QToolButton)
        left_button = None
        right_button = None
        for button in scroll_buttons:
            if button.arrowType() == Qt.LeftArrow:
                left_button = button
            elif button.arrowType() == Qt.RightArrow:
                right_button = button
        if index == 0:
            left_button.click()
        else:
            right_button.click()
    
    def customStyle(self, style:dict):
        UIUpdater.set(style.get('main_height',60), self.setFixedHeight)
        bg_colors = style.get('background_colors', ["#F7F7F7", "#FFC300", "#FF5733"])
        font_colors = style.get('font_colors', ["#000000", "#000000", "#000000"])
        padding = style.get('padding', [0, 10, 0, 10])
        close_icon0 = UIUpdater.config[atuple(self.pre+['path', 'tab_close_icon0'])]
        if not close_icon0:
            close_icon0 = ''
        else:
            close_icon0 = close_icon0.replace('\\', '/')
        close_icon1 = UIUpdater.config[atuple(self.pre+['path', 'tab_close_icon1'])]
        if not close_icon1:
            close_icon1 = ''
        else:
            close_icon1 = close_icon1.replace('\\', '/')
        close_icon2 = UIUpdater.config[atuple(self.pre+['path', 'tab_close_icon2'])]
        if not close_icon2:
            close_icon2 = ''
        else:
            close_icon2 = close_icon2.replace('\\', '/')
        self.tab_style_d = {
            "QTabBar": {
                "border": style.get('main_border', "none"),
                "background": style.get('main_background', "transparent"),
                'border-radius': style.get('main_border_radius', 10),
            },
            "QTabBar::tab": {
                "margin-right": f"{style.get('tab_margin_right', 10)}px",
                "padding": f"{padding[2]}px {padding[1]}px {padding[3]}px {padding[0]}px", 
                "border-radius": f"{style.get('tab_border_radius', 10)}px",
                "height": f"{style.get('tab_height', 50)}px",
                "background": bg_colors[0],
                "color": font_colors[0],
                'border': style.get('tab_border', 'none'),
            },
            "QTabBar::tab:selected": {
                "background": bg_colors[2],
                "color": font_colors[2],    
            },
            "QTabBar::tab:hover": {
                "background": bg_colors[1],
                "color": font_colors[1],
            },
            "QTabBar::close-button": {
                "image": f"url({close_icon0});",
                "subcontrol-position": "right",
                "margin": "2px",
            },
            "QTabBar::close-button:hover": {
                "image": f"url({close_icon1});",
            },
            "QTabBar::close-button:pressed": {
                "image": f"url({close_icon2});",
            },
            "QTabBar::scroller": {
                "width": "0px",
                "height": "0px",
                "background-color": "transparent",
            }
        }
        self.sheetcontrol_stylesheet = style_make(self.tab_style_d)
        self.setStyleSheet(self.sheetcontrol_stylesheet)

    def _setMenuStyle(self, menu:QMenu, style:dict):
        padding = style.get('padding', [10,5,5,5])
        self.menu_style_d = {
            "QMenu": {
                "background-color": style.get('background', "#F7F7F7"),
                "border": style.get('border', "none"),
            },
            "QMenu::item": {
                "padding": f"{padding[2]}px {padding[1]}px {padding[3]}px {padding[0]}px",     # top, right, bottom, left
                "background-color": 'transparent',
                "color": style.get('font_color', "#000000"),
            },
            "QMenu::item:selected": {
                "background-color": style.get('background_hover', "#FF5733"),
                "color": style.get('font_color_hover', "#FFFFFF"),
            }
        }
        self.menu_stylesheet = style_make(self.menu_style_d)
        menu.setStyleSheet(self.menu_stylesheet)
    
    def get_texts(self):
        texts = []
        for index in range(self.count()):  
            texts.append(self.tabText(index))  
        return texts
    
    def get_current_text(self):
        index = self.currentIndex()
        return self.tabText(index)
    
    def set_current_tab(self, name:str):
        if name in self.get_texts():
            index = self.get_texts().index(name)
            self.setCurrentIndex(index)

    def open_context_menu(self, position): 
        index = self.tabAt(position)
        if index == -1:
            return
        menu = QMenu()
        self._setMenuStyle(menu, self.config[atuple(self.pre+['style', 'menu'])])
        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")
        action = menu.exec_(self.mapToGlobal(position))
        if action == rename_action:
            self.tab_operation.emit({'action':'rename', 'index':index})
        elif action == delete_action:
            self.tab_operation.emit({'action':'delete', 'index':index})

    def move_tab(self, from_index, to_index):
        self.tab_operation.emit({'action':'move', 'from':from_index, 'to':to_index})

    def _rename(self, index:int, name_n):
        self.setTabText(index, name_n)
    
    def _delete(self, index:int):
        self.removeTab(index)
        
class BaseLauncherSetting(QWidget):
    def __init__(self, config:Config_Manager, parent:QMainWindow, manager:LauncherPathManager):
        super().__init__(parent)
        self.up = parent
        self.manager = manager
        self.config = config.deepcopy()
        self.name = 'LauncherSetting'
        self.config.group_chose(mode='Settings', widget=self.name)
        self._load_var()
        self._layout_load()
        self._process_ori_df()
    
    def _process_ori_df(self):
        self.df:dict[str:pandas.DataFrame] = self.manager.df
        self.df_l = []
        permit_col = ['Name', 'Chinese Name', 'EXE Path']
        for name_i, df_i in self.df.items():
            target_df = df_i.copy(deep=True)
            for col in target_df.columns:
                if col not in permit_col:
                    target_df.drop(col, axis=1, inplace=True)
            target_df.reset_index(drop=True, inplace=True)
            target_df.loc[:,'IconID'] = None
            self.df_l.append([name_i, target_df])
        self.df_n = self.df_l[0][1]

    def _load_var(self):
        self.num = int(self.config.get('ori_line_num', obj=None))
        self.line_num = 0

        pre = ['Settings', self.name, 'path']
        self.tmp_icon_folder = self.config.get('tmp_icon_folder', obj='path')
        self.default_app_icon = atuple('Launcher', 'shortcut_obj', 'path', 'default_button_icon')
        self.searcher_icon = atuple(pre+['searcher_icon'])
        self.add_button_icon = atuple(pre+['add_button_icon'])
        self.tab_delete_icon = atuple(pre+['tab_delete_icon'])
        self.add_sheet_button_icon = atuple(pre+['add_sheet_button_icon'])

        pre = ['Settings', self.name, 'font']
        self.name_font = atuple(pre+['name'])
        self.chname_font = atuple(pre+['chname'])
        self.exe_font = atuple(pre+['exe'])
        self.title_font = atuple(pre+['title'])
        self.number_font = atuple(pre+['number'])
        self.save_button_font = atuple(pre+['save_button'])
        self.discard_button_font = atuple(pre+['discard_button'])
        self.reset_button_font = atuple(pre+['reset_button'])
        self.tab_font = atuple(pre+['tab'])

        pre = ['Settings', self.name, 'Size']
        self.line_height = atuple(pre+['line_height'])
        self.add_button_margin = atuple(pre+['add_button_margin'])
        self.col_margin = atuple(pre+['col_margin'])
        self.nameedit_length = atuple(pre+['nameedit_max_length'])
        self.exeedit_min_length = atuple(pre+['exeedit_min_length'])
        self.bottom_margin = atuple(pre+['bottom_margin'])
        self.tab_height = atuple(pre+['tab_height'])
        self.line_spaing = atuple(pre+['line_spacing'])
        self.layout_spacing = atuple(pre+['layout_spacing'])
        self.frame_thickness = atuple(pre+['frame_thickness'])
        self.min_handle_height = atuple(pre+['min_handle_height'])
        self.numbercol_width = atuple(pre+['numbercol_width'])
        self.number_width = atuple(pre+['number_width'])
        self.tabbar_height = atuple(pre+['tabbar_height'])
        
        pre = ['Settings', self.name, 'style']
        self.icon_button_style = atuple(pre+['icon_button'])
        self.nameedit_style = atuple(pre+['name_edit'])
        self.exeedit_style = atuple(pre+['exe_edit'])
        self.tooltip_style = atuple(pre+['exe_tip'])
        self.folder_button_style = atuple(pre+['folder_search_button'])
        self.add_button_style = atuple(pre+['add_line_button'])
        self.tab_style = atuple(pre+['sheet_control'])
        self.meunu_style = atuple(pre+['menu'])
        self.tab_add_style = atuple(pre+['tab_add_button'])
        self.save_button_style = atuple(pre+['save_button'])
        self.reset_button_style = atuple(pre+['reset_button'])
        self.title_style = atuple(pre+['title'])
        self.frame_style = atuple(pre+['outer_frame'])
        self.scroll_area_style = atuple(pre+['scroll_bar'])
        self.number_style = atuple(pre+['number_label'])

    def _layout_load(self):
        self.layout_0 = amlayoutV(align_h='c', spacing=5)
        UIUpdater.set(self.layout_spacing, self.layout_0.setSpacing)
        self.setLayout(self.layout_0)
        self.objs_l = {}
        self.widget_l = []
        self.tab_index = 0

    def _get_default_df(self, group:str):
        # ['Name', 'Chinese Name', 'Description', 'EXE Path', 'Group']
        data = OrderedDict([['Name', ['']], ['Chinese Name', ['']], ['EXE Path', ['']], ['Group', [group]], ['IconID',[None]]])
        return pandas.DataFrame(data)
class UILauncherSetting(BaseLauncherSetting):
    def __init__(self, config:Config_Manager, parent:QMainWindow, manager:LauncherPathManager):
        super().__init__(config, parent , manager)
        self._initUI()
    
    def _initUI(self):
        self._init_tiles()
        self._init_layout()
        self._init_multi_line()
        self._init_add_line()
        self._init_bottom_control()
        add_obj(self.add_button_lo, parent_f=self.obj_layout)
        self.obj_layout.addStretch()
        add_obj(self.title_layout, self.scroll_area,parent_f=self.layout_0)
        self.layout_0.addLayout(self.bottom_layout)
        self._line_fresh(0)
    
    def _init_layout(self):
        self.obj_layout = amlayoutV()
        UIUpdater.set(self.line_spaing, self.obj_layout.setSpacing)
        # Create a scroll area and add the content layout to it
        self.scroll_content = QWidget()  # Create a widget to contain the layout
        self.scroll_content.setLayout(self.obj_layout)
        self.frame = QFrame()  # Create a frame to contain the scroll area
        self.frame_layout = QVBoxLayout()
        self.frame_layout.addWidget(self.scroll_content)
        self.frame_layout.setContentsMargins(0, 0, 0, 0)
        self.frame.setLayout(self.frame_layout)
        self.frame.setObjectName("OuterFrame")
        UIUpdater.set(self.frame_style, self._frameStyle)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("myScrollArea")
        self.scroll_area.setWidget(self.frame)  # Set the frame as the widget of the scroll area
        self.scroll_area.setWidgetResizable(True)
        UIUpdater.set(self.scroll_area_style,
                      self._scrollAreaStyle,
                      alist())
    
    def _frameStyle(self, frame_style:dict):
        self.frame_style_d = {
            'QFrame#OuterFrame':{
                'background': frame_style.get('background', 'transparent'),
                'border-radius': f"{frame_style.get('border-radius', 10)}px",
                'border': frame_style.get('border', '5px solid gray'),
            }
        }
        self.frame_stylesheet = style_make(self.frame_style_d)
        self.frame.setStyleSheet(self.frame_stylesheet)

    def _scrollAreaStyle(self, scroll_style:dict):
        orbit_color = scroll_style.get('orbit_color', 'transparent')
        background_colors = scroll_style.get('background_colors', ["#F7F7F7", "#FFC300", "#FF5733"])
        border_radius = scroll_style.get('border_radius', 10)
        min_height = scroll_style.get('min_height', 20)
        width = scroll_style.get('width', 20)
        border = scroll_style.get('border', 'none')

        self.scroll_area_style_d = {
            "QScrollArea#myScrollArea": {
                "background": 'transparent',
                "border": 'none',
            },
            "QScrollBar": {
                "border": border,
                "background": orbit_color,
                "width": f"{width}px",
                "margin": "5px",
                "border-radius": f"{border_radius}px",
            },
            "QScrollBar::handle": {
                "background": background_colors[0],
                "min-height": f"{min_height}px",
                "border-radius": f"{border_radius}px",
            },
            "QScrollBar::handle:vertical:hover": {
                "background": background_colors[1],
            },
            "QScrollBar::handle:selected": {
                "background": background_colors[2],
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
        self.scroll_stylesheet = style_make(self.scroll_area_style_d)
        self.scroll_area.setStyleSheet(self.scroll_stylesheet)

    def _init_tiles(self):
        self.title_layout = amlayoutH()
        UIUpdater.set(self.col_margin, self.title_layout.setContentsMargins, 'margin')
        self.titles = ['number_col', 'icon_col', 'name_col', 'chname_col','exe_col', 'searcher']
        width_l = [self.numbercol_width, self.line_height, self.nameedit_length, self.nameedit_length, self.exeedit_min_length, self.line_height]
        for i, title_i in enumerate(self.titles):
            icon_i = atuple('Settings', 'LauncherSetting', 'path', f'{title_i}_icon')
            col_i = AutoLabel(text='', font=self.title_font,icon_f=icon_i, width=width_l[i], style_config=self.title_style)
            if self.titles[i] == 'exe_col':
                col_i.setMinimumWidth(0)
                col_i.setMaximumWidth(99999)
            col_i.setAlignment(Qt.AlignCenter)
            setattr(self, title_i, col_i)
            self.title_layout.addWidget(getattr(self, title_i))

    def _init_single_line(self, index_f:int, df:pandas.DataFrame=None, default:bool=False, insert:bool=False):
        if default is not False:
            icon_i = self.default_app_icon
            name = ''
            chname = ''
            exe_path = ''
        else:
            name = df.iloc[index_f, 0]
            icon_i = self.manager.get_icon(name)
            chname = df.iloc[index_f, 1]
            exe_path = df.iloc[index_f, 3]
            if os.path.isfile(exe_path):
                exe_path = os.path.basename(exe_path)
        index_i = len(self.objs_l.keys())
        
        nummber_w = AutoLabel(font=self.number_font,
                              text=str(index_i),
                              width=self.number_width,
                              height=self.line_height,
                              style_config=self.number_style
                              )

        icon_w = YohoPushButton(icon_i=icon_i, size_f=self.line_height, style_config=self.icon_button_style)
        icon_w.setProperty('index', index_i)
        icon_w.setProperty('icon_path', '')
        icon_w.clicked.connect(lambda: self._change_icon(index_i))
        name_label = NameEdit(text_f=name, style_d=self.nameedit_style, height=self.line_height, font=self.name_font)
        name_label.setProperty('index', index_i)
        name_label.setProperty('type', 'name')
        UIUpdater.set(self.nameedit_length, name_label.setMaximumWidth)
        name_label.textChanged.connect(self.name_edit_change)
        chname_label = NameEdit(text_f=chname, style_d=self.nameedit_style, height=self.line_height, font=self.name_font)
        chname_label.setProperty('index', index_i)
        chname_label.setProperty('type', 'chname')
        chname_label.textChanged.connect(self.name_edit_change)
        exe_edit = ExePathLine(style_d=self.exeedit_style,tooltip_style=self.tooltip_style, height_f=self.line_height, 
                               place_holder=exe_path, font=self.exe_font)
        exe_edit.setProperty('index', index_i)
        UIUpdater.set(self.exeedit_min_length, exe_edit.setMinimumWidth)
        folder_button = YohoPushButton(icon_i=self.searcher_icon, size_f=self.line_height, style_config=self.folder_button_style)
        folder_button.clicked.connect(lambda: self._exe_search(index_f))
        self.objs_l[len(self.objs_l.keys())] = {'number':nummber_w, 'icon':icon_w, 'name':name_label, 'chname':chname_label, 'exe':exe_edit, 'search':folder_button}
        layout_i = amlayoutH()
        layout_i.setMargin(0)
        setattr(self, f'widget_{len(self.objs_l.keys())}', QWidget())
        widget_i = getattr(self, f'widget_{len(self.objs_l.keys())}')
        widget_i.setLayout(layout_i)
        add_obj(nummber_w, icon_w, name_label, chname_label, exe_edit, folder_button, parent_f=layout_i)
        self.widget_l.append(widget_i)
        if insert:
            self.obj_layout.insertWidget(self.obj_layout.count()-2, widget_i)
        else:
            self.obj_layout.addWidget(widget_i)
        #return nummber_w, icon_w, name_label, chname_label, exe_edit, folder_button
    
    def _init_multi_line(self):
        for i in range(self.num):
            self._init_single_line(i, default=True)

    def _init_add_line(self):
        self.add_button = YohoPushButton(icon_i=self.add_button_icon, 
                                         style_config=self.add_button_style,
                                        )
        UIUpdater.set(self.line_height, self.add_button.setFixedHeight)
        self.add_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.add_button.clicked.connect(self._insert_line)
        self.add_button_lo = amlayoutH()
        UIUpdater.set(self.add_button_margin, self.add_button_lo.setContentsMargins, 'margin')
        add_obj(self.add_button, parent_f=self.add_button_lo)
    
    @abstractmethod
    def change_icon(self):
        pass
    @abstractmethod
    def name_edit_change(self):
        pass
    @abstractmethod
    def _change_icon(self):
        pass
    @abstractmethod
    def _exe_search(self):
        pass
class LauncherSetting(UILauncherSetting):
    def __init__(self, config:Config_Manager, parent:QMainWindow, manager:LauncherPathManager):
        super().__init__(config, parent , manager)
    
    def _writein_data(self, index_f:int):
        name_l = []
        chname_l = []
        exe_l = []
        icon_l = []
        for i in range(self.line_num):
            name_i = self.objs_l[i]['name'].text()
            if not name_i or name_i in name_l:
                continue
            chname_i = self.objs_l[i]['chname'].text()
            exe_i = self.objs_l[i]['exe'].text()
            icon_i = self.objs_l[i]['icon'].property('icon_path')
            name_l.append(name_i)
            chname_l.append(chname_i)
            exe_l.append(exe_i)
            icon_l.append(icon_i)
        df_data = [{'Name':name_l[i], 'Chinese Name':chname_l[i], 'EXE Path':exe_l[i], 'IconID':icon_l[i]} for i in range(len(name_l))]
        self.df_l[index_f][1] = pandas.DataFrame(df_data)

    def _line_fresh(self, index_f:int):
        self.line_num = 0
        self.df_n = self.df_l[index_f][1]
        for i in range(self.df_n.shape[0]):
            if i >= self.num:
                self._insert_line()
            self.widget_l[i].setVisible(True)
            self.objs_l[i]['number'].setText(str(i))
            self.objs_l[i]['name'].setText(self.df_n.iloc[i, 0])
            self.objs_l[i]['chname'].setText(self.df_n.iloc[i, 1])
            self.objs_l[i]['exe'].setText(self.df_n.iloc[i, 3])
            icon_c = self.df_n.iloc[i].loc['IconID']
            if icon_c:
                print(icon_c)
                self.objs_l[i]['icon'].setIcon(QIcon(self.df_n.iloc[i, -1]))
            else:
                icon_d = self.manager.get_app_icon(self.df_n.iloc[i, 0], self.df_l[index_f][0])
                if isinstance(icon_d, atuple):
                    icon_d = self.config.get(icon_d,'')
                self.objs_l[i]['icon'].setIcon(AIcon(icon_d))
            self.line_num += 1
        for i in range(len(self.widget_l)):
            if i >= self.df_n.shape[0]:
                self.widget_l[i].setVisible(False)
    
    def _init_bottom_control(self):
        self.bottom_layout = amlayoutH('c', spacing=25)
        self.tab_wdiget = QWidget()
        self.tab_layout = amlayoutH('l', spacing=10)
        self.tab_wdiget.setLayout(self.tab_layout)
        self.tab_bar = SheetControl(parent=self, font_f=self.tab_font, style_main=self.tab_style, style_menu=self.meunu_style)
        
        for name_i in [i[0] for i in self.df_l]:
            self.tab_bar.addTab(name_i)
        
        self.tab_bar.currentChanged.connect(self.change_tab)
        self.tab_bar.setCurrentIndex(0)
        self.b_add_button = YohoPushButton(icon_i=self.add_sheet_button_icon, style_config=self.tab_add_style, size_f=self.tab_height)
        self.b_add_button.clicked.connect(self.add_tab)
        self.tab_layout.addWidget(self.tab_bar)
        add_obj(self.b_add_button, parent_f=self.tab_layout)
        
        self.save_button = YohoPushButton(text_f='Save', font_f=self.save_button_font, style_config=self.save_button_style, size_f=self.line_height)
        self.save_button.clicked.connect(self._save)
        self.reset_button = YohoPushButton(text_f='Reset', font_f=self.reset_button_font, style_config=self.reset_button_style, size_f=self.line_height)
        self.reset_button.clicked.connect(self._reset)
        # self.discard_button = ChangeControl('Discard', self.config.get('discard_button', obj='color'), self.config.get('discard_button', obj='font'), self.line_height)
        # self.discard_button.clicked.connect(self._discard)
        UIUpdater.set(self.bottom_margin, self.bottom_layout.setContentsMargins, 'margin')
        self.bottom_layout.addWidget(self.tab_wdiget)
        self.bottom_layout.addStretch()
        add_obj(self.save_button, self.reset_button, parent_f=self.bottom_layout)
        
    def _insert_line(self):
        page_text = self.tab_bar.get_current_text()
        index_f = [i for i, j in enumerate(self.df_l) if j[0]==page_text]
        if not index_f:
            return
        page_index = index_f[0]
        #self.df_n.loc[len(self.df_n)] = ['', '', '', '', page_text, None]
        if self.line_num >= len(self.widget_l):
            self._init_single_line(self.line_num, default=True, insert=True)
        else:
            self.widget_l[self.line_num].setVisible(True)
            self.objs_l[self.line_num]['number'].setText(str(self.line_num))
            self.objs_l[self.line_num]['name'].setText('')
            self.objs_l[self.line_num]['chname'].setText('')
            self.objs_l[self.line_num]['exe'].setText('')
            self.objs_l[self.line_num]['icon'].setIcon(AIcon(self.config[self.default_app_icon]))
        self.line_num += 1
        self.sroll_down()
    
    def sroll_down(self):
        self.scroll_content.updateGeometry()
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum()+96)

    def add_tab(self, name='new_sheet', refresh:bool=True):
        text_l = self.tab_bar.get_texts()
        for i in range(99):
            name_t = f'{name}_{i}'
            if name_t not in text_l:
                break
        self.tab_bar.addTab(name_t)
        self.df_l.append([name_t, self._get_default_df(name_t)])
        if refresh:
            self.tab_bar.set_current_tab(name_t)
    
    def change_tab(self, index_new:int):
        self._writein_data(self.tab_index)
        self.tab_index = index_new
        self._line_fresh(index_new)

    def rename_tab(self, index):
        current_name = self.tab_bar.tabText(index)
        new_name, ok = QInputDialog.getText(self, "Rename Sheet", "Enter New Name:", text=current_name)
        if ok and new_name.strip():
            if new_name in self.tab_bar.get_texts():
                self.up.tip('Warning', 'Name already exists', {'OK':False}, False)
                return
            self.tab_bar.setTabText(index, new_name)
            self.df_l[index][0] = new_name
    
    def delete_tab(self, index):
        tip_prompt = f'Are you sure to DELETE sheet "{self.tab_bar.tabText(index)}"?'
        out_f = self.up.tip('Warning', tip_prompt, {'Yes':True, 'No':False}, False)
        if out_f:
            self.tab_bar.removeTab(index)
            self.df_l.pop(index)
    
    def sort_tab(self):
        tab_text_l = self.tab_bar.get_texts()
        index_i = self.tab_bar.currentIndex()
        df_l = []
        for i in tab_text_l:
            for j in self.df_l:
                if j[0] == i:
                    df_l.append(j)
        self.df_l = df_l
        self.tab_index = index_i

    def _change_icon(self, index_f:int):
        file_filter = "Images (*.svg *.png *.jpg *.jpeg *.ico)"
        file_path, _ = QFileDialog.getOpenFileName(self, "Select an image", "", file_filter)
        if not file_path:
            return
        icon_i = QIcon(file_path)
        self.objs_l[index_f]['icon'].setIcon(icon_i)
        self.objs_l[index_f]['icon'].setProperty('icon_path', file_path)
        # _, ext = os.path.splitext(file_path)
        # id_l = self.df_n.loc[:,'IconID'].to_list()
        # name = self.objs_l[index_f]['name'].text()
        # id_ls = [i.split('.')[0] for i in id_l if i]
        # if name in id_ls:
        #     for path_i in glob(os.path.join(self.tmp_icon_folder, f'{name}.*')):
        #         os.remove(path_i)
        
        # self.df_n.loc[index_f, 'IconID'] = f'{name}{ext}'
        # dst = os.path.join(self.tmp_icon_folder, f'{name}{ext}')
        # shutil.copy(file_path, dst)
    
    def name_edit_change(self):
        edit_f = self.sender()
        text = edit_f.text()
        # index_f = edit_f.property('index')
        type_f = edit_f.property('type')
        # if type_f == 'name':
        #     self.df_n.iloc[index_f, 0] = text
        # else:
        #     self.df_n.iloc[index_f, 1] = text
        # if type_f == 'name':
        #     names = self.df_n.loc[:,'Name'].to_list()
        # else:
        #     names = self.df_n.loc[:,'Chinese Name'].to_list()
        names = [i['name'].text() for i in self.objs_l.values()]
        if names.count(text) > 1:
            if type_f == 'name':
                edit_f._setStlye(False)
            else:
                pass
        else:
            edit_f._setStlye(True)

    def _exe_search(self, index_f:int):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "",
                                                  "All Files (*);;Python Files (*.py)", options=options)
        if file_name:
            file_name = file_name.replace('/', '\\')
            self.objs_l[index_f]['exe'].setText(file_name)
    
    def _reset(self):
        title_f = 'Warning'
        prompt_f = 'Are you sure to reset pages to last stage?'
        value_d = {'Reset All':2, "Reset This Page":1, 'Cancel':-5}
        out_f = self.up.tip(title_f, prompt_f, value_d, -5)
        page_n = self.tab_bar.get_current_text()
        page_index = self.tab_bar.currentIndex()
        match out_f:
            case 1:
                if page_n not in self.df.keys():
                    self.df_l[page_index][1] = self._get_default_df(page_n)
                else:
                    self.df_l[page_index][1] = self.df[page_n].copy(deep=True)
                    self.df_l[page_index][1].loc[:,'IconID'] = None
                self._line_fresh(page_index)
            case 2:
                self._process_ori_df()
                self._line_fresh(page_index)

    def _save(self):
        title_f = 'Warning'
        prompt_f = 'Are you sure to write in pages to local data?'
        value_d = {'Save All':2, "Save This Page":1, 'Cancel':-5}
        out_f = self.up.tip(title_f, prompt_f, value_d, -5)
        page_n = self.tab_bar.get_current_text()
        page_index = self.tab_bar.currentIndex()
        page_names = [i[0] for i in self.df_l]
        ori_pages = self.df.keys()
        match out_f:
            case 1:
                self._writein_data(page_index)
                df_toadd = self.df_l[page_index][1].drop('IconID', axis=1)
                self.df[page_n] = df_toadd
                self.df = OrderedDict([[key, self.df[key]] for key in page_names if key in ori_pages])
                self.manager.save_xlsx()
            case 2:
                self._writein_data(page_index)
                df_to_write = OrderedDict()
                for name, df in self.df_l:
                    df_to_write[name] = df.drop('IconID', axis=1, inplace=False)
                self.df = df_to_write
                self.manager.save_xlsx()
            case _:
                return

class InfoTip(QDialog):
    def __init__(self,
                 type_f:Literal['Info', 'Warning', 'Error'], 
                 prompt_f:str, 
                 buttons:OrderedDict[str,Union[str, Dict[Literal['colors', 'value',], Union[bool, str, List[str]]]]],
                 config:Config_Manager=None,):
        super().__init__()
        self.VALUE = -10
        if config and not hasattr(self, 'config'):
            self._load_config(config)
        self.config.group_chose(mode='MainWindow', widget='Tip')
        self.type = type_f
        self.prompt = prompt_f
        self.buttons = buttons
        self._load()
        self._init_ui()
        UIUpdater.set(atuple('MainWindow', 'Tip', 'color', 'background'), self._setStyle)
    @classmethod
    def _load_config(cls, config:Config_Manager):
        cls.config = config.deepcopy()
    
    def _load(self):
        pre = ['MainWindow', 'Tip', 'font']
        self.title_font = atuple(pre+['title'])
        self.prompt_font = atuple(pre+['prompt'])
        self.button_font = atuple(pre+['button'])

        pre = ['MainWindow', 'Tip', 'Size']
        self.button_margin = atuple(pre+['button_margin'])
        self.prompt_margin = atuple(pre+['prompt_margin'])
        self.title_height = atuple(pre+['title_height'])
        self.button_size = atuple(pre+['button_size'])
        self.widget_size = atuple(pre+['widget_size'])

        self.button_colors = atuple('MainWindow', 'Tip', 'color', 'button')
        self.info_icon = atuple('MainWindow', 'Tip', 'path', 'info_icon')
        self.warning_icon = atuple('MainWindow', 'Tip', 'path', 'warning_icon')
        self.error_icon = atuple('MainWindow', 'Tip', 'path', 'error_icon')

    def _init_ui(self):
        self.layout0 = amlayoutV()
        self.setLayout(self.layout0)
        self.layout_tile = amlayoutH(spacing=15)
        self.layout_prompt = amlayoutH()
        UIUpdater.set(self.prompt_margin, self.layout_prompt.setContentsMargins,type_f='margin')

        self.layout_button = amlayoutH()
        UIUpdater.set(self.button_margin, self.layout_button.setContentsMargins, type_f='margin')
        UIUpdater.set(self.title_font, self.setFont, 'font')
        
        self.title_icon = AutoLabel(text='', icon_f=self.title_icon,width=self.title_height, height=self.title_height)
        self.title_icon.setAlignment(Qt.AlignCenter)

        self.title_name = AutoLabel(text=self.type, font=self.title_font)
        self.title_name.setAlignment(Qt.AlignLeft)
        add_obj(self.title_icon, self.title_name, parent_f=self.layout_tile)
        
        self.promt_label = AutoLabel(text=self.prompt, font=self.prompt_font)
        self.promt_label.setWordWrap(True)
        self.promt_label.setAlignment(Qt.AlignCenter)
        self.layout_prompt.addWidget(self.promt_label)

        for name, value in self.buttons.items():
            button_i  = ColorfulButton(name, self.button_colors, self.title_font)
            button_i.setProperty('value', value)
            UIUpdater.set(self.button_size, button_i.setFixedSize, 'size')
            self.layout_button.addWidget(button_i)
            button_i.clicked.connect(self._return)
        
        add_obj(self.layout_tile, self.layout_prompt, self.layout_button, parent_f=self.layout0)
        UIUpdater.set(self.widget_size, self.setFixedSize, 'size')
    
    def _setStyle(self, background_color):
        style_sheet = f'''
            QWidget {{
                background-color: {background_color};
                border-radius: 10px;
            }}
        '''
        self.setStyleSheet(style_sheet)
    
    def _return(self):
        button = self.sender()
        self.VALUE = button.property('value')
        super().accept()

