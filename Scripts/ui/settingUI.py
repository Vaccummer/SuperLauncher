import os
from PySide2.QtWidgets import QListWidget, QMainWindow, QWidget,QListWidgetItem,QPushButton, QHBoxLayout, QVBoxLayout, QLabel
from PySide2.QtGui import QFontMetrics, QIcon
from PySide2.QtCore import QSize, Qt
from functools import partial
import shutil
import pandas
from abc import abstractmethod
from typing import Literal, Union, OrderedDict
# local import
from ..ui.custom_widget import *
from ..manager.config_ui import *
from ..tools.toolbox import *
from ..manager.paths_transfer import *

class UIShortcutSetting(QWidget):
    def __init__(self, parent:QMainWindow, config:Config_Manager, shortcuts_manager:ShortcutsPathManager):
        super().__init__()
        self.up = parent
        self.name = 'shortcut_obj'
        self.config = config.deepcopy().group_chose(mode="Launcher", widget=self.name)
        self.manager:ShortcutsPathManager = shortcuts_manager
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
        w_1, h_1 = UIUpdater.config[atuple('Launcher', self.name, 'Size', 'setting_window_size')]
        try:
            x_t = x + w//2 - w_1//2
            y_t = y + h//2 - h_1//2
            self.setGeometry(x_t, y_t, w_1, h_1)
        except Exception as e:
            warnings.warn(f"UIShortcutSetting.showWin error: {e}")
            x_t = x + w//2 - 1200
            y_t = y + h//2 - 600
            self.setGeometry(x_t, y_t, 1200, 600)
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
    refresh_signal = Signal()
    def __init__(self, parent:QMainWindow, config:Config_Manager, shortcuts_manager:ShortcutsPathManager):
        super().__init__(parent, config, shortcuts_manager)
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
        self.refresh_signal.emit()
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

class ExePathLine(AutoEdit):
    def __init__(self, style_d, tooltip_style, height_f:int, font:QFont, place_holder:str=None, disable_scroll:bool=False):
        super().__init__(text='', font=font, style_d=style_d, height=height_f, disable_scroll=disable_scroll)
        self.setPlaceholderText(place_holder)
        self.place_holder = place_holder
        self.style_ctl.force_escape_sign[atuple('QLineEdit', 'background-color')] = True
        UIUpdater.set(tooltip_style, self._customTooltip)
        self.textChanged.connect(self.customBackground)
    
    def _customTooltip(self, tooltip_style:dict):
        return
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

    def customBackground(self, text:str)->None:
        self.setToolTip(text)
        normal_color = atuple('Settings', 'LauncherSetting', 'style', 'exe_edit', 'background')
        error_color = atuple('Settings', 'LauncherSetting', 'style', 'exe_edit', 'background_error')
        warning_color = atuple('Settings', 'LauncherSetting', 'style', 'exe_edit', 'background_warning')

        if os.path.exists(text) or (not text):
            color_n = UIUpdater.get(normal_color, '#F7F7F7')
        elif os.path.isabs(text):
            color_n = UIUpdater.get(warning_color, '#FFC300')
        else:
            color_n = UIUpdater.get(error_color, '#FF5733')
        self.extra_style_dict[atuple('QLineEdit', 'background-color')] = color_n
        self.setStyleSheet(style_make(self.style_dict|self.extra_style_dict))

class NameEdit(AutoEdit):
    def __init__(self, text_f:str,style_d,font:QFont, height:int,
                 ):
        super().__init__(text=text_f, font=font, height=height, style_d=style_d)
        self.style_d = style_d
    
    def customBackground(self, sign_f:bool=True):
        color_normal = atuple('Settings', 'LauncherSetting', 'style', 'name_edit', 'background')
        color_error = atuple('Settings', 'LauncherSetting', 'style', 'name_edit', 'background_error')
        if sign_f:
            color_t = UIUpdater.get(color_normal, '#F7F7F7')
        else:
            color_t = UIUpdater.get(color_error, '#FF5733')
        self.extra_style_dict[atuple('QLineEdit', 'background-color')] = color_t
        self.setStyleSheet(style_make(self.style_dict|self.extra_style_dict))

