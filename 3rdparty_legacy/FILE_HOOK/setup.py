from setuptools import setup, Extension
import pybind11

# 获取 pybind11 的编译选项
pybind11_include = pybind11.get_include()

# 定义扩展模块
ext_modules = [
    Extension(
        "file_watcher",  # 模块名
        sources=["python_warcher.cpp", 'WatchData.cpp', 'Win32FSHook.cpp'],  # 源文件
        include_dirs=[pybind11_include, '.'],  # 包含路径
        language="c++",
        extra_compile_args=["/std:c++17"],
    )
]

setup(
    name="file_watcher",
    version="0.1",
    author="Vaccummer",
    description="A Python wrapper for Windows File Watcher",
    ext_modules=ext_modules,
)
