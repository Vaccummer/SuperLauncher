import Scripts as py_src
import os
import sys
from PySide2.QtWidgets import QApplication

if __name__ == "__main__":
    py_src.exc_cb_init()
    path_t = os.path.abspath('./launcher_cfg_new.yaml')
    py_src.Config_Manager.set_config_path(path_t)
    py_src.check_admin(py_src.Config_Manager.config)
    py_src.app_set(py_src.Config_Manager.config)
    app = QApplication([])
    config = py_src.Config_Manager(wkdir=os.getcwd())
    py_src.UIUpdater._primary_init(config)
    uiupdater = py_src.UIUpdater()
    launcher = py_src.ControlLauncher(config, app)
    # uiupdater.update_task.connect(launcher._updateUI)
    launcher.show()
    sys.exit(app.exec_())