import cv2
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkFont
from PIL import Image, ImageTk
import os
import datetime
import random
import json
import threading
import time
import math
import numpy as np

#####################
# Constants and Config Helpers
#####################

DEFAULT_VIDEO_WIDTH = 1280
DEFAULT_VIDEO_HEIGHT = 720
SETTINGS_PANEL_HEIGHT = 400

def parse_resolution(res_str):
    try:
        w, h = map(int, res_str.lower().split("x"))
        return w, h
    except Exception:
        return DEFAULT_VIDEO_WIDTH, DEFAULT_VIDEO_HEIGHT

def load_config(config_file="maintenance.json"):
    try:
        with open(config_file, "r") as f:
            config = json.load(f)
    except Exception:
        config = {}
    res_str = config.get("camera_settings", {}).get("resolution", f"{DEFAULT_VIDEO_WIDTH}x{DEFAULT_VIDEO_HEIGHT}")
    video_width, video_height = parse_resolution(res_str)
    config["video_width"] = video_width
    config["video_height"] = video_height
    return config

def save_config(config, config_file="maintenance.json"):
    with open(config_file, "w") as f:
        json.dump(config, f, indent=4)

#####################
# Image Augmentation Functions
#####################

def random_variation(frame, alpha_range=(1.0, 1.0), beta_range=(-20, 20)):
    alpha = random.uniform(*alpha_range)
    beta = random.uniform(*beta_range)
    modified = cv2.convertScaleAbs(frame, alpha=alpha, beta=int(beta))
    return modified, alpha, beta

def apply_hsv_adjustment(frame, hue_delta, sat_scale):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:,:,0] = hsv[:,:,0] + hue_delta * 180  # OpenCV hue: 0-180.
    hsv[:,:,1] = hsv[:,:,1] * sat_scale
    hsv = np.clip(hsv, 0, 255).astype(np.uint8)
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

def apply_translation(frame, translate_range):
    h, w = frame.shape[:2]
    tx = random.uniform(*translate_range) * w
    ty = random.uniform(*translate_range) * h
    M = np.float32([[1, 0, int(tx)], [0, 1, int(ty)]])
    translated = cv2.warpAffine(frame, M, (w, h),
                                borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0))
    return translated

def apply_shear(frame, shear_deg):
    h, w = frame.shape[:2]
    shear_rad = math.radians(shear_deg)
    M = np.float32([[1, math.tan(shear_rad), 0],
                    [0, 1, 0]])
    nW = w + int(h * math.tan(shear_rad))
    sheared = cv2.warpAffine(frame, M, (nW, h),
                             borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0))
    sheared = cv2.resize(sheared, (w, h))
    return sheared

def apply_flip(frame, flip_prob):
    if random.random() < flip_prob:
        return cv2.flip(frame, 1)
    return frame

