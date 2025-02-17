#include <pybind11/pybind11.h>
#include <pybind11/functional.h>
#include <pybind11/stl.h>
#include <locale>
#include <codecvt>
#include <string>
#include <vector>
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

std::wstring utf8_to_wstring(const std::string &utf8_str)
{
    int size_needed = MultiByteToWideChar(CP_UTF8, 0, utf8_str.c_str(), (int)utf8_str.size(), NULL, 0);
    std::wstring wstr(size_needed, 0);
    MultiByteToWideChar(CP_UTF8, 0, utf8_str.c_str(), (int)utf8_str.size(), &wstr[0], size_needed);
    return wstr;
}

WCHAR *string_to_wchar(const std::string &str)
{
    // 计算转换后所需缓冲区大小
    int size_needed = MultiByteToWideChar(CP_UTF8, 0, str.c_str(), (int)str.size(), NULL, 0);
    // 分配缓冲区
    WCHAR *wstr = new WCHAR[size_needed + 1]; // +1 留出空间给终止符
    // 执行转换
    MultiByteToWideChar(CP_UTF8, 0, str.c_str(), (int)str.size(), wstr, size_needed);
    wstr[size_needed] = L'\0'; // 添加字符串终止符
    return wstr;
}

class FileWatcher
{
private:
    Win32FSHook win32FSHook;
    int watchID;
    bool isWatching;
    static std::wstring filename;
    static py::function callback;

    static void callback_wrapper(int watchID, int action, const WCHAR *rootPath, const WCHAR *filePath)
    {
        char tmp[256];
        char filename[256];
        strcpy(filename, wchar2char(rootPath, tmp));
        strcat(filename, wchar2char(filePath, tmp));

        py::gil_scoped_acquire acquire; // 确保持有 GIL

        switch (action)
        {
        case 1:
            callback(std::string("create"), std::string(filename));
            std::cout << "create" << std::endl;
            break;
        default:
            break;
        }
    }

public:
    FileWatcher() : watchID(-1), isWatching(false) {}

    void start(const std::vector<std::string> &paths, const std::string filepath, const std::string filename, py::function callback_func)
    {
        callback = callback_func;
        // std::wstring filename = utf8_to_wstring(filename);
        if (isWatching)
        {
            throw std::runtime_error("Already watching a directory.");
        }

        std::cout << filepath << std::endl;
        std::wstring wpath = utf8_to_wstring(filepath);
        std::wcout << wpath << std::endl;
        const WCHAR *wchar_path = wpath.c_str();
        std::wcout << wchar_path << std::endl;

        DWORD err;
        watchID = win32FSHook.add_watch(wchar_path, 1 | 2 | 4 | 8, true, err);
        if (err == 2)
        {
            throw std::runtime_error("Cannot supervise the given directory.");
        }
        isWatching = true;
        win32FSHook.init(callback_wrapper);
    }

    void stop()
    {
        if (!isWatching)
        {
            throw std::runtime_error("No active supervision to stop.");
        }
        win32FSHook.remove_watch(watchID);
        isWatching = false;
    }
};

std::wstring FileWatcher::filename;
py::function FileWatcher::callback;
// ... existing code ...

// 在文件末尾添加以下代码
PYBIND11_MODULE(filewatcher, m)
{
    py::class_<FileWatcher>(m, "FileWatcher")
        .def(py::init<>())
        .def("start", &FileWatcher::start,
             py::arg("paths"),
             py::arg("filepath"),
             py::arg("filename"),
             py::arg("callback_func"),
             "Start watching the specified directories")
        .def("stop", &FileWatcher::stop,
             "Stop watching all directories");
}