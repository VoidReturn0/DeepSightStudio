#!/usr/bin/env python3
"""
maintenance_ui.py

This module provides a pop-up interface for editing the configuration
stored in maintenance.json using the ConfigManager.
Each top-level configuration key is displayed on its own tab within a QGroupBox
with a user-friendly title.
"""

import sys
import json
from PyQt6 import QtWidgets, QtCore
from config_manager import ConfigManager

class MaintenanceDialog(QtWidgets.QDialog):
    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Maintenance / Settings")
        self.resize(600, 400)
        self.move(100, 100)
        self.config_manager = config_manager
        self.widgetMaps = {}

        main_layout = QtWidgets.QVBoxLayout(self)
        self.tabs = QtWidgets.QTabWidget(self)
        main_layout.addWidget(self.tabs)

        for category, settings in self.config_manager.settings.items():
            tab = QtWidgets.QWidget(self)
            tab_layout = QtWidgets.QVBoxLayout(tab)

            group_title = category.replace("_", " ").title()
            group_box = QtWidgets.QGroupBox(group_title, self)
            form_layout = QtWidgets.QFormLayout(group_box)

            if isinstance(settings, dict):
                sub_widgets = {}
                for key, value in settings.items():
                    line_edit = QtWidgets.QLineEdit(self)
                    line_edit.setText(json.dumps(value))
                    form_layout.addRow(f"{key}:", line_edit)
                    sub_widgets[key] = line_edit
                self.widgetMaps[category] = sub_widgets
            else:
                line_edit = QtWidgets.QLineEdit(self)
                line_edit.setText(json.dumps(settings))
                form_layout.addRow(f"{category}:", line_edit)
                self.widgetMaps[category] = line_edit

            tab_layout.addWidget(group_box)
            tab_layout.addStretch()
            self.tabs.addTab(tab, group_title)

        button_layout = QtWidgets.QHBoxLayout()
        self.saveButton = QtWidgets.QPushButton("Save Settings", self)
        self.cancelButton = QtWidgets.QPushButton("Cancel", self)
        button_layout.addStretch()
        button_layout.addWidget(self.saveButton)
        button_layout.addWidget(self.cancelButton)
        main_layout.addLayout(button_layout)

        self.saveButton.clicked.connect(self.saveSettings)
        self.cancelButton.clicked.connect(self.reject)

    def saveSettings(self):
        for category, widget in self.widgetMaps.items():
            if isinstance(widget, dict):
                new_settings = {}
                for key, line_edit in widget.items():
                    text = line_edit.text().strip()
                    try:
                        new_settings[key] = json.loads(text)
                    except json.JSONDecodeError:
                        new_settings[key] = text
                self.config_manager.update_setting([category], new_settings)
            else:
                text = widget.text().strip()
                try:
                    new_value = json.loads(text)
                except json.JSONDecodeError:
                    new_value = text
                self.config_manager.update_setting([category], new_value)
        QtWidgets.QMessageBox.information(self, "Settings Saved", "Configuration updated successfully.")
        self.accept()

def main():
    app = QtWidgets.QApplication(sys.argv)
    config_manager = ConfigManager(filepath="maintenance.json")
    dlg = MaintenanceDialog(config_manager)
    dlg.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
