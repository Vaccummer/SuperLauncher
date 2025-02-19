from PySide2.QtCore import Signal, Slot
from PySide2.QtGui import QIcon, QFont, QPixmap, QWheelEvent
from PySide2.QtWidgets import QPushButton, QWidget, QListWidget, QLineEdit, QMainWindow, QVBoxLayout
import random
from typing import Tuple, Union
# local import
from ..manager.config_ui import *
from ..manager.paths_transfer import *

class YohoPushButton(QPushButton):
    right_button_clicked = Signal(dict)
    def __init__(self, style_config:atuple,
                 icon_i:Union[str, AIcon, Tuple]='',
                 text_f:str='',
                 font_f:QFont=None,
                 size_f:Union[int, QSize, Tuple]=None, 
                 height_f:int=None,
                 width_f:int=None,
                 an_time:int=180,
                 change_size:float=0.5,
                 change_period:float=0.7,
                 icon_proportion:float=0.95,
                 parent=None):
        if parent is None:
            super().__init__()
        else:
            super().__init__(parent)
        self.setText(text_f)
        self.right_button_clicked_data:dict = {}
        self.an_type = "resize"
        self.force_antype = None
        self.an_time = an_time
        self.default_an_time = an_time
        self.extra_style_dict = {}
        UIUpdater.set(font_f, self.setFont, type_f='font')
        UIUpdater.set(icon_proportion, self._loadIconProportion)
        if style_config == atuple('MainWindow', 'switch_button', 'style'):
            self.style_ctl = self.customStyle(style_config)
        else:
            self.style_ctl = self.customStyle(style_config)
        # 设置按钮图标
        if icon_i is not None:
            UIUpdater.set(icon_i, self.setIcon, type_f='icon')
        if size_f is not None:
            UIUpdater.set(size_f, self.setFixedSize, type_f='size')
        if height_f is not None:
            UIUpdater.set(height_f, self.setFixedHeight, type_f='height')
        if width_f is not None:
            UIUpdater.set(width_f, self.setFixedWidth, type_f='width')

        self.change_size = change_size
        self.change_period = change_period
        self.clicked.connect(self.start_animation)
    
    def start_animation(self):
        if self.force_antype is not None:
            an_type_t = self.force_antype
        else:
            an_type_t = self.an_type
        if an_type_t == "shake":
            self.shake_icon()
        elif an_type_t == "resize":
            self.resize_icon()
    
    def shake_icon(self):
        self.animation = QPropertyAnimation(self, b"geometry")
        start_rect = self.geometry()
        self.animation.setDuration(self.an_time)
        self.animation.setStartValue(QRect(start_rect))
        self.animation.setKeyValueAt(0.2, QRect(start_rect.x() - 5, start_rect.y(), start_rect.width(), start_rect.height()))
        self.animation.setKeyValueAt(0.4, QRect(start_rect.x() + 5, start_rect.y(), start_rect.width(), start_rect.height()))
        self.animation.setKeyValueAt(0.6, QRect(start_rect.x() - 5, start_rect.y(), start_rect.width(), start_rect.height()))
        self.animation.setKeyValueAt(0.8, QRect(start_rect.x() + 5, start_rect.y(), start_rect.width(), start_rect.height()))
        self.animation.setEndValue(QRect(start_rect))
        self.animation.start()
    
    def resize_icon(self):
        self.animation = QPropertyAnimation(self, b"iconSize")
        self.animation.setDuration(self.an_time)
        size_n = self.iconSize()
        size_t = QSize(int(self.change_size*size_n.width()), int(self.change_size*size_n.height()))
        self.animation.setStartValue(size_n)
        self.animation.setKeyValueAt(self.change_period, size_t)  
        self.animation.setEndValue(size_n)  
        self.animation.start()

    def _loadIconProportion(self, icon_proportion:float):
        self.icon_proportion = icon_proportion
        self._resize(self.size())

    def resizeEvent(self, event):
        # automatically resize the icon to fit the button size
        super().resizeEvent(event)
        new_size = self.size()
        w, h = new_size.width(), new_size.height()
        rf = min(w, h)
        self.setIconSize(QSize(int(rf*self.icon_proportion), int(rf*self.icon_proportion)))
    
    def _resize(self, size_f:Union[int, QSize, list]):
        if isinstance(self.icon_proportion, float):
            res_factor = self.icon_proportion
        elif isinstance(self.icon_proportion, atuple):
            res_factor = UIUpdater.get(self.icon_proportion, 0.9)
        else:
            res_factor = 0.9
        if isinstance(size_f, int):
            size_f = QSize(size_f, size_f)
        elif isinstance(size_f, list):
            size_f = QSize(size_f[0], size_f[1])
        self.size_f = size_f
        self.setFixedSize(size_f)
        self.setIconSize(QSize(int(size_f.width()*res_factor), int(size_f.height()*res_factor)))

    @dynamic_load(type_f='style')
    def customStyle(self, format_dict:dict, escape_sign:dict={}):
        self.an_type = format_dict.get('animation_type', None)
        self.an_time = format_dict.get('animation_time', self.default_an_time)
        if not isinstance(self.an_time, int):
            self.an_time = self.default_an_time
        
        bg_colors = Udata(atuple('background_colors'), ["rgba(255,255,255,80)", "rgba(255,255,255,180)", "rgba(255,255,255,240)"])
        border_radius = Udata(atuple('border_radius'), 10)
        border = Udata(atuple('border'), 'none')
        padding = Udata(atuple('padding'), [0,0,0,0])
        text_align = Udata(atuple('text_align'), 'center')
        temp_dict = {
            'QPushButton': {
                'background-color': bg_colors[0],
                'border': border,
                'padding': padding,
                'border-top-left-radius': border_radius[0],
                'border-top-right-radius': border_radius[1],
                'border-bottom-right-radius': border_radius[2],
                'border-bottom-left-radius': border_radius[3],
                'text-align': text_align,
            },
            'QPushButton:hover': {
                'background-color': bg_colors[1],
            },
            'QPushButton:pressed': {
                'background-color': bg_colors[2],
            }
        }
        if not hasattr(self, 'style_dict'):
            self.style_dict = {}
        self.style_dict = process_style_dict(self.style_dict, temp_dict, escape_sign, format_dict)
        self.setStyleSheet(style_make(self.style_dict|self.extra_style_dict))
        
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.RightButton:
            self.right_button_clicked.emit(self.right_button_clicked_data)
        super().mousePressEvent(event)