class SheetControl(QTabBar):
    tab_operation = Signal(dict)
    def __init__(self, parent:QWidget, font_f:QFont, style_main:dict, style_menu:dict):
        super().__init__(parent)
        self._init_menu()
        self.up = parent
        UIUpdater.set(font_f, self.setFont, 'font')
        self.style_ctl = self.customStyle(style_main)
        height_f = atuple('Settings', 'LauncherSetting', 'style', 'sheet_control', 'main_height')
        self.height_ctrl = UIUpdater.set(height_f, self.setFixedHeight, 'height')
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
    
    @dynamic_load(type_f='style')
    def customStyle(self, style:dict, escape_sign:dict={}):
        bg_color = Udata(atuple('main_background'),'transparent')
        main_border = Udata(atuple('main_border'),'none')
        main_border_radius = Udata(atuple('main_border_radius'),10)

        tab_margin_right = Udata(atuple('tab_margin_right'),10)
        padding = Udata(atuple('padding'),[0, 10, 0, 10])
        tab_height = Udata(atuple('tab_height'),50)
        tab_border = Udata(atuple('tab_border'),'none')
        tab_border_radius = Udata(atuple('tab_border_radius'),[10,10,10,10])
        bg_colors = Udata(atuple('background_colors'),["#F7F7F7", "#FFC300", "#FF5733"])
        font_colors = Udata(atuple('font_colors'),["#000000", "#000000", "#000000"])
        close_icon0 = Udata(atuple('path', 'tab_close_icon0'),'')
        close_icon1 = Udata(atuple('path', 'tab_close_icon1'),'')
        close_icon2 = Udata(atuple('path', 'tab_close_icon2'),'')
        close_icon_margin = Udata(atuple('close_icon_margin'),2)
        if not hasattr(self, 'tab_style_d'):
            self.tab_style_d = {}
        style_temp = {
            "QTabBar": {
                "border": main_border,
                "background": bg_color,
                'border-radius': main_border_radius,
            },
            "QTabBar::tab": {
                "margin-right": tab_margin_right,
                "padding": padding, 
                'border-bottom-left-radius': tab_border_radius[0],
                'border-bottom-right-radius': tab_border_radius[1],
                'border-top-left-radius': tab_border_radius[2],
                'border-top-right-radius': tab_border_radius[3],
                "height": tab_height,
                "background": bg_colors[0],
                "color": font_colors[0],
                'border': tab_border,
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
                "image": close_icon0,
                "subcontrol-position": "right",
                "margin": close_icon_margin,
            },
            "QTabBar::close-button:hover": {
                "image": close_icon1,
            },
            "QTabBar::close-button:pressed": {
                "image": close_icon2,
            },
            "QTabBar::scroller": {
                "width": "0px",
                "height": "0px",
                "background-color": "transparent",
            }
        }
        self.tab_style_d = process_style_dict(self.tab_style_d, style_temp, escape_sign, style)
        self.setStyleSheet(style_make(self.tab_style_d))

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

    def _init_menu(self):
        menu_style_d = atuple('Settings', 'LauncherSetting', 'style', 'tab_menu', 'main')
        item_style_d = atuple('Settings', 'LauncherSetting', 'style', 'tab_menu', 'item_button')
        actions = ['rename', 'delete']
        font_f = atuple('Settings', 'LauncherSetting', 'font', 'tab_menu')
        width_f = atuple('Settings', 'LauncherSetting', 'Size', 'tab_menu_button_width')
        height_f = atuple('Settings', 'LauncherSetting', 'Size', 'tab_menu_button_height')
        self.menu = AutoMenu(main_style_d=menu_style_d, item_style_d=item_style_d, actions=actions, values={}, font=font_f, width_f=width_f, height_f=height_f)
        self.menu.hide()

    def open_context_menu(self, position:QPoint): 
        index = self.tabAt(position)
        page_name = self.tabText(index)
        if not index:
            return
        self.menu.value_l = [{'action':'rename', 'index':index, 'page':page_name}, {'action':'delete', 'index':index, 'page':page_name}]
        self.menu.action(index, position, self.mapToGlobal(QPoint(0, 0)))
        
    def move_tab(self, from_index, to_index):
        self.tab_operation.emit({'action':'move', 'from':from_index, 'to':to_index})

    def _rename(self, index:int, name_n):
        self.setTabText(index, name_n)
    
    def _delete(self, index:int):
        if isinstance(index, str):
            index = self.get_texts().index(index)
        self.removeTab(index)

