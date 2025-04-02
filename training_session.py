import os
import json
import yaml
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2
import torch

# --------------------------
# Utility: Load configuration from JSON
# --------------------------
def load_config(config_file="maintenance.json"):
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            try:
                return json.load(f)
            except Exception as e:
                messagebox.showerror("Config Error", f"Error reading {config_file}: {e}")
    return {}

# --------------------------
# Utility: Load data.yaml to get class names
# --------------------------
def load_class_names(data_yaml_path):
    if os.path.exists(data_yaml_path):
        with open(data_yaml_path, "r") as f:
            try:
                data_cfg = yaml.safe_load(f)
                return data_cfg.get("names", [])
            except Exception as e:
                messagebox.showerror("YAML Error", f"Error reading {data_yaml_path}: {e}")
    else:
        messagebox.showerror("YAML Error", f"data.yaml not found at {data_yaml_path}")
    return []

# --------------------------
# Model Tester Class
# --------------------------
class ModelTester(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Live Model Tester")
        self.geometry("1000x800")
        self.configure(bg="#1e1e1e")
        
        # Load settings from maintenance.json
        self.config_data = load_config("maintenance.json")
        training_settings = self.config_data.get("training_settings", {})
        
        # Get model weights and type
        self.weights_path = training_settings.get("model_weights", "yolov5s.pt")
        self.model_type = training_settings.get("model_used", "YOLOv5")
        try:
            self.img_size = int(training_settings.get("img_size", "640"))
        except ValueError:
            self.img_size = 640
        
        # Get data.yaml file path (assume relative to the current file)
        data_config = training_settings.get("data_config", "yolo_training_data/data.yaml")
        if not os.path.isabs(data_config):
            self.data_yaml = os.path.join(os.path.dirname(os.path.abspath(__file__)), data_config.replace("\\", os.sep))
        else:
            self.data_yaml = data_config

        self.model = None
        self.cap = None
        self.delay = 15  # ms delay between frames
        
        self.create_widgets()
        self.load_model()
        self.start_video()

    def create_widgets(self):
        # Video display label
        self.video_label = tk.Label(self, bg="black")
        self.video_label.pack(fill=tk.BOTH, expand=True)
        # Quit button
        self.quit_btn = tk.Button(self, text="Quit Tester", command=self.on_close, font=("Helvetica", 14))
        self.quit_btn.pack(pady=10)

    def load_model(self):
        try:
            if self.model_type == "YOLOv5":
                self.model = torch.hub.load('ultralytics/yolov5', 'custom',
                                            path=self.weights_path,
                                            force_reload=False)
            elif self.model_type == "YOLOv8":
                from ultralytics import YOLO
                self.model = YOLO(self.weights_path)
            else:
                messagebox.showerror("Model Error", f"Unsupported model type: {self.model_type}")
                return

            # Load class names from data.yaml and assign to the model
            class_names = load_class_names(self.data_yaml)
            if class_names:
                self.model.names = class_names
            else:
                print("Warning: No class names found in data.yaml.")
        except Exception as e:
            messagebox.showerror("Model Load Error", f"Failed to load model: {e}")

    def start_video(self):
        # Open default webcam
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Video Error", "Unable to access video capture device.")
            return
        self.update_frame()

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            # Convert frame from BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            annotated_frame = rgb_frame.copy()
            try:
                results = self.model(rgb_frame, size=self.img_size)
                # Check if any predictions exist
                if hasattr(results, "imgs") and len(results.imgs) > 0:
                    results.render()  # Draw bounding boxes on results.imgs in place
                    annotated_frame = results.imgs[0]
                else:
                    print("Inference returned no results.")
            except Exception as e:
                print(f"Inference error: {e}")
                # Continue using the original frame if inference fails
                annotated_frame = rgb_frame

            # Convert to PIL image and resize to fit label
            image_pil = Image.fromarray(annotated_frame)
            width = self.video_label.winfo_width() or 800
            height = self.video_label.winfo_height() or 600
            image_pil = image_pil.resize((width, height))
            self.photo = ImageTk.PhotoImage(image_pil)
            self.video_label.config(image=self.photo)
        self.after(self.delay, self.update_frame)

    def on_close(self):
        if self.cap is not None:
            self.cap.release()
        self.destroy()

# --------------------------
# Main: Run Model Tester
# --------------------------
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    tester = ModelTester(root)
    tester.protocol("WM_DELETE_WINDOW", tester.on_close)
    root.mainloop()
