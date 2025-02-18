import ctypes

def get_display_refresh_rate()->int:
    try:
        hdc = ctypes.windll.user32.GetDC(0)
        # 获取显示器的刷新率
        refresh_rate = ctypes.windll.gdi32.GetDeviceCaps(hdc, 116)  # 116 是 VREFRESH 的常量值
        # 释放设备上下文
        ctypes.windll.user32.ReleaseDC(0, hdc)
        output = int(refresh_rate)
        if 30<output<180:
            return output
        else:
            return 60
    except Exception as e:
        return 60

if __name__ == "__main__":
    refresh_rate = get_display_refresh_rate()
    print(f"Display refresh rate: {refresh_rate} Hz")
