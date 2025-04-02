import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinter.font as tkFont
import cv2
import threading
from PIL import Image, ImageTk
import torch
import json

# Utility: Load maintenance config if available
def load_config(config_file="maintenance.json"):
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print("Error loading config:", e)
    return {}

# Utility: Load custom font on Windows
def load_custom_font(font_path):
    import ctypes
    if os.name == "nt" and os.path.exists(font_path):
        FR_PRIVATE = 0x10
        try:
            ctypes.windll.gdi32.AddFontResourceExW(font_path, FR_PRIVATE, 0)
        except Exception as e:
            print(f"Could not load font: {e}")

class VisionTestingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Vision Testing")
        self.configure(bg="#1e1e1e")
        self.geometry("1000x800")

        # Load custom font (e.g., Orbitron) if available
        font_file = "Orbitron-VariableFont_wght.ttf"
        if os.path.exists(font_file):
            load_custom_font(font_file)
        available_fonts = tkFont.families()
        if "Orbitron" in available_fonts:
            self.custom_font_large = tkFont.Font(family="Orbitron", size=28, weight="bold")
            self.custom_font_button = tkFont.Font(family="Orbitron", size=18, weight="bold")
        else:
            self.custom_font_large = tkFont.Font(family="Helvetica", size=28, weight="bold")
            self.custom_font_button = tkFont.Font(family="Helvetica", size=18, weight="bold")

        # Load configuration settings
        self.config_data = load_config()
        self.camera_index = tk.IntVar(value=self.config_data.get("camera_settings", {}).get("selected_camera", 0))
        res_str = self.config_data.get("camera_settings", {}).get("resolution", "640x480")
        self.resolution = tk.StringVar(value=res_str)
        self.model_weights = tk.StringVar(value=self.config_data.get("training_settings", {}).get("model_weights", "yolov5s.pt"))
        self.running = False
        self.cap = None
        self.video_thread = None
        self.model = None

        self.create_widgets()

    def create_widgets(self):
        # Top Control Frame
        control_frame = tk.Frame(self, bg="#1e1e1e")
        control_frame.pack(side=tk.TOP, pady=10)

        # Camera Selection Dropdown
        tk.Label(control_frame, text="Camera:", font=self.custom_font_button, bg="#1e1e1e", fg="white").grid(row=0, column=0, padx=5)
        cam_options = [str(i) for i in range(5)]
        self.cam_combo = ttk.Combobox(control_frame, values=cam_options, textvariable=tk.StringVar(value=str(self.camera_index.get())), width=5, state="readonly")
        self.cam_combo.grid(row=0, column=1, padx=5)
        self.cam_combo.bind("<<ComboboxSelected>>", self.update_camera)

        # Resolution Dropdown
        tk.Label(control_frame, text="Resolution:", font=self.custom_font_button, bg="#1e1e1e", fg="white").grid(row=0, column=2, padx=5)
        res_options = ["640x480", "800x600", "1280x720", "1920x1080"]
        self.res_combo = ttk.Combobox(control_frame, values=res_options, textvariable=self.resolution, width=10, state="readonly")
        self.res_combo.grid(row=0, column=3, padx=5)

        # Model Weights File Selection
        tk.Label(control_frame, text="Model Weights:", font=self.custom_font_button, bg="#1e1e1e", fg="white").grid(row=0, column=4, padx=5)
        self.weights_entry = ttk.Entry(control_frame, textvariable=self.model_weights, width=20)
        self.weights_entry.grid(row=0, column=5, padx=5)
        tk.Button(control_frame, text="Browse", font=self.custom_font_button, command=self.browse_weights).grid(row=0, column=6, padx=5)

        # Start/Stop Buttons
        self.start_button = tk.Button(control_frame, text="Start Test", font=self.custom_font_button, command=self.start_test)
        self.start_button.grid(row=0, column=7, padx=5)
        self.stop_button = tk.Button(control_frame, text="Stop Test", font=self.custom_font_button, command=self.stop_test, state="disabled")
        self.stop_button.grid(row=0, column=8, padx=5)

        # Video Display Frame
        self.video_panel = tk.Label(self, bg="#000000")
        self.video_panel.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

    def update_camera(self, event):
        try:
            self.camera_index.set(int(self.cam_combo.get()))
        except Exception:
            self.camera_index.set(0)

    def browse_weights(self):
        path = filedialog.askopenfilename(title="Select Model Weights", filetypes=[("PT Files", "*.pt")])
        if path:
            self.model_weights.set(path)

    def start_test(self):
        # Load model weights (using YOLOv5 via torch.hub in this example)
        try:
            self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=self.model_weights.get(), force_reload=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load model weights:\n{e}")
            return

        # Parse resolution
        try:
            width, height = map(int, self.resolution.get().split("x"))
        except Exception:
            width, height = 640, 480

        # Open camera capture
        self.cap = cv2.VideoCapture(self.camera_index.get())
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Unable to open camera.")
            return

        self.running = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.video_thread = threading.Thread(target=self.video_loop, daemon=True)
        self.video_thread.start()

    def video_loop(self):
        while self.running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                continue

            # Run inference on the frame
            try:
                results = self.model(frame)
                # Draw bounding boxes and labels from YOLO results
                annotated_frame = results.render()[0]  # results.render() returns a list of images
            except Exception as e:
                print("Inference error:", e)
                annotated_frame = frame

            # Convert to RGB for PIL
            image_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            image_pil = Image.fromarray(image_rgb)
            imgtk = ImageTk.PhotoImage(image=image_pil)

            # Update video panel
            self.video_panel.imgtk = imgtk
            self.video_panel.configure(image=imgtk)

        self.cap.release()

    def stop_test(self):
        self.running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")

    def on_closing(self):
        self.stop_test()
        self.destroy()

if __name__ == "__main__":
    app = VisionTestingApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
