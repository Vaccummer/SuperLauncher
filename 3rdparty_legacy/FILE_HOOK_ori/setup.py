from setuptools import setup, Extension
import pybind11
import os

ext_modules = [
    Extension(
        "FileWatcher",
        ["python_watcher.cpp", "Win32FSHook.cpp",'WatchData.cpp'],
        include_dirs=[pybind11.get_include()],
        language='c++',
        extra_compile_args=['/std:c++17'] if os.name == 'nt' else ['-std=c++17'],
    ),
]

setup(
    name="FileWatcher",
    ext_modules=ext_modules,
    install_requires=['pybind11>=2.6.0'],
    python_requires=">=3.6",
)