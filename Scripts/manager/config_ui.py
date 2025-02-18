from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *
from sympy import symbols, sympify
import math
from typing import Union, Callable, Any
import inspect
import types
# local import 
from ..tools.toolbox import *
from .. import global_var as GV



class Asize(QSize):
    def __init__(self, width:int, height:int):
        super().__init__(width, height)
    def __mul__(self, c:Union[int, float]):
        return QSize(int(self.width()*c), int(self.height()*c))
    def q(self):
        return QSize(self.width(), self.height())

class AIcon(QIcon):
    def __init__(self, file_path):
        if isinstance(file_path, atuple):
            self.file_path = UIUpdater.get(file_path,'')
            super().__init__(self.file_path)
        elif isinstance(file_path, str):
            self.file_path = file_path
            super().__init__(file_path)
        else:
            self.file_path = ''
            super().__init__(file_path)
        
    def get_file_path(self):
        return self.file_path
    def q(self):
        QIcon(self.file_path)

class APixmap(QPixmap):
    def __init__(self, size:int|tuple[int, int]=None):
        if size is None:
            super().__init__()
        else:
            self.size_f = size if isinstance(size, tuple) else (size, size)
            super().__init__(*self.size_f)

    def save(self, file_path:str):
        return super().save(file_path, quality=100)
    
    def icon(self):
        return QIcon(self)

class Config_Manager(object):
    @classmethod
    def set_config_path(cls,yaml_path:str):
        if not hasattr(cls, 'config'):
            config = yml.read(yaml_path)
            cls.config = dicta.flatten_dict(config)
            cls.yaml_path = yaml_path
            config_0 = cls._calSize(cls.config)
            config_1 = dicta.unflatten_dict(config_0)
            cls.config = adict(config_1)
    
    def __init__(self, 
                 wkdir:str,
                 mode_name:str=None, 
                 widget_name:str=None, 
                 obj_name:str=None,
                 copy:bool=False):
        self.wkdr = wkdir
        self.mode = mode_name
        self.widget = widget_name
        self.obj = obj_name
        self.pre = []
    
    def deepcopy(self):
        new_copy = Config_Manager(self.wkdr, None, None, None, True)
        return new_copy
    @staticmethod
    def _calSize(config:dict):
        scr_x, scr_y = get_screen_size('pixel')
        res_x = math.sqrt(scr_x*scr_y/(2560*1600))
        res_y = res_x
        # resize 
        targets = ['win_x', "win_y", "gap", "het", "srh_r"]
        default_size = [1600,900,60,60,80]
        base_d = {}
        for i, target_i in enumerate(targets):
            value_i = config.get(('Common','Size',target_i),default_size[i])
            value_f = int(res_x*value_i)
            base_d[target_i] = value_f
        base_d = base_d | {'scr_x':scr_x, 'scr_y':scr_y, 'res_x':res_x, 'res_y':res_y}
        for key_i, value_i in config.items():
            if "Size" in key_i:
                config[key_i] = Config_Manager._str2int(value_i, base_d)
        return config
    
    def _calculate_legacy(self):
        self.scr_x, self.scr_y = get_screen_size('pixel')
        res_x = math.sqrt(self.scr_x*self.scr_y/(2560*1600))
        res_y = res_x
        # resize 
        targets = ['win_x', "win_y", "gap", "het", "srh_r"]
        for target_i in targets:
            value_i = self.config[('Common','Size',target_i)]
            value_f = int(res_x*value_i)
            self.config[('Common','Size',target_i)] = value_f
            setattr(self, target_i, value_f)
        
        for key_i, value_i in self.config.items():
            if "Size" in key_i:
                self.config[key_i] = self._str2int(value_i)

    @staticmethod
    def _str2int(input_f:Union[list, str], base_d:dict):
        scr_x, scr_y, win_x, win_y, gap, het, srh_r= symbols('scr_x scr_y win_x win_y gap het srh_r')
        values = {
                scr_x: base_d['scr_x'],
                scr_y: base_d['scr_y'],
                win_x: base_d['win_x'],
                win_y: base_d['win_y'],
                gap: base_d['gap'],
                het: base_d['het'],
                srh_r: base_d['srh_r'],
                }
        if isinstance(input_f, list):
            results = [int(sympify(expr).evalf(subs=values)) for expr in input_f]
            return results
        elif isinstance(input_f, str):
            return int(sympify(input_f).evalf(subs=values))
        else:
            return input_f
    
    def group_chose(self, mode="_", widget="_", obj="_"):
        self.mode = mode if mode != "_" else self.mode
        self.widget = widget if widget != "_" else self.widget
        self.obj = obj if obj!="_" else self.obj
        return self
        
    def get(self, name_f:str, mode:str="_", widget:str="_", obj:str="_", default_v='^default_for_get_func$',ae:bool=True):
        mode = mode if mode!="_" else self.mode
        widget = widget if widget!="_" else self.widget
        obj = obj if obj!="_" else self.obj
        args_a = [i for i in [mode, widget, obj, name_f] if i != None]
        args_a = atuple(args_a)
        out_a = self.config[args_a]
        if ae:
            return self.after_process(args_a, out_a)
        else:
            return out_a

    def get2(self, paras:tuple)->tuple:
        para_t = self.pre
        for para_i in paras:
            para_t.append(para_i)
        return tuple(para_t)
    
    def set_pre(self, paras:tuple):
        self.pre = []
        for para_i in paras:
            self.pre.append(para_i)
    
    def __getitem__(self, key):
        if isinstance(key, atuple):
            out_a = self.config[key]
            if out_a is None:
                return out_a 
            else:
                return self.after_process(key, out_a)
        else:
            return self.get(key)

    def after_process(self, args_a:tuple, target_f):
        if "path" in args_a:
            if isinstance(target_f, list):
                out_l = []
                for i in target_f:
                    if os.path.isabs(i):
                        out_l.append(i)
                    else:
                        out_l.append(str((pathlib.Path(self.wkdr)/pathlib.Path(i)).resolve()))
                return out_l
            elif isinstance(target_f, str):
                if os.path.isabs(target_f):
                    return target_f
                else:
                    return str((pathlib.Path(self.wkdr)/pathlib.Path(target_f)).resolve())
            else:
                return target_f
        elif "font" in args_a:
            font_dict = {i[0]:i[1] for i in target_f}
            return font_get(font_dict)
        else:
            return target_f

