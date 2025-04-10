#!/usr/bin/env python3
import sys
from PyQt6 import QtWidgets
from PyQt6.QtCore import QProcess
from ui_deepsightstudio import Ui_MainWindow
from config_manager import ConfigManager

def main():
    app = QtWidgets.QApplication(sys.argv)

    # Load configuration, which now includes screen_settings.
    config = ConfigManager(filepath="maintenance.json")
    screen_settings = config.get_setting(["screen_settings"])
    
    # Retrieve screen settings with fallbacks.
    width = screen_settings.get("width", 1200)
    height = screen_settings.get("height", 864)
    scaling = screen_settings.get("scaling", 1.0)
    
    # Create MainWindow and adjust its size based on the screen settings.
    MainWindow = QtWidgets.QMainWindow()
    # Optionally, if you want to apply scaling:
    MainWindow.resize(int(width * scaling), int(height * scaling))
    
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)

    # Function to launch the maintenance UI.
    def openMaintenance():
        print("Maintenance/Settings action triggered. Launching maintenance_ui.py...")
        if not QProcess.startDetached("python", ["maintenance_ui.py"]):
            print("Failed to launch maintenance_ui.py")
    
    # Connect the Settings action to open the maintenance UI.
    ui.actionSettings.triggered.connect(openMaintenance)

    MainWindow.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
