import traceback
from dataclasses import dataclass
import time
import sys
from functools import partial

from rich.console import Console
console = Console(highlight=False)
print_r = console.print

# try:
#     from rich.console import Console
#     console = Console(highlight=False)
#     print_r = console.print
# except ImportError:
#     print_r = print
#     raise ImportError('Module "rich" not found, use "pip install rich" to install it!')

@dataclass
class TerminalErrorColorConfig2:
    error:tuple = (('color', '#DCD7D7'), ('bold', True), ('italic', False), ('underline', False), ('strike', False))
    message:tuple = (('color', '#00CED1'), ('bold', False), ('italic', True), ('underline', False), ('strike', False))
    date:tuple = (('color', '#1B55DD'), ('bold', False), ('italic', True), ('underline', False), ('strike', False))
    time:tuple = (('color', '#10E46C'), ('bold', False), ('italic', True), ('underline', False), ('strike', False))
    text:tuple = (('color', '#DCD7D7'), ('bold', False), ('italic', False), ('underline', False), ('strike', False))
    filename:tuple = (('color', '#189731'), ('bold', False), ('italic', False), ('underline', False), ('strike', False))
    lineno:tuple = (('color', '#00FF00'), ('bold', False), ('italic', False), ('underline', False), ('strike', False))
    name:tuple = (('color', '#0000FF'), ('bold', False), ('italic', False), ('underline', False), ('strike', False))
    line:tuple = (('color', '#E6E0E0'), ('bold', False), ('italic', False), ('underline', False), ('strike', False))
    locals:tuple = (('color', '#000000') , ('bold', False), ('italic', False), ('underline', False), ('strike', False))

class TerminalErrorColorConfig:
    r'''
    default: default style when style not set
    stop: the stop sign of the format
    trace_key: "Traceback" Keyword
    exc_key: "Exception" Keyword
    preposition: "at", "in" Keyword

    file_key: "File" keyword
    lt_key: "Launch Time" keyward
    comma: ",", ":"
    date: "2025-02-06"
    time: "13:55:48"
    filepath: "D:\SuperLauncher\trial3.py"
    lineno: line number
    function: the function name to raise the exc
    line: the code line to raise the exc
    exc: exc.__name__
    exc_str: str(exc)
    lc_emoji: the emoji in front of the start time
    exc_emoji: the emoji in front of the exception time
    '''
    _time_f:float = time.time()
    _date:str = time.strftime('%Y-%m-%d', time.localtime())
    _time:str = time.strftime('%H:%M:%S', time.localtime())
    default:str = "[#DCD7D7]"
    stop:str = "[/]"
    trace_key:str = "[#DCD7D7 bold]"
    exc_key:str = "[#DCD7D7 bold]"
    lt_key:str = "[#DCD7D7 bold]"

    preposition:str = "[#DCD7D7]"
    file_key:str = "[#DCD7D7]"
    launch_time_key:str = "[#DCD7D7]"
    comma:str = "[#DCD7D7]"
    date:str = "[#DCD7D7]"
    time:str = "[#DCD7D7]"
    filepath:str = "[#DCD7D7]"
    lineno:str = "[#DCD7D7]"
    function:str = "[#DCD7D7]"
    line:str = "[#DCD7D7]"
    exc:str = "[#DCD7D7]"
    exc_str:str = "[#DCD7D7]"
    lc_emoji:str = "🚀"
    exc_emoji:str = "❌"
    
def process_config(color_config:TerminalErrorColorConfig):
    properties = [i for i in color_config.__dict__.keys() if i not in ['_time', 'default']]
    if not color_config.default:
        color_config.default = "[#DCD7D7]"
    for name_i in properties:
        if not getattr(color_config, name_i):
            setattr(color_config, name_i, color_config.default)
    return color_config

process_config(TerminalErrorColorConfig)

def f(c:str, format_str:str):
    return f'{format_str}{c}{TerminalErrorColorConfig.stop}'

def call_back_exception(exc_type: Exception, exc_value: Exception, exc_traceback,cf:TerminalErrorColorConfig=TerminalErrorColorConfig):
    # __slots__ = ('filename', 'lineno', 'name', '_line', 'locals')
    exc_type = exc_type.__name__
    exc_value = exc_value

    tb_str_list:list[traceback.FrameSummary] = traceback.extract_tb(exc_traceback)
    date_n = time.strftime('%Y-%m-%d', time.localtime(float(cf._time_f))) 
    time_n = time.strftime('%H:%M:%S', time.localtime())
    console.print("-" * console.width, style="dim")
    str_all = f('Traceback', cf.trace_key)+f('(', cf.comma)+f('Exception', cf.exc_key)+f(' at ', cf.preposition)+f(date_n, cf.date)+" "+f(time_n, cf.time)+f(')\n', cf.comma)

    #  tb.__slots__ = ('filename', 'lineno', 'name', '_line', 'locals')
    for tb in tb_str_list:
        str_all += "  "+f('File', cf.file_key)+f(f' "{tb.filename}"', cf.file_key)+f(f':{cf.comma}', cf.comma)+f(f'{tb.lineno}', cf.lineno)
        str_all += f(f' in ', cf.preposition)+f(tb.name, cf.function)
        str_all += '\n    '+f(tb.line, cf.line)+'\n'
    str_all += f(exc_type, cf.exc)+f(':', cf.comma)+' '+f(exc_value, cf.exc_str) + '\n'
    lt_s = 'Launch Time'
    tn_s = 'Exception Time'
    lt_s += ' '*(len(tn_s)-len(lt_s))

    if cf.lc_emoji:
        str_all += cf.lc_emoji +' '
    str_all += f(lt_s, cf.lt_key)+f(': ',cf.comma)+f(cf._date, cf.date)+' '+f(cf._time, cf.time) +'\n'
    if cf.exc_emoji:
        str_all += cf.exc_emoji +' '
    str_all += f(tn_s, cf.lt_key)+f(': ',cf.comma)+f(date_n, cf.date)+' '+f(time_n, cf.time)
    print_r(str_all)



    console.print("-" * console.width, style="dim")

def exc_cb_init():
    sys.excepthook = partial(call_back_exception, cf=TerminalErrorColorConfig)



