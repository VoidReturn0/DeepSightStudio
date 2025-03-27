import os
import re
import csv
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import yaml
from PIL import Image, ImageTk
import torch
import cv2
import webbrowser

# Try to import tkinterweb for embedding TensorBoard
try:
    from tkinterweb import HtmlFrame
    EMBED_TB = True
except ImportError:
    EMBED_TB = False

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
TRAIN_SCRIPT_DIR = os.path.join(PROJECT_ROOT, "yolov5")
TRAIN_SCRIPT = os.path.join(TRAIN_SCRIPT_DIR, "train.py")

def launch_tensorboard(logdir="yolo_training_data", port="6007"):
    try:
        from tensorboard import program
        tb = program.TensorBoard()
        tb.configure(argv=[None, "--logdir", logdir, "--port", port])
        tb_url = tb.launch()  # tb.launch() returns the URL, e.g. "http://localhost:6007"
        print(f"TensorBoard running at {tb_url}")
        return tb_url
    except Exception as e:
        print(f"Error launching TensorBoard: {e}")
        return None

class TrainingSessionPage(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.state("zoomed")
        self.title("YOLOv5 Training Session")
        self.configure(bg="#1e1e1e")
        self.autotune_results = []
        # Launch TensorBoard and capture its URL
        self.tb_url = launch_tensorboard()  # e.g., "http://localhost:6007"
        self.create_widgets()
        self.after(100, self.update_last_metrics)

    def create_widgets(self):
        try:
            with open("maintenance.json", "r") as f:
                maintenance_data = json.load(f)
            training_settings = maintenance_data.get("training_settings", {})
        except Exception as e:
            print(f"Error loading maintenance.json: {e}")
            training_settings = {}

        header = tk.Label(self, text="YOLOv5 Training Session", font=("Orbitron", 24, "bold"),
                          bg="#1e1e1e", fg="white")
        header.pack(pady=10)

        main_container = tk.Frame(self, bg="#1e1e1e")
        main_container.pack(pady=10, padx=20, fill="x")

        # Parameters Panel (Left)
        params_frame = tk.Frame(main_container, bg="#1e1e1e")
        params_frame.pack(side="left", fill="x", expand=True)
        tk.Label(params_frame, text="Model Weights:", bg="#1e1e1e", fg="white", font=("Helvetica", 12)).grid(row=0, column=0, sticky="w", pady=5)
        model_weights_path = training_settings.get("model_weights", "yolov5s.pt")
        model_type = training_settings.get("model_used", "YOLOv5")
        self.model_var = tk.StringVar(value=model_weights_path)
        model_info_text = f"{model_type}: {os.path.basename(model_weights_path)}"
        model_info = tk.Entry(params_frame, font=("Helvetica", 12), bg="#2e2e2e", fg="white",
                              readonlybackground="#2e2e2e")
        model_info.insert(0, model_info_text)
        model_info.config(state="readonly")
        model_info.grid(row=0, column=1, sticky="w", pady=5, ipadx=50)

        tk.Label(params_frame, text="Data Config File:", bg="#1e1e1e", fg="white", font=("Helvetica", 12)).grid(row=1, column=0, sticky="w", pady=5)
        self.data_config_var = tk.StringVar(value=training_settings.get("data_config", ""))
        self.data_config_entry = tk.Entry(params_frame, textvariable=self.data_config_var, font=("Helvetica", 12), width=30)
        self.data_config_entry.grid(row=1, column=1, sticky="w", pady=5)
        browse_data_btn = tk.Button(params_frame, text="Browse", font=("Helvetica", 12), command=self.browse_data_config)
        browse_data_btn.grid(row=1, column=2, padx=5, pady=5)

        tk.Label(params_frame, text="Image Size (--img):", bg="#1e1e1e", fg="white", font=("Helvetica", 12)).grid(row=2, column=0, sticky="w", pady=5)
        self.img_size_var = tk.StringVar(value=training_settings.get("img_size", "640"))
        self.img_size_entry = tk.Entry(params_frame, textvariable=self.img_size_var, font=("Helvetica", 12), width=20)
        self.img_size_entry.grid(row=2, column=1, sticky="w", pady=5)

        tk.Label(params_frame, text="Batch Size (--batch):", bg="#1e1e1e", fg="white", font=("Helvetica", 12)).grid(row=3, column=0, sticky="w", pady=5)
        self.batch_var = tk.StringVar(value=training_settings.get("batch_size", "16"))
        self.batch_entry = tk.Entry(params_frame, textvariable=self.batch_var, font=("Helvetica", 12), width=20)
        self.batch_entry.grid(row=3, column=1, sticky="w", pady=5)

        tk.Label(params_frame, text="Epochs (--epochs):", bg="#1e1e1e", fg="white", font=("Helvetica", 12)).grid(row=4, column=0, sticky="w", pady=5)
        self.epochs_var = tk.StringVar(value=training_settings.get("epochs", "50"))
        self.epochs_entry = tk.Entry(params_frame, textvariable=self.epochs_var, font=("Helvetica", 12), width=20)
        self.epochs_entry.grid(row=4, column=1, sticky="w", pady=5)

        tk.Label(params_frame, text="Project Name (--project):", bg="#1e1e1e", fg="white", font=("Helvetica", 12)).grid(row=5, column=0, sticky="w", pady=5)
        self.project_var = tk.StringVar(value=training_settings.get("project_name", "runs/train"))
        self.project_entry = tk.Entry(params_frame, textvariable=self.project_var, font=("Helvetica", 12), width=30)
        self.project_entry.grid(row=5, column=1, sticky="w", pady=5)
        browse_proj_btn = tk.Button(params_frame, text="Browse", font=("Helvetica", 12), command=self.browse_project)
        browse_proj_btn.grid(row=5, column=2, padx=5, pady=5)

        # TensorBoard Dashboard Panel (Right)
        tb_frame = tk.Frame(main_container, bg="#1e1e1e", bd=2, relief="sunken")
        tb_frame.pack(side="left", fill="both", expand=True, padx=20)
        tk.Label(tb_frame, text="TensorBoard Dashboard", bg="#1e1e1e", fg="white", font=("Helvetica", 12, "bold")).pack(pady=5)
        if EMBED_TB:
            self.tensorboard_frame = HtmlFrame(tb_frame, horizontal_scrollbar="auto")
            self.tensorboard_frame.pack(fill="both", expand=True)
            # Wait 5 seconds before loading the URL (so TensorBoard can start)
            self.after(5000, lambda: self.tensorboard_frame.load_url(self.tb_url if self.tb_url else "http://localhost:6007"))
        else:
            self.tensorboard_frame = tk.Frame(tb_frame, bg="#333333")
            self.tensorboard_frame.pack(fill="both", expand=True, padx=10, pady=10)
            tk.Label(self.tensorboard_frame, text="TensorBoard running at http://localhost:6007",
                     bg="#333333", fg="white", font=("Helvetica", 12)).pack(pady=5)
            tk.Button(self.tensorboard_frame, text="Open in Browser",
                      command=lambda: webbrowser.open(self.tb_url if self.tb_url else "http://localhost:6007")).pack(pady=5)

        # Action Buttons (below main container)
        action_frame = tk.Frame(self, bg="#1e1e1e")
        action_frame.pack(pady=10, fill="x")
        self.train_btn = tk.Button(action_frame, text="Start Training", font=("Helvetica", 14, "bold"),
                                   command=self.start_training, bg="#007acc", fg="white", width=10)
        self.train_btn.pack(side="left", padx=10)
        self.resume_btn = tk.Button(action_frame, text="Resume Training", font=("Helvetica", 14, "bold"),
                                    command=self.resume_training, bg="#007acc", fg="white", width=12)
        self.resume_btn.pack(side="left", padx=10)
        self.test_btn = tk.Button(action_frame, text="Test Training", font=("Helvetica", 14, "bold"),
                                  command=self.open_test_training, bg="#007acc", fg="white", width=10)
        self.test_btn.pack(side="left", padx=10)
        self.autotune_btn = tk.Button(action_frame, text="AutoTune", font=("Helvetica", 14, "bold"),
                                      command=self.run_autotune, bg="#007acc", fg="white", width=10)
        self.autotune_btn.pack(side="left", padx=10)

        # Progress Bar
        progress_frame = tk.Frame(self, bg="#1e1e1e")
        progress_frame.pack(pady=5, fill="x", padx=20)
        tk.Label(progress_frame, text="Training Progress:", bg="#1e1e1e", fg="white", font=("Helvetica", 12)).pack(side="left", padx=5)
        self.progress_var = tk.DoubleVar()
        self.progress_var.set(0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=5)

        # Output Text Widget (height reduced to 4)
        self.output_text = tk.Text(self, height=4, bg="black", fg="lime", font=("Courier", 10))
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

        cwd_before = os.getcwd()
        self.output_text.insert(tk.END, f"Current directory before: {cwd_before}\n")
        self.output_text.insert(tk.END, f"PROJECT_ROOT: {PROJECT_ROOT}\n")

        data_yaml_content = None
        try:
            with open(data_config, 'r') as f:
                data_yaml_content = yaml.safe_load(f)
            if data_yaml_content and not os.path.isabs(data_yaml_content.get('train', '')):
                train_path = os.path.join(PROJECT_ROOT, data_yaml_content['train'])
                val_path = os.path.join(PROJECT_ROOT, data_yaml_content['val'])
                temp_yaml_path = os.path.join(PROJECT_ROOT, "temp_data.yaml")
                data_yaml_content['train'] = train_path
                data_yaml_content['val'] = val_path
                with open(temp_yaml_path, 'w') as f:
                    yaml.dump(data_yaml_content, f)
                data_config = temp_yaml_path
                self.output_text.insert(tk.END, "Using temporary data.yaml with absolute paths\n")
        except Exception as e:
            self.output_text.insert(tk.END, f"Warning: Failed to fix data paths: {e}\n")

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
                self.update_progress_from_line(line)
                self.update()
            process.wait()
            self.output_text.insert(tk.END, "\nTraining process completed.\n")
            self.update_last_metrics()
        except Exception as e:
            messagebox.showerror("Execution Error", f"An error occurred:\n{e}")

    def resume_training(self):
        try:
            with open("maintenance.json", "r") as f:
                maintenance_data = json.load(f)
            training_settings = maintenance_data.get("training_settings", {})
        except Exception as e:
            messagebox.showerror("Error", f"Error loading maintenance.json: {e}")
            return

        model_weights = training_settings.get("model_weights", "yolov5s.pt")
        data_config = training_settings.get("data_config", "")
        img_size = training_settings.get("img_size", "640")
        batch = training_settings.get("batch_size", "16")
        epochs = training_settings.get("epochs", "50")
        project = training_settings.get("project_name", "runs/train")

        if not data_config or not os.path.exists(data_config):
            messagebox.showerror("Input Error", "Please select a valid data config file.")
            return

        try:
            with open(data_config, 'r') as f:
                data_yaml_content = yaml.safe_load(f)
            if data_yaml_content and not os.path.isabs(data_yaml_content.get('train', '')):
                train_path = os.path.join(PROJECT_ROOT, data_yaml_content['train'])
                val_path = os.path.join(PROJECT_ROOT, data_yaml_content['val'])
                temp_yaml_path = os.path.join(PROJECT_ROOT, "temp_data.yaml")
                data_yaml_content['train'] = train_path
                data_yaml_content['val'] = val_path
                with open(temp_yaml_path, 'w') as f:
                    yaml.dump(data_yaml_content, f)
                data_config = temp_yaml_path
                self.output_text.insert(tk.END, "Using temporary data.yaml with absolute paths\n")
        except Exception as e:
            self.output_text.insert(tk.END, f"Warning: Failed to fix data paths: {e}\n")

        command = ["python", TRAIN_SCRIPT,
                   "--img", img_size,
                   "--batch", batch,
                   "--epochs", epochs,
                   "--data", data_config,
                   "--weights", model_weights,
                   "--project", project,
                   "--resume"]

        self.output_text.insert(tk.END, f"Executing resume command:\n{' '.join(command)}\n\n")
        self.output_text.see(tk.END)

        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in process.stdout:
                self.output_text.insert(tk.END, line)
                self.output_text.see(tk.END)
                self.update_progress_from_line(line)
                self.update()
            process.wait()
            self.output_text.insert(tk.END, "\nResume Training process completed.\n")
            self.update_last_metrics()
        except Exception as e:
            messagebox.showerror("Execution Error", f"An error occurred:\n{e}")

    def update_progress_from_line(self, line):
        match = re.search(r"(\d+)%", line)
        if match:
            try:
                percentage = float(match.group(1))
                self.progress_var.set(percentage)
            except ValueError:
                pass

    def update_last_metrics(self):
        project = self.project_var.get().strip()
        if not project or not os.path.exists(project):
            return
        exp_dirs = [d for d in os.listdir(project) if os.path.isdir(os.path.join(project, d)) and d.startswith("exp")]
        if not exp_dirs:
            return
        exp_dirs.sort(key=lambda d: os.path.getmtime(os.path.join(project, d)), reverse=True)
        last_exp = os.path.join(project, exp_dirs[0])
        results_csv = os.path.join(last_exp, "results.csv")
        if not os.path.exists(results_csv):
            return
        try:
            with open(results_csv, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
                if rows:
                    last_row = rows[-1]
                    map_val = last_row.get("mAP@0.5", last_row.get("mAP50", "N/A"))
                    prec_val = last_row.get("Precision", "N/A")
                    recall_val = last_row.get("Recall", "N/A")
                    try:
                        self.map_label.config(text=f"mAP@0.5: {map_val}")
                        self.precision_label.config(text=f"Precision: {prec_val}")
                        self.recall_label.config(text=f"Recall: {recall_val}")
                    except AttributeError:
                        pass
                else:
                    pass
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse results CSV:\n{e}")

    def open_test_training(self):
        pass

    def run_autotune(self):
        pass

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    TrainingSessionPage(root)
    root.mainloop()