class ColorfulButton(QPushButton):
    def __init__(self, text_f:str, colors:list[str], font:QFont, height:int=None, width:int=None):
        super().__init__()
        self.setText(text_f)
        UIUpdater.set(font, self.setFont, type_f='font')
        UIUpdater.set(height, self.setFixedHeight)
        UIUpdater.set(width, self.setFixedWidth)
        self._setstyle(colors)
    
    def _setstyle(self, colors):
        style_sheet = f'''
        QPushButton {{
            background-color: {colors[0]};
            border-radius: 10px;
            padding: 10px;
        }}
        QPushButton:hover {{
            background-color: {colors[1]};
        }}
        QPushButton:pressed {{
            background-color: {colors[2]};
        }}
        '''
        self.setStyleSheet(style_sheet)

class LabelAlikeButton(QPushButton):
    def __init__(self, text_f:str, style_config:atuple, font_f:QFont, height_f:int=None, width_f:int=None):
        super().__init__()
        self.setText(text_f)
        UIUpdater.set(font_f, self.setFont, type_f='font')
        if height_f is not None:
            UIUpdater.set(height_f, self.setFixedHeight)
        if width_f is not None:
            UIUpdater.set(width_f, self.setFixedWidth)
        self.extra_style_dict = {}
        self.bg_color_ptr = style_config | atuple(['background_colors'])
        self.style_ctl = self.customStyle(style_config)

    @dynamic_load(type_f='style')
    def customStyle(self, format_dict:dict, escape_sign:dict={}):
        bg_color = Udata(atuple('background_colors'), ['transparent', 'transparent', 'transparent'])
        border_radius = Udata(atuple('border_radius'), [10,10,10,10])
        border = Udata(atuple('border'), 'none')
        padding = Udata(atuple('padding'), [10,5,5,5])
        text_align = Udata(atuple('text_align'), 'left')
        temp_dict = {
            'QPushButton': {
                'background-color': bg_color[0],
                'border': border,
                'padding': padding,
                'text-align': text_align,
                'border-top-left-radius': border_radius[0],
                'border-top-right-radius': border_radius[1],
                'border-bottom-right-radius': border_radius[2],
                'border-bottom-left-radius': border_radius[3],
            },
            'QPushButton:hover': {
                'background-color': bg_color[1],
            },
            'QPushButton:pressed': {
                'background-color': bg_color[2],
            }
        }
        if not hasattr(self, 'style_dict'):
            self.style_dict = {}
        self.style_dict = process_style_dict(self.style_dict, temp_dict, escape_sign, format_dict)
        self.setStyleSheet(style_make(self.style_dict|self.extra_style_dict))

    def setSelected(self, selected:bool):
        bg_color = enlarge_list(UIUpdater.get(self.bg_color_ptr, ["white", "yellow", "red"]),3)
        if selected:
            self.extra_style_dict[atuple('QPushButton', 'background-color')] = bg_color[2]
            self.extra_style_dict[atuple('QPushButton:hover', 'background-color')] = bg_color[2]
            self.setStyleSheet(style_make(self.style_dict|self.extra_style_dict))
        else:
            self.extra_style_dict.pop(atuple('QPushButton', 'background-color'), None)
            self.extra_style_dict.pop(atuple('QPushButton:hover', 'background-color'), None)
            self.setStyleSheet(style_make(self.style_dict|self.extra_style_dict))

class AutoLabel(QLabel):
    def __init__(self, text:str, font:Union[QFont,atuple], style_config:atuple, icon_f:Union[str,atuple,QIcon]=None, 
                 height=None, width=None):
        super().__init__()
        if isinstance(text, str):
            self.setText(text)
        else:
            UIUpdater.set(text, self.setText)
        UIUpdater.set(height, self.setFixedHeight, type_f='height')
        UIUpdater.set(width, self.setFixedWidth, type_f='width')
        UIUpdater.set(font, self.setFont, type_f='font')
        UIUpdater.set(icon_f, self.set_icon, type_f='icon')
        self.extra_style_dict = {}
        self.style_config = style_config
        self.cl_pointer = style_config | atuple(['background_colors'])
        self.style_ctl = self.customStyle(style_config)
        self.setAlignment(Qt.AlignCenter)

    @dynamic_load(type_f='style')
    def customStyle(self, format_dict:dict, escape_sign:dict={}):
        bg_color = Udata(atuple('background_colors'), ['transparent', 'transparent', 'transparent'])
        border_radius = Udata(atuple('border_radius'), [10,10,10,10])
        border = Udata(atuple('border'), 'none')
        padding = Udata(atuple('padding'), [5,5,5,5])
        text_align = Udata(atuple('text_align'), 'left')
        temp_dict = {
            'QLabel': {
                'background-color': bg_color[0],
                'border-top-left-radius': border_radius[0],
                'border-top-right-radius': border_radius[1],
                'border-bottom-right-radius': border_radius[2],
                'border-bottom-left-radius': border_radius[3],
                'border': border,
                'padding': padding,
                'text-align': text_align,
            },
            'QLabel::hover': {
                'background-color': bg_color[1],
            },
            'QLabel::pressed': {
                'background-color': bg_color[2],
            }
        }
        if not hasattr(self, 'style_dict'):
            self.style_dict = {}
        self.style_dict = process_style_dict(self.style_dict, temp_dict, escape_sign, format_dict)
        self.setStyleSheet(style_make(self.style_dict|self.extra_style_dict))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            color_l = UIUpdater.get(self.cl_pointer, [])
            if isinstance(color_l, list) and len(color_l) == 3:
                self.extra_style_dict[atuple('QLabel', 'background-color')] = color_l[-1]
                self.extra_style_dict[atuple('QLabel::hover', 'background-color')] = color_l[-1]
                self.setStyleSheet(style_make(self.style_dict|self.extra_style_dict))
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.extra_style_dict.pop(atuple('QLabel', 'background-color'), None)
            self.extra_style_dict.pop(atuple('QLabel::hover', 'background-color'), None)
            self.setStyleSheet(style_make(self.style_dict|self.extra_style_dict))
        super().mouseReleaseEvent(event)
    
    def setSelected(self, selected:bool):
        if selected:
            color_l = UIUpdater.get(self.cl_pointer, [])
            if isinstance(color_l, list) and len(color_l) == 3:
                self.extra_style_dict[atuple('QLabel', 'background-color')] = color_l[-1]
                self.extra_style_dict[atuple('QLabel::hover', 'background-color')] = color_l[-1]
                self.setStyleSheet(style_make(self.style_dict|self.extra_style_dict))
        else:
            self.extra_style_dict.pop(atuple('QLabel', 'background-color'), None)
            self.extra_style_dict.pop(atuple('QLabel::hover', 'background-color'), None)
            self.setStyleSheet(style_make(self.style_dict|self.extra_style_dict))

    def set_icon(self, icon:Union[str,QIcon]):
        if isinstance(icon, str):
            self.setPixmap(QPixmap(icon))
        elif isinstance(icon, QIcon):
            self.setPixmap(icon.pixmap(-1,-1))

    def setBgColor(self, color:str):
        self.extra_style_dict[atuple('QLabel', 'background-color')] = color
        self.extra_style_dict[atuple('QLabel::hover', 'background-color')] = color
        self.setStyleSheet(style_make(self.style_dict|self.extra_style_dict))

