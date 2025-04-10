#!/usr/bin/env python3
"""
config_manager.py

This module provides a ConfigManager class that encapsulates interactions
with a JSON configuration file. It supports:
  - Loading settings and merging with defaults.
  - Saving updated settings (creating the file if it doesn't exist).
  - Updating nested settings via a list of keys.
  - Notifying registered callbacks on file changes.
  - Watching the configuration file for external updates using watchdog.

Usage:
    from config_manager import ConfigManager
    config = ConfigManager(filepath="maintenance.json")
    camera_index = config.get_setting(["camera_settings", "selected_camera"])
    config.update_setting(["camera_settings", "selected_camera"], 1)
"""

import json
import os
import threading
import time
from typing import Any, Callable, Dict, List, Optional

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False


class ConfigFileHandler(FileSystemEventHandler):
    def __init__(self, callback: Callable[[], None]):
        super().__init__()
        self.callback = callback

    def on_modified(self, event):
        if not event.is_directory:
            self.callback()


class ConfigManager:
    def __init__(self, filepath: str = "maintenance.json", defaults: Optional[Dict[str, Any]] = None):
        self.filepath = os.path.abspath(filepath)
        self._callbacks: List[Callable[[], None]] = []
        self._lock = threading.RLock()

        if defaults is None:
            defaults = {
                "camera_settings": {"selected_camera": 0, "resolution": "1920x1080"},
                "current_roi": [0, 0, 640, 480],
                "training_center": [320, 240],
                "labeling_settings": {
                    "canny_threshold1": {"min": 0, "max": 750, "value": 475},
                    "canny_threshold2": {"min": 0, "max": 750, "value": 400},
                },
                "training_settings": {
                    "model_used": "YOLOv5",
                    "model_weights": "yolov5s.pt",
                    "data_config": "yolo_training_data/data.yaml",
                    "img_size": "640",
                    "batch_size": "8",
                    "epochs": "1",
                    "project_name": "yolo_training_data"
                },
                "hardware_settings": {
                    "com_port": "COM9",
                    "baud_rate": "115200"
                },
                "video_width": 640,
                "video_height": 480,
                "screen_settings": {
                    "width": 1200,
                    "height": 864,
                    "scaling": 1.0
                }
            }
        self.defaults = defaults
        self.settings = self.load_settings()
        #self.save_settings()  # Persist merged defaults (creates file if missing)

        if WATCHDOG_AVAILABLE:
            self._observer = Observer()
            event_handler = ConfigFileHandler(self._on_file_modified)
            config_dir = os.path.dirname(self.filepath) or "."
            self._observer.schedule(event_handler, path=config_dir, recursive=False)
            self._observer.start()
        else:
            self._observer = None

    def load_settings(self) -> Dict[str, Any]:
        if os.path.exists(self.filepath):
            try:
                file_size = os.stat(self.filepath).st_size
                print(f"Loading configuration from {self.filepath}, size = {file_size} bytes")
                if file_size == 0:
                    print(f"Configuration file {self.filepath} is empty. Using default settings.")
                    return self.defaults.copy()
                with open(self.filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    print(f"File content starts with: {content[:100]!r}")
                    settings = json.loads(content)
                return self._merge_defaults(settings, self.defaults)
            except Exception as e:
                print(f"Error loading configuration file: {e}. Using default settings.")
                return self.defaults.copy()
        else:
            print(f"Configuration file {self.filepath} not found. Using default settings.")
            return self.defaults.copy()

    def _merge_defaults(self, settings: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]:
        for key, default_value in defaults.items():
            if key not in settings:
                settings[key] = default_value
            elif isinstance(default_value, dict) and isinstance(settings.get(key), dict):
                settings[key] = self._merge_defaults(settings[key], default_value)
        return settings

    def save_settings(self) -> None:
        with self._lock:
            try:
                with open(self.filepath, "w", encoding="utf-8") as f:
                    json.dump(self.settings, f, indent=4)
                print(f"Configuration saved to {self.filepath}")
            except Exception as e:
                print(f"Error saving configuration: {e}")

    def update_setting(self, key_path: List[str], value: Any) -> None:
        with self._lock:
            d = self.settings
            for key in key_path[:-1]:
                d = d.setdefault(key, {})
            d[key_path[-1]] = value
            self.save_settings()
            self._notify_callbacks()

    def get_setting(self, key_path: List[str]) -> Any:
        d = self.settings
        for key in key_path:
            d = d.get(key)
            if d is None:
                return None
        return d

    def register_callback(self, callback: Callable[[], None]) -> None:
        self._callbacks.append(callback)

    def _notify_callbacks(self) -> None:
        for callback in self._callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Error in callback: {e}")

    def _on_file_modified(self):
        with self._lock:
            new_settings = self.load_settings()
            if new_settings != self.settings:
                self.settings = new_settings
                self._notify_callbacks()

    def stop_watching(self) -> None:
        if self._observer is not None:
            self._observer.stop()
            self._observer.join()


if __name__ == "__main__":
    config = ConfigManager()
    print("Initial Configuration:")
    print(config.settings)

    def on_update():
        print("Configuration updated:")
        print(config.settings)
    config.register_callback(on_update)

    config.update_setting(["camera_settings", "selected_camera"], 1)
    print("Updated camera index to 1.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        config.stop_watching()
        print("Stopped watching configuration file.")
