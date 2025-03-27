import os
import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk, filedialog, messagebox
import subprocess
import ctypes  # For loading the font on Windows
from PIL import Image, ImageTk
import json
import serial.tools.list_ports  # For COM port listing

# Utility function to load a TTF font at runtime on Windows
def load_custom_font(font_path):
    if os.name == "nt":
        FR_PRIVATE = 0x10
        FR_NOT_ENUM = 0x20
        try:
            ctypes.windll.gdi32.AddFontResourceExW(font_path, FR_PRIVATE, 0)
        except Exception as e:
            print(f"Could not load font {font_path} via AddFontResourceExW: {e}")

# Helper function to load maintenance.json config
def load_maintenance_config(config_file="maintenance.json"):
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {}

# Main GUI
class DeepSightStudio(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DeepSight Studio")
        self.geometry("1000x800")
        self.configure(bg="#1e1e1e")

        # Load custom font if available.
        font_file = "Orbitron-VariableFont_wght.ttf"
        if os.path.exists(font_file):
            load_custom_font(font_file)
        else:
            print(f"Warning: {font_file} not found.")

        available_families = tkFont.families()
        if "Orbitron" in available_families:
            self.custom_font_large = tkFont.Font(family="Orbitron", size=28, weight="bold")
            self.custom_font_button = tkFont.Font(family="Orbitron", size=18, weight="bold")
        elif "Orbitron Variable" in available_families:
            self.custom_font_large = tkFont.Font(family="Orbitron Variable", size=28, weight="bold")
            self.custom_font_button = tkFont.Font(family="Orbitron Variable", size=18, weight="bold")
        else:
            messagebox.showwarning("Font Warning", "Orbitron not found; using Helvetica fallback.")
            self.custom_font_large = ("Helvetica", 28, "bold")
            self.custom_font_button = ("Helvetica", 18, "bold")

        self.create_widgets()

    def create_widgets(self):
        # Load header image resized to 275x275
        try:
            ouroboros_img = Image.open("DeepSightStudio.jpg")
            try:
                resample_method = Image.Resampling.LANCZOS
            except AttributeError:
                resample_method = Image.LANCZOS
            ouroboros_img = ouroboros_img.resize((275, 275), resample_method)
            self.ouroboros_photo = ImageTk.PhotoImage(ouroboros_img)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load DeepSightStudio.jpg:\n{e}")
            self.ouroboros_photo = None

        # Header frame with image and title
        header_frame = tk.Frame(self, bg="#1e1e1e")
        header_frame.pack(pady=20)
        if self.ouroboros_photo:
            left_img = tk.Label(header_frame, image=self.ouroboros_photo, bg="#1e1e1e")
            left_img.grid(row=0, column=0, padx=10)
        shadow_label = tk.Label(header_frame, text="DeepSight Studio",
                                font=self.custom_font_large, bg="#1e1e1e", fg="#000000")
        shadow_label.grid(row=0, column=1, padx=(12,10), pady=(12,10))
        title_label = tk.Label(header_frame, text="DeepSight Studio",
                               font=self.custom_font_large, bg="#1e1e1e", fg="white")
        title_label.grid(row=0, column=1, padx=(10,10), pady=(10,10))
        if self.ouroboros_photo:
            right_img = tk.Label(header_frame, image=self.ouroboros_photo, bg="#1e1e1e")
            right_img.grid(row=0, column=2, padx=10)

        # Main buttons frame (vertical stack)
        button_frame = tk.Frame(self, bg="#1e1e1e")
        button_frame.pack(pady=20)
        btn_acquisition = tk.Button(button_frame, text="Vision Acquisition",
                                    font=self.custom_font_button, width=25,
                                    command=lambda: subprocess.Popen(["python", "image_acquisition.py"], cwd=os.getcwd()))
        btn_acquisition.grid(row=0, column=0, padx=10, pady=10)
        btn_labeling = tk.Button(button_frame, text="Data Labeling",
                                 font=self.custom_font_button, width=25,
                                 command=lambda: subprocess.Popen(["python", "image_labeling.py"], cwd=os.getcwd()))
        btn_labeling.grid(row=1, column=0, padx=10, pady=10)
        btn_hardware = tk.Button(button_frame, text="Training Hardware",
                                 font=self.custom_font_button, width=25,
                                 command=lambda: subprocess.Popen(["python", "training_hardware.py"], cwd=os.getcwd()))
        btn_hardware.grid(row=2, column=0, padx=10, pady=10)
        btn_training = tk.Button(button_frame, text="Training Session",
                                 font=self.custom_font_button, width=25,
                                 command=lambda: subprocess.Popen(["python", "training_session.py"], cwd=os.getcwd()))
        btn_training.grid(row=3, column=0, padx=10, pady=10)
        btn_maintenance = tk.Button(button_frame, text="Maintenance Settings",
                                    font=self.custom_font_button, width=25,
                                    command=self.launch_maintenance_settings)
        btn_maintenance.grid(row=4, column=0, padx=10, pady=10)
        btn_exit = tk.Button(button_frame, text="Exit",
                             font=self.custom_font_button, width=25,
                             command=self.quit)
        btn_exit.grid(row=5, column=0, padx=10, pady=10)

    def launch_maintenance_settings(self):
        MaintenanceSettings(self)

# Maintenance Settings window with 4 buttons.
class MaintenanceSettings(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Maintenance Settings")
        self.geometry("400x350")
        self.configure(bg="#1e1e1e")
        self.create_widgets()

    def create_widgets(self):
        header = tk.Label(self, text="Maintenance Settings", font=("Helvetica", 18, "bold"),
                          bg="#1e1e1e", fg="white")
        header.pack(pady=10)
        btn_frame = tk.Frame(self, bg="#1e1e1e")
        btn_frame.pack(pady=20)
        btn_vision = tk.Button(btn_frame, text="Vision Settings", font=("Helvetica", 14), width=20,
                               command=lambda: VisionSettingsWindow(self))
        btn_vision.pack(pady=5)
        btn_labeling = tk.Button(btn_frame, text="Labeling Settings", font=("Helvetica", 14), width=20,
                                 command=lambda: LabelingSettingsWindow(self))
        btn_labeling.pack(pady=5)
        btn_hardware = tk.Button(btn_frame, text="Hardware Settings", font=("Helvetica", 14), width=20,
                                 command=lambda: HardwareSettingsWindow(self))
        btn_hardware.pack(pady=5)
        btn_training = tk.Button(btn_frame, text="Training Settings", font=("Helvetica", 14), width=20,
                                 command=lambda: TrainingSettingsWindow(self))
        btn_training.pack(pady=5)

# Vision Settings window.
class VisionSettingsWindow(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Vision Settings")
        self.geometry("400x250")
        self.configure(bg="#1e1e1e")
        self.config_data = load_maintenance_config("maintenance.json")
        cam_settings = self.config_data.get("camera_settings", {})
        self.default_camera = cam_settings.get("selected_camera", 0)
        self.default_resolution = cam_settings.get("resolution", "640x480")
        self.create_widgets()

    def create_widgets(self):
        header = tk.Label(self, text="Vision Settings", font=("Helvetica", 16, "bold"),
                          bg="#1e1e1e", fg="white")
        header.pack(pady=10)
        frame_cam = tk.Frame(self, bg="#1e1e1e")
        frame_cam.pack(pady=5, fill="x", padx=10)
        tk.Label(frame_cam, text="Camera Index:", bg="#1e1e1e", fg="white", font=("Helvetica", 12)).pack(side="left")
        self.camera_var = tk.StringVar()
        available = self.get_available_cameras()
        self.camera_combo = ttk.Combobox(frame_cam, textvariable=self.camera_var, values=available, state="readonly", width=10)
        self.camera_combo.pack(side="left", padx=10)
        if available:
            if str(self.default_camera) in available:
                self.camera_combo.set(str(self.default_camera))
            else:
                self.camera_combo.current(0)
        frame_res = tk.Frame(self, bg="#1e1e1e")
        frame_res.pack(pady=5, fill="x", padx=10)
        tk.Label(frame_res, text="Resolution:", bg="#1e1e1e", fg="white", font=("Helvetica", 12)).pack(side="left")
        self.resolution_var = tk.StringVar()
        common_res = ["640x480", "800x600", "1024x768", "1280x720", "1280x800", "1366x768", "1920x1080"]
        self.resolution_combo = ttk.Combobox(frame_res, textvariable=self.resolution_var, values=common_res, state="readonly", width=12)
        self.resolution_combo.pack(side="left", padx=10)
        if self.default_resolution in common_res:
            self.resolution_combo.set(self.default_resolution)
        else:
            self.resolution_combo.current(0)
        btn_preview = tk.Button(self, text="Preview", font=("Helvetica", 14), command=self.preview_camera)
        btn_preview.pack(pady=10)
        btn_save = tk.Button(self, text="Save Settings", font=("Helvetica", 14), command=self.save_settings)
        btn_save.pack(pady=10)

    def get_available_cameras(self):
        import cv2
        available = []
        for i in range(5):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap is not None and cap.isOpened():
                available.append(str(i))
                cap.release()
        if not available:
            available.append("0")
        return available

    def preview_camera(self):
        import cv2
        cam_index = int(self.camera_var.get())
        cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            messagebox.showerror("Error", "Unable to open camera.")
            return
        cv2.namedWindow("Camera Preview", cv2.WINDOW_NORMAL)
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            try:
                res = self.resolution_var.get().split("x")
                width, height = int(res[0]), int(res[1])
            except Exception:
                width, height = 640, 480
            frame = cv2.resize(frame, (width, height))
            cv2.imshow("Camera Preview", frame)
            key = cv2.waitKey(30) & 0xFF
            if key == 27 or cv2.getWindowProperty("Camera Preview", cv2.WND_PROP_VISIBLE) < 1:
                break
        cap.release()
        cv2.destroyAllWindows()

    def save_settings(self):
        settings = {
            "selected_camera": int(self.camera_var.get()),
            "resolution": self.resolution_var.get()
        }
        self.save_to_json(settings, "camera_settings")
        messagebox.showinfo("Saved", "Vision settings saved.")
        self.destroy()

    def save_to_json(self, settings, key):
        maintenance_file = "maintenance.json"
        if os.path.exists(maintenance_file):
            with open(maintenance_file, "r") as f:
                data = json.load(f)
        else:
            data = {}
        data[key] = settings
        with open(maintenance_file, "w") as f:
            json.dump(data, f, indent=4)

# Labeling Settings window with additional fields for actual Canny values.
class LabelingSettingsWindow(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Labeling Settings")
        self.geometry("400x300")
        self.configure(bg="#1e1e1e")
        self.config_data = load_maintenance_config("maintenance.json")
        self.labeling_settings = self.config_data.get("labeling_settings", {})
        self.create_widgets()

    def create_widgets(self):
        header = tk.Label(self, text="Labeling Settings", font=("Helvetica", 16, "bold"),
                          bg="#1e1e1e", fg="white")
        header.pack(pady=10)
        frame_thresh1 = tk.Frame(self, bg="#1e1e1e")
        frame_thresh1.pack(pady=5, fill="x", padx=10)
        tk.Label(frame_thresh1, text="Canny 1 Min:", bg="#1e1e1e", fg="white", font=("Helvetica", 12)).pack(side="left")
        self.thresh1_min = tk.Spinbox(frame_thresh1, from_=0, to=300, width=5)
        self.thresh1_min.pack(side="left", padx=5)
        tk.Label(frame_thresh1, text="Max:", bg="#1e1e1e", fg="white", font=("Helvetica", 12)).pack(side="left")
        self.thresh1_max = tk.Spinbox(frame_thresh1, from_=0, to=300, width=5)
        self.thresh1_max.pack(side="left", padx=5)
        frame_thresh1_val = tk.Frame(self, bg="#1e1e1e")
        frame_thresh1_val.pack(pady=5, fill="x", padx=10)
        tk.Label(frame_thresh1_val, text="Canny 1 Value:", bg="#1e1e1e", fg="white", font=("Helvetica", 12)).pack(side="left")
        self.thresh1_val = tk.Entry(frame_thresh1_val, width=10, font=("Helvetica", 12))
        self.thresh1_val.pack(side="left", padx=5)
        self.thresh1_min.delete(0, tk.END)
        self.thresh1_min.insert(0, self.labeling_settings.get("canny_threshold1", {}).get("min", 0))
        self.thresh1_max.delete(0, tk.END)
        self.thresh1_max.insert(0, self.labeling_settings.get("canny_threshold1", {}).get("max", 300))
        self.thresh1_val.delete(0, tk.END)
        self.thresh1_val.insert(0, self.labeling_settings.get("canny_threshold1", {}).get("value", 100))
        frame_thresh2 = tk.Frame(self, bg="#1e1e1e")
        frame_thresh2.pack(pady=5, fill="x", padx=10)
        tk.Label(frame_thresh2, text="Canny 2 Min:", bg="#1e1e1e", fg="white", font=("Helvetica", 12)).pack(side="left")
        self.thresh2_min = tk.Spinbox(frame_thresh2, from_=0, to=300, width=5)
        self.thresh2_min.pack(side="left", padx=5)
        tk.Label(frame_thresh2, text="Max:", bg="#1e1e1e", fg="white", font=("Helvetica", 12)).pack(side="left")
        self.thresh2_max = tk.Spinbox(frame_thresh2, from_=0, to=300, width=5)
        self.thresh2_max.pack(side="left", padx=5)
        frame_thresh2_val = tk.Frame(self, bg="#1e1e1e")
        frame_thresh2_val.pack(pady=5, fill="x", padx=10)
        tk.Label(frame_thresh2_val, text="Canny 2 Value:", bg="#1e1e1e", fg="white", font=("Helvetica", 12)).pack(side="left")
        self.thresh2_val = tk.Entry(frame_thresh2_val, width=10, font=("Helvetica", 12))
        self.thresh2_val.pack(side="left", padx=5)
        self.thresh2_min.delete(0, tk.END)
        self.thresh2_min.insert(0, self.labeling_settings.get("canny_threshold2", {}).get("min", 0))
        self.thresh2_max.delete(0, tk.END)
        self.thresh2_max.insert(0, self.labeling_settings.get("canny_threshold2", {}).get("max", 300))
        self.thresh2_val.delete(0, tk.END)
        self.thresh2_val.insert(0, self.labeling_settings.get("canny_threshold2", {}).get("value", 200))
        btn_save = tk.Button(self, text="Save Settings", font=("Helvetica", 14), command=self.save_settings)
        btn_save.pack(pady=10)

    def save_settings(self):
        settings = {
            "canny_threshold1": {
                "min": int(self.thresh1_min.get()),
                "max": int(self.thresh1_max.get()),
                "value": int(self.thresh1_val.get())
            },
            "canny_threshold2": {
                "min": int(self.thresh2_min.get()),
                "max": int(self.thresh2_max.get()),
                "value": int(self.thresh2_val.get())
            }
        }
        self.save_to_json(settings, "labeling_settings")
        messagebox.showinfo("Saved", "Labeling settings saved.")
        self.destroy()

    def save_to_json(self, settings, key):
        maintenance_file = "maintenance.json"
        if os.path.exists(maintenance_file):
            with open(maintenance_file, "r") as f:
                data = json.load(f)
        else:
            data = {}
        data[key] = settings
        with open(maintenance_file, "w") as f:
            json.dump(data, f, indent=4)

# Hardware Settings window with geometry set to 600x200.
class HardwareSettingsWindow(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Hardware Settings")
        self.geometry("600x200")
        self.configure(bg="#1e1e1e")
        self.config_data = load_maintenance_config("maintenance.json")
        self.hardware_settings = self.config_data.get("hardware_settings", {})
        self.create_widgets()

    def create_widgets(self):
        header = tk.Label(self, text="Hardware Settings", font=("Helvetica", 16, "bold"),
                          bg="#1e1e1e", fg="white")
        header.pack(pady=10)
        frame_com = tk.Frame(self, bg="#1e1e1e")
        frame_com.pack(pady=5, padx=10, fill="x")
        tk.Label(frame_com, text="COM Port:", bg="#1e1e1e", fg="white", font=("Helvetica", 12)).pack(side="left")
        self.com_var = tk.StringVar()
        ports = self.get_com_ports()
        self.com_combo = ttk.Combobox(frame_com, textvariable=self.com_var, values=ports, state="readonly", width=15)
        self.com_combo.pack(side="left", padx=10)
        if ports:
            default_com = self.hardware_settings.get("com_port", ports[0])
            if default_com in ports:
                self.com_combo.set(default_com)
            else:
                self.com_combo.current(0)
        self.device_label = tk.Label(frame_com, text="", bg="#1e1e1e", fg="white", font=("Helvetica", 12))
        self.device_label.pack(side="left", padx=10)
        frame_baud = tk.Frame(self, bg="#1e1e1e")
        frame_baud.pack(pady=5, padx=10, fill="x")
        tk.Label(frame_baud, text="Baud Rate:", bg="#1e1e1e", fg="white", font=("Helvetica", 12)).pack(side="left")
        self.baud_var = tk.StringVar()
        baud_rates = ["9600", "19200", "38400", "57600", "115200"]
        self.baud_combo = ttk.Combobox(frame_baud, textvariable=self.baud_var, values=baud_rates, state="readonly", width=10)
        self.baud_combo.pack(side="left", padx=10)
        default_baud = self.hardware_settings.get("baud_rate", "115200")
        if default_baud in baud_rates:
            self.baud_combo.set(default_baud)
        else:
            self.baud_combo.current(4)
        btn_save = tk.Button(self, text="Save Settings", font=("Helvetica", 14), command=self.save_settings)
        btn_save.pack(pady=10)
        self.com_combo.bind("<<ComboboxSelected>>", self.update_device_info)
        self.update_device_info()

    def get_com_ports(self):
        ports = serial.tools.list_ports.comports()
        return [f"{port.device}" for port in ports]

    def update_device_info(self, event=None):
        port = self.com_var.get()
        for p in serial.tools.list_ports.comports():
            if p.device == port:
                self.device_label.config(text=p.description)
                return
        self.device_label.config(text="")

    def save_settings(self):
        settings = {
            "com_port": self.com_var.get(),
            "baud_rate": self.baud_var.get()
        }
        self.save_to_json(settings, "hardware_settings")
        messagebox.showinfo("Saved", "Hardware settings saved.")
        self.destroy()

    def save_to_json(self, settings, key):
        maintenance_file = "maintenance.json"
        if os.path.exists(maintenance_file):
            with open(maintenance_file, "r") as f:
                data = json.load(f)
        else:
            data = {}
        data[key] = settings
        with open(maintenance_file, "w") as f:
            json.dump(data, f, indent=4)

# Training Settings window with updated model settings.
class TrainingSettingsWindow(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Training Settings")
        self.geometry("600x350")
        self.configure(bg="#1e1e1e")
        self.custom_weights_filepath = None
        self.config_data = load_maintenance_config("maintenance.json")
        self.training_settings = self.config_data.get("training_settings", {})
        self.create_widgets()

    def create_widgets(self):
        header = tk.Label(self, text="Training Settings", font=("Helvetica", 16, "bold"),
                          bg="#1e1e1e", fg="white")
        header.pack(pady=10)
        # Model Used frame
        frame_model_used = tk.Frame(self, bg="#1e1e1e")
        frame_model_used.pack(pady=5, padx=10, fill="x")
        tk.Label(frame_model_used, text="Model Used:", bg="#1e1e1e", fg="white", font=("Helvetica", 12)).pack(side="left")
        self.model_used_var = tk.StringVar()
        common_models_used = ["YOLOv5", "YOLOv8"]
        self.model_used_combo = ttk.Combobox(frame_model_used, textvariable=self.model_used_var,
                                             values=common_models_used, state="readonly", width=15)
        self.model_used_combo.pack(side="left", padx=10)
        default_used = self.training_settings.get("model_used", common_models_used[0])
        if default_used in common_models_used:
            self.model_used_combo.set(default_used)
        else:
            self.model_used_combo.current(0)
        # Model Weights frame
        frame_model_weights = tk.Frame(self, bg="#1e1e1e")
        frame_model_weights.pack(pady=5, padx=10, fill="x")
        tk.Label(frame_model_weights, text="Model Weights:", bg="#1e1e1e", fg="white", font=("Helvetica", 12)).pack(side="left")
        self.model_weights_var = tk.StringVar()
        common_weights = ["yolov5s.pt", "yolov5m.pt", "yolov5l.pt", "yolov5x.pt", "Custom"]
        self.model_weights_combo = ttk.Combobox(frame_model_weights, textvariable=self.model_weights_var,
                                                values=common_weights, state="readonly", width=15)
        self.model_weights_combo.pack(side="left", padx=10)
        default_weights = self.training_settings.get("model_weights", common_weights[0])
        if default_weights in common_weights:
            self.model_weights_combo.set(default_weights)
        else:
            self.model_weights_combo.set("Custom")
            self.custom_weights_filepath = default_weights
        # When "Custom" is selected, open a file dialog filtering for .pt files.
        self.model_weights_combo.bind("<<ComboboxSelected>>", self.on_model_weights_selected)
        # Data Config with Browse
        frame_data = tk.Frame(self, bg="#1e1e1e")
        frame_data.pack(pady=5, padx=10, fill="x")
        tk.Label(frame_data, text="Data Config:", bg="#1e1e1e", fg="white", font=("Helvetica", 12)).pack(side="left")
        self.data_config_entry = tk.Entry(frame_data, font=("Helvetica", 12))
        self.data_config_entry.pack(side="left", padx=10, fill="x", expand=True)
        default_data_config = self.training_settings.get("data_config", "")
        self.data_config_entry.insert(0, default_data_config)
        btn_data = tk.Button(frame_data, text="Browse", font=("Helvetica", 12), command=self.browse_data_config)
        btn_data.pack(side="left", padx=5)
        # Project Folder with Browse
        frame_proj = tk.Frame(self, bg="#1e1e1e")
        frame_proj.pack(pady=5, padx=10, fill="x")
        tk.Label(frame_proj, text="Project Folder:", bg="#1e1e1e", fg="white", font=("Helvetica", 12)).pack(side="left")
        self.project_entry = tk.Entry(frame_proj, font=("Helvetica", 12))
        self.project_entry.pack(side="left", padx=10, fill="x", expand=True)
        default_proj = self.training_settings.get("project_name", "")
        self.project_entry.insert(0, default_proj)
        btn_proj = tk.Button(frame_proj, text="Browse", font=("Helvetica", 12), command=self.browse_project)
        btn_proj.pack(side="left", padx=5)
        # Other parameters: Image Size, Batch, Epochs
        frame_params = tk.Frame(self, bg="#1e1e1e")
        frame_params.pack(pady=5, padx=10, fill="x")
        tk.Label(frame_params, text="Img Size:", bg="#1e1e1e", fg="white", font=("Helvetica", 12)).grid(row=0, column=0, sticky="w")
        self.img_size_entry = tk.Entry(frame_params, font=("Helvetica", 12), width=10)
        self.img_size_entry.grid(row=0, column=1, padx=5)
        default_img_size = self.training_settings.get("img_size", "640")
        self.img_size_entry.insert(0, default_img_size)
        tk.Label(frame_params, text="Batch:", bg="#1e1e1e", fg="white", font=("Helvetica", 12)).grid(row=0, column=2, sticky="w")
        self.batch_entry = tk.Entry(frame_params, font=("Helvetica", 12), width=10)
        self.batch_entry.grid(row=0, column=3, padx=5)
        default_batch = self.training_settings.get("batch_size", "16")
        self.batch_entry.insert(0, default_batch)
        tk.Label(frame_params, text="Epochs:", bg="#1e1e1e", fg="white", font=("Helvetica", 12)).grid(row=0, column=4, sticky="w")
        self.epochs_entry = tk.Entry(frame_params, font=("Helvetica", 12), width=10)
        self.epochs_entry.grid(row=0, column=5, padx=5)
        default_epochs = self.training_settings.get("epochs", "50")
        self.epochs_entry.insert(0, default_epochs)
        btn_save = tk.Button(self, text="Save Settings", font=("Helvetica", 14), command=self.save_settings)
        btn_save.pack(pady=20)

    def on_model_weights_selected(self, event):
        # When "Custom" is selected, open a file dialog filtering for .pt files.
        if self.model_weights_var.get() == "Custom":
            file_path = filedialog.askopenfilename(title="Select Custom Model Weights",
                                                   filetypes=[("PyTorch Weights", "*.pt")],
                                                   initialdir=os.getcwd())
            if file_path:
                self.custom_weights_filepath = file_path
                messagebox.showinfo("Custom Weights", f"Custom weights file set to:\n{file_path}")
            else:
                self.model_weights_combo.current(0)

    def browse_data_config(self):
        file_path = filedialog.askopenfilename(title="Select Data Config File",
                                               filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*.*")])
        if file_path:
            self.data_config_entry.delete(0, tk.END)
            self.data_config_entry.insert(0, file_path)

    def browse_project(self):
        folder_path = filedialog.askdirectory(title="Select Project Folder")
        if folder_path:
            self.project_entry.delete(0, tk.END)
            self.project_entry.insert(0, folder_path)

    def save_settings(self):
        project_root = os.path.abspath(os.path.dirname(__file__))
        
        # Convert the selected file paths to relative paths
        data_config_abs = self.data_config_entry.get()
        project_abs = self.project_entry.get()
        data_config_rel = os.path.relpath(data_config_abs, project_root)
        project_rel = os.path.relpath(project_abs, project_root)
        
        if self.model_weights_var.get() == "Custom":
            model_weights_abs = self.custom_weights_filepath
            model_weights_rel = os.path.relpath(model_weights_abs, project_root)
        else:
            model_weights_rel = self.model_weights_var.get()
        
        settings = {
            "model_used": self.model_used_var.get() if hasattr(self, "model_used_var") else None,
            "model_weights": model_weights_rel,
            "data_config": data_config_rel,
            "img_size": self.img_size_entry.get(),
            "batch_size": self.batch_entry.get(),
            "epochs": self.epochs_entry.get(),
            "project_name": project_rel
        }
        self.save_to_json(settings, "training_settings")
        messagebox.showinfo("Saved", "Training settings saved.")
        self.destroy()


    def save_to_json(self, settings, key):
        maintenance_file = "maintenance.json"
        if os.path.exists(maintenance_file):
            with open(maintenance_file, "r") as f:
                data = json.load(f)
        else:
            data = {}
        data[key] = settings
        with open(maintenance_file, "w") as f:
            json.dump(data, f, indent=4)

if __name__ == "__main__":
    app = DeepSightStudio()
    app.mainloop()