class NameTag(QLabel):
    def __init__(self, font:QFont, style_config:atuple, height:int=None, width:int=None):
        super().__init__()
        UIUpdater.set(font, self.setFont, type_f='font')
        self.extra_style_dict = {}
        self.style_ctl = self.customStyle(style_config)
        if height is not None:
            UIUpdater.set(height, self.setFixedHeight, type_f='height')
        if width is not None:
            UIUpdater.set(width, self.setFixedWidth, type_f='width')

    @dynamic_load(type_f='style')
    def customStyle(self, style_dict:dict, escape_sign:dict={}):
        bg_color = Udata(atuple('background_colors'), ['white', 'white', 'white'])
        font_color = Udata(atuple('font_color'), 'black')
        border_radius = Udata(atuple('border_radius'), 10)
        border = Udata(atuple('border'), 'none')
        padding = Udata(atuple('padding'), [10,0,5,5])
        text_align = Udata(atuple('text_align'), 'left')
        temp_dict = {
            'QLabel': {
                'background-color': bg_color[0],
                'color': font_color,
                'border-top-left-radius': border_radius[0],
                'border-top-right-radius': border_radius[1],
                'border-bottom-right-radius': border_radius[2],
                'border-bottom-left-radius': border_radius[3],
                'border': border,
                'padding': padding,
                'text-align': text_align,
            }
        }
        if not hasattr(self, 'style_dict'):
            self.style_dict = {}
        self.style_dict = process_style_dict(self.style_dict, temp_dict, escape_sign, style_dict)
        self.setStyleSheet(style_make(self.style_dict|self.extra_style_dict))

class AutoEdit(QLineEdit):
    geometry_signal = Signal(dict)
    def __init__(self, text='', font:atuple=None, style_d={}, height:atuple=None, width:atuple=None, disable_scroll:bool=True):
        super().__init__()
        self.extra_style_dict = {}
        self.scroll_step = 10  # 基础滚动步长
        self.scroll_acceleration = 1.5  # 滚动加速度
        self.max_scroll_step = 30  # 最大滚动步长
        self.disable_scroll = disable_scroll
        # 平滑滚动
        self.scroll_timer = QTimer(self)
        self.scroll_timer.timeout.connect(self._smooth_scroll)
        self.target_position = 0
        self.current_velocity = 0
        self.setText(text)
        UIUpdater.set(font, self.setFont, type_f='font')
        UIUpdater.set(height, self.setFixedHeight)
        if width is not None:
            UIUpdater.set(width, self.setFixedWidth)
        self.style_ctl = self.customStyle(style_d)
        self.cursor_paint_time = 0
        
    @dynamic_load(type_f='style')   
    def customStyle(self, style_dict:dict, escape_sign:dict={}):
        bg_color = Udata(atuple('background'), 'white')
        font_color = Udata(atuple('font_color'), 'black')
        border_radius = Udata(atuple('border_radius'), 10)
        border = Udata(atuple('border'), 'none')
        padding = Udata(atuple('padding'), [10,0,5,5])
        text_selected_color = Udata(atuple('text_selected_color'), '#2471A3')
        text_selected_font_color = Udata(atuple('text_selected_font_color'), None)
        placeholder_style = Udata(atuple('placeholder_font_style'), 'normal')
        placeholder_color = Udata(atuple('placeholder_color'), 'gray')
        temp_dict = {
            'QLineEdit': {
                'background-color': bg_color,
                'color': font_color,
                'border-top-left-radius': border_radius[0],
                'border-top-right-radius': border_radius[1],
                'border-bottom-right-radius': border_radius[2],
                'border-bottom-left-radius': border_radius[3],
                'border': border,
                'padding-left': padding[0],
                'padding-top': padding[1],
                'padding-right': padding[2],
                'padding-bottom': padding[3],
                'selection-background-color': text_selected_color,
                'selection-color': text_selected_font_color,
            },
            "QLineEdit::placeholder": {
                'color': placeholder_color,
                'font-style': placeholder_style,
            }
        }
        if not hasattr(self, 'style_dict'):
            self.style_dict = {}
        self.style_dict = process_style_dict(self.style_dict, temp_dict, escape_sign, style_dict)
        self.setStyleSheet(style_make(self.style_dict|self.extra_style_dict))
    
    def wheelEvent(self, event: QWheelEvent):
        if self.disable_scroll:
            super().wheelEvent(event)
            return
        text_width = self.fontMetrics().width(self.text())
        visible_width = self.width() - self.textMargins().left() - self.textMargins().right()
        if text_width <= visible_width:
            super().wheelEvent(event)
            return
        delta = event.angleDelta().y()
        scroll_amount = self.scroll_step * (1 if delta < 0 else -1)
        current_pos = self.cursorPosition()
        self.target_position = max(0, min(len(self.text()), 
                                        current_pos + scroll_amount))
        
        if not self.scroll_timer.isActive():
            self.scroll_timer.start(16)  
        event.accept()
    
    def _smooth_scroll(self):
        current_pos = self.cursorPosition()
    
        if current_pos == self.target_position:
            self.scroll_timer.stop()
            self.current_velocity = 0
            return
            
        # 计算新位置
        direction = 1 if self.target_position > current_pos else -1
        self.current_velocity = min(self.max_scroll_step, 
                                  abs(self.current_velocity + self.scroll_acceleration)) * direction
        
        new_pos = int(current_pos + self.current_velocity)
        new_pos = max(0, min(len(self.text()), new_pos))
        
        # 更新位置
        self.setCursorPosition(new_pos)
        
        # 如果接近目标位置，直接设置到目标位置
        if abs(new_pos - self.target_position) < abs(self.current_velocity):
            self.setCursorPosition(self.target_position)
            self.scroll_timer.stop()
            self.current_velocity = 0
            
    def setText(self, text: str):
        super().setText(text)
        self.setCursorPosition(len(self.text()))

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.hasFocus():
            self.cursor_paint_time +=1
            if self.cursor_paint_time % 2 == 0:
                color = '#943126' 
            else:
                color = 'transparent'
            painter = QPainter(self)
            rect = self.cursorRect()
            painter.fillRect(
                QRect(rect.x(), rect.y(), 5, rect.height()),
                color
            )

    def moveEvent(self, event):
        super().moveEvent(event)   
        self._emit_rec()

    def resizeEvent(self, event):
        super().resizeEvent(event)  
        self._emit_rec()

    def _emit_rec(self):
        point_ori = self.pos()
        point_new = self.mapToGlobal(QPoint(0,0))
        self.geometry_signal.emit({'abs':QRect(point_new.x(), point_new.y(), self.width(), self.height()), 'rel':QRect(point_ori.x(), point_ori.y(), self.width(), self.height())})

