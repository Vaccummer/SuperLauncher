from filewatcher import FileWatcher
import time
def callback(event, filename):
    print(f"Event: {event}, File: {filename}")

watcher = FileWatcher()
watcher.start(
    paths=["C:\\", 'D:\\'],
    filepath="D:\\迅雷下载\\2024.12.02.626353v1.full.pdf",
    filename="2024.12.02.626353v1.full.pdf",
    callback_func=callback
)
while True:
    time.sleep(1)
