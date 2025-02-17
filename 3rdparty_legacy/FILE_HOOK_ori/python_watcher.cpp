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

class FileWatcher
{
private:
    Win32FSHook win32FSHook;
    int watchID;
    bool isWatching;
    static std::function<void(const std::string &)> callback_py;
    // static py::dict dict_f;

    static void callback_wrapper(int watchID, int action, const WCHAR *rootPath, const WCHAR *filePath)
    {
        char tmp[2048];
        char filename[2048];
        strcpy(filename, wchar2char(rootPath, tmp));
        strcat(filename, wchar2char(filePath, tmp));
        py::gil_scoped_acquire acquire;
        switch (action)
        {
        case 1:
            callback_py(filename);
            std::cout << "create: " << filename << std::endl;
            break;
        case 2:
            callback_py(filename);
            std::cout << "delete: " << filename << std::endl;
            break;
        case 3:
            callback_py(filename);
            std::cout << "replicate: " << filename << std::endl;
            break;
        case 4:
            callback_py(filename);
            std::cout << "rename: " << filename;
            break;
        case 5:
            callback_py(filename);
            std::cout << ", newname: " << filename << std::endl;
            break;
        default:
            callback_py(filename);
            std::cout << "operation '" << action << "': " << filename << std::endl;
        }
    }

public:
    FileWatcher() : watchID(-1), isWatching(false) {}

    void start(const std::string &path, const std::string filename, const std::function<void(const std::string &)> &callback)
    {
        std::cout << "start" << std::endl;
        callback_py = callback;
        if (isWatching)
        {
            throw std::runtime_error("Already watching a directory.");
        }
        std::wstring wpath = std::wstring(path.begin(), path.end());
        const WCHAR *wchar_path = wpath.c_str();
        win32FSHook.init(callback_wrapper);

        DWORD err;
        watchID = win32FSHook.add_watch(wchar_path, 1 | 2 | 4 | 8, true, err);
        if (err == 2)
        {
            throw std::runtime_error("Cannot supervise the given directory.");
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
        callback_py = nullptr;
    }
};
std::function<void(const std::string &)> FileWatcher::callback_py = nullptr;
;
PYBIND11_MODULE(file_watcher, m)
{
    py::class_<FileWatcher>(m, "FileWatcher")
        .def(py::init<>())
        .def("start", &FileWatcher::start, "Start watching a directory")
        .def("stop", &FileWatcher::stop, "Stop watching");
}