class WheelEdit(AutoEdit):
    wheel_signal = Signal(int)
    def __init__(self, text='', font:atuple=None, style_d={}, height:atuple=None, width:atuple=None):
        super().__init__(text=text, font=font, style_d=style_d, height=height, width=width)
        self.setReadOnly(True)
        self.setMouseTracking(True)
        self.setContextMenuPolicy(Qt.NoContextMenu)
    
    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.wheel_signal.emit(1)
        else:
            self.wheel_signal.emit(-1)

class ModeButton(YohoPushButton):
    textChanged = Signal(str)
    wheel_signal = Signal(int)
    def __init__(self, style_d, text_f='', font_f=None, height_f=None, color_state=0, parent=None):
        super().__init__(style_config=style_d, text_f=text_f, font_f=font_f, height_f=height_f)
        self.color_state = color_state
        UIUpdater.set(font_f, self.setFont, type_f='font')
        self.textChanged.connect(self._AutoResize)
        self.setText(text_f)
        UIUpdater.set(height_f, self.setFixedHeight, type_f='height')
        self.style_ctl.force_escape_sign = {atuple('background_colors'):True}

    def setText(self, text_f:str):
        super().setText(text_f)
        self.textChanged.emit(text_f)
    
    @Slot(str)
    def _AutoResize(self, text_f:str):
        size_ori = self.sizeHint().width() + 30
        self.setFixedWidth(size_ori)
    
    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.wheel_signal.emit(-1)
        else:
            self.wheel_signal.emit(1)

    def setBackgoundColors(self, colors:str|list[str]|atuple):
        if isinstance(colors, atuple):
            colors = UIUpdater.get(colors, default_v=None)
            if not colors:
                return
        colors = enlarge_list(colors, 3)
        self.style_ctl.force_escape_sign[atuple('background_colors')] = True
        self.extra_style_dict[atuple('QPushButton', 'background-color')] = colors[0]
        self.extra_style_dict[atuple('QPushButton::hover', 'background-color')] = colors[1]
        self.extra_style_dict[atuple('QPushButton::pressed', 'background-color')] = colors[2]
        self.setStyleSheet(style_make(self.style_dict|self.extra_style_dict))

class ModeListWidget(QListWidget):
    def __init__(self, style_d, max_height=None, font_f=None, parent=None, color_state=0):
        self.color_state = color_state
        if parent is None:
            super().__init__()
        else:
            super().__init__(parent=parent)
        self.default_item_margin = 1
        self.deault_extra_height = 35
        self.deault_extra_width = 80
        UIUpdater.set(font_f, self.setFont, type_f='font')
        self.setWindowFlags(Qt.FramelessWindowHint)  
        self.style_ctl = self.customStyle(style_d)
        self.scrollbar_style()
        UIUpdater.set(max_height, self.setMaximumHeight, type_f='height')

    @dynamic_load(type_f='style')
    def customStyle(self, style_d:dict, escape_sign:dict={}):
        '''
        self.color_state: decide color group to use
        mainly influence background and font color
        0: default, don't use color_state
        1: use background_colors_1 and font_colors_1
        2: use background_colors_2 and font_colors_2
        '''
    
        menu_border = Udata(atuple('menu', 'border'), 'none')
        menu_border_radius = Udata(atuple('menu', 'border_radius'), 10)
        menu_padding = Udata(atuple('menu', 'padding'), 5)
        menu_bg = Udata(atuple('menu', 'background'), 'rgba(255, 255, 255, 80)')
        
        style_f = dicta.flatten_dict(style_d)
        self.extra_height = style_f.get(atuple('item','extra_height'), self.deault_extra_height)
        self.extra_width = style_f.get(atuple('item','extra_width'), self.deault_extra_width)
        self.item_height = style_f.get(atuple('item','item_height'), 60)
        self.item_spacing = style_f.get(atuple('item','spacing'), 1)
        self.setSpacing(self.item_spacing)
        item_margin = Udata(atuple('item', 'margin'), 1)
        bg_colors = Udata(atuple('item', 'background_colors'), ['#2C51C1', '#FFC300', '#FF5733'])
        font_colors = Udata(atuple('item', 'font_colors'), ['#000000', '#000000', '#000000'])
        border = Udata(atuple('item', 'border'), 'none')
        border_radius = Udata(atuple('item', 'border_radius'), 10)
        padding = Udata(atuple('item', 'padding'), [10, 5, 5, 5])

        temp_dict = {
            'QListWidget':{
                'background-color': menu_bg,
                'border': menu_border,
                'padding': menu_padding,
                'border-top-left-radius': menu_border_radius[0],
                'border-top-right-radius': menu_border_radius[1],
                'border-bottom-right-radius': menu_border_radius[2],
                'border-bottom-left-radius': menu_border_radius[3],
            },
            'QListWidget::item':{
                'background-color': bg_colors[0],
                'color': font_colors[0],
                'padding': padding,
                'margin': item_margin,
                'border': border,
                'border-top-left-radius': border_radius[0],
                'border-top-right-radius': border_radius[1],
                'border-bottom-right-radius': border_radius[2],
                'border-bottom-left-radius': border_radius[3],
            },
            'QListWidget::item:hover':{
                'background-color': bg_colors[1],
                'color': font_colors[1],
            },
            'QListWidget::item:selected':{
                'background-color': bg_colors[2],
                'color': font_colors[2],
            },
        }
        if not hasattr(self, 'style_dict'):
            self.style_dict = {}
        self.style_dict = process_style_dict(self.style_dict, temp_dict, escape_sign, style_d)
        self.setStyleSheet(style_make(self.style_dict))

    def scrollbar_style(self):
        self.ver_style = """
            QScrollBar:vertical {
                width: 0px;  /* 设置垂直滚动条的宽度 */
                background: transparent;  /* 设置背景颜色 */
            }
            QScrollBar::handle:vertical {
                background: transparent;  /* 设置滚动条滑块的颜色 */
                border-radius: 0px;   /* 设置滑块的圆角 */
            }
            QScrollBar::add-line:vertical, 
            QScrollBar::sub-line:vertical {
                background: none;  /* 隐藏上下箭头 */
            }
            QScrollBar::add-page:vertical, 
            QScrollBar::sub-page:vertical {
                background: none;  /* 隐藏滚动条的背景 */
            }
        """
        self.hor_style = """
            QScrollBar:horizontal {
                height: 0px;
                background: transparent;
            }
            QScrollBar::handle:horizontal {
                background: transparent;
                border-radius: 0px;
            }
            QScrollBar::add-line:horizontal, 
            QScrollBar::sub-line:horizontal {
                background: none;
            }
            QScrollBar::add-page:horizontal, 
            QScrollBar::sub-page:horizontal {
                background: none;
            }
        """
        self.horizontalScrollBar().setStyleSheet(self.hor_style)
        self.verticalScrollBar().setStyleSheet(self.ver_style)

    def get_size(self):
        width_l = [self.fontMetrics().width(self.item(i).text()) for i in range(self.count())]
        height_l = [self.fontMetrics().height() for i in range(self.count())]
        width_n = max(width_l) + self.extra_width
        height_i = max(height_l) 
        height_n = height_i*(self.count())+ self.extra_height+self.item_spacing*(self.count()-1)
        for i in range(self.count()):
            self.item(i).setSizeHint(QSize(width_n-10, height_i))
        return width_n, height_n
    
    def get_max_width(self):
        return self.get_size()[0]
    
    def get_max_height(self):
        return self.get_size()[1]