def apply_zoom_centered(frame, zoom_factor, center=None):
    h, w = frame.shape[:2]
    if zoom_factor < 0.001:
        return frame
    new_w = int(w / zoom_factor)
    new_h = int(h / zoom_factor)
    if center is None:
        cx, cy = w // 2, h // 2
    else:
        cx, cy = center
    x1 = max(cx - new_w // 2, 0)
    y1 = max(cy - new_h // 2, 0)
    x2 = min(cx + new_w // 2, w)
    y2 = min(cy + new_h // 2, h)
    cropped = frame[y1:y2, x1:x2]
    return cv2.resize(cropped, (w, h))

def apply_random_rotation(frame, rotation_range):
    angle = random.uniform(*rotation_range)
    h, w = frame.shape[:2]
    center = (w//2, h//2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(frame, M, (w, h), flags=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0))
    return rotated, angle

def create_folder_structure(base_dir, category, label):
    category_folder = os.path.join(base_dir, category)
    if not os.path.exists(category_folder):
        os.makedirs(category_folder)
    label_folder = os.path.join(category_folder, label)
    if not os.path.exists(label_folder):
        os.makedirs(label_folder)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    final_folder = os.path.join(label_folder, timestamp)
    os.makedirs(final_folder)
    return final_folder

#####################
# Main Training Application Class
#####################

class TrainingApp(tk.Tk):
    def __init__(self, config_file="maintenance.json"):
        super().__init__()
        # Set dark background and maximize window
        self.configure(bg="#1e1e1e")
        self.state('zoomed')
        self.config_file = config_file
        self.config_data = load_config(config_file)
        self.video_width = self.config_data["video_width"]
        self.video_height = self.config_data["video_height"]
        self.window_width = self.video_width * 2
        self.window_height = self.video_height + SETTINGS_PANEL_HEIGHT

        self.title("Training Image Capture")
        self.geometry(f"{self.window_width}x{self.window_height}")
        
        # Set minimum window size to prevent shrinking
        self.minsize(800, 600)
        # Set maximum window size to prevent growing
        self.maxsize(1920, 1080)

        # Setup custom fonts (Orbitron if available, else Helvetica)
        available_fonts = tkFont.families()
        if "Orbitron" in available_fonts:
            self.custom_font_large = tkFont.Font(family="Orbitron", size=20, weight="bold")
            self.custom_font_button = tkFont.Font(family="Orbitron", size=14, weight="bold")
        else:
            self.custom_font_large = tkFont.Font(family="Helvetica", size=20, weight="bold")
            self.custom_font_button = tkFont.Font(family="Helvetica", size=14, weight="bold")

        self.running = True
        self.training_thread = None
        self.current_roi = None
        self.training_center = None

        # Open camera using the selected index from JSON
        selected_camera = self.config_data.get("camera_settings", {}).get("selected_camera", 0)
        self.cap = cv2.VideoCapture(selected_camera)
        if not self.cap.isOpened():
            print("Warning: Camera could not be opened. Using fallback blank image.")
            self.cap = None

        # ROI variables
        self.roi = None
        self.start_x = None
        self.start_y = None
        
        # Load existing ROI and center from config if available
        if "current_roi" in self.config_data:
            self.roi = self.config_data["current_roi"]
        if "training_center" in self.config_data:
            self.training_center = self.config_data["training_center"]

        # --- Video Panels ---
        video_container = tk.Frame(self, width=self.window_width, height=self.video_height, bg="#1e1e1e")
        video_container.pack(side=tk.TOP, fill=tk.BOTH)

        # Left panel: Raw Feed
        self.raw_frame = tk.Frame(video_container, bg="#1e1e1e")
        self.raw_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.raw_label = tk.Label(self.raw_frame, bg="#1e1e1e")
        self.raw_label.pack(fill=tk.BOTH, expand=True)

        # Right panel: Processed Output
        self.proc_frame = tk.Frame(video_container, bg="#1e1e1e")
        self.proc_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.proc_label = tk.Label(self.proc_frame, bg="#1e1e1e")
        self.proc_label.pack(fill=tk.BOTH, expand=True)

        # --- Settings Panel ---
        self.settings_frame = tk.Frame(self, bg="#1e1e1e", height=SETTINGS_PANEL_HEIGHT)
        self.settings_frame.pack(side=tk.BOTTOM, fill=tk.X)
        header_label = tk.Label(self.settings_frame, text="Training Settings", font=self.custom_font_large, bg="#1e1e1e", fg="white")
        header_label.pack(pady=10)

        # Category and Label Dropdowns
        options_frame = tk.Frame(self.settings_frame, bg="#1e1e1e")
        options_frame.pack(pady=5)
        tk.Label(options_frame, text="Category:", bg="#1e1e1e", fg="white", font=self.custom_font_button).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.category_var = tk.StringVar(self)
        self.category_var.set("Dominos")
        categories = ["Dominos", "Cards", "Dice"]
        self.category_menu = ttk.Combobox(options_frame, textvariable=self.category_var, values=categories, state="readonly", font=self.custom_font_button)
        self.category_menu.grid(row=0, column=1, padx=5, pady=5)
        self.category_menu.bind("<<ComboboxSelected>>", self.update_label_options)
        tk.Label(options_frame, text="Label:", bg="#1e1e1e", fg="white", font=self.custom_font_button).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.label_var = tk.StringVar(self)
        self.label_options = [f"{i}x{j}" for i in range(7) for j in range(7)]
        self.label_var.set(self.label_options[0])
        self.label_menu = ttk.Combobox(options_frame, textvariable=self.label_var, values=self.label_options, state="readonly", font=self.custom_font_button)
        self.label_menu.grid(row=0, column=3, padx=5, pady=5)

        # --- Augmentation Sliders ---
        training_defaults = self.config_data.get("training_settings", {})
        self.aug_sliders = {}
        slider_frame = tk.Frame(self.settings_frame, bg="#1e1e1e")
        slider_frame.pack(pady=10)
        row_counter = 0
        aug_params = [
            ("num_pictures", "", "num_pictures", "", 1, 1000, 25, 25),
            ("min_rotation", "Min Rotation (deg)", "max_rotation", "Max Rotation (deg)", -65, 65, -15, 15),
            ("min_beta", "Min Brightness Offset", "max_beta", "Max Brightness Offset", -100, 100, -20, 20),
            ("min_alpha", "Min Alpha", "max_alpha", "Max Alpha", 0.1, 3.0, 1.0, 1.0),
            ("min_zoom", "Min Zoom Factor", "max_zoom", "Max Zoom Factor", 0.0, 3.0, 1.0, 1.0),
            ("frame_rate", "Frame Rate (ms)", "frame_rate", "Frame Rate (ms)", 5, 1000, 500, 500),
            ("min_hue", "Min Hue Shift", "max_hue", "Max Hue Shift", -0.1, 0.1, -0.05, 0.05),
            ("min_saturation", "Min Saturation Scale", "max_saturation", "Max Saturation Scale", 0.5, 1.5, 0.9, 1.1),
            ("min_translate", "Min Translate Fraction", "max_translate", "Max Translate Fraction", 0.0, 0.5, 0.0, 0.1),
            ("min_shear", "Min Shear (deg)", "max_shear", "Max Shear (deg)", 0.0, 20.0, 0.0, 5.0),
            ("flip_lr", "Flip LR Prob", "flip_lr", "Flip LR Prob", 0.0, 1.0, 0.5, 0.5)
        ]
        col = 0
        for params in aug_params:
            if params[0] == params[2]:
                key = params[0]
                label_text = params[1] if params[1] else key
                default_value = training_defaults.get(key, params[6])
                tk.Label(slider_frame, text=label_text, bg="#1e1e1e", fg="white", font=self.custom_font_button)\
                    .grid(row=row_counter, column=col, padx=5, pady=5, sticky="w")
                res_val = 0.01 if isinstance(params[6], float) else 1
                slider = tk.Scale(slider_frame, from_=params[4], to=params[5], orient=tk.HORIZONTAL,
                                  resolution=res_val, length=150, bg="#1e1e1e", fg="white", font=self.custom_font_button)
                slider.set(default_value)
                slider.grid(row=row_counter, column=col+1, padx=5, pady=5)
                self.aug_sliders[key] = slider
                col += 2
            else:
                key_min, label_min, key_max, label_max, min_range, max_range, default_min, default_max = params
                default_min = training_defaults.get(key_min, default_min)
                default_max = training_defaults.get(key_max, default_max)
                tk.Label(slider_frame, text=label_min, bg="#1e1e1e", fg="white", font=self.custom_font_button)\
                    .grid(row=row_counter, column=col, padx=5, pady=5, sticky="w")
                res_val = 0.01 if isinstance(default_min, float) else 1
                slider_min = tk.Scale(slider_frame, from_=min_range, to=max_range, orient=tk.HORIZONTAL,
                                      resolution=res_val, length=150, bg="#1e1e1e", fg="white", font=self.custom_font_button)
                slider_min.set(default_min)
                slider_min.grid(row=row_counter, column=col+1, padx=5, pady=5)
                self.aug_sliders[key_min] = slider_min
                col += 2

                tk.Label(slider_frame, text=label_max, bg="#1e1e1e", fg="white", font=self.custom_font_button)\
                    .grid(row=row_counter, column=col, padx=5, pady=5, sticky="w")
                res_val = 0.01 if isinstance(default_max, float) else 1
                slider_max = tk.Scale(slider_frame, from_=min_range, to=max_range, orient=tk.HORIZONTAL,
                                      resolution=res_val, length=150, bg="#1e1e1e", fg="white", font=self.custom_font_button)
                slider_max.set(default_max)
                slider_max.grid(row=row_counter, column=col+1, padx=5, pady=5)
                self.aug_sliders[key_max] = slider_max
                col += 2

            if col >= 8:
                row_counter += 1
                col = 0

        # --- Control Buttons ---
        button_frame = tk.Frame(self.settings_frame, bg="#1e1e1e")
        button_frame.pack(pady=10)
        self.train_button = tk.Button(button_frame, text="Train", command=self.start_training,
                                      font=self.custom_font_button, bg="#333333", fg="white")
        self.train_button.grid(row=0, column=0, padx=10, pady=10)
        self.save_button = tk.Button(button_frame, text="Save Training Settings", command=self.save_training_settings,
                                     font=self.custom_font_button, bg="#333333", fg="white")
        self.save_button.grid(row=0, column=1, padx=10, pady=10)
        self.status_label = tk.Label(button_frame, text="Status: Waiting", bg="#1e1e1e", fg="white", font=self.custom_font_button)
        self.status_label.grid(row=0, column=2, padx=10, pady=10)

        # Bind ROI mouse events on the raw feed panel.
        self.raw_label.bind("<ButtonPress-1>", self.on_mouse_down)
        self.raw_label.bind("<B1-Motion>", self.on_mouse_move)
        self.raw_label.bind("<ButtonRelease-1>", self.on_mouse_up)

        self.delay = 15
        self.after(self.delay, self.update_raw_feed)

    def update_label_options(self, event=None):
        cat = self.category_var.get()
        if cat == "Dominos":
            options = [f"{i}x{j}" for i in range(7) for j in range(7)]
        elif cat == "Cards":
            ranks = [str(n) for n in range(2,11)] + ['J','Q','K','A']
            suits = ['H', 'S', 'D', 'C']
            options = [f"{s}{r}" for s in suits for r in ranks]
            options.append("Joker")
        elif cat == "Dice":
            options = [str(n) for n in range(1,7)]
        else:
            options = []
        self.label_options = options
        self.label_menu.config(values=options)
        if options:
            self.label_var.set(options[0])
        else:
            self.label_var.set("")

    def get_aug_params(self):
        params = {}
        for key, slider in self.aug_sliders.items():
            params[key] = slider.get()
        return params

    # --- ROI Mouse Handlers ---
    def on_mouse_down(self, event):
        # Get label dimensions to calculate scaling
        label_width = self.raw_label.winfo_width()
        label_height = self.raw_label.winfo_height()
        
        # Adjust coordinates based on the actual displayed image size
        if label_width > 1 and label_height > 1:
            scale_x = self.video_width / label_width
            scale_y = self.video_height / label_height
            self.start_x = int(event.x * scale_x)
            self.start_y = int(event.y * scale_y)
        else:
            self.start_x = event.x
            self.start_y = event.y
        
        self.roi = None

    def on_mouse_move(self, event):
        if self.start_x is None or self.start_y is None:
            return
            
        # Get label dimensions to calculate scaling
        label_width = self.raw_label.winfo_width()
        label_height = self.raw_label.winfo_height()
        
        # Adjust coordinates based on the actual displayed image size
        if label_width > 1 and label_height > 1:
            scale_x = self.video_width / label_width
            scale_y = self.video_height / label_height
            current_x = int(event.x * scale_x)
            current_y = int(event.y * scale_y)
        else:
            current_x = event.x
            current_y = event.y
            
        self.roi = (min(self.start_x, current_x), min(self.start_y, current_y),
                   max(self.start_x, current_x), max(self.start_y, current_y))
        self.update_display()

    def on_mouse_up(self, event):
        if self.start_x is None or self.start_y is None:
            return
            
        # Get label dimensions to calculate scaling
        label_width = self.raw_label.winfo_width()
        label_height = self.raw_label.winfo_height()
        
        # Adjust coordinates based on the actual displayed image size
        if label_width > 1 and label_height > 1:
            scale_x = self.video_width / label_width
            scale_y = self.video_height / label_height
            current_x = int(event.x * scale_x)
            current_y = int(event.y * scale_y)
        else:
            current_x = event.x
            current_y = event.y
            
        self.roi = (min(self.start_x, current_x), min(self.start_y, current_y),
                   max(self.start_x, current_x), max(self.start_y, current_y))
                   
        self.training_center = ((self.roi[0] + self.roi[2]) // 2, (self.roi[1] + self.roi[3]) // 2)
        self.config_data["current_roi"] = self.roi
        self.config_data["training_center"] = self.training_center
        save_config(self.config_data, self.config_file)
        print("ROI set to:", self.roi, "Center:", self.training_center)
        self.update_display()

    def update_display(self):
        """Update the display with ROI and crosshair."""
        ret, frame = (self.cap.read() if self.cap is not None else (False, None))
        if not ret:
            return
        
        # Create a copy of the frame to draw on
        display_frame = frame.copy()
        display_frame = cv2.resize(display_frame, (self.video_width, self.video_height))
        
        # Draw ROI rectangle if it exists
        if self.roi:
            x1, y1, x2, y2 = self.roi
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            
            # Draw green crosshair at center of ROI
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            cross_size = 15
            cross_color = (0, 255, 0)  # Green
            cv2.line(display_frame, (center_x - cross_size, center_y), (center_x + cross_size, center_y), cross_color, 2)
            cv2.line(display_frame, (center_x, center_y - cross_size), (center_x, center_y + cross_size), cross_color, 2)
        
        # Convert to RGB and update the display
        display_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        self.update_image(self.raw_label, display_rgb, (self.video_width, self.video_height))

    def update_raw_feed(self):
        if not self.running:
            return
        ret, frame = (self.cap.read() if self.cap is not None else (False, None))
        if ret:
            # Resize the frame to the fixed display dimensions
            frame_resized = cv2.resize(frame, (self.video_width, self.video_height))
            display_frame = frame_resized.copy()
            
            # Draw ROI and crosshair if they exist
            if self.roi:
                x1, y1, x2, y2 = self.roi
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                
                # Draw green crosshair at center of ROI
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                cross_size = 15
                cross_color = (0, 255, 0)  # Green
                cv2.line(display_frame, (center_x - cross_size, center_y), (center_x + cross_size, center_y), cross_color, 2)
                cv2.line(display_frame, (center_x, center_y - cross_size), (center_x, center_y + cross_size), cross_color, 2)
            
            # Convert to RGB for display
            video_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            
            # Use fixed dimensions for display
            self.update_image(self.raw_label, video_rgb, (self.video_width, self.video_height))
        else:
            blank = 255 * np.ones((self.video_height, self.video_width, 3), dtype="uint8")
            self.update_image(self.raw_label, blank, (self.video_width, self.video_height))
        
        self.after(self.delay, self.update_raw_feed)

    def update_image(self, label, cv_img, size):
        if cv_img.size == 0:
            cv_img = 255 * np.ones((size[1], size[0], 3), dtype="uint8")
        # Maintain aspect ratio when resizing
        h, w = cv_img.shape[:2]
        target_w, target_h = size
        
        # Calculate scaling to fit within the target size while preserving aspect ratio
        scale = min(target_w / w, target_h / h)
        new_w, new_h = int(w * scale), int(h * scale)
        
        # Resize the image to fit within the label while maintaining aspect ratio
        img = Image.fromarray(cv_img).resize((new_w, new_h), Image.LANCZOS)
        imgtk = ImageTk.PhotoImage(image=img)
        label.imgtk = imgtk
        label.configure(image=imgtk)

    def start_training(self):
        # Use model weights from json
        model_weights = self.model_var.get()
        data_config = self.data_config_var.get().strip()
        img_size = self.img_size_var.get().strip()
        batch = self.batch_var.get().strip()
        epochs = self.epochs_var.get().strip()
        project = self.project_var.get().strip()
        
        if not data_config or not os.path.exists(data_config):
            messagebox.showerror("Input Error", "Please select a valid data config file.")
            return
        
        command = ["python", TRAIN_SCRIPT,
                "--img", img_size,
                "--batch", batch,
                "--epochs", epochs,
                "--data", data_config,
                "--weights", model_weights,
                "--project", project]
        
        self.output_text.insert(tk.END, f"Executing command:\n{' '.join(command)}\n\n")
        self.output_text.see(tk.END)
        
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in process.stdout:
                self.output_text.insert(tk.END, line)
                self.output_text.see(tk.END)
                self.update()
            process.wait()
            self.output_text.insert(tk.END, "\nTraining process completed.\n")
            # After training, update the metrics from the last run.
            self.update_last_metrics()
        except Exception as e:
            messagebox.showerror("Execution Error", f"An error occurred:\n{e}")

    def training_capture_loop(self):
        print("Starting training capture loop...")
        self.status_label.config(text="Status: Capturing images...")
        category = self.category_var.get()
        label_name = self.label_var.get()
        base_dir = "training_data"
        target_folder = create_folder_structure(base_dir, category, label_name)
        self.status_label.config(text=f"Saving to {target_folder}")

        aug = self.get_aug_params()
        num_captures = int(aug["num_pictures"])
        rotation_range = (aug["min_rotation"], aug["max_rotation"])
        beta_range = (aug["min_beta"], aug["max_beta"])
        alpha_range = (aug["min_alpha"], aug["max_alpha"])
        zoom_range = (aug["min_zoom"], aug["max_zoom"])
        frame_rate = aug["frame_rate"]
        hue_range = (aug["min_hue"], aug["max_hue"])
        sat_range = (aug["min_saturation"], aug["max_saturation"])
        translate_range = (aug["min_translate"], aug["max_translate"])
        shear_range = (aug["min_shear"], aug["max_shear"])
        flip_prob = aug["flip_lr"]
        interval = frame_rate / 1000.0

        current_config = load_config(self.config_file)
        current_roi = current_config.get("current_roi", None)

        for i in range(num_captures):
            if not self.running:
                break
            start_time = time.time()
            ret, frame = (self.cap.read() if self.cap is not None else (False, None))
            if not ret:
                print("Frame read failed at iteration", i)
                continue
            frame = cv2.resize(frame, (self.video_width, self.video_height))
            print(f"Iteration {i}: Frame captured in {time.time()-start_time:.3f} sec")

            # 1. Crop to ROI if defined; otherwise use full frame.
            if current_roi:
                x1, y1, x2, y2 = current_roi
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(self.video_width, x2)
                y2 = min(self.video_height, y2)
                cropped = frame[y1:y2, x1:x2]
            else:
                cropped = frame

            # 2. Apply zoom on the cropped image.
            zoom_factor = random.uniform(*zoom_range)
            if zoom_factor < 0.001:
                zoomed = cropped
            else:
                crop_h, crop_w = cropped.shape[:2]
                center = (crop_w // 2, crop_h // 2)
                zoomed = apply_zoom_centered(cropped, zoom_factor, center=center)
                print(f"Iteration {i}: Cropped ROI size ({crop_w}x{crop_h}), Zoom factor: {zoom_factor:.2f}")

            # 3. Brightness/contrast adjustment.
            varied, used_alpha, used_beta = random_variation(zoomed, alpha_range=alpha_range, beta_range=beta_range)
            # 4. Hue and saturation adjustment.
            hue_shift = random.uniform(*hue_range)
            sat_scale = random.uniform(*sat_range)
            hsv_adjusted = apply_hsv_adjustment(varied, hue_shift, sat_scale)
            # 5. Translation.
            translated = apply_translation(hsv_adjusted, translate_range)
            # 6. Shear.
            shear_val = random.uniform(*shear_range)
            sheared = apply_shear(translated, shear_val)
            # 7. Horizontal flip.
            flipped = apply_flip(sheared, flip_prob)
            # 8. Rotation.
            rotated, used_angle = apply_random_rotation(flipped, rotation_range)
            proc_frame = rotated

            proc_disp = cv2.resize(proc_frame, (self.video_width, self.video_height))
            proc_rgb = cv2.cvtColor(proc_disp, cv2.COLOR_BGR2RGB)
            self.update_image(self.proc_label, proc_rgb, (self.video_width, self.video_height))

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = os.path.join(target_folder, f"{label_name}_{i}_{timestamp}.jpg")
            cv2.imwrite(filename, proc_frame)
            print(f"Saved image {i} to {filename} (Rotation: {used_angle:.2f}°)")
            elapsed = time.time() - start_time
            print(f"Iteration {i} took {elapsed:.3f} sec")
            time.sleep(max(0, interval - elapsed))

        self.status_label.config(text="Status: Training capture complete.")
        print("Training capture loop complete.")

    def save_training_settings(self):
        aug_params = {}
        for key, slider in self.aug_sliders.items():
            aug_params[key] = slider.get()
        self.config_data["training_settings"] = aug_params
        save_config(self.config_data, self.config_file)
        self.status_label.config(text="Status: Training settings saved.")
        print("Training settings saved:", aug_params)

    def on_close(self):
        print("Closing application...")
        self.running = False
        if self.training_thread and self.training_thread.is_alive():
            self.training_thread.join(timeout=2)
        if self.cap is not None:
            self.cap.release()
        self.destroy()

if __name__ == "__main__":
    app = TrainingApp(config_file="maintenance.json")
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()