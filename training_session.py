import os
import re
import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import yaml
from PIL import Image, ImageTk
import torch  # YOLOv5 requires torch for inference
import cv2

# Define relative paths (assuming this file is in the project root "Deepsight Studio")
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
TRAIN_SCRIPT_DIR = os.path.join(PROJECT_ROOT, "yolov5")
TRAIN_SCRIPT = os.path.join(TRAIN_SCRIPT_DIR, "train.py")

class TrainingSessionPage(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Training Session")
        self.geometry("1200x900")
        self.configure(bg="#1e1e1e")
        self.autotune_results = []
        self.create_widgets()
        # Call update_last_metrics on window open
        self.update_last_metrics()
        
    def create_widgets(self):
        # Header label
        header = tk.Label(self, text="YOLOv5 Training Session", font=("Orbitron", 24, "bold"),
                          bg="#1e1e1e", fg="white")
        header.pack(pady=10)

        # Frame for training parameters
        params_frame = tk.Frame(self, bg="#1e1e1e")
        params_frame.pack(pady=10, padx=10, fill="x")
        
        # Model selection dropdown (YOLOv5 variants)
        tk.Label(params_frame, text="Select Model Weights:", bg="#1e1e1e", fg="white",
                 font=("Helvetica", 12)).grid(row=0, column=0, sticky="w", pady=5)
        self.model_var = tk.StringVar(value="yolov5s.pt")
        models = ["yolov5s.pt", "yolov5m.pt", "yolov5l.pt", "yolov5x.pt"]
        self.model_menu = ttk.Combobox(params_frame, textvariable=self.model_var,
                                       values=models, state="readonly", font=("Helvetica", 12))
        self.model_menu.grid(row=0, column=1, pady=5, sticky="ew")
        
        # Data config file selection
        tk.Label(params_frame, text="Data Config File:", bg="#1e1e1e", fg="white",
                 font=("Helvetica", 12)).grid(row=1, column=0, sticky="w", pady=5)
        self.data_config_var = tk.StringVar()
        self.data_config_entry = tk.Entry(params_frame, textvariable=self.data_config_var, font=("Helvetica", 12))
        self.data_config_entry.grid(row=1, column=1, pady=5, sticky="ew")
        browse_data_btn = tk.Button(params_frame, text="Browse", font=("Helvetica", 12),
                                    command=self.browse_data_config)
        browse_data_btn.grid(row=1, column=2, padx=5, pady=5)

        # Image size entry
        tk.Label(params_frame, text="Image Size (--img):", bg="#1e1e1e", fg="white",
                 font=("Helvetica", 12)).grid(row=2, column=0, sticky="w", pady=5)
        self.img_size_var = tk.StringVar(value="640")
        self.img_size_entry = tk.Entry(params_frame, textvariable=self.img_size_var, font=("Helvetica", 12))
        self.img_size_entry.grid(row=2, column=1, pady=5, sticky="ew")
        
        # Batch size entry
        tk.Label(params_frame, text="Batch Size (--batch):", bg="#1e1e1e", fg="white",
                 font=("Helvetica", 12)).grid(row=3, column=0, sticky="w", pady=5)
        self.batch_var = tk.StringVar(value="16")
        self.batch_entry = tk.Entry(params_frame, textvariable=self.batch_var, font=("Helvetica", 12))
        self.batch_entry.grid(row=3, column=1, pady=5, sticky="ew")
        
        # Epochs entry
        tk.Label(params_frame, text="Epochs (--epochs):", bg="#1e1e1e", fg="white",
                 font=("Helvetica", 12)).grid(row=4, column=0, sticky="w", pady=5)
        self.epochs_var = tk.StringVar(value="50")
        self.epochs_entry = tk.Entry(params_frame, textvariable=self.epochs_var, font=("Helvetica", 12))
        self.epochs_entry.grid(row=4, column=1, pady=5, sticky="ew")
        
        # Project name entry (with Browse button)
        tk.Label(params_frame, text="Project Name (--project):", bg="#1e1e1e", fg="white",
                 font=("Helvetica", 12)).grid(row=5, column=0, sticky="w", pady=5)
        self.project_var = tk.StringVar(value="runs/train")
        self.project_entry = tk.Entry(params_frame, textvariable=self.project_var, font=("Helvetica", 12))
        self.project_entry.grid(row=5, column=1, pady=5, sticky="ew")
        browse_proj_btn = tk.Button(params_frame, text="Browse", font=("Helvetica", 12),
                                    command=self.browse_project)
        browse_proj_btn.grid(row=5, column=2, padx=5, pady=5)
        
        params_frame.columnconfigure(1, weight=1)

        # Action buttons frame: Start Training, Test Training, and AutoTune
        action_frame = tk.Frame(self, bg="#1e1e1e")
        action_frame.pack(pady=10, fill="x")
        
        self.train_btn = tk.Button(action_frame, text="Start Training", font=("Helvetica", 14, "bold"),
                                   command=self.start_training, bg="#007acc", fg="white", width=10)
        self.train_btn.pack(side="left", padx=10)
        
        self.test_btn = tk.Button(action_frame, text="Test Training", font=("Helvetica", 14, "bold"),
                                  command=self.open_test_training, bg="#007acc", fg="white", width=10)
        self.test_btn.pack(side="left", padx=10)

        self.autotune_btn = tk.Button(action_frame, text="AutoTune", font=("Helvetica", 14, "bold"),
                                      command=self.run_autotune, bg="#007acc", fg="white", width=10)
        self.autotune_btn.pack(side="left", padx=10)
        
        # Metrics panel: small text boxes to show last run's metrics
        metrics_frame = tk.Frame(action_frame, bg="#1e1e1e")
        metrics_frame.pack(side="left", padx=10)
        self.map_label = tk.Label(metrics_frame, text="mAP@0.5: N/A", font=("Helvetica", 10), bg="#1e1e1e", fg="white")
        self.map_label.pack(anchor="w")
        self.precision_label = tk.Label(metrics_frame, text="Precision: N/A", font=("Helvetica", 10), bg="#1e1e1e", fg="white")
        self.precision_label.pack(anchor="w")
        self.recall_label = tk.Label(metrics_frame, text="Recall: N/A", font=("Helvetica", 10), bg="#1e1e1e", fg="white")
        self.recall_label.pack(anchor="w")
        
        # Frame for displaying previous AutoTune results
        results_frame = tk.Frame(self, bg="#1e1e1e")
        results_frame.pack(pady=5, fill="x")
        tk.Label(results_frame, text="Previous AutoTune Results:", bg="#1e1e1e", fg="white",
                 font=("Helvetica", 12, "bold")).pack(anchor="w", padx=10)
        self.autotune_listbox = tk.Listbox(results_frame, height=4, font=("Courier", 10))
        self.autotune_listbox.pack(padx=10, pady=5, fill="x")
        
        # Output text widget for command output
        self.output_text = tk.Text(self, height=8, bg="black", fg="lime", font=("Courier", 10))
        self.output_text.pack(fill="both", padx=10, pady=10, expand=True)
        
    def browse_data_config(self):
        file_path = filedialog.askopenfilename(title="Select Data Config File",
                                               filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*.*")])
        if file_path:
            self.data_config_var.set(file_path)
            
    def browse_project(self):
        folder_path = filedialog.askdirectory(title="Select Project Folder")
        if folder_path:
            self.project_var.set(folder_path)
            
    def start_training(self):
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
            
    def update_last_metrics(self):
        """
        Automatically finds the most recent exp folder in the project folder and
        attempts to extract metrics from a results.csv file.
        """
        project = self.project_var.get().strip()
        if not project or not os.path.exists(project):
            self.map_label.config(text="mAP@0.5: N/A")
            self.precision_label.config(text="Precision: N/A")
            self.recall_label.config(text="Recall: N/A")
            return
        # List directories in the project folder that start with "exp"
        exp_dirs = [d for d in os.listdir(project) if os.path.isdir(os.path.join(project, d)) and d.startswith("exp")]
        if not exp_dirs:
            self.map_label.config(text="mAP@0.5: N/A")
            self.precision_label.config(text="Precision: N/A")
            self.recall_label.config(text="Recall: N/A")
            return
        # Sort by modification time, newest first
        exp_dirs.sort(key=lambda d: os.path.getmtime(os.path.join(project, d)), reverse=True)
        last_exp = os.path.join(project, exp_dirs[0])
        results_csv = os.path.join(last_exp, "results.csv")
        if not os.path.exists(results_csv):
            self.map_label.config(text="mAP@0.5: N/A")
            self.precision_label.config(text="Precision: N/A")
            self.recall_label.config(text="Recall: N/A")
            return
        try:
            with open(results_csv, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
                if rows:
                    last_row = rows[-1]
                    # Try alternate key names if needed
                    map_val = last_row.get("mAP@0.5", last_row.get("mAP50", "N/A"))
                    prec_val = last_row.get("Precision", "N/A")
                    recall_val = last_row.get("Recall", "N/A")
                    self.map_label.config(text=f"mAP@0.5: {map_val}")
                    self.precision_label.config(text=f"Precision: {prec_val}")
                    self.recall_label.config(text=f"Recall: {recall_val}")
                else:
                    self.map_label.config(text="mAP@0.5: N/A")
                    self.precision_label.config(text="Precision: N/A")
                    self.recall_label.config(text="Recall: N/A")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse results CSV:\n{e}")
            
    def open_test_training(self):
        TestTrainingWindow(self, data_config=self.data_config_var.get().strip(),
                           project_folder=self.project_var.get().strip())

    def run_autotune(self):
        """
        A placeholder for an automated hyperparameter search.
        This demo tests two lr0 values and records their mAP.
        """
        data_config = self.data_config_var.get().strip()
        if not data_config or not os.path.exists(data_config):
            messagebox.showerror("Input Error", "Please select a valid data config file first.")
            return

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, "=== AutoTune Starting ===\n")
        self.output_text.see(tk.END)

        lr0_candidates = [0.01, 0.001]
        best_map = 0.0
        best_lr0 = None

        epochs = "5"  # fewer epochs for demo
        project = self.project_var.get().strip()

        for lr0 in lr0_candidates:
            hyp_file = "temp_autotune_hyp.yaml"
            with open(hyp_file, "w") as hyp:
                hyp.write(f"lr0: {lr0}\n")
                hyp.write("lrf: 0.1\n")
                hyp.write("momentum: 0.937\n")
                hyp.write("weight_decay: 0.0005\n")

            command = [
                "python", TRAIN_SCRIPT,
                "--data", data_config,
                "--hyp", hyp_file,
                "--epochs", epochs,
                "--batch", "8",
                "--weights", "yolov5s.pt",
                "--project", project,
                "--name", f"autotune_lr0_{lr0}"
            ]
            self.output_text.insert(tk.END, f"\nRunning trial with lr0={lr0}...\n{' '.join(command)}\n")
            self.output_text.see(tk.END)
            self.update()

            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            console_output, _ = process.communicate()

            match = re.search(r"mAP@0\.5:\s+([\d\.]+)", console_output)
            if match:
                map_val = float(match.group(1))
                self.output_text.insert(tk.END, f"Trial lr0={lr0} => mAP@0.5={map_val}\n")
                self.autotune_listbox.insert(tk.END, f"lr0={lr0} : mAP={map_val}")
                if map_val > best_map:
                    best_map = map_val
                    best_lr0 = lr0
            else:
                self.output_text.insert(tk.END, f"Could not parse mAP@0.5 for lr0={lr0}\n")

        self.output_text.insert(tk.END, "\n=== AutoTune Complete ===\n")
        if best_lr0 is not None:
            self.output_text.insert(tk.END, f"Best lr0={best_lr0} with mAP@0.5={best_map}\n")
            self.map_label.config(text=f"mAP@0.5: {best_map}")
            self.precision_label.config(text="Precision: N/A")
            self.recall_label.config(text="Recall: N/A")
        else:
            self.output_text.insert(tk.END, "No valid trials found.\n")

# -------------------------------
# Test Training Window Definition
# -------------------------------

class TestTrainingWindow(tk.Toplevel):
    def __init__(self, master=None, data_config="", project_folder=""):
        super().__init__(master)
        self.title("Test Training")
        self.geometry("800x600")
        self.configure(bg="#1e1e1e")
        self.data_config = data_config
        self.project_folder = project_folder
        self.weights_path = os.path.join(self.project_folder, "exp", "weights", "best.pt")
        self.image_list = []
        self.current_index = 0
        self.model = None
        self.create_widgets()
        self.weights_label.config(text=f"Using weights: {self.weights_path}")
        self.load_training_images()
        self.show_image()
        
    def create_widgets(self):
        self.weights_label = tk.Label(self, text="", font=("Helvetica", 10), bg="#1e1e1e", fg="white")
        self.weights_label.pack(pady=5)
        
        self.image_frame = tk.Frame(self, bg="black")
        self.image_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.image_label = tk.Label(self.image_frame, bg="black")
        self.image_label.pack(expand=True)
        
        nav_frame = tk.Frame(self, bg="#1e1e1e")
        nav_frame.pack(pady=10)
        prev_btn = tk.Button(nav_frame, text="<< Previous", font=("Helvetica", 12),
                             command=self.show_previous)
        prev_btn.pack(side="left", padx=10)
        next_btn = tk.Button(nav_frame, text="Next >>", font=("Helvetica", 12),
                             command=self.show_next)
        next_btn.pack(side="left", padx=10)
        
    def load_training_images(self):
        if not os.path.exists(self.data_config):
            messagebox.showerror("Error", "Data config file not found.")
            return
        try:
            with open(self.data_config, "r") as f:
                data = yaml.safe_load(f)
            train_folder = data.get("train", "")
            if not os.path.isabs(train_folder):
                train_folder = os.path.join(PROJECT_ROOT, train_folder)
            if not os.path.exists(train_folder):
                messagebox.showerror("Error", f"Training folder not found: {train_folder}")
                return
            for f in os.listdir(train_folder):
                if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                    self.image_list.append(os.path.join(train_folder, f))
            if not self.image_list:
                messagebox.showinfo("Info", "No images found in the training folder.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load training images:\n{e}")
    
    def run_inference(self, img):
        if self.model is None:
            try:
                self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=self.weights_path, force_reload=False)
            except Exception as e:
                messagebox.showerror("Inference Error", f"Failed to load model:\n{e}")
                return img
        try:
            results = self.model(img)
            rendered = results.render()
            processed_img = rendered[0]
            return processed_img
        except Exception as e:
            messagebox.showerror("Inference Error", f"Failed during inference:\n{e}")
            return img
        
    def show_image(self):
        if not self.image_list:
            return
        image_path = self.image_list[self.current_index]
        try:
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError("Image not loaded properly.")
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            processed_img = self.run_inference(img_rgb)
            im_pil = Image.fromarray(processed_img)
            im_pil.thumbnail((800, 600))
            self.photo = ImageTk.PhotoImage(im_pil)
            self.image_label.configure(image=self.photo)
            self.image_label.image = self.photo
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image:\n{e}")
    
    def show_previous(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_image()
            
    def show_next(self):
        if self.current_index < len(self.image_list) - 1:
            self.current_index += 1
            self.show_image()

# -------------------------------
# For testing this module independently:
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide main window for testing
    TrainingSessionPage(root)
    root.mainloop()
