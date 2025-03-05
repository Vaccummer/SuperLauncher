import subprocess
import wexpect as px
import sys
import threading
from typing import Optional, Callable

class ScpController:
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self._output_buffer = []
        self._error_buffer = []
        self._is_running = False

    def run_scp(
        self,
        source: str,
        destination: str,
        on_output: Callable[[str], None] = None,
        on_error: Callable[[str], None] = None,
        password: str = None
    ) -> int:
        """
        执行 SCP 命令
        :param source: 源路径（如 user@host:/path）
        :param destination: 目标路径（如 C:/dest）
        :param on_output: 实时输出回调
        :param on_error: 实时错误回调
        :param password: 密码（非安全方式，建议用密钥）
        :return: 退出码
        """
        # 构建命令（Windows 路径需转义）
        cmd = ['scp.exe', '-r', '-v', source, destination.replace('\\', '/')]
        
        # 启动进程
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            text=True,
            encoding=sys.stdout.encoding,
            errors='replace'
        )
        
        # 若需密码，自动输入（非安全！仅演示）
        if password:
            self.process.stdin.write(password + '\n')
            self.process.stdin.flush()

        self._is_running = True

        # 启动线程捕获输出
        def read_stream(stream, buffer, callback):
            for line in iter(stream.readline, ''):
                if not line:
                    break
                buffer.append(line)
                if callback:
                    callback(line.strip())
            stream.close()

        # 输出线程
        stdout_thread = threading.Thread(
            target=read_stream,
            args=(self.process.stdout, self._output_buffer, on_output)
        )
        stderr_thread = threading.Thread(
            target=read_stream,
            args=(self.process.stderr, self._error_buffer, on_error)
        )
        
        stdout_thread.daemon = True
        stderr_thread.daemon = True
        
        stdout_thread.start()
        stderr_thread.start()

        # 等待进程结束
        return_code = self.process.wait()
        self._is_running = False
        
        stdout_thread.join(timeout=1)
        stderr_thread.join(timeout=1)
        
        return return_code

    def stop(self):
        """终止正在运行的 SCP 进程"""
        if self.process and self._is_running:
            self.process.terminate()  # 温和终止
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()  # 强制终止
            self._is_running = False

    def get_output(self) -> str:
        """获取所有标准输出"""
        return ''.join(self._output_buffer)

    def get_errors(self) -> str:
        """获取所有错误输出"""
        return ''.join(self._error_buffer)

    def is_running(self) -> bool:
        """检查进程是否在运行"""
        return self._is_running

def parse_scp_progress(line: str) -> Optional[float]:
    """
    从 SCP 的详细输出中解析进度百分比
    示例输入: 'Transferred: 1024 bytes, 53% Done, 1.2 MB/s'
    """
    if '%' in line:
        parts = line.split()
        for part in parts:
            if '%' in part:
                percent_str = part.replace('%', '')
                try:
                    return float(percent_str)
                except ValueError:
                    pass
    return None

# 使用方式
def on_stderr(line):
    percent = parse_scp_progress(line)
    if percent is not None:
        print(f"\r进度: {percent}%", end='')

if __name__ == "__main__":
    import wexpect
    import re
    # 启动 Windows cmd.exe
    child = wexpect.spawn('''scp.exe -r am@172.28.14.64:/home/am/cache "c:/Users/assdasd/hello"''')

    while True:
        index = child.expect([".*password:", ".+", wexpect.EOF])
        match index:
            case 0:
                child.sendline("1984")
            case 1:
                print(child.after)
                with open('a2.log', 'a', encoding="utf-8") as f:
                    f.write(f"{re.escape(child.after)}\n") 
            case 2:
                break