class GroupEdit(QWidget):
    menu_show_signal = Signal(dict)
    def __init__(self, text_f:str, font_f:QFont, edit_style:atuple, button_style:atuple, height_f:atuple, width_f:atuple, index:int):
        super().__init__()
        self.index = index
        UIUpdater.set(font_f, self.setFont, 'font')
        self.font_f = font_f
        self.edit_d = edit_style
        self.button_d = button_style
        self.height_f = height_f
        self.width_f = width_f
        self._initUI()
        self.edit.setText(text_f)
        self.setStyleSheet('background-color:black;')

    def _initUI(self)->None:
        self.layout0 = amlayoutH()
        self.layout0.setContentsMargins(0, 0, 0, 0)

        self.edit = AutoEdit(style_d=self.edit_d, height=self.height_f, width=self.width_f, font=self.font_f)
        self.edit_rect = self.edit.geometry()
        self.edit.geometry_signal.connect(self.move_obj)

        self.button = YohoPushButton(style_config=self.button_d, height_f=self.height_f, width_f=self.height_f,parent=self)
        # self.button.extra_style_dict[atuple('QPushButton', 'border-top-left-radius')] = 0
        # self.button.extra_style_dict[atuple('QPushButton', 'border-bottom-left-radius')] = 0
        self.button.clicked.connect(self.menu_show)

        self.layout0.addWidget(self.edit)
        self.setLayout(self.layout0)
        UIUpdater.set(alist(self.width_f, self.height_f), self.setFixedSize, alist('width', 'height'))

    @Slot(dict)
    def move_obj(self, rect:dict)->None:
        edit_geo = self.edit.geometry()
        x = edit_geo.x() + edit_geo.width() - self.button.width()
        y = edit_geo.y()
        self.button.raise_()
        self.button.setGeometry(x, y, self.button.width(), self.button.height())
        # self.button.setGeometry(x, y, self.button.width(), self.button.height())
    
    @Slot()
    def menu_show(self)->None:
        self.menu_show_signal.emit({'index':self.index, 'rect':self.edit_rect})


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
        self.app_info_d = self.manager.app_d
        # self.df:dict[str:pandas.DataFrame] = self.manager.df
        self.data_dict:dict[str, dict[int, GV.LauncherAppInfo]] = {}
        for name_i, info_i in self.app_info_d.items():
            list_i = self.data_dict.setdefault(info_i.group, [])
            list_i.append(info_i.deepcopy())
        for group_i, list_i in self.data_dict.items():
            self.data_dict[group_i] = {i:app_i for i, app_i in enumerate(list_i)}
        
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
        self.nameedit_length = atuple(pre+['nameedit_length'])
        self.chnameedit_length = atuple(pre+['chnameedit_length'])
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
        self.control_button_width = atuple(pre+['control_button_width'])
        
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
        self.objs_l:dict[int, dict[str, QWidget]] = {}
        self.widget_l:list[QWidget] = []
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
        self._line_fresh(next(iter(self.data_dict.keys())))
    
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
        UIUpdater.set(self.frame_style, self.customFrameStyle, 'style')
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("myScrollArea")
        self.scroll_area.setWidget(self.frame)  # Set the frame as the widget of the scroll area
        self.scroll_area.setWidgetResizable(True)
        UIUpdater.set(self.scroll_area_style,
                      self.customScrollAreaStyle,
                      'style')
    
    def customFrameStyle(self, frame_style:dict, escape_sign:dict={}):
        bg_color = Udata(atuple('background'), 'transparent')
        border_radius = Udata(atuple('border-radius'), 10)
        border = Udata(atuple('border'), '5px solid gray')
        if not hasattr(self, 'frame_style_dict'):
            self.frame_style_dict = {}
        if not hasattr(self, 'extra_frame_style_dict'):
            self.extra_frame_style_dict = {}
        temp_dict = {
            'QFrame#OuterFrame':{
                'background': bg_color,
                'border-top-left-radius': border_radius[0],
                'border-top-right-radius': border_radius[1],
                'border-bottom-left-radius': border_radius[2],
                'border-bottom-right-radius': border_radius[3],
                'border': border,
            }
        }
        self.frame_style_dict = process_style_dict(self.frame_style_dict, temp_dict, escape_sign, frame_style)
        self.frame.setStyleSheet(style_make(self.frame_style_dict|self.extra_frame_style_dict))

    def customScrollAreaStyle(self, scroll_style:dict, escape_sign:dict={}):
        orbit_color = Udata(atuple('orbit_color'), 'rgba(255, 255, 255, 40)')

        handle_colors = Udata(atuple('background_colors'), ["#F7F7F7", "#FFC300", "#FF5733"])
        border_radius = Udata(atuple('border_radius'), 10)
        min_height = Udata(atuple('min_height'), 20)
        width = Udata(atuple('width'), 20)
        border = Udata(atuple('border'), 'none')
        margin = Udata(atuple('margin'), 5)

        if not hasattr(self, 'scroll_area_style_dict'):
            self.scroll_area_style_dict = {}
        if not hasattr(self, 'extra_scroll_area_style_dict'):
            self.extra_scroll_area_style_dict = {}
        
        temp_dict = {
            "QScrollArea#myScrollArea": {
                "background": 'transparent',
                "border": 'none',
            },
            "QScrollBar": {
                "border": border,
                "background": orbit_color,
                "width": width,
                "margin": margin,
                "border-top-left-radius": border_radius[0],
                "border-top-right-radius": border_radius[1],
                "border-bottom-left-radius": border_radius[2],
                "border-bottom-right-radius": border_radius[3],
            },
            "QScrollBar::handle": {
                "background": handle_colors[0],
                "min-height": min_height,
                "border-top-left-radius": border_radius[0],
                "border-top-right-radius": border_radius[1],
                "border-bottom-left-radius": border_radius[2],
                "border-bottom-right-radius": border_radius[3],
            },
            "QScrollBar::handle:vertical:hover": {
                "background": handle_colors[1],
            },
            "QScrollBar::handle:vertical:pressed": {
                "background": handle_colors[2],
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

        self.scroll_area_style_dict = process_style_dict(self.scroll_area_style_dict, temp_dict, escape_sign, scroll_style)
        self.scroll_area.setStyleSheet(style_make(self.scroll_area_style_dict|self.extra_scroll_area_style_dict))

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
        UIUpdater.set(self.nameedit_length, name_label.setFixedWidth)
        name_label.textChanged.connect(self.name_edit_change)
        chname_label = NameEdit(text_f=chname, style_d=self.nameedit_style, height=self.line_height, font=self.chname_font)
        chname_label.setProperty('index', index_i)
        chname_label.setProperty('type', 'chname')
        UIUpdater.set(self.chnameedit_length, chname_label.setFixedWidth)
        chname_label.textChanged.connect(self.name_edit_change)
        exe_edit = ExePathLine(style_d=self.exeedit_style,tooltip_style=self.tooltip_style, height_f=self.line_height, 
                               place_holder=exe_path, font=self.exe_font)
        exe_edit.setProperty('index', index_i)
        UIUpdater.set(self.exeedit_min_length, exe_edit.setMinimumWidth)
        exe_edit.textChanged.connect(self.exe_edit_write)
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
        # self.add_button = YohoPushButton(icon_i=self.add_button_icon, 
        #                                  style_config=self.add_button_style,
        #                                 )
        # UIUpdater.set(self.line_height, self.add_button.setFixedHeight)
        # self.add_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        icon_proportion = atuple('Settings', 'LauncherSetting', 'style', 'tab_add_button', 'icon_proportion')
        #self.add_button = AddButton(style_d=self.add_button_style, icon_f=self.add_button_icon, height_f=self.line_height)
        self.add_button = YohoPushButton(icon_i=self.add_button_icon, style_config=self.add_button_style, 
                                         icon_proportion=icon_proportion)
        UIUpdater.set(self.line_height, self.add_button.setFixedHeight, 'height')
        self.add_button.setMaximumWidth(99999)
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
    @abstractmethod
    def exe_edit_write(self):
        pass
class LauncherSetting(UILauncherSetting):
    def __init__(self, config:Config_Manager, parent:QMainWindow, manager:LauncherPathManager)->None:
        super().__init__(config, parent , manager)
    
    def _line_fresh(self, page_name:str)->None:
        self.line_num = 0
        self.data_dict.setdefault(page_name, {})
        self.dict_n:dict[int, GV.LauncherAppInfo] = self.data_dict[page_name]
        for i in range(len(self.dict_n.keys())):
            if i >= self.num:
                self._insert_line()
            self.widget_l[i].setVisible(True)
            self.objs_l[i]['number'].setText(str(i))
            self.objs_l[i]['name'].setText(self.dict_n[i].name)
            self.objs_l[i]['chname'].setText(self.dict_n[i].chname)
            self.objs_l[i]['exe'].setText(self.dict_n[i].exe_path)
            icon_c = self.dict_n[i].icon_path
            if icon_c:
                self.objs_l[i]['icon'].setIcon(AIcon(icon_c))
            else:
                if not self.dict_n[i].name:
                    icon_c = self.manager.default_app_icon
                else:
                    type_f = 'app'
                    name_f = self.dict_n[i].name
                    path_f = self.dict_n[i].exe_path
                    host_f = 'Local'
                    request = GV.IconQuery(type_f=type_f, name=name_f, group=page_name, path=path_f, host=host_f)
                    icon_c = self.manager.get_app_icon(request)
                self.objs_l[i]['icon'].setIcon(icon_c)
                self.dict_n[i].icon_path = icon_c.file_path
            self.line_num += 1
        for i in range(len(self.widget_l)):
            if i >= len(self.dict_n.keys()):
                self.widget_l[i].setVisible(False)
    
    def _init_bottom_control(self)->None:
        self.bottom_layout = amlayoutH('c', spacing=25)
        self.tab_wdiget = QWidget()
        self.tab_layout = amlayoutH('l', spacing=10)
        self.tab_wdiget.setLayout(self.tab_layout)
        self.tab_bar = SheetControl(parent=self, font_f=self.tab_font, style_main=self.tab_style, style_menu=self.meunu_style)
        self.tab_bar.menu.action_signal.connect(self.tab_menu_action)
        for name_i in self.data_dict.keys():
            self.tab_bar.addTab(name_i)
        
        self.tab_bar.currentChanged.connect(self.change_tab)
        self.tab_bar.setCurrentIndex(0)
        self.b_add_button = YohoPushButton(icon_i=self.add_sheet_button_icon, style_config=self.tab_add_style, size_f=self.tab_height)
        self.b_add_button.clicked.connect(self.add_tab)
        self.tab_layout.addWidget(self.tab_bar)
        add_obj(self.b_add_button, parent_f=self.tab_layout)
        
        self.save_button = YohoPushButton(text_f='Save', font_f=self.save_button_font, style_config=self.save_button_style)
        UIUpdater.set(self.line_height, self.save_button.setFixedHeight)
        UIUpdater.set(self.control_button_width, self.save_button.setFixedWidth)

        self.save_button.clicked.connect(self._save)
        self.reset_button = YohoPushButton(text_f='Reset', font_f=self.reset_button_font, style_config=self.reset_button_style, )
        UIUpdater.set(self.line_height, self.reset_button.setFixedHeight)
        UIUpdater.set(self.control_button_width, self.reset_button.setFixedWidth)

        self.reset_button.clicked.connect(self._reset)
        # self.discard_button = ChangeControl('Discard', self.config.get('discard_button', obj='color'), self.config.get('discard_button', obj='font'), self.line_height)
        # self.discard_button.clicked.connect(self._discard)
        UIUpdater.set(self.bottom_margin, self.bottom_layout.setContentsMargins, 'margin')
        self.bottom_layout.addWidget(self.tab_wdiget)
        self.bottom_layout.addStretch()
        add_obj(self.save_button, self.reset_button, parent_f=self.bottom_layout)
        
    def _insert_line(self)->None:
        page_text = self.tab_bar.get_current_text()
        self.data_dict[page_text][len(self.data_dict[page_text].keys())] = {'Name':'', 'Chinese Name':'', 'EXE Path':'', 'IconPath':''}
        #self.df_n.loc[len(self.df_n)] = ['', '', '', '', page_text, None]
        if self.line_num >= len(self.widget_l):
            self._init_single_line(self.line_num, default=True, insert=True)
            self.dict_n[self.line_num] = GV.LauncherAppInfo(None, name='', chname='', group=page_text, exe_path='')
        else:
            self.widget_l[self.line_num].setVisible(True)
            self.objs_l[self.line_num]['number'].setText(str(self.line_num))
            self.objs_l[self.line_num]['name'].setText('')
            self.objs_l[self.line_num]['chname'].setText('')
            self.objs_l[self.line_num]['exe'].setText('')
            self.objs_l[self.line_num]['icon'].setIcon(AIcon(self.config[self.default_app_icon]))
        self.line_num += 1
        
        self.sroll_down()
    
    def sroll_down(self)->None:
        bar = self.scroll_area.verticalScrollBar()
        for i in range(10):
            bar.triggerAction(QScrollBar.SliderSingleStepAdd)

    def add_tab(self, name='new_sheet', refresh:bool=True)->None:
        text_l = self.tab_bar.get_texts()
        for i in range(99):
            name_t = f'{name}_{i}'
            if name_t not in text_l:
                break
        self.data_dict[name_t] = {0:GV.LauncherAppInfo(None, name='', chname='', group=name_t, exe_path='')}
        self.tab_bar.addTab(name_t)
        if refresh:
            self.tab_bar.set_current_tab(name_t)
    
    def change_tab(self, index_new:int)->None:
        self.tab_index = index_new
        self._line_fresh(self.tab_bar.get_texts()[index_new])

    def rename_tab(self, index)->None:
        current_name = self.tab_bar.tabText(index)
        new_name, ok = QInputDialog.getText(self, "Rename Sheet", "Enter New Name:", text=current_name)
        if ok and new_name.strip():
            if new_name in self.tab_bar.get_texts():
                #self.up.tip('Warning', 'Name already exists', {'OK':False}, False)
                return
            self.tab_bar.setTabText(index, new_name)
            self.data_dict[new_name] = self.data_dict.pop(current_name)
    
    def delete_tab(self, page_name:str)->None:
        tip_prompt = f'Are you sure to DELETE sheet "{page_name}"?'
        #out_f = self.up.tip('Warning', tip_prompt, {'Yes':True, 'No':False}, False)
        out_f = True
        if out_f:
            self.data_dict.pop(page_name)
            self.tab_bar._delete(page_name)
    
    def sort_tab(self)->None:
        tab_text_l = self.tab_bar.get_texts()
        index_i = self.tab_bar.currentIndex()
        self.tab_index = index_i
        return
        df_l = []
        for i in tab_text_l:
            for j in self.df_l:
                if j[0] == i:
                    df_l.append(j)
        self.df_l = df_l
        self.tab_index = index_i

    def _change_icon(self, index_f:int)->None:
        file_filter = "Icons (*.svg *.png *.jpg *.jpeg *.ico *.bmp)"
        file_path, _ = QFileDialog.getOpenFileName(self, "Select an image", "", file_filter)
        if not file_path:
            return
        icon_i = QIcon(file_path)
        self.objs_l[index_f]['icon'].setIcon(icon_i)
        self.objs_l[index_f]['icon'].setProperty('icon_path', file_path)
        self.dict_n[index_f].icon_path = file_path
    
    def name_edit_change(self, text:str)->None:
        edit_f:NameEdit = self.sender()
        type_f:str = edit_f.property('type')
        index_f:int = edit_f.property('index')
        if type_f == 'name':
            self.dict_n[index_f].name = text
        elif type_f == 'chname':
            self.dict_n[index_f].chname = text
        names = [i['name'].text() for i in self.objs_l.values()]
        if not text:
            edit_f.customBackground(True)
        elif names.count(text) > 1:
            if type_f == 'name':
                edit_f.customBackground(False)
            else:
                pass
        else:
            edit_f.customBackground(True)     

    def exe_edit_write(self, text:str)->None:
        line_f = self.sender()
        index_f = line_f.property('index')
        self.dict_n[index_f].exe_path = text

    def _exe_search(self, index_f:int)->None:
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "",
                                                  "All Files (*);;Python Files (*.py)", options=options)
        if file_name:
            file_name = file_name.replace('/', '\\')
            self.objs_l[index_f]['exe'].setText(file_name)
    
    def _read_data(self, data_dict:dict, group_name:str)->None:
        df_t = pandas.DataFrame()
        df_list = []
        for key, value in data_dict.items():
            if not value['Name']:
                continue
            df_list.append(pandas.DataFrame([value | {'Group': group_name}]))
        return pandas.concat(df_list, ignore_index=True) if df_list else pandas.DataFrame()

    def _reset(self)->None:
        out_f =2
        page_n = self.tab_bar.get_current_text()
        match out_f:
            case 1:
                if page_n not in self.data_dict.keys():
                    self.data_dict[page_n] = {0:GV.LauncherAppInfo(None, name='', chname='', group=page_n, exe_path='')}
                else:
                    self.data_dict[page_n].clear()
                    index_i = 0
                    for info_i in self.app_info_d.values():
                        if info_i.group == page_n:
                            self.data_dict[page_n][index_i] = info_i
                            index_i += 1
                self._line_fresh(self.tab_bar.get_current_text())
            case 2:
                self._process_ori_df()
                page_i = next(iter(self.data_dict.keys()))
                self.tab_bar.set_current_tab(page_i)
                self._line_fresh(page_i)
                
    def _save(self):
        # title_f = 'Warning'
        # prompt_f = 'Are you sure to write in pages to local data?'
        # value_d = {'Save All':2, "Save This Page":1, 'Cancel':-5}
        # out_f = self.up.tip(title_f, prompt_f, value_d, -5)
        out_f = 2
        page_n = self.tab_bar.get_current_text()
        match out_f:
            case 1:
                for info_i in self.data_dict[page_n].values():
                    if info_i.name:
                        self.manager.app_d[info_i.name] = info_i
                self.manager.xlsx_save_signal.emit()
            case 2:
                self.manager.app_d.clear()
                for info_d in self.data_dict.values():
                    for info_i in info_d.values():
                        if info_i.name:
                            self.manager.app_d[info_i.name] = info_i
                self.manager.xlsx_save_signal.emit()

    @Slot(dict)
    def tab_menu_action(self, action_d:dict)->None:
        if not action_d:
            return
        page_f = action_d['page']
        match action_d['action']:
            case 'rename':
                self.rename_tab(page_f)
            case 'delete':
                self.delete_tab(page_f)


class SoftwareInitializer(QWidget):
    def __init__(self, manager:LauncherPathManager)->None:
        self.edge_threshold = 10
        self.drag_position = None
        super().__init__()
        self.manager = manager
        self.name = 'LauncherInitializer'
        self._initPara()
        self._initData()
        self._initUI()

    def _windowset(self):
        self.drag_position = None
        self.edge_drag = None
        self.edge_threshold = 20
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("Launcher Software Initializate")
        UIUpdater.set(atuple("Settings", self.name,'path','taskbar_icon'), self.setWindowIcon,type_f='icon')
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

    def showWin(self)->None:
        self.setGeometry(GV.GEOMETRY[0], GV.GEOMETRY[1], 1600,900)
        self.show()

    def _initPara(self)->None:
        self.temp_icon_folder = UIUpdater.get(atuple("Settings", self.name, 'path', 'temp_icon_folder'), 'path')
        self.software_path_folder = UIUpdater.get(atuple("Settings", self.name, 'path', 'software_path_folder'), 'path')
        self.app_d = {}

        self.re_filters_ptr = atuple("Settings", self.name, 'app_name_filter')
        self.load_filters(self.re_filters_ptr)

        self.arrow_icon = atuple("Settings", self.name, 'path', 'arrow_icon')
        self.group_icon = atuple("Settings", self.name, 'path', 'group_icon')
        self.icon_icon = atuple("Settings", self.name, 'path', 'icon_icon')
        self.name_icon = atuple("Settings", self.name, 'path', 'name_icon')
        self.chname_icon = atuple("Settings", self.name, 'path', 'chname_icon')
        self.exe_icon = atuple("Settings", self.name, 'path', 'exe_icon')

        self.colname_button_d = atuple("Settings", self.name, 'style', 'colname_button')
        self.exe_paths = [app.exe_path for app in self.manager.app_d.values()]
        self.group_edit_d = atuple("Settings", self.name, 'style', 'group_edit')
        self.group_button_d = atuple("Settings", self.name, 'style', 'group_button')
        self.name_edit_d = atuple("Settings", self.name, 'style', 'name_edit')
        self.chname_edit_d = atuple("Settings", self.name, 'style', 'chname_edit')
        self.exe_edit_d = atuple("Settings", self.name, 'style', 'exe_edit')
        self.icon_button_d = atuple("Settings", self.name, 'style', 'icon_button')
        self.frame_d = atuple("Settings", self.name, 'style', 'frame')
        self.scroll_area_d = atuple("Settings", self.name, 'style', 'scroll_area')
        self.control_button_d = atuple("Settings", self.name, 'style', 'control_button')
        self.menu_main_d = atuple("Settings", self.name, 'style', 'group_menu', 'main')
        self.menu_item_d = atuple("Settings", self.name, 'style', 'group_menu', 'item_button')
        self.title_style = atuple("Settings", self.name, 'style', 'title')
        self.tooltip_style = atuple("Settings", self.name, 'style', 'tooltip')

        self.line_height = atuple("Settings", self.name, 'Size', 'line_height')
        self.group_width = atuple("Settings", self.name, 'Size', 'group_width')
        self.name_edit_width = atuple("Settings", self.name, 'Size', 'name_edit_width')
        self.chname_edit_width = atuple("Settings", self.name, 'Size', 'chname_edit_width')
        self.exe_edit_width = atuple("Settings", self.name, 'Size', 'exe_edit_width')
        self.line_spaing = atuple("Settings", self.name, 'Size', 'line_spaing')
        self.line_obj_spacing = atuple("Settings", self.name, 'Size', 'line_obj_spacing')
        self.colname_margin = atuple("Settings", self.name, 'Size', 'colname_margin')
        self.line_margin = atuple("Settings", self.name, 'Size', 'line_margin')
        self.control_button_width = atuple("Settings", self.name, 'Size', 'control_button_width')
        self.control_button_height = atuple("Settings", self.name, 'Size', 'control_button_height')
        self.control_button_margin = atuple("Settings", self.name, 'Size', 'control_button_margin')

        self.group_font = atuple("Settings", self.name, 'font', 'group_font')
        self.name_font = atuple("Settings", self.name, 'font', 'name_font')
        self.chname_font = atuple("Settings", self.name, 'font', 'chname_font')
        self.exe_font = atuple("Settings", self.name, 'font', 'exe_font')
        self.control_button_font = atuple("Settings", self.name, 'font', 'control_button_font')
        self.title_font = atuple("Settings", self.name, 'font', 'title_font')
        self.menu_font = atuple("Settings", self.name, 'font', 'menu_font')

    @dynamic_load()
    def load_filters(self, filters:list[list[str]])->list[tuple[str,re.Pattern]]:
        filters = filters if filters else []
        re_filters:list[tuple[str,re.Pattern]] = []
        for filter_i in filters:
            if filter_i[0].startswith('-'):
                option_i = filter_i[0][1:]
                filter_i = filter_i[1:]
            else:
                option_i = 'pf'
            if 'p' in option_i:
                match_dir = True
            else:
                match_dir = False
            if 'a' in option_i:
                match_case = False
            else:
                match_case = True
            pattern_str = '|'.join(filter_i)
            if match_case:
                pattern_f = re.compile(pattern_str)
            else:
                pattern_f = re.compile(pattern_str, re.IGNORECASE)
            if match_dir:
                re_filters.append(('dir', pattern_f))
            else:
                re_filters.append(('file', pattern_f))
        self.re_filters = re_filters

    def filter_path(self, path_f:str)->bool:
        for filter_i in self.re_filters:
            if filter_i[0] == 'dir':
                dirnames = os.path.dirname(path_f).split(os.sep)
                for dirname in dirnames:
                    if bool(filter_i[1].match(dirname)):
                        return False
            else:
                if bool(filter_i[1].match(os.path.basename(path_f))):
                    return False
        return True

    def filter_path_l(self, path_l:list[str])->list[str]:
        return [i for i in path_l if self.filter_path(i)]
    

    def _initData(self)->None:
        path_l = glob(os.path.join(self.software_path_folder, '**'), recursive=True)
        path_d = [link2path(i) for i in path_l if (not os.path.isdir(i)) and i not in self.exe_paths]
        self.path_l = self.filter_path_l(path_d)
        self.app_d = {}
        for path_i in self.path_l:
            ext:str = os.path.splitext(path_i)[1]
            name = os.path.basename(path_i).split('.')[0]
            chname = ''
            if is_path(path_i, exist_check=True) and ext.lower() in ['.exe','dll']:
                icon_f = self.manager.extract_exe_icon(path_i)
                if icon_f:
                    icon_f.save(os.path.join(self.temp_icon_folder, f'{name}.png'))
                    icon_path = os.path.join(self.temp_icon_folder, f'{name}.png')
                else:
                    continue
            else:
                continue
            self.app_d[name] = GV.LauncherAppInfo(None, name, chname, 'Default', path_i, icon_path)

    def _initUI(self)->None:
        self.obj_l = []
        self.layout0 = amlayoutV(align_h='center')
        self.setLayout(self.layout0)
        self._initTitles()
        self._initLines()
        self._initControl()
    
    def _initTitles(self)->None:
        self.title_label = AutoLabel(style_config=self.title_style, text='Software Initializer', font=self.title_font)
        self.layout_title = amlayoutH(align_v='center')
        self.group_icon_button = YohoPushButton(icon_i=self.group_icon, style_config=self.colname_button_d, height_f=self.line_height, width_f=self.group_width)
        self.name_icon_button = YohoPushButton(icon_i=self.name_icon, style_config=self.colname_button_d, height_f=self.line_height, width_f=self.name_edit_width)
        self.chname_icon_button = YohoPushButton(icon_i=self.chname_icon, style_config=self.colname_button_d, height_f=self.line_height, width_f=self.chname_edit_width)
        self.exe_icon_button = YohoPushButton(icon_i=self.exe_icon, style_config=self.colname_button_d, height_f=self.line_height, width_f=self.exe_edit_width)
        self.icon_icon_button = YohoPushButton(icon_i=self.icon_icon, style_config=self.colname_button_d, height_f=self.line_height, width_f=self.line_height)
        add_obj(self.group_icon_button, self.name_icon_button, self.chname_icon_button, self.exe_icon_button, self.icon_icon_button, parent_f=self.layout_title)

        self.layout0.addWidget(self.title_label)
        self.layout0.addLayout(self.layout_title)
    
    @Slot(dict)
    def showMenu(self, instruction:dict)->None:
        index_f = instruction['index']
        rec_f = instruction['rec']
        groups_ori = [i['group'].text() for i in self.obj_l]
        groups_new = []
        values_new = []
        for i in groups_ori:
            if i not in groups_new:
                groups_new.append(i)
                values_new.append({'group':i, 'index':index_f})

        if hasattr(self, 'menu'):
            self.menu.close()

        self.menu = AutoMenu(main_style_d=self.menu_main_d, item_style_d=self.menu_item_d, 
                             actions=groups_new, values=values_new,font=self.menu_font)
        self.menu.action_signal.connect(self.group_menu_action)
        self.menu.action(0, rec_f.pos())
    
    @Slot(dict)
    def group_menu_action(self, action_d:dict)->None:
        index_f = action_d['index']
        group_f = action_d['group']
        self.obj_l[index_f]['group'].setText(group_f)

    def _initLine(self, app_i:GV.LauncherAppInfo, index:int)->list:
        group_edit = GroupEdit(text_f=app_i.group, edit_style=self.group_edit_d, button_style=self.group_button_d, font_f=self.group_font, height_f=self.line_height, width_f=self.group_width, index=index)
        UIUpdater.set(self.arrow_icon, group_edit.button.setIcon, type_f='icon')

        name_edit = NameEdit(style_d=self.name_edit_d, text_f=app_i.name, font=self.name_font, height=self.line_height)
        UIUpdater.set(self.name_edit_width, name_edit.setMaximumWidth)

        chname_edit = NameEdit(style_d=self.name_edit_d, text_f=app_i.chname, font=self.chname_font, height=self.line_height)
        UIUpdater.set(self.chname_edit_width, chname_edit.setMaximumWidth)

        exe_edit = ExePathLine(style_d=self.exe_edit_d,tooltip_style=self.tooltip_style, font=self.exe_font, height_f=self.line_height)

        exe_edit.setText(app_i.exe_path)
        exe_edit.setMaximumWidth((99999))


        icon_button = YohoPushButton(style_config=self.icon_button_d, icon_i=app_i.icon_path, font_f=self.icon_button_d, height_f=self.line_height, width_f=self.line_height)

        return [group_edit, name_edit, chname_edit, exe_edit, icon_button]
    
    def _initLines(self)->None:
        self.scroll_area = ScrollArea(self, self.frame_d, self.scroll_area_d, self.line_spaing)
        self.layout0.addWidget(self.scroll_area)
        self.scroll_l = self.scroll_area.obj_layout
        self.line_layout_l = []
        for name_i, app_i in self.app_d.items():
            group_edit, name_edit, chname_edit, exe_edit, icon_button = self._initLine(app_i, len(self.obj_l))
            group_edit.menu_show_signal.connect(self.showMenu)
            self.obj_l.append({'group':group_edit, 'name':name_edit, 'chname':chname_edit, 'exe':exe_edit, 'icon':icon_button})
            line_layout = amlayoutH(align_v='center')
            UIUpdater.set(self.line_obj_spacing, line_layout.setSpacing, 'spacing')
            UIUpdater.set(self.line_margin, line_layout.setContentsMargins, 'margin')
            add_obj(icon_button,group_edit, name_edit, chname_edit, exe_edit,  parent_f=line_layout)
            self.line_layout_l.append(line_layout)
            self.scroll_l.addLayout(line_layout)
    
    def _initControl(self)->None:
        self.layout_bottom = amlayoutH(align_v='center')
        self.save_button = YohoPushButton(style_config=self.control_button_d, text_f='Save', font_f=self.control_button_font, height_f=self.control_button_height, width_f=self.control_button_width)

        self.cancel_button = YohoPushButton(style_config=self.control_button_d, text_f='Cancel', font_f=self.control_button_font, height_f=self.control_button_height, width_f=self.control_button_width)

        self.cancel_button.clicked.connect(partial(self.closeAction, False))
        self.save_button.clicked.connect(partial(self.closeAction, True))
        add_obj(self.save_button, self.cancel_button, parent_f=self.layout_bottom)
        UIUpdater.set(self.control_button_margin, self.layout_bottom.setContentsMargins, 'margin')
        self.layout0.addLayout(self.layout_bottom)

    def closeAction(self, save_f:bool)->None:
        pass
    

