#include <iostream>
#include <string.h>
#include <windows.h>
#include "WatchData.h"
#include "Win32FSHook.h"

char *wchar2char(const wchar_t *wchar, char *m_char)
{
    int len = WideCharToMultiByte(CP_ACP, 0, wchar, wcslen(wchar), NULL, 0, NULL, NULL);
    WideCharToMultiByte(CP_ACP, 0, wchar, wcslen(wchar), m_char, len, NULL, NULL);
    m_char[len] = '\0';
    return m_char;
}

wchar_t *char2wchar(const char *cchar, wchar_t *m_wchar)
{
    int len = MultiByteToWideChar(CP_ACP, 0, cchar, strlen(cchar), NULL, 0);
    MultiByteToWideChar(CP_ACP, 0, cchar, strlen(cchar), m_wchar, len);
    m_wchar[len] = '\0';
    return m_wchar;
}

void win32FSCallback(int watchID, int action, const WCHAR *rootPath, const WCHAR *filePath)
{
    char tmp[256]; // windows系统文件名只需要256个字节就可以了
    char filename[256];
    strcpy(filename, wchar2char(rootPath, tmp));
    strcat(filename, wchar2char(filePath, tmp)); // 把根目录和相对根目录的文件名拼起来就是完整的文件名了
    // std::cout<<"watchID: "<<watchID<<std::endl;
    switch (action)
    {
    case 1:
    {
        std::cout << "create:" << filename << std::endl;
        break;
    }
    case 2:
    {
        std::cout << "delete:" << filename << std::endl;
        break;
    }
    case 3:
    {
        std::cout << "replicate" << filename << std::endl;
        break;
    }
    case 4: // 在4时别急着换行，因为windows在回调了4之后，就会回调5，拼起来意思才完整
    {
        std::cout << "rename" << filename;
        break;
    }
    case 5:
    {
        std::cout << ",newname:" << filename << std::endl;
        break;
    }
    default: // 其他的一些操作，因为没有文档，我也不知道还有没有其他的action
    {
        std::cout << "operation'" << action << "':" << filename << std::endl;
    }
    }
}

int main()
{
    std::cout << "Hello, World!" << std::endl;
    int watchID;

    Win32FSHook win32FSHook;
    win32FSHook.init(win32FSCallback);
    DWORD err;
    // wchar_t path[256];
    std::string str = "F:\\";
    std::wstring wstr = std::wstring(str.begin(), str.end());
    const WCHAR* path = wstr.c_str();
    std::wcout << path << std::endl;
    watchID = win32FSHook.add_watch(path,
                                    1 | 2 | 4 | 8,
                                    true,
                                    err);
    if (err == 2)
    {
        std::cout << "cant supervise" << std::endl;
    }
    else
    {
        std::cout << "start supervise" << std::endl;
        getchar();
        win32FSHook.remove_watch(watchID);
        std::cout << "end supervise" << std::endl;
        getchar();
    }
    return 0;
}
