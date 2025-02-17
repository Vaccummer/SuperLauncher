from tkinter import simpledialog
from ZIPmanager import ZIPmanager
import os
from glob import glob
from PySide2.QtWidgets import QApplication, QInputDialog

if __name__ == "__main__":
    app = QApplication([])
    fa = 0
    def f(a):
        print(a)
        global fa
        fa = a

    def progress(a):
        print(a)
        return True

    def r(name):
        print(name)

    def get_password()->str:
        try:
            password, ok = QInputDialog.getText(None, "Input Dialog", "Enter your password:")
            if not ok:
                return ''       
            else:
                return password
        except Exception as e:
            print(e)
            return ''
    paths = glob('D:\\Document\\Desktop\\bit7z\\*')
    manager = ZIPmanager()

    # manager.compress(paths, "output_archive.zip","zip",'1234', progress, r, 100, 4)
    a = manager.decompress("./output_archive.zip", "D:\\Document\\Desktop\\output_archive", "zip", get_password, progress, r, 100, 4)
    print(a)