class CustomComboBox(QWidget):
    index_changed = Signal(int)
    def __init__(self, modes:list, style_d:dict, box_height=None, box_font=QFont(), menu_font=QFont(),
                 parent:QMainWindow=None):
        super().__init__(parent)
        self.color_state = 0 
        self.up = parent
        self.modes = modes
        self.default_an_time = 300
        self.enable_wheel_event = True
        self.style_d = style_d
        self.box_height = box_height
        self.box_font = box_font
        self.menu_font = menu_font
        self.initUI()
        self.setStyleSheet('''background-color: transparent;''')
        
    def initUI(self):
        # Layout
        self.layout0 = QVBoxLayout(self)
        self.layout0.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout0) 

        # Create line edit for display
        self.box_w = ModeButton(self.style_d, text_f='', font_f=self.box_font, height_f=self.box_height, color_state=self.color_state)
        self.box_w.clicked.connect(self.show_menu)
        self.box_w.wheel_signal.connect(self.wheel_signal_receiver)

        # Create list widget for dropdown
        self.menu_w = ModeListWidget(style_d=self.style_d, font_f=self.menu_font, parent=self.up, color_state=self.color_state)
        self.menu_w.hide()
        for mode in self.modes:
            self.add_item(mode)
        # self.menu_w.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.menu_w.setFixedSize(*self.menu_w.get_size())

        # Connect signals
        self.menu_w.itemClicked.connect(self.menu_click)
        add_obj(self.box_w, parent_f=self.layout0)

    def add_item(self, text):
        self.menu_w.addItem(text)
        if not self.box_w.text():
            self.box_w.setText(text)

    def show_menu(self):
        if self.menu_w.isVisible():
            self.menu_w.hide()
            return
        
        box_g = self.box_w.geometry()
        uper_g = self.geometry()
        x_n = box_g.x() + uper_g.x()
        y_n = box_g.y() + uper_g.y() + self.box_w.height() - 5
        self.menu_w.setFixedSize(*self.menu_w.get_size())
        # pos = self.box_w.geometry()
        self.menu_w.setGeometry(
            x_n, 
            y_n,
            self.menu_w.get_size()[0],
            0
        )
        self.menu_w.show()
        self.menu_animation()
        
    def menu_animation(self):
        self.animation = QPropertyAnimation(self.menu_w, b"geometry")
        self.animation.setDuration(self.default_an_time)
        # width_n = self.menu_w.get_max_width()
        start_rect = QRect(self.menu_w.x(), self.menu_w.y(), self.menu_w.get_size()[0], 0)
        end_rect = QRect(self.menu_w.x(), self.menu_w.y(), self.menu_w.get_size()[0], self.menu_w.get_size()[1])
        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        self.animation.start()
        self.menu_w.raise_()

    def menu_click(self, item):
        if self.menu_w.isVisible():
            index = self.modes.index(item.text())
            self.setIndex(index)
            self.menu_w.hide()
            item.setSelected(False)

    def setFixedWidth(self, w):
        self.box_w.setFixedWidth(w)
        # self.menu_w.setFixedWidth(w)
        return super().setFixedWidth(w)

    def setIndex(self, index:int):
        index = max(0, min(index, len(self.modes)-1))
        if index == self.getIndex():
            return
        self.box_w.setText(self.modes[index])
        self.index_changed.emit(index)
    
    def getIndex(self):
        return self.modes.index(self.box_w.text())
    
    def getMode(self, index_f:int=None):
        if index_f is None:
            return self.box_w.text()
        else:
            return self.modes[index_f]
    
    def wheel_signal_receiver(self, sign:int):
        if not self.enable_wheel_event:
            return
        index_n = self.getIndex()
        index_n += sign
        self.setIndex(index_n)
    
    def setWidth(self, text_f:str):
        text_f = self.box_w.text()
        line_edit_font = self.box_w.font()
        font_metrics = QFontMetrics(line_edit_font)
        text_width = font_metrics.width(text_f) + 70
        self.setFixedWidth(text_width)

    def setEnableWheelEvent(self, enable:bool):
        self.enable_wheel_event = enable

class PolygonWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_shapes()  # 初始化多边形和圆形
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_positions)
        self.timer.start(50)  # 每50毫秒更新一次位置

        # 每隔一段时间随机改变方向
        self.change_direction_timer = QTimer(self)
        self.change_direction_timer.timeout.connect(self.change_directions)
        self.change_direction_timer.start(2000)  # 每2秒改变一次方向

        # 添加模糊效果
        blur_effect = QGraphicsBlurEffect(self)
        blur_effect.setBlurRadius(100)
        self.setGraphicsEffect(blur_effect)

    def init_shapes(self):
        """初始化固定形状、颜色的多边形和圆形，以及它们的速度向量"""
        # 初始化多边形
        self.polygons = [
            {"polygon": QPolygonF([QPointF(0, 0), QPointF(600, 0), QPointF(600, 500), QPointF(0, 500)]), "color": QColor("#17AAAE")},
            {"polygon": QPolygonF([QPointF(10, 150), QPointF(200, 150), QPointF(175, 200)]), "color": QColor("#7015AE")},
            {"polygon": QPolygonF([QPointF(10, 250), QPointF(300, 250), QPointF(275, 300)]), "color": QColor("#C312A9")}
        ]

        # 初始化圆形（定义圆的圆心和半径）
        self.circles = [
            {"center": QPointF(50, 50), "radius": 40, "color": QColor("#FF5733")}
        ]

        # 初始位移量（所有形状的初始位移设为0）
        self.offsets = [QPointF(0, 0), QPointF(0, 0), QPointF(0, 0)]
        self.circle_offsets = [QPointF(0, 0)]  # 圆形的初始位移

        # 初始速度向量 (vx, vy) 均匀运动
        self.velocities = [
            QPointF(random.randint(-5, 5), random.randint(-5, 5)),
            QPointF(random.randint(-5, 5), random.randint(-5, 5)),
            QPointF(random.randint(-5, 5), random.randint(-5, 5))
        ]
        self.circle_velocities = [
            QPointF(random.randint(-5, 5), random.randint(-5, 5))
        ]  # 圆形的速度向量

    def change_directions(self):
        """每隔一定时间随机改变一次速度向量"""
        for i in range(len(self.velocities)):
            self.velocities[i] = QPointF(random.randint(-5, 5), random.randint(-5, 5))
        for i in range(len(self.circle_velocities)):
            self.circle_velocities[i] = QPointF(random.randint(-5, 5), random.randint(-5, 5))

    def update_positions(self):
        """更新多边形和圆的位置（均匀运动）"""
        # 更新多边形
        for i in range(len(self.polygons)):
            self.offsets[i] += self.velocities[i]
            # 判断边界，超出视野重置到中心
            translated_polygon = self.polygons[i]["polygon"].translated(self.offsets[i])
            centroid = self.calculate_centroid(translated_polygon)
            if self.is_out_of_bounds(centroid):
                window_center = QPointF(self.width() / 2, self.height() / 2)
                reset_offset = window_center - centroid
                self.offsets[i] += reset_offset  # 更新偏移量

        # 更新圆的位置
        for i in range(len(self.circles)):
            self.circle_offsets[i] += self.circle_velocities[i]
            center_with_offset = self.circles[i]["center"] + self.circle_offsets[i]
            if self.is_out_of_bounds(center_with_offset):
                window_center = QPointF(self.width() / 2, self.height() / 2)
                reset_offset = window_center - center_with_offset
                self.circle_offsets[i] += reset_offset  # 更新偏移量

        self.update()  # 触发窗口重绘

    def calculate_centroid(self, polygon):
        """计算多边形的重心"""
        x_coords = [point.x() for point in polygon]
        y_coords = [point.y() for point in polygon]
        centroid_x = sum(x_coords) / len(polygon)
        centroid_y = sum(y_coords) / len(polygon)
        return QPointF(centroid_x, centroid_y)

    def is_out_of_bounds(self, centroid):
        """判断重心或圆心是否超出窗口视野"""
        rect = self.rect()  # 获取窗口的矩形区域
        return not rect.contains(centroid.toPoint())  # 将 QPointF 转换为 QPoint

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 清除上一次的绘图（填充背景色）
        painter.fillRect(self.rect(), Qt.white)  # 使用白色背景清空之前的绘制内容
        
        # 绘制多边形（应用位移）
        for i, poly_data in enumerate(self.polygons):
            polygon = poly_data["polygon"]
            color = poly_data["color"]
            offset = self.offsets[i]
            translated_polygon = polygon.translated(offset)
            painter.setBrush(color)
            painter.drawPolygon(translated_polygon)

        # 绘制圆形（应用位移）
        for i, circle_data in enumerate(self.circles):
            center = circle_data["center"]
            radius = circle_data["radius"]
            color = circle_data["color"]
            offset = self.circle_offsets[i]
            painter.setBrush(color)
            painter.drawEllipse(center + offset, radius, radius)  # 绘制圆形

class ProgressBar(QProgressBar):
    def __init__(self, parent:QMainWindow, 
                 style_d:dict,  
                 max_value:float=100, 
                 height:int=10, 
                 ):
        super().__init__(parent)
        self.extra_style_dict = {}
        self.max_value = max_value
        self.setRange(0, max_value)  
        self.setValue(0)  
        UIUpdater.set(height, self.setFixedHeight, 'height')
        self.style_ctl = self.customStyle(style_d)
        self.setTextVisible(False)
        

    def update(self, value_add:int):
        self.setValue(self.value()+value_add)
    
    @dynamic_load(type_f='style')
    def customStyle(self, style_d:dict, escape_sign:dict={}):
        bg_color = Udata(atuple('background'), 'rgba(255, 255, 255, 100)')
        bar_color = Udata(atuple('bar_color'), 'rgba(255, 255, 255, 100)')
        border_radius = Udata(atuple('border_radius'), 6)
        border = Udata(atuple('border'), '1px solid rgba(255, 255, 255, 100)')
        temp_dict = {
            'QProgressBar':{
                'background-color': bg_color,
                'border-top-left-radius': border_radius[0],
                'border-top-right-radius': border_radius[1],
                'border-bottom-left-radius': border_radius[2],
                'border-bottom-right-radius': border_radius[3],
                'border': border,
            },
            'QProgressBar::chunk':{
                'background-color': bar_color,
                'border-top-left-radius': border_radius[0],
                'border-top-right-radius': border_radius[1],
                'border-bottom-left-radius': border_radius[2],
                'border-bottom-right-radius': border_radius[3],
            }
        }
        if not hasattr(self, 'style_dict'):
            self.style_dict = {}
        self.style_dict = process_style_dict(self.style_dict, temp_dict, escape_sign, style_d)
        self.setStyleSheet(style_make(self.style_dict|self.extra_style_dict))