class UIData(object):
    def __init__(self, index:int, key:atuple|alist[atuple], action:callable, 
                 type_f:Literal[None, 'size', 'font', 'icon', 'config', 'height','margin','unpack']| Literal[None, 'size', 'font', 'icon', 'config', 'height','margin','unpack'], value_t:dict|list|str|int, value_ae:dict|list|str|int, 
                 escape_sign:dict, force_escape_sign:dict|list|bool={}, traceinfo:GV.FuncInfo=None):
        self.index = index
        self.key = key
        self.action = action
        self.type = type_f
        self.value_t = value_t
        self.value_ae = value_ae
        self.escape_sign = escape_sign
        self.force_escape_sign = force_escape_sign
        self.traceinfo = traceinfo

    def get_escape_sign(self):
        if not self.force_escape_sign:
            return self.escape_sign
        elif isinstance(self.escape_sign, dict):
            re_dict = copy.deepcopy(self.escape_sign)
            for key_i, value_i in self.force_escape_sign.items():
                re_dict[key_i] = value_i
            return re_dict
        elif isinstance(self.escape_sign, list):
            list_f = []
            for i in range(len(self.escape_sign)):
                if self.force_escape_sign[i] is None:
                    list_f.append(self.escape_sign[i])
                else:
                    list_f.append(self.force_escape_sign[i])
            return list_f
        else:
            return self.force_escape_sign

