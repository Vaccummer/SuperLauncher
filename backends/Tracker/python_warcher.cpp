#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <pybind11/complex.h>
#include <string>
#include <thread>
#include "Win32FSHook.h"
#include <iostream>
enum class WatcherErrorCode
{
    Success = 0,
    AlreadyWatching = -1,
    CannotSupervise = -2,
    NotInWatchList = -3,
    UnknowAddWatchError = -4,
    UnknowRemoveWatchError = -5,
    UnknowError = -6,
};

namespace py = pybind11;
using fptr = std::shared_ptr<py::function>;
using iptr = std::shared_ptr<bool>;
using sptr = std::shared_ptr<std::string>;
using func = std::function<void(int watchID, int action, const WCHAR *rootPath, const WCHAR *filePath)>;

char *wchar2char(const wchar_t *wchar, char *m_char)
{
    size_t len = WideCharToMultiByte(CP_UTF8, 0, wchar, wcslen(wchar), NULL, 0, NULL, NULL);
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

// void callback_wrapper2(fptr callback_py, sptr tar_filename, sptr ori_file_path, iptr conduct_cb, int watchID, int action, const WCHAR *rootPath, const WCHAR *filePath)
// {
//     if (!*conduct_cb)
//     {
//         return;
//     }
//     std::cout << "callback_wrapper" << std::endl;
//     char tmp[256];
//     char filename[512];
//     strcpy(filename, wchar2char(rootPath, tmp));
//     strcat(filename, wchar2char(filePath, tmp));
//     if (check_filename(filename, *tar_filename, *ori_file_path))
//     {
//         switch (action)
//         {
//         case 1:
//             py::gil_scoped_acquire acquire;
//             (*callback_py)(filename);
//             break;
//         }
//     }
// }

class FileWatcher
{
private:
    Win32FSHook win32FSHook;
    std::unordered_map<std::string, int> watch_map;
    bool isWatching;
    std::vector<std::string> drivers;
    static sptr tar_filename;
    static sptr ori_file_path;
    static iptr conduct_cb;
    static fptr cb_py_ptr;
    static ChangeCallback cb_c;
    static void callback_wrapper(int watchID, int action, const WCHAR *rootPath, const WCHAR *filePath)
    {
        if (!*conduct_cb)
        {
            return;
        }
        char tmp[256];
        char filename[512];
        strcpy(filename, wchar2char(rootPath, tmp));
        strcat(filename, wchar2char(filePath, tmp));
        if (check_filename(filename, *tar_filename, *ori_file_path))
        {
            switch (action)
            {
            case 1:
                py::gil_scoped_acquire acquire;
                if (cb_py_ptr != nullptr)
                    (*cb_py_ptr)(filename);
                break;
            }
        }
    }

public:
    FileWatcher(const std::vector<std::string> &d_list) : drivers(d_list), isWatching(false)
    {
    }

    void initSet(py::function &callback, std::string &filename, std::string &filepath)
    {
        cb_py_ptr = std::make_shared<py::function>(callback);
        tar_filename = std::make_shared<std::string>(filename);
        ori_file_path = std::make_shared<std::string>(filepath);
        conduct_cb = std::make_shared<bool>(false);
        win32FSHook.init(callback_wrapper);
        for (const auto &driver : drivers)
        {
            monitor(driver);
        }
    }

    WatcherErrorCode monitor(const std::string &driver)
    {
        try
        {
            if (watch_map.find(driver) != watch_map.end())
                return WatcherErrorCode::AlreadyWatching;
            std::wstring wpath = std::wstring(driver.begin(), driver.end());
            const WCHAR *wchar_path = wpath.c_str();
            DWORD err;
            int id = win32FSHook.add_watch(wchar_path, 1 | 2 | 4 | 8, true, err);
            if (err == 2)
            {
                return WatcherErrorCode::CannotSupervise;
            }
            watch_map[driver] = id;
            return WatcherErrorCode::Success;
        }
        catch (const std::exception &e)
        {
            std::cout << "Error when monitoring: " << driver << "," << e.what() << std::endl;
            return WatcherErrorCode::UnknowAddWatchError;
        }
    }

    WatcherErrorCode removeWatch(const std::string &driver)
    {
        if (watch_map.find(driver) == watch_map.end())
            return WatcherErrorCode::NotInWatchList;
        try
        {
            win32FSHook.remove_watch(watch_map[driver]);
            watch_map.erase(driver);
            return WatcherErrorCode::Success;
        }
        catch (const std::exception &e)
        {
            std::cout << "Error when removing watch: " << driver << "," << e.what() << std::endl;
            return WatcherErrorCode::UnknowRemoveWatchError;
        }
    }

    std::vector<WatcherErrorCode> setDrivers(const std::vector<std::string> &driver_l)
    {
        std::vector<WatcherErrorCode> ret;
        for (const auto &pair : watch_map)
        {
            ret.push_back(removeWatch(pair.first));
        }
        watch_map.clear();
        for (const auto &driver_item : driver_l)
        {
            ret.push_back(monitor(driver_item));
        }
        return ret;
    }

    void setCallback(py::function &callback)
    {
        *cb_py_ptr = callback;
    }

    void start()
    {
        *conduct_cb = true;
    }

    void pause()
    {
        *conduct_cb = false;
    }

    void setWatch(const std::string &filename, const std::string &filepath)
    {
        *tar_filename = filename;
        *ori_file_path = filepath;
    }

    void terminate()
    {
        try
        {
            for (const auto &pair : watch_map)
            {
                win32FSHook.remove_watch(pair.second);
            }
            isWatching = false;
            cb_py_ptr = nullptr;
            watch_map.clear();
        }
        catch (const std::exception &e)
        {
            std::cout << "Error when terminating " << e.what() << std::endl;
        }
    }
};

sptr FileWatcher::tar_filename = nullptr;
sptr FileWatcher::ori_file_path = nullptr;
iptr FileWatcher::conduct_cb = nullptr;
fptr FileWatcher::cb_py_ptr = nullptr;
ChangeCallback FileWatcher::cb_c = nullptr;

PYBIND11_MODULE(file_watcher, m)
{
    py::class_<FileWatcher>(m, "FileWatcher")
        .def(py::init<const std::vector<std::string> &>())
        .def("initSet", &FileWatcher::initSet, py::arg("callback"), py::arg("filename"), py::arg("filepath"))
        .def("setDrivers", &FileWatcher::setDrivers, py::arg("driver_l"))
        .def("setCallback", &FileWatcher::setCallback, py::arg("callback"))
        .def("start", &FileWatcher::start)
        .def("pause", &FileWatcher::pause)
        .def("setWatch", &FileWatcher::setWatch, py::arg("filename"), py::arg("filepath"))
        .def("terminate", &FileWatcher::terminate);
}