class SmartStackWidget(QStackedWidget):
    in_animation_signal = Signal(bool)
    def __init__(self, parent:QWidget,an_time=200):
        super().__init__(parent)
        self.an_time = an_time

        self._load()
        self.in_animation = False
    
    def _load(self):
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1)  # 初始透明度

    # def wheelEvent(self, event):
    #     current_index = self.currentIndex()
    #     num_pages = self.count()
    #     if event.angleDelta().y() > 0:  # 向上滚动
    #         new_index = (current_index + 1) % num_pages
    #     else:  
    #         new_index = (current_index - 1 + num_pages) % num_pages
    #     self.setCurrentIndex(new_index)

    def remove_page(self, index:int):
        index_n = self.currentIndex()
        if index == index_n:
            self.setCurrentIndex((index_n+1 ) % self.count())
        widget_to_rm = self.widget(index)
        self.removeWidget(widget_to_rm)
        widget_to_rm.deleteLater()
    
    def animate_transition(self, index: int, sign: int):
        if self.in_animation:
            return
        self.in_animation_signal.emit(True)
        self.in_animation = True
        current_widget = self.widget(self.currentIndex())
        next_widget = self.widget(index)

        # current_widget.setGeometry(self.geometry())
        # next_widget.setGeometry(self.geometry())

        ori_pos = current_widget.geometry()
        animation_group = QParallelAnimationGroup(self)
        self.current_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.current_animation.setDuration(self.an_time//3)
        self.current_animation.setStartValue(1)
        self.current_animation.setKeyValueAt(0.2, 0.5)
        self.current_animation.setKeyValueAt(0.8, 0.4)
        self.current_animation.setEndValue(0)
        # current_animation.setEndValue(QRect(0, 0, current_widget.width(), current_widget.height()))
        self.current_animation.setEasingCurve(QEasingCurve.OutQuad)

        next_animation = QPropertyAnimation(next_widget, b"geometry")
        next_animation.setDuration(2*self.an_time//3)
        if sign > 0:
            next_animation.setStartValue(QRect(self.width(), 0, self.width()-5, self.height()-5))
        else:
            next_animation.setStartValue(QRect(-self.width(), 0, self.width()-5, self.height()-5))
        next_animation.setEndValue(QRect(0, 0, self.width(), self.height()))
        next_animation.setEasingCurve(QEasingCurve.OutCubic)

        next_animation2 = QPropertyAnimation(self.opacity_effect, b"opacity")
        next_animation2.setDuration(2*self.an_time//3)
        next_animation2.setStartValue(0)
        next_animation2.setEndValue(1)
        animation_group.addAnimation(next_animation)
        animation_group.addAnimation(next_animation2)
        next_animation.setEasingCurve(QEasingCurve.OutCubic)

        # animation_group.addAnimation(current_animation)
        # animation_group.start()
        self.current_animation.start()
        self.current_animation.finished.connect(lambda: self.animation_later(current_widget, next_widget, animation_group, sign))

    def animation_later(self, current_widget, next_widget, later_animation,sign):
        current_widget.hide()
        next_widget.hide()
        self.opacity_effect.setOpacity(1)
        self.setCurrentWidget(next_widget)
        if sign > 0:
            next_widget.setGeometry(QRect(self.width(), 0, self.width()-5, self.height()-5))
        else:
            next_widget.setGeometry(QRect(-self.width(), 0, self.width()-5, self.height()-5))
        next_widget.show()

        self.l_animation = later_animation

        self.l_animation.start()
        self.l_animation.finished.connect(self.animation_end)

    def animation_end(self):
        self.in_animation = False
        self.in_animation_signal.emit(False)

    # def wheelEvent(self, event):
    #     if event.angleDelta().y() > 0:
    #         self.setIndex(self.currentIndex()-1)
    #     else:
    #         self.setIndex(self.currentIndex()+1)

    def setIndex(self, index):
        index = min(max(0, index), self.count()-1)
        if index != self.currentIndex():
            if index < self.currentIndex():
                self.animate_transition(index, sign=-1)
            else:
                self.animate_transition(index, sign=1)
            #self.setCurrentIndex(index)

class TipButton(QPushButton):
    def __init__(self, style_d:dict, text_f:str, font_f:QFont=QFont(), width_f=None, height_f=None, radius_set:List[bool]=[True, True, True, True]):
        super().__init__()
        UIUpdater.set(text_f, self.setText, 'text')
        UIUpdater.set(font_f, self.setFont, 'font')
        UIUpdater.set(width_f, self.setFixedWidth, 'width')
        UIUpdater.set(height_f, self.setFixedHeight, 'height')
        self.radius_set = radius_set
        self.style_ctl = self.customStyle(style_d)

    @dynamic_load(type_f='style')
    def customStyle(self, style_d:dict, escape_sign:dict={}):
        bg_colors = Udata(atuple('background_colors'), ['#F7F7F7', '#FFC300', '#FF5733'])
        font_colors = Udata(atuple('font_colors'), ['#000000', '#000000', '#000000'])
        border = Udata(atuple('border'), 'none')
        border_radius = Udata(atuple('border_radius'), 6)
        padding = Udata(atuple('padding'), [5, 5, 5, 5])
        temp_dict = {}
        self.style_dict = {
            'QPushButton':{
                'background-color': bg_colors[0],
                'color': font_colors[0],
                'border': border,
                'border-top-left-radius': border_radius[0],
                'border-top-right-radius': border_radius[1],
                'border-bottom-left-radius': border_radius[2],
                'border-bottom-right-radius': border_radius[3],
                'padding': padding,
            },
            'QPushButton::hover':{
                'background-color': bg_colors[1],
                'color': font_colors[1],
            },
            'QPushButton::pressed':{
                'background-color': bg_colors[2],
                'color': font_colors[2],
            },
        }
        self.style_sheet = style_make(self.style_dict)
        self.setStyleSheet(self.style_sheet)

class AutoMenu(QWidget):
    action_signal = Signal(dict)
    def __init__(self, main_style_d:dict, item_style_d:dict, actions:list[str], values:list[dict], font:QFont=QFont(), width_f=None, height_f=None):
        super().__init__()
        self.height_f = height_f
        self.action_l = actions
        self.value_l = values
        self.item_style_d = item_style_d
        self.button_list = []
        self.main_style_ctl = self.customStyle(main_style_d)
        self.extra_width = main_style_d | atuple('extra_width')
        self.extra_height = main_style_d | atuple('extra_height')

        self.font_f = font
        self.setWindowFlags(self.windowFlags()|Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setAttribute(Qt.WA_TranslucentBackground)  # 设置窗口属性为透明
        # self.setWindowOpacity(1)
        self._init_action()
        UIUpdater.set(self.font_f, self.setFont, 'font')
        # self.move_signal.connect(self.async_Move)
        self.relative_position = QPoint(0, 0)
        self.exit_sign = 'hide'
    
    def eventFilter(self, obj, event):
        if self.isVisible():
            if event.type() == QEvent.ActivationChange:
                if not self.isActiveWindow():
                    self.am_exit()
            elif event.type() == QEvent.MouseButtonPress:
                if not self.geometry().contains(event.globalPos()):
                    self.am_exit()
        return super().eventFilter(obj, event)
    
    @dynamic_load(type_f='style')
    def customStyle(self, style_d:dict, escape_sign:dict={}):
        background = Udata(atuple('background'), 'transparent')
        border = Udata(atuple('border'), 'none')
        border_radius = Udata(atuple('border_radius'), 10)
        temp_dict = {
            'QWidget':{
                'background-color': background,
                'border': border,
                'border-top-left-radius': border_radius[0],
                'border-top-right-radius': border_radius[1],
                'border-bottom-left-radius': border_radius[2],
                'border-bottom-right-radius': border_radius[3],
            }
        }
        if not hasattr(self, 'style_dict'):
            self.style_dict = {}
        if not hasattr(self, 'extra_style_dict'):
            self.extra_style_dict = {}
        self.style_dict = process_style_dict(self.style_dict, temp_dict, escape_sign, style_d)
        self.setStyleSheet(style_make(self.style_dict|self.extra_style_dict))

    def _init_action(self)->None:
        self.layout_0 = amlayoutV(align_h='l')
        self.setLayout(self.layout_0)
        spacing_f = self.item_style_d | atuple('spacing')
        UIUpdater.set(spacing_f, self.layout_0.setSpacing, 'spacing')
        for i, action_i in enumerate(self.action_l):
            button_i = YohoPushButton(style_config=self.item_style_d, text_f=action_i, font_f=self.font_f)
            button_i.extra_style_dict[atuple('QPushButton', 'text-align')] = 'left'
            if len(self.action_l) == 1:
                pass
            elif i == 0:
                button_i.extra_style_dict[atuple('QPushButton', 'border-bottom-left-radius')] = 0
                button_i.extra_style_dict[atuple('QPushButton', 'border-bottom-right-radius')] = 0
            elif i == len(self.action_l)-1:
                button_i.extra_style_dict[atuple('QPushButton', 'border-top-left-radius')] = 0
                button_i.extra_style_dict[atuple('QPushButton', 'border-top-right-radius')] = 0
            else:
                button_i.extra_style_dict[atuple('QPushButton', 'border-top-left-radius')] = 0
                button_i.extra_style_dict[atuple('QPushButton', 'border-top-right-radius')] = 0
                button_i.extra_style_dict[atuple('QPushButton', 'border-bottom-left-radius')] = 0
                button_i.extra_style_dict[atuple('QPushButton', 'border-bottom-right-radius')] = 0
            style_d = style_make(button_i.style_dict|button_i.extra_style_dict)
            button_i.setStyleSheet(style_d)
            self.layout_0.addWidget(button_i)
            button_i.clicked.connect(lambda: self.emit_action(i))
            self.button_list.append(button_i)
        # update the position offset of the menu
        self.x_offset = self.item_style_d | atuple('display_x_offset')
        self.y_offset = self.item_style_d | atuple('display_y_offset')
        UIUpdater.set(alist(self.x_offset, self.y_offset), self._load_offset, alist())
        paras = alist(spacing_f, self.height_f, self.extra_width, self.extra_height)
        UIUpdater.set(paras, self.set_size, alist())
    
    def _load_offset(self, x_offset:int, y_offset:int):
        self.x_offset = x_offset
        self.y_offset = y_offset

    def action(self, index:int, relative_position:QPoint, parent_pos:QPoint=QPoint(0, 0))->None:
        self.tab_index = index
        self.relative_position = relative_position
        # self.set_size()
        x = self.relative_position.x() + parent_pos.x()+self.x_offset
        y = self.relative_position.y() + parent_pos.y()+self.y_offset
        self.move(x, y)
        self.show()
        self.raise_()
        QApplication.instance().installEventFilter(self)

    def emit_action(self, index_f:dict):
        self.action_signal.emit(self.value_l[index_f])
        self.hide()

    def am_exit(self):
        try:
            QApplication.instance().removeEventFilter(self)
        except Exception:
            pass
        if self.exit_sign == 'hide':
            self.hide()
        else:
            self.close()

    def set_width(self, extra_width:int):
        width_f = max(QFontMetrics(self.button_list[0].font()).width(action_i) for action_i in self.action_l)+extra_width
        for button_i in self.button_list:
            button_i.setFixedWidth(width_f)
        self.setFixedWidth(width_f+30)

    def set_height(self, extra_height:int):
        spacing_f = self.item_style_d | atuple('spacing')
        height_t = self.height_f*len(self.button_list)+spacing_f*(len(self.button_list)-1)+extra_height
        self.setFixedHeight(height_t+5)
        pass

    def set_size(self, spacing_f:int, height_f:int, extra_width:int, extra_height:int):
        # spacing_f = UIUpdater.get(self.item_style_d|atuple('spacing'), 0)
        # height_f = UIUpdater.get(self.height_f, 60)
        # extra_width = UIUpdater.get(self.extra_width, 10)
        # extra_height = UIUpdater.get(self.extra_height, 10)
        width_f = max(QFontMetrics(self.button_list[0].font()).width(action_i) for action_i in self.action_l)+extra_width
        for button_i in self.button_list:
            button_i.setFixedSize(width_f, height_f)
        height_t = height_f*len(self.button_list)+spacing_f*(len(self.button_list)-1)+extra_height
        self.setFixedWidth(width_f+50)
        self.setFixedHeight(height_t+5)

    def hide(self):
        self.action_signal.emit({})
        super().hide()

class ScrollArea(QScrollArea):
    def __init__(self, parent:QWidget, frame_d:dict, scroll_area_d:dict, line_spaing:int):
        super().__init__(parent)
        self.line_spaing = line_spaing
        self.frame_d = frame_d
        self.scroll_area_d = scroll_area_d
        self.setObjectName("myScrollArea")
        self._initUI()
    
    def _initUI(self)->None:
        self.obj_layout = amlayoutV()
        self.setLayout(self.obj_layout)
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
        self.frame_ctl = self.customFrameStyle(self.frame_d)
        self.scroll_area_ctl = self.customScrollAreaStyle(self.scroll_area_d)

        self.setWidget(self.frame)  # Set the frame as the widget of the scroll area
        self.setWidgetResizable(True)

    
    @dynamic_load(type_f='style')
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

    @dynamic_load(type_f='style')
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
        self.setStyleSheet(style_make(self.scroll_area_style_dict|self.extra_scroll_area_style_dict))