class UIUpdater(QObject):
    ui_set_l = []
    update_task=Signal(dict)
    @classmethod
    def _primary_init(cls,config:Config_Manager):
        cls.config_manager:Config_Manager = config.deepcopy()
        cls.config:dict = copy.deepcopy(cls.config_manager.config)
        cls.wkdr = config.wkdr

    @classmethod
    def after_process(cls, args_a:tuple, target_f):
        if "path" in args_a:
            if isinstance(target_f, list):
                out_l = []
                for i in target_f:
                    if os.path.isabs(i):
                        out_l.append(i)
                    else:
                        out_l.append(str((pathlib.Path(cls.wkdr)/pathlib.Path(i)).resolve()))
                return out_l
            elif isinstance(target_f, str):
                if os.path.isabs(target_f):
                    return target_f
                else:
                    return str((pathlib.Path(cls.wkdr)/pathlib.Path(target_f)).resolve())
            else:
                return target_f
        elif "font" in args_a:
            font_dict = {i[0]:i[1] for i in target_f}
            return font_get(font_dict)
        else:
            return target_f
        
    @classmethod
    def action(cls, key_f:atuple|alist[atuple], action_f:Callable, type_f:None|str=None):
        value_t = cls._getValue(key_f, cls.config)
        atuple_check = False
        if isinstance(key_f, atuple):
            atuple_check = True
        elif isinstance(key_f, alist):
            atuple_check = all(isinstance(i, atuple) for i in key_f)
        if not value_t:
            value_ae = value_t
        elif isinstance(value_t, alist):
            if not type_f:
                type_f = alist([None]*len(value_t))
            value_ae = [cls._value_ae(cls, value_t[i], type_f[i]) for i in range(len(value_t))]
        else:
            value_ae = cls._value_ae(cls, value_t, type_f)
        match type_f:
            case _ if value_ae is None:
                pass
            case _ if isinstance(key_f, alist):
                action_f(*value_ae)
            case 'margin':
                action_f(*value_ae)
            case 'unpack':
                action_f(*value_ae)
            case _:
                if value_ae:
                    action_f(value_ae)
        return atuple_check, value_t, value_ae
    @classmethod
    def get(cls, key_f:atuple|alist[atuple], default_v=None):
        if isinstance(key_f, atuple):
            value_t = cls.config[key_f]
            if not value_t:
                return default_v
            else:
                return cls.after_process(key_f, value_t)
        elif isinstance(key_f, alist):
            value_l = []
            for i in key_f:
                if isinstance(i, atuple):
                    value_l.append(cls.get(i, default_v))
                else:
                    value_l.append(default_v)
            return value_l
        else:
            warnings.warn(f"UIUpdater.get: Invalid key type: {key_f}")
            return default_v
    @classmethod
    def set(cls, key_f:Union[atuple,alist],action_f:Callable,
             type_f:Union[alist[GV.UpdateSign], GV.UpdateSign]=None, traceinfo:Optional[GV.FuncInfo]=None):
        if not traceinfo:
            frame_f = inspect.currentframe().f_back
            inspect_info = inspect.getframeinfo(frame_f)
            classname_f = UIUpdater.get_classname(frame_f)
            traceinfo = GV.FuncInfo(classname=classname_f, methodname=inspect_info.function, filename=inspect_info.filename, linenum=inspect_info.lineno)
        atuple_check, value_t, value_ae = cls.action(key_f, action_f, type_f)
        if atuple_check:
            if not traceinfo:
                traceinfo = get_func_info(action_f)
            escape_sign = UIUpdater.cal_escape_sign(value_t, value_t, init_value=True)
            if type_f != 'style':
                action_f = UIwarpper(action_f)

            data_c = UIData(index=len(cls.ui_set_l), key=key_f, action=action_f, type_f=type_f, value_t=value_t, 
                            value_ae=value_ae, escape_sign=escape_sign, force_escape_sign={}, traceinfo=traceinfo)
            cls.ui_set_l.append(data_c)
        else:
            cls.action(key_f, action_f, type_f)
            return None
        return data_c
        
    @staticmethod
    def cal_escape_sign(value_t:str|dict|list|int|alist, value_n:str|dict|list|int|alist, init_value:bool=False)->dict|bool:
        if isinstance(value_t, alist):
            if init_value:
                return [False]*len(value_t)
            else:
                return [value_t[i]==value_n[i] for i in range(len(value_t))]
        elif isinstance(value_t, dict):
            target_d = {}
            value_t_flatten = dicta.flatten_dict(value_t)
            value_n_flatten = dicta.flatten_dict(value_n)
            if init_value:
                target_d = {i:False for i in value_t_flatten.keys()}
                return target_d
            for key_t, value_t_i in value_t_flatten.items():
                value_n_i = value_n_flatten.get(key_t, None)
                if value_n_i is None or value_t_i != value_n_i:
                    target_d[key_t] = False
                else:
                    target_d[key_t] = True
            for key_n, value_n_i in value_n_flatten.items():
                if key_n not in target_d:
                    target_d[key_n] = False
            return target_d
        else:
            if init_value:
                return False
            else:
                return value_t==value_n
    @staticmethod
    def get_classname(frame_f):
        locals_f = frame_f.f_locals
        if 'self' in locals_f:
            return locals_f['self'].__class__.__name__
        else:
            return ""
    
    def __init__(self):
        super().__init__()
        self.update_delay = QTimer()
        self.update_delay.setSingleShot(False)
        self.update_delay.timeout.connect(self.on_yaml_change)
        self.init_watcher()

    def init_watcher(self):
        self.watcher = QFileSystemWatcher([self.config_manager.yaml_path])
        self.watcher.fileChanged.connect(self.restart_timer)  # 连接文件变化信号
        
    def restart_timer(self):
        self.update_delay.start(400)
    
    def on_yaml_change(self):
        self.update_delay.stop()
        try:
            yml_file0 = yml.read(self.config_manager.yaml_path)
            yml_file1 = dicta.flatten_dict(yml_file0)
            yml_file2 = self._calSize(yml_file1)
            yml_file3 = dicta.unflatten_dict(yml_file2)
        except Exception as e:
            warnings.warn(f"Yaml file read failed: {e}")
            return
        if not yml_file3:
            return
        self._updateUI(adict(yml_file3))
        self.update_config(yml_file3)
    
    @classmethod
    def update_config(cls, yml_file:dict):
        cls.config = adict(copy.deepcopy(yml_file))
        
    def _calSize(self, config:dict):
        config_r = copy.deepcopy(config)
        scr_x, scr_y = get_screen_size('pixel')
        res_x = math.sqrt(scr_x*scr_y/(2560*1600))
        res_y = res_x
        # resize 
        targets = ['win_x', "win_y", "gap", "het", "srh_r"]
        default_size = [1600,900,60,60,80]
        base_d = {}
        for i, target_i in enumerate(targets):
            value_i = config.get(atuple('Common','Size',target_i),default_size[i])
            value_f = int(res_x*value_i)
            base_d[target_i] = value_f
        base_d = base_d | {'scr_x':scr_x, 'scr_y':scr_y, 'res_x':res_x, 'res_y':res_y}
        for key_i, value_i in config.items():
            if "Size" in key_i:
                config_r[key_i] = self._str2int(value_i, base_d)
        return config_r
    def _str2int(self, input_f:Union[list, str], base_d:dict):
        scr_x, scr_y, win_x, win_y, gap, het, srh_r= symbols('scr_x scr_y win_x win_y gap het srh_r')
        values = {
                scr_x: base_d['scr_x'],
                scr_y: base_d['scr_y'],
                win_x: base_d['win_x'],
                win_y: base_d['win_y'],
                gap: base_d['gap'],
                het: base_d['het'],
                srh_r: base_d['srh_r'],
                }
        if isinstance(input_f, list):
            results = [int(sympify(expr).evalf(subs=values)) for expr in input_f]
            return results
        elif isinstance(input_f, str):
            return int(sympify(input_f).evalf(subs=values))
        else:
            return input_f

    def _updateUI(self, yml_file:adict):
        for order_i in range(len(self.ui_set_l)):
            i:UIData = self.ui_set_l[order_i]
            # read the value from the new yaml file
            if isinstance(i.key, atuple):
                value_new = yml_file[i.key]
                if value_new is None:
                    self._key_missing_warning(i)
                    continue
                elif value_new == i.value_t:
                    continue
            elif isinstance(i.key, alist):
                value_new = alist()
                for i_f, key_i in enumerate(i.key):
                    vi = yml_file[key_i]
                    if vi is None:
                        self._key_missing_warning(i)
                    value_new.append(vi)
            else:
                warnings.warn(f"Invalid key: {i.key}")

                continue
            
            escape_sign_server = UIUpdater.cal_escape_sign(i.value_t, value_new)
            i.escape_sign = escape_sign_server
            escape_sign = i.get_escape_sign()
            if escape_sign is True:
                continue
            elif isinstance(escape_sign, dict) and all(escape_sign.values()):
                continue
            elif isinstance(escape_sign, list) and all(escape_sign):
                continue

            if isinstance(value_new, alist):
                value_ae = alist()
                for i_f, value_i in enumerate(value_new):
                    if i.type:
                        value_ae.append(self._value_ae(value_i, i.type[i_f]))
                    else:
                        value_ae.append(value_i)
            else:
                value_ae = self._value_ae(value_new, i.type)
            i.value_ae = value_ae
            update_result = self._objUpdate(i)
            i.value_t = value_new
    
    @staticmethod
    def _key_missing_warning(data_i:UIData):
        key_f = data_i.key
        traceinfo = data_i.traceinfo
        classname_f = traceinfo.classname
        methodname_f = traceinfo.methodname
        filename_f = traceinfo.filename
        linenum_f = traceinfo.linenum
        if classname_f == '':
            GV.logger.warning(title="YAML Key Missing", message=f'Key {key_f} not found in new yaml file, Function {methodname_f} at "{filename_f}:{linenum_f}"')
        else:
            GV.logger.warning(title="YAML Key Missing", message=f'Key {key_f} not found in new yaml file, {classname_f}.{methodname_f} at "{filename_f}:{linenum_f}"')
    
    def _objUpdate(self, uidata_f:UIData):
        try:
            action_i = uidata_f.action
            type_i = uidata_f.type
            value_new = uidata_f.value_ae
            match type_i:
                case 'unpack' | 'margin':
                    action_i(*value_new, escape_sign=uidata_f.get_escape_sign())
                case _ if isinstance(value_new, alist):
                    action_i(*value_new, escape_sign=uidata_f.get_escape_sign())
                case _:
                    action_i(value_new, escape_sign=uidata_f.get_escape_sign())
            return True, ''
        except Exception as e:
            print(f"Update {uidata_f.key} use {uidata_f.action} failed: {e}")
            return False, e

    def _value_ae(self, value_i, type_f:Literal[None, 'size', 'font', 'icon', 'config', 'height','margin','unpack']):
        match type_f:
            case 'size':
                match value_i:
                    case _ if isinstance(value_i, int):
                        return QSize(value_i, value_i)
                    case _ if isinstance(value_i, list):
                        return QSize(*value_i[:2])
                    case _ if isinstance(value_i, QSize):
                        return value_i
                    case _:
                        return None
            case 'font':
                return font_get(value_i)
            case 'icon':
                return AIcon(value_i)
            case _:
                return value_i
    
    @staticmethod
    def _getValue(key_f, config_f):
        if isinstance(key_f, atuple):
            return config_f[key_f]
        elif isinstance(key_f, alist):
            return alist(UIUpdater._getValue(i, config_f) for i in key_f)
        else:
            return key_f

