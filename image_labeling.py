import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import font as tkFont
from PIL import Image, ImageTk, ImageDraw
import cv2
import numpy as np
import os
import yaml
import shutil
import json
import torch  # For YOLOv5
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)  # Suppress AMP deprecation warning temporarily

def load_labeling_settings(config_file="maintenance.json"):
    try:
        with open(config_file, "r") as f:
            data = json.load(f)
        return data.get("labeling_settings", {}), data.get("training_settings", {})
    except Exception as e:
        print("Error loading settings:", e)
        return {}, {}

def update_yaml_file(new_label, yaml_path="data.yaml"):
    data = {
        "train": os.path.join(r"C:/Users/michaelg/Anaconda_envs/Deepsight Studio/yolo_training_data", "images"),
        "val": os.path.join(r"C:/Users/michaelg/Anaconda_envs/Deepsight Studio/yolo_training_data", "images"),
        "nc": 0,
        "names": []
    }
    if os.path.exists(yaml_path):
        with open(yaml_path, "r") as f:
            try:
                data = yaml.safe_load(f) or data
            except Exception:
                pass
    if new_label not in data.get("names", []):
        data.setdefault("names", []).append(new_label)
        data["nc"] = len(data["names"])
        with open(yaml_path, "w") as f:
            yaml.dump(data, f)
    return data["names"].index(new_label)

def compute_yolo_bbox(self, img, th1, th2, min_area=1000):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, th1, th2)
    kernel = np.ones((3, 3), np.uint8)
    edges_closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    nonzero = cv2.findNonZero(edges_closed)
    if nonzero is None or cv2.boundingRect(nonzero)[2] * cv2.boundingRect(nonzero)[3] < min_area:
        return None
    x, y, w, h = cv2.boundingRect(nonzero)
    h_img, w_img = img.shape[:2]
    if w >= w_img * 0.95 and h >= h_img * 0.95:
        return None
    # Add padding using the slider value
    return self.compute_padded_bbox(img, x, y, x + w, y + h, padding_factor=self.padding_factor)

def compute_padded_bbox(self, img, x1, y1, x2, y2, padding_factor):
    """Add padding to a bounding box while ensuring it stays within image bounds."""
    h_img, w_img = img.shape[:2]
    # Compute padding in pixels
    w = x2 - x1
    h = y2 - y1
    pad_w = int(w * padding_factor)
    pad_h = int(h * padding_factor)
    # Apply padding
    x1 = max(0, x1 - pad_w)
    y1 = max(0, y1 - pad_h)
    x2 = min(w_img, x2 + pad_w)
    y2 = min(h_img, y2 + pad_h)
    # Convert to YOLO format (normalized center coordinates and width/height)
    x_center_norm = (x1 + x2) / 2 / w_img
    y_center_norm = (y1 + y2) / 2 / h_img
    w_norm = (x2 - x1) / w_img
    h_norm = (y2 - y1) / h_img
    return x_center_norm, y_center_norm, w_norm, h_norm

class ImageLabelingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image Labeling Tool")
        self.geometry("1200x900")
        self.configure(bg="gray")
        
        # Font setup
        available_fonts = tkFont.families()
        if "Orbitron" in available_fonts:
            self.custom_font = tkFont.Font(family="Orbitron", size=14)
            self.custom_font_large = tkFont.Font(family="Orbitron", size=18, weight="bold")
        else:
            self.custom_font = tkFont.Font(family="Helvetica", size=14)
            self.custom_font_large = tkFont.Font(family="Helvetica", size=18, weight="bold")
        
        self.labeling_settings, self.training_settings = load_labeling_settings()
        self.image_folder = None
        self.image_paths = []
        self.current_index = 0
        self.image_path = None
        self.original_image = None
        self.display_image = None
        self.zoom_factor = 1.0
        self.roi = None
        self.hull_points = []
        self.points = []
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        
        self.label_var = tk.StringVar(value="domino")
        self.custom_weights_path = self.training_settings.get("model_weights", "yolov5s.pt")
        self.model_type = self.training_settings.get("model_used", "YOLOv5")
        self.padding_factor = tk.DoubleVar(value=0.1)  # Default padding factor of 10%
        self.model = None  # Will store the loaded YOLO model
        
        self.create_widgets()
        self.load_yolo_model(self.custom_weights_path)  # Load default model on startup
        
    def create_widgets(self):
        top_frame = tk.Frame(self, bg="gray")
        top_frame.pack(side=tk.TOP, pady=5)
        tk.Button(top_frame, text="Select Folder", command=self.select_folder, font=self.custom_font).pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="Previous Image", command=self.prev_image, font=self.custom_font).pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="Next Image", command=self.next_image, font=self.custom_font).pack(side=tk.LEFT, padx=5)
        tk.Label(top_frame, text="Label:", bg="gray", fg="white", font=self.custom_font).pack(side=tk.LEFT, padx=5)
        tk.Entry(top_frame, textvariable=self.label_var, width=10, font=self.custom_font).pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="Delete Picture", command=self.delete_picture, font=self.custom_font).pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="Auto Label Folder", command=self.auto_label_folder, font=self.custom_font).pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="Auto Label with YOLO", command=self.auto_label_with_yolo, font=self.custom_font).pack(side=tk.LEFT, padx=5)
        
        canny_frame = tk.Frame(self, bg="gray")
        canny_frame.pack(side=tk.TOP, pady=5)
        tk.Label(canny_frame, text="Canny Threshold1:", bg="gray", fg="white", font=self.custom_font).pack(side=tk.LEFT, padx=5)
        canny1 = self.labeling_settings.get("canny_threshold1", {"min": 0, "max": 750, "value": 475})
        self.canny_th1 = tk.Scale(canny_frame, from_=canny1["min"], to=canny1["max"], orient=tk.HORIZONTAL, font=self.custom_font)
        self.canny_th1.set(canny1["value"])
        self.canny_th1.pack(side=tk.LEFT, padx=5)
        tk.Label(canny_frame, text="Canny Threshold2:", bg="gray", fg="white", font=self.custom_font).pack(side=tk.LEFT, padx=5)
        canny2 = self.labeling_settings.get("canny_threshold2", {"min": 0, "max": 750, "value": 400})
        self.canny_th2 = tk.Scale(canny_frame, from_=canny2["min"], to=canny2["max"], orient=tk.HORIZONTAL, font=self.custom_font)
        self.canny_th2.set(canny2["value"])
        self.canny_th2.pack(side=tk.LEFT, padx=5)
        tk.Button(canny_frame, text="Analyze ROI (Edge Detect)", command=self.analyze_roi, font=self.custom_font).pack(side=tk.LEFT, padx=5)
        
        # Add padding slider frame
        padding_frame = tk.Frame(self, bg="gray")
        padding_frame.pack(side=tk.TOP, pady=5)
        tk.Label(padding_frame, text="YOLO Padding Factor (%):", bg="gray", fg="white", font=self.custom_font).pack(side=tk.LEFT, padx=5)
        self.padding_slider = tk.Scale(padding_frame, from_=0.0, to=0.5, orient=tk.HORIZONTAL, resolution=0.01, 
                                       variable=self.padding_factor, font=self.custom_font)
        self.padding_slider.pack(side=tk.LEFT, padx=5)
        tk.Label(padding_frame, text="Adjust padding for YOLO bounding boxes", bg="gray", fg="white", font=self.custom_font).pack(side=tk.LEFT, padx=5)
        
        bbox_frame = tk.Frame(self, bg="gray")
        bbox_frame.pack(side=tk.TOP, pady=5)
        tk.Label(bbox_frame, text="Min Bounding Box Area:", bg="gray", fg="white", font=self.custom_font).pack(side=tk.LEFT, padx=5)
        self.min_bbox_area_slider = tk.Scale(bbox_frame, from_=0, to=5000, orient=tk.HORIZONTAL, font=self.custom_font)
        self.min_bbox_area_slider.set(1000)
        self.min_bbox_area_slider.pack(side=tk.LEFT, padx=5)
        
        extra_btn_frame = tk.Frame(self, bg="gray")
        extra_btn_frame.pack(side=tk.TOP, pady=5)
        tk.Button(extra_btn_frame, text="Save Domino Edge Data", command=self.save_domino_edge_data, font=self.custom_font).pack(side=tk.LEFT, padx=5)
        
        self.canvas = tk.Canvas(self, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_button_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)
        
    def load_yolo_model(self, weights_path):
        try:
            if self.model_type == "YOLOv5":
                self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=weights_path, force_reload=True)
            elif self.model_type == "YOLOv8":
                from ultralytics import YOLO
                self.model = YOLO(weights_path)
            else:
                raise ValueError(f"Unsupported model type: {self.model_type}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load YOLO model {self.model_type} with weights {weights_path}: {e}")
            self.model = None

    def select_folder(self):
        folder = filedialog.askdirectory(title="Select Folder with Images")
        if folder:
            self.image_folder = folder
            self.image_paths = [os.path.join(folder, f) for f in os.listdir(folder)
                                if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            if not self.image_paths:
                messagebox.showwarning("Warning", "No image files found in the selected folder.")
            else:
                self.current_index = 0
                self.load_image(self.image_paths[self.current_index])
        
    def prev_image(self):
        if self.image_paths and self.current_index > 0:
            self.current_index -= 1
            self.load_image(self.image_paths[self.current_index])
        
    def next_image(self):
        if self.image_paths and self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
            self.load_image(self.image_paths[self.current_index])
        
    def load_image(self, path):
        self.image_path = path
        self.original_image = cv2.imread(path)
        if self.original_image is None:
            messagebox.showerror("Error", "Failed to load image.")
            return
        self.zoom_factor = 1.0
        self.roi = None
        self.hull_points = []
        self.points = []
        h, w = self.original_image.shape[:2]
        new_w = int(w * self.zoom_factor)
        new_h = int(h * self.zoom_factor)
        self.display_image = cv2.resize(self.original_image, (new_w, new_h))
        self.update_display()
        
    def update_display(self):
        if self.display_image is None:
            return
        image_rgb = cv2.cvtColor(self.display_image, cv2.COLOR_BGR2RGB)
        self.photo = ImageTk.PhotoImage(Image.fromarray(image_rgb))
        self.canvas.delete("all")
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        if canvas_w < 50 or canvas_h < 50:
            canvas_w, canvas_h = 800, 600
        center_x = canvas_w // 2
        center_y = canvas_h // 2
        self.image_offset_x = center_x - self.display_image.shape[1] // 2
        self.image_offset_y = center_y - self.display_image.shape[0] // 2
        self.canvas.create_image(center_x, center_y, image=self.photo, anchor="center")
        if self.roi:
            self.canvas.create_rectangle(*self.roi, outline="red", width=2)
            rx1, ry1, rx2, ry2 = self.roi
            cx = (rx1 + rx2) // 2
            cy = (ry1 + ry2) // 2
            self.canvas.create_line(cx-10, cy-10, cx+10, cy+10, fill="red", width=3)
            self.canvas.create_line(cx-10, cy+10, cx+10, cy-10, fill="red", width=3)
        for hull in self.hull_points:
            if len(hull) > 1:
                flat = []
                for pt in hull:
                    flat.extend(pt)
                flat.extend(hull[0])
                self.canvas.create_line(*flat, fill="yellow", width=2)
        for pt in self.points:
            self.canvas.create_oval(pt[0]-3, pt[1]-3, pt[0]+3, pt[1]+3, fill="blue")
        
    def on_mouse_wheel(self, event):
        if hasattr(event, 'delta'):
            self.zoom_factor *= 1.1 if event.delta > 0 else 0.9
        else:
            self.zoom_factor *= 1.1 if event.num == 4 else 0.9
        h, w = self.original_image.shape[:2]
        new_w = int(w * self.zoom_factor)
        new_h = int(h * self.zoom_factor)
        self.display_image = cv2.resize(self.original_image, (new_w, new_h))
        self.update_display()
        
    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.roi = None
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            self.rect_id = None
        
    def on_button_drag(self, event):
        if self.start_x is None or self.start_y is None:
            return
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, event.x, event.y, outline="red", width=2)
        
    def on_button_release(self, event):
        if self.start_x is None or self.start_y is None:
            return
        x1, y1 = self.start_x, self.start_y
        x2, y2 = event.x, event.y
        self.roi = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        self.update_display()
        
    def analyze_roi(self):
        if self.roi is None:
            messagebox.showwarning("Warning", "Please select an ROI by clicking and dragging on the image.")
            return
        x1, y1, x2, y2 = self.roi
        img_x1 = int(max(0, min(x1 - self.image_offset_x, self.display_image.shape[1])))
        img_y1 = int(max(0, min(y1 - self.image_offset_y, self.display_image.shape[0])))
        img_x2 = int(max(0, min(x2 - self.image_offset_x, self.display_image.shape[1])))
        img_y2 = int(max(0, min(y2 - self.image_offset_y, self.display_image.shape[0])))
        if img_x2 - img_x1 <= 0 or img_y2 - img_y1 <= 0:
            messagebox.showerror("Error", "ROI is invalid after conversion to image coordinates.")
            return
        roi_image = self.display_image[img_y1:img_y2, img_x1:img_x2]
        th1 = self.canny_th1.get()
        th2 = self.canny_th2.get()
        gray = cv2.cvtColor(roi_image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, th1, th2)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        self.hull_points = []
        self.points = []
        for cnt in contours:
            hull = cv2.convexHull(cnt)
            hull_list = []
            for point in hull:
                px, py = point[0]
                canvas_x = int(px + img_x1 + self.image_offset_x)
                canvas_y = int(py + img_y1 + self.image_offset_y)
                hull_list.append((canvas_x, canvas_y))
            if hull_list:
                self.hull_points.append(hull_list)
        self.update_display()
        
    def delete_picture(self):
        if self.image_path is None:
            messagebox.showwarning("Warning", "No image loaded.")
            return
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this image?")
        if confirm:
            try:
                os.remove(self.image_path)
                self.image_paths.remove(self.image_path)
                if self.image_paths:
                    self.current_index = 0
                    self.load_image(self.image_paths[self.current_index])
                else:
                    self.original_image = None
                    self.display_image = None
                    self.canvas.delete("all")
                messagebox.showinfo("Deleted", f"Deleted {self.image_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Error deleting image: {e}")
        
    def save_domino_edge_data(self):
        if self.image_path is None or self.roi is None:
            messagebox.showwarning("Warning", "No image loaded or ROI selected.")
            return
        x1, y1, x2, y2 = self.roi
        orig_x1 = int(max(0, (x1 - self.image_offset_x) / self.zoom_factor))
        orig_y1 = int(max(0, (y1 - self.image_offset_y) / self.zoom_factor))
        orig_x2 = int(min(self.original_image.shape[1], (x2 - self.image_offset_x) / self.zoom_factor))
        orig_y2 = int(min(self.original_image.shape[0], (y2 - self.image_offset_y) / self.zoom_factor))
        if orig_x2 - orig_x1 <= 0 or orig_y2 - orig_y1 <= 0:
            messagebox.showerror("Error", "Invalid ROI for saving.")
            return
        crop_img = self.original_image[orig_y1:orig_y2, orig_x1:orig_x2]
        base_name = os.path.basename(self.image_path)
        gray_crop = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
        th1 = self.canny_th1.get()
        th2 = self.canny_th2.get()
        edges_crop = cv2.Canny(gray_crop, th1, th2)
        kernel = np.ones((3, 3), np.uint8)
        edges_closed = cv2.morphologyEx(edges_crop, cv2.MORPH_CLOSE, kernel)
        nonzero = cv2.findNonZero(edges_closed)
        if nonzero is None:
            messagebox.showwarning("Warning", "No edge pixels found in the ROI.")
            return
        x, y, w, h = cv2.boundingRect(nonzero)
        crop_h, crop_w = crop_img.shape[:2]
        if w >= crop_w * 0.95 and h >= crop_h * 0.95:
            messagebox.showwarning("Warning", "Bounding box covers nearly the entire ROI.")
            return
        x_center_norm = (x + w / 2) / crop_w
        y_center_norm = (y + h / 2) / crop_h
        w_norm = w / crop_w
        h_norm = h / crop_h
        save_folder = r"C:/Users/michaelg/Anaconda_envs/Deepsight Studio/yolo_training_data"
        images_dir = os.path.join(save_folder, "images")
        labels_dir = os.path.join(save_folder, "labels")
        os.makedirs(images_dir, exist_ok=True)
        os.makedirs(labels_dir, exist_ok=True)
        dest_img_path = os.path.join(images_dir, base_name)
        cv2.imwrite(dest_img_path, crop_img)
        label_idx = update_yaml_file(self.label_var.get().strip(), yaml_path=os.path.join(save_folder, "data.yaml"))
        base_filename, _ = os.path.splitext(base_name)
        dest_txt_path = os.path.join(labels_dir, base_filename + ".txt")
        with open(dest_txt_path, "w") as f:
            f.write(f"{label_idx} {x_center_norm:.6f} {y_center_norm:.6f} {w_norm:.6f} {h_norm:.6f}\n")
        messagebox.showinfo("Saved", f"Training data saved.\nImage: {dest_img_path}\nAnnotation: {dest_txt_path}")

    def auto_label_folder(self):
        if not self.image_paths:
            messagebox.showwarning("Warning", "No images in the folder.")
            return
        results = []
        for path in self.image_paths:
            img = cv2.imread(path)
            if img is None:
                continue
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, self.canny_th1.get(), self.canny_th2.get())
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                continue
            largest = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest) < 100:
                continue
            overlay = img.copy()
            hull = cv2.convexHull(largest)
            cv2.drawContours(overlay, [hull], -1, (0, 255, 255), 2)
            ratio = 200 / overlay.shape[1]
            thumb = cv2.resize(overlay, (200, int(overlay.shape[0] * ratio)))
            thumb_rgb = cv2.cvtColor(thumb, cv2.COLOR_BGR2RGB)
            thumb_pil = Image.fromarray(thumb_rgb)
            results.append({"path": path, "thumbnail": thumb_pil})
        self.show_gallery(results, "Auto Label Report (Canny)")

    def auto_label_with_yolo(self):
        if not self.image_paths:
            messagebox.showwarning("Warning", "No images in the folder.")
            return
        weights_path = filedialog.askopenfilename(
            title=f"Select Custom YOLO Weights (Default: {self.custom_weights_path})",
            filetypes=[("PyTorch weights", "*.pt"), ("All files", "*.*")],
            initialdir=os.getcwd(),
            initialfile=self.custom_weights_path if os.path.isfile(self.custom_weights_path) else None
        )
        if weights_path:
            self.custom_weights_path = weights_path
            self.load_yolo_model(weights_path)
        if self.model is None:
            messagebox.showwarning("Warning", "No valid YOLO model loaded. Using default or last loaded model.")
            self.load_yolo_model(self.training_settings.get("model_weights", "yolov5s.pt"))
            if self.model is None:
                return

        results = []
        for path in self.image_paths:
            img = cv2.imread(path)
            if img is None:
                continue
            if self.model_type == "YOLOv5":
                predictions = self.model(path)
                overlay = img.copy()
                bbox_found = False
                if len(predictions.xyxy[0]) > 0:  # Check if there are detections
                    box = predictions.xyxy[0][0]  # Take the first detection
                    x1, y1, x2, y2 = map(int, box[:4])
                    if (x2 - x1) * (y2 - y1) < self.min_bbox_area_slider.get():
                        continue
                    # Use the padding factor from the slider
                    x_center_norm, y_center_norm, w_norm, h_norm = self.compute_padded_bbox(img, x1, y1, x2, y2, self.padding_factor.get())
                    # Draw the padded box for visualization
                    x1_padded = int((x_center_norm - w_norm / 2) * img.shape[1])
                    y1_padded = int((y_center_norm - h_norm / 2) * img.shape[0])
                    x2_padded = int((x_center_norm + w_norm / 2) * img.shape[1])
                    y2_padded = int((y_center_norm + h_norm / 2) * img.shape[0])
                    cv2.rectangle(overlay, (x1_padded, y1_padded), (x2_padded, y2_padded), (0, 255, 255), 2)
                    bbox_found = True
            elif self.model_type == "YOLO8":  # Note: Should be "YOLOv8" to match your JSON and GUI
                predictions = self.model.predict(path, conf=0.25)
                overlay = img.copy()
                bbox_found = False
                for result in predictions:
                    if result.boxes:
                        box = result.boxes[0]
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        if (x2 - x1) * (y2 - y1) < self.min_bbox_area_slider.get():
                            continue
                        # Use the padding factor from the slider
                        x_center_norm, y_center_norm, w_norm, h_norm = self.compute_padded_bbox(img, x1, y1, x2, y2, self.padding_factor.get())
                        # Draw the padded box for visualization
                        x1_padded = int((x_center_norm - w_norm / 2) * img.shape[1])
                        y1_padded = int((y_center_norm - h_norm / 2) * img.shape[0])
                        x2_padded = int((x_center_norm + w_norm / 2) * img.shape[1])
                        y2_padded = int((y_center_norm + h_norm / 2) * img.shape[0])
                        cv2.rectangle(overlay, (x1_padded, y1_padded), (x2_padded, y2_padded), (0, 255, 255), 2)
                        bbox_found = True
                        break
            if not bbox_found:
                continue
            ratio = 200 / overlay.shape[1]
            thumb = cv2.resize(overlay, (200, int(overlay.shape[0] * ratio)))
            thumb_rgb = cv2.cvtColor(thumb, cv2.COLOR_BGR2RGB)
            thumb_pil = Image.fromarray(thumb_rgb)
            results.append({"path": path, "thumbnail": thumb_pil})
        self.show_gallery(results, f"Auto Label Report ({self.model_type})")

    def show_gallery(self, results, title):
        if not results:
            messagebox.showinfo(title, "No images with sufficient detection were found.")
            return
        gallery_win = tk.Toplevel(self)
        gallery_win.title(title)
        close_btn = tk.Button(gallery_win, text="X", font=self.custom_font_large, fg="white", bg="red",
                              command=gallery_win.destroy)
        close_btn.pack(side=tk.TOP, anchor="ne", padx=10, pady=10)
        gallery_win.attributes("-fullscreen", True)
        
        gallery_canvas = tk.Canvas(gallery_win)
        gallery_canvas.pack(side="left", fill="both", expand=True)
        v_scrollbar = tk.Scrollbar(gallery_win, orient="vertical", command=gallery_canvas.yview)
        v_scrollbar.pack(side="right", fill="y")
        gallery_canvas.configure(yscrollcommand=v_scrollbar.set)
        
        def _on_mousewheel(event):
            gallery_canvas.yview_scroll(-int(event.delta/120), "units")
        gallery_canvas.bind("<MouseWheel>", _on_mousewheel)
        gallery_canvas.bind("<Button-4>", lambda e: gallery_canvas.yview_scroll(-1, "units"))
        gallery_canvas.bind("<Button-5>", lambda e: gallery_canvas.yview_scroll(1, "units"))
        
        scrollable_frame = tk.Frame(gallery_canvas)
        gallery_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        scrollable_frame.bind("<Configure>", lambda e: gallery_canvas.configure(scrollregion=gallery_canvas.bbox("all")))
        
        selected_vars = []
        for idx, item in enumerate(results):
            var = tk.BooleanVar(value=True)
            selected_vars.append(var)
            frame = tk.Frame(scrollable_frame, bd=2, relief=tk.RIDGE)
            frame.grid(row=idx // 4, column=idx % 4, padx=5, pady=5)
            thumb_photo = ImageTk.PhotoImage(item["thumbnail"])
            lbl = tk.Label(frame, image=thumb_photo)
            lbl.image = thumb_photo
            lbl.bind("<Button-1>", lambda e, p=item["path"]: self.open_image_in_zoom(p))
            lbl.pack()
            cb = tk.Checkbutton(frame, text=os.path.basename(item["path"]), variable=var, font=self.custom_font)
            cb.pack()
        
        def process_selection():
            total_selected = sum(1 for var in selected_vars if var.get())
            if total_selected == 0:
                messagebox.showinfo(title, "No images selected for saving.")
                gallery_win.destroy()
                return
            
            progress_win = tk.Toplevel(gallery_win)
            progress_win.title("Processing Images")
            progress_win.geometry("300x100")
            progress_win.transient(gallery_win)
            progress_win.grab_set()
            tk.Label(progress_win, text="Processing images, please wait...").pack(pady=5)
            progress_bar = ttk.Progressbar(progress_win, maximum=total_selected, mode='determinate')
            progress_bar.pack(pady=5, padx=10, fill="x")
            
            saved = 0
            skipped = 0
            warnings_list = []
            base_dir = r"C:/Users/michaelg/Anaconda_envs/Deepsight Studio/yolo_training_data"
            images_dir = os.path.join(base_dir, "images")
            labels_dir = os.path.join(base_dir, "labels")
            os.makedirs(images_dir, exist_ok=True)
            os.makedirs(labels_dir, exist_ok=True)
            label_idx = update_yaml_file(self.label_var.get().strip(), yaml_path=os.path.join(base_dir, "data.yaml"))
            method = "YOLO" if self.custom_weights_path else "Canny"
            
            for idx, item in enumerate(results):
                if not selected_vars[idx].get():
                    skipped += 1
                    continue
                src_path = item["path"]
                base_name = os.path.basename(src_path)
                dest_img_path = os.path.join(images_dir, base_name)
                shutil.copy(src_path, dest_img_path)
                img = cv2.imread(src_path)
                bbox = None
                if method == "Canny":
                    bbox = compute_yolo_bbox(self, img, self.canny_th1.get(), self.canny_th2.get(), 
                                             min_area=self.min_bbox_area_slider.get())
                else:  # YOLO with padding from slider
                    if self.model_type == "YOLOv5":
                        predictions = self.model(src_path)
                        if len(predictions.xyxy[0]) > 0:
                            box = predictions.xyxy[0][0]
                            x1, y1, x2, y2 = map(int, box[:4])
                            area = (x2 - x1) * (y2 - y1)
                            if area >= self.min_bbox_area_slider.get():
                                bbox = self.compute_padded_bbox(img, x1, y1, x2, y2, self.padding_factor.get())
                    elif self.model_type == "YOLOv8":
                        predictions = self.model.predict(src_path, conf=0.25)
                        for result in predictions:
                            if result.boxes:
                                box = result.boxes[0]
                                x1, y1, x2, y2 = map(int, box.xyxy[0])
                                area = (x2 - x1) * (y2 - y1)
                                if area >= self.min_bbox_area_slider.get():
                                    bbox = self.compute_padded_bbox(img, x1, y1, x2, y2, self.padding_factor.get())
                                break
                if bbox is None:
                    warnings_list.append(f"Could not compute a valid bounding box for {base_name}.")
                    skipped += 1
                else:
                    x_center_norm, y_center_norm, w_norm, h_norm = bbox
                    base_filename, _ = os.path.splitext(base_name)
                    dest_txt_path = os.path.join(labels_dir, base_filename + ".txt")
                    with open(dest_txt_path, "w") as f:
                        f.write(f"{label_idx} {x_center_norm:.6f} {y_center_norm:.6f} {w_norm:.6f} {h_norm:.6f}\n")
                    saved += 1
                progress_bar['value'] = saved + skipped
                progress_win.update()
            progress_win.destroy()
            report = f"Auto Labeling Complete ({method})\nSaved: {saved} images\nSkipped: {skipped} images"
            if warnings_list:
                report += "\nWarnings:\n" + "\n".join(warnings_list)
            messagebox.showinfo(title, report)
            gallery_win.destroy()
        
        btn = tk.Button(scrollable_frame, text="Save Selected", command=process_selection, font=self.custom_font)
        btn.grid(row=(len(results) // 4) + 1, column=0, columnspan=4, pady=10)

    def open_image_in_zoom(self, image_path):
        zoom_win = tk.Toplevel(self)
        zoom_win.title("Image Preview")
        canvas = tk.Canvas(zoom_win, bg="black")
        canvas.pack(fill="both", expand=True)
        image = cv2.imread(image_path)
        if image is None:
            messagebox.showerror("Error", f"Failed to load image: {image_path}")
            return
        method = "YOLO" if self.custom_weights_path else "Canny"
        if method == "Canny":
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, self.canny_th1.get(), self.canny_th2.get())
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest = max(contours, key=cv2.contourArea)
                if cv2.contourArea(largest) > 100:
                    overlay = image.copy()
                    hull = cv2.convexHull(largest)
                    cv2.drawContours(overlay, [hull], -1, (0, 255, 255), 2)
                    image = overlay
        else:
            if self.model_type == "YOLOv5":
                predictions = self.model(image_path)
                overlay = image.copy()
                if len(predictions.xyxy[0]) > 0:
                    box = predictions.xyxy[0][0]
                    x1, y1, x2, y2 = map(int, box[:4])
                    x_center_norm, y_center_norm, w_norm, h_norm = self.compute_padded_bbox(image, x1, y1, x2, y2, self.padding_factor.get())
                    x1_padded = int((x_center_norm - w_norm / 2) * image.shape[1])
                    y1_padded = int((y_center_norm - h_norm / 2) * image.shape[0])
                    x2_padded = int((x_center_norm + w_norm / 2) * image.shape[1])
                    y2_padded = int((y_center_norm + h_norm / 2) * image.shape[0])
                    cv2.rectangle(overlay, (x1_padded, y1_padded), (x2_padded, y2_padded), (0, 255, 255), 2)
                    image = overlay
            elif self.model_type == "YOLOv8":
                predictions = self.model.predict(image_path, conf=0.25)
                overlay = image.copy()
                for result in predictions:
                    if result.boxes:
                        box = result.boxes[0]
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        x_center_norm, y_center_norm, w_norm, h_norm = self.compute_padded_bbox(image, x1, y1, x2, y2, self.padding_factor.get())
                        x1_padded = int((x_center_norm - w_norm / 2) * image.shape[1])
                        y1_padded = int((y_center_norm - h_norm / 2) * image.shape[0])
                        x2_padded = int((x_center_norm + w_norm / 2) * image.shape[1])
                        y2_padded = int((y_center_norm + h_norm / 2) * image.shape[0])
                        cv2.rectangle(overlay, (x1_padded, y1_padded), (x2_padded, y2_padded), (0, 255, 255), 2)
                        image = overlay
                        break

        zoom_factor = 1.0

        def update_display():
            nonlocal zoom_factor
            h, w = image.shape[:2]
            new_w = int(w * zoom_factor)
            new_h = int(h * zoom_factor)
            resized = cv2.resize(image, (new_w, new_h))
            image_rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            photo = ImageTk.PhotoImage(Image.fromarray(image_rgb))
            canvas.delete("all")
            canvas.create_image(canvas.winfo_width() // 2, canvas.winfo_height() // 2, image=photo, anchor="center")
            canvas.image = photo

        def on_mouse_wheel(event):
            nonlocal zoom_factor
            if hasattr(event, "delta"):
                zoom_factor *= 1.1 if event.delta > 0 else 0.9
            else:
                zoom_factor *= 1.1 if event.num == 4 else 0.9
            update_display()

        canvas.bind("<MouseWheel>", on_mouse_wheel)
        canvas.bind("<Button-4>", on_mouse_wheel)
        canvas.bind("<Button-5>", on_mouse_wheel)
        update_display()
        canvas.bind("<Configure>", lambda e: update_display())

    def run(self):
        self.mainloop()

if __name__ == "__main__":
    app = ImageLabelingApp()
    app.run()