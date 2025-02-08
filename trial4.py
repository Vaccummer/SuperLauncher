import warnings
import sys
import traceback
from dataclasses import dataclass, fields
from functools import partial
import time


programm_start_time_color_config = time.time()
try:
    from rich.console import Console
    console = Console(highlight=False)
    print_r = console.print
    use_rich = True
except ImportError:
    warnings.warn('Module "rich" not found, use "pip install rich" to install it!')
    use_rich = False
    console = None


@dataclass
class TerminalErrorColorConfig:
    error:tuple = (('color', '#FF0000'), ('bold', False), ('italic', False), ('underline', False), ('strike', False))

    message:tuple = (('color', '#FF0000'), ('bold', False), ('italic', False), ('underline', False), ('strike', False))

    date:tuple = (('color', '#1B55DD'), ('bold', False), ('italic', True), ('underline', False), ('strike', False))

    time:tuple = (('color', '#10E46C'), ('bold', False), ('italic', True), ('underline', False), ('strike', False))

    text:tuple = (('color', '#DCD7D7'), ('bold', False), ('italic', False), ('underline', False), ('strike', False))

    filename:tuple = (('color', '#189731'), ('bold', False), ('italic', False), ('underline', False), ('strike', False))

    lineno:tuple = (('color', '#00FF00'), ('bold', False), ('italic', False), ('underline', False), ('strike', False))

    name:tuple = (('color', '#0000FF'), ('bold', False), ('italic', False), ('underline', False), ('strike', False))

    line:tuple = (('color', '#E6E0E0'), ('bold', False), ('italic', False), ('underline', False), ('strike', False))

    locals:tuple = (('color', '#000000') , ('bold', False), ('italic', False), ('underline', False), ('strike', False))


def tuple_to_style(tuple_list:list[tuple])->str|None:
    dict_t = dict(tuple_list)
    start_str = '['
    list_s = []
    if not dict_t.get('color'):
        return None
    list_s.append(dict_t.get("color"))
    if dict_t.get('bold'):
        list_s.append('bold')
    if dict_t.get('italic'):
        list_s.append('italic')
    if dict_t.get('underline'):
        list_s.append('underline')
    if dict_t.get('strike'):
        list_s.append('strike')
    return start_str + ' '.join(list_s) + ']'


# Traceback (most recent call last):
#   File "d:\SuperLauncher\trial4.py", line 15, in <module>
#     a = 1/0
# ZeroDivisionError: division by zero


def call_back_exception(exc_type: Exception, exc_value: Exception, exc_traceback: Exception,color_config:TerminalErrorColorConfig=TerminalErrorColorConfig()):
    # __slots__ = ('filename', 'lineno', 'name', '_line', 'locals')
    exc_type = exc_type.__name__
    exc_value = exc_value
    tb_str_list:list[traceback.FrameSummary] = traceback.extract_tb(exc_traceback)
    time_str_date = time.strftime('%Y-%m-%d', time.localtime()) 
    time_str_time = time.strftime('%H:%M:%S', time.localtime())

    if use_rich:
        print_r(f'{color_config.error}Traceback[/] (Exception at {color_config.date}{time_str_date}[/] {color_config.time}{time_str_time}[/])', highlight=False)
    else:
        print(f'Traceback (Exception at {time_str_date} {time_str_time})')
    for tb in tb_str_list:

        if use_rich:
            print_r(f'  File {color_config.filename}"{tb.filename}"[/], line {color_config.lineno}{tb.lineno}[/], in {color_config.name}{tb.name}[/]')
            print_r(f'    {color_config.line}{tb.line}[/]')
        else:
            print(f'  File "{tb.filename}", line {tb.lineno}, in {tb.name}')
            print(f'    {tb.line}')
        if tb.locals:
            print(f'  Locals: {tb.locals}')

    if use_rich:
        print_r(f'{color_config.error}{exc_type}[/]: {color_config.message}{exc_value}[/]')
        print_r(f'{color_config.text}Launch Time[/]: {color_config.date}{time_str_date}[/] {color_config.time}{time_str_time}[/]')
        print_r(f"{color_config.text}Exception Time[/]: {color_config.date}{time_str_date}[/] {color_config.time}{time_str_time}[/]")
        console.print("-" * console.width, style="dim")
    else:
        print(f'{exc_type}: {exc_value}')
        print(f'Launch Time: {time_str_date} {time_str_time}')
        print(f"Exception Time: {time_str_date} {time_str_time}")
        print('\n')
        print('-'*100)









color_config = TerminalErrorColorConfig()

if use_rich:
    for name_i in fields(color_config):
        setattr(color_config, name_i.name, tuple_to_style(getattr(color_config, name_i.name)))
    
sys.excepthook = partial(call_back_exception, color_config=color_config)
a = 2/0