def dynamic_load(type_f:Literal[None, 'size', 'font', 'icon', 'config', 'height','margin','unpack', 'style']|alist=None):
    def inner_func(func_f:Callable):
        def inner2_func(*args)->UIData:
            obj_f = args[0]
            function_f = types.MethodType(func_f, obj_f)
            if len(args) == 2:
                out_f = UIUpdater.set(args[1], function_f, type_f, traceinfo=get_func_info(function_f))
            else:

                arg_l = alist([i for i in args[1:]])
                if not type_f:
                    out_f = UIUpdater.set(arg_l, function_f, type_f=alist(), traceinfo=get_func_info(function_f))
                else:
                    out_f = UIUpdater.set(arg_l, function_f, type_f, traceinfo=get_func_info(function_f))
            return out_f


        return inner2_func
    return inner_func

def UIwarpper(func_f:Callable):
    def inner_func(*args, escape_sign:bool=False, **kwargs):
        if isinstance(escape_sign, list):
            if all(escape_sign):
                return
        else:
            if escape_sign:
                return
        func_f(*args, **kwargs)
    return inner_func

class Udata(object):
    def __init__(self, key_f:atuple, default_v=None, index:int=None):
        self.key_f = key_f
        self.default_v = default_v
        self.add_str = ''
        self.index = index

    def __getitem__(self, index:int):
        return Udata(self.key_f, self.default_v, index)
    
    def value(self, config:dict)->str|int|list|dict|None:
        if self.index is None:
            return config.get(self.key_f, self.default_v)
        else:
            temp_data = config.get(self.key_f, self.default_v)
            if isinstance(temp_data, list) and self.index is not None:
                return temp_data[min(self.index, len(temp_data)-1)]
            else:
                return temp_data

def process_style_dict(pre_d:dict, temp_d:dict, escape_sign:dict, config_f:dict)->dict:
    config = dicta.flatten_dict(config_f)
    pre_f = dicta.flatten_dict(pre_d)
    temp_f = dicta.flatten_dict(temp_d)
    out_d = {}
    if pre_d == {}:
        for key_i, value_i in temp_f.items():
            if not isinstance(value_i, Udata):
                out_d[key_i] = value_i
            else:
                out_d[key_i] = value_i.value(config)
    else:
        for key_i, value_i in pre_f.items():
            value_n = temp_f.get(key_i, None)
            if isinstance(value_n, Udata):
                value_n = value_n.value(config)
            if value_n is None or escape_sign.get(key_i, False):
                out_d[key_i] = value_i.value(config) if isinstance(value_i, Udata) else value_i
            else:
                out_d[key_i] = value_n
    
    return out_d

