from setuptools import setup, Extension
import pybind11

# 获取 pybind11 的编译选项
pybind11_include = pybind11.get_include()

# 定义扩展模块
ext_modules = [
    Extension(
        "ZIPmanager",  # 模块名
        sources=["main.cpp"],  # 源文件
        include_dirs=[pybind11_include, '.', './include'],  # 包含路径
        language="c++",
        libraries=["bit7z","OleAut32"],  # 链接的库名（不包含扩展名）
        library_dirs=["./lib"],  # 库文件所在目录
        extra_compile_args=["/std:c++17"],
    )
]

setup(
    name="ZIPmanager",
    version="0.1",
    author="Vaccummer",
    description="A Python wrapper for ZIPmanager using pybind11",
    ext_modules=ext_modules,
)
