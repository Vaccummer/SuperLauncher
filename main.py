import Scripts as src
import os
import sys
from PySide2.QtWidgets import QApplication

if __name__ == "__main__":
    src.init()
    path_t = os.path.abspath('./launcher_cfg_new.yaml')
    src.Config_Manager.set_config_path(path_t)
    src.check_admin(src.Config_Manager.config)
    src.app_set(src.Config_Manager.config)
    app = QApplication([])
    config = src.Config_Manager(wkdir=os.getcwd())
    src.UIUpdater._primary_init(config)
    uiupdater = src.UIUpdater()
    launcher = src.ControlLauncher(config, app)
    # uiupdater.update_task.connect(launcher._updateUI)
    launcher.show()
    sys.exit(app.exec_())