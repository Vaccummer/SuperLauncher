from Scripts.backends.file_watcher import FileWatcher
import time
import atexit

def cb(file_path):
    print(f"File {file_path} has been modified")


watcher = FileWatcher()
watcher.start([r'F:\Windows_Data\Desktop_File\16-TD3 Solution for MountainCarContinuous-v0.pdf'], "16-TD3 Solution for MountainCarContinuous-v0.pdf", cb)
while True:
    time.sleep(0.1)
atexit.register(watcher.stop)



