#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <pybind11/complex.h>
#include <string>
#include <thread>
#include "Win32FSHook.h"
#include <iostream>

namespace py = pybind11;

char *wchar2char(const wchar_t *wchar, char *m_char)
{
    int len = WideCharToMultiByte(CP_UTF8, 0, wchar, wcslen(wchar), NULL, 0, NULL, NULL);
    WideCharToMultiByte(CP_UTF8, 0, wchar, wcslen(wchar), m_char, len, NULL, NULL);
    m_char[len] = '\0';
    return m_char;
}

wchar_t *char2wchar(const char *cchar, wchar_t *m_wchar)
{
    int len = MultiByteToWideChar(CP_UTF8, 0, cchar, strlen(cchar), NULL, 0);
    MultiByteToWideChar(CP_UTF8, 0, cchar, strlen(cchar), m_wchar, len);
    m_wchar[len] = '\0';
    return m_wchar;
}

bool check_filename(const char current_path[2048], const std::string &target_filename, const std::string &ori_file_name)
{
    // 检查 current_path 是否与 ori_file_name 相同
    if (std::string(current_path) == ori_file_name)
    {
        return false;
    }

    // 检查 current_path 是否以 target_filename 结尾
    std::string current_path_str(current_path);
    if (current_path_str.size() >= target_filename.size() &&
        current_path_str.compare(current_path_str.size() - target_filename.size(), target_filename.size(), target_filename) == 0)
    {
        return true;
    }

    return false;
}

class FileWatcher
{
private:
    Win32FSHook win32FSHook;
    int watchID;
    bool isWatching;
    static py::function callback_py;
    static std::string tar_filename;
    static std::string ori_file_path;

    static void callback_wrapper(int watchID, int action, const WCHAR *rootPath, const WCHAR *filePath)
    {
        char tmp[256];
        char filename[512];
        strcpy(filename, wchar2char(rootPath, tmp));
        strcat(filename, wchar2char(filePath, tmp));
        py::gil_scoped_acquire acquire;
        if (check_filename(filename, tar_filename, ori_file_path))
        {
            switch (action)
            {
            case 1:
                callback_py(filename);
                break;
            }
        }
    }

public:
    FileWatcher() : watchID(-1), isWatching(false) {}

    void start(const std::string ori_filepath,
               const std::string filename,
               const py::function &callback)
    {
        callback_py = callback;
        tar_filename = filename;
        if (isWatching)
        {
            throw std::runtime_error("Already watching a directory.");
        }
        win32FSHook.init(callback_wrapper);
        std::wstring wpath = std::wstring(ori_filepath.begin(), ori_filepath.end());
        const WCHAR *wchar_path = wpath.c_str();
        DWORD err;
        int id = win32FSHook.add_watch(wchar_path, 1 | 2 | 4 | 8, true, err);
        if (err == 2)
        {
            throw std::runtime_error("Cannot supervise the directory: " + ori_filepath);
        }
        isWatching = true;
    }

    void stop()
    {
        if (!isWatching)
        {
            throw std::runtime_error("No active supervision to stop.");
        }
        win32FSHook.remove_watch(watchID);
        isWatching = false;
        callback_py = py::none();
    }
};

py::function FileWatcher::callback_py = py::none();
std::string FileWatcher::tar_filename = "";
std::string FileWatcher::ori_file_path = "";

PYBIND11_MODULE(file_watcher, m)
{
    py::class_<FileWatcher>(m, "FileWatcher")
        .def(py::init<>())
        .def("start", &FileWatcher::start, "Start watching a directory",
             py::arg("ori_filepath"),
             py::arg("filename"),
             py::arg("callback"))
        .def("stop", &FileWatcher::stop, "Stop watching");
}
