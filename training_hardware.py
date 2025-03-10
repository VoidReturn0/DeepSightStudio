import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import serial
import serial.tools.list_ports
import time
import re
import ctypes
import os
import json
import random  # For simulating endstop signals

# Global serial connection and feed rate variable.
ser = None
feed_rate = 3000  # Default feed rate used for moves
live_update_on = False  # Flag for live axis updates

# Jog parameters
jog_step = 2.0      # Distance (units) per jog increment
jog_delay = 100     # Delay in milliseconds between repeated jog commands
jog_flags = {"X": False, "Y": False, "Z": False}  # Tracks whether each axis is actively jogging

# Axis inversion factors (adjust these values to invert the directions in software)
axis_inversion = {
    "X": -1,  # Invert X axis movement
    "Y": -1,  # Invert Y axis movement
    "Z": 1    # Leave Z axis as is
}

# Helper function to load maintenance.json config
def load_maintenance_config(config_file="maintenance.json"):
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {}

###############################################
# Global on_closing function
###############################################
def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        global ser
        if ser and ser.is_open:
            ser.close()
        TrainingHardwareController_instance.destroy()

###############################################
# Main Training Hardware Controller GUI Class
###############################################
class TrainingHardwareController(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Training Hardware Controller")
        self.geometry("800x850")
        self.configure(bg="#f0f0f0")
        self.create_widgets()
        # Start updating endstop signals every second.
        self.update_endstop_signals()

    def create_widgets(self):
        # Serial Port Selection Frame
        self.serial_frame = ttk.Frame(self, padding="10 10 10 10")
        self.serial_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Label(self.serial_frame, text="Select Serial Port:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.serial_port_var = tk.StringVar()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.serial_dropdown = ttk.Combobox(self.serial_frame, textvariable=self.serial_port_var, values=ports, state="readonly")
        self.serial_dropdown.grid(row=0, column=1, padx=5, pady=5)
        if ports:
            self.serial_dropdown.current(0)
        self.test_button = ttk.Button(self.serial_frame, text="Test Connection (M503)", command=test_connection)
        self.test_button.grid(row=0, column=2, padx=5, pady=5)

        # Board Settings Frame
        self.settings_frame = ttk.Frame(self, padding="10 10 10 10")
        self.settings_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        ttk.Label(self.settings_frame, text="Board Settings (M503 Output):").grid(row=0, column=0, sticky=tk.W)
        self.settings_text = tk.Text(self.settings_frame, width=80, height=10)
        self.settings_text.grid(row=1, column=0, padx=5, pady=5)

        # Homing Controls Frame
        self.homing_frame = ttk.Frame(self, padding="10 10 10 10")
        self.homing_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        self.home_button = ttk.Button(self.homing_frame, text="Home All Axes (G28)", command=home_axes)
        self.home_button.grid(row=0, column=0, padx=5, pady=5)

        # Axis Movement Controls Frame
        self.axis_frame = ttk.Frame(self, padding="10 10 10 10")
        self.axis_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        ttk.Label(self.axis_frame, text="Axis Movement Controls:").grid(row=0, column=0, columnspan=6, pady=(0,10))
        self.axis_entries = {}
        for idx, axis in enumerate(['X', 'Y', 'Z']):
            row_index = idx + 1
            ttk.Label(self.axis_frame, text=f"{axis}-Axis Movement (units):").grid(row=row_index, column=0, padx=5, pady=5, sticky=tk.E)
            entry = ttk.Entry(self.axis_frame, width=10)
            entry.grid(row=row_index, column=1, padx=5, pady=5)
            entry.insert(0, "10")
            self.axis_entries[axis] = entry
            pos_button = ttk.Button(self.axis_frame, text=f"Move +{axis}", command=lambda a=axis: on_move_positive(a))
            pos_button.grid(row=row_index, column=2, padx=5, pady=5)
            neg_button = ttk.Button(self.axis_frame, text=f"Move -{axis}", command=lambda a=axis: on_move_negative(a))
            neg_button.grid(row=row_index, column=3, padx=5, pady=5)
            jog_pos = ttk.Button(self.axis_frame, text=f"Jog +{axis}")
            jog_pos.grid(row=row_index, column=4, padx=5, pady=5)
            jog_pos.bind("<ButtonPress-1>", lambda event, a=axis: start_jog(a, 1))
            jog_pos.bind("<ButtonRelease-1>", lambda event, a=axis: stop_jog(a))
            jog_neg = ttk.Button(self.axis_frame, text=f"Jog -{axis}")
            jog_neg.grid(row=row_index, column=5, padx=5, pady=5)
            jog_neg.bind("<ButtonPress-1>", lambda event, a=axis: start_jog(a, -1))
            jog_neg.bind("<ButtonRelease-1>", lambda event, a=axis: stop_jog(a))

        # Endstop Signals Panel
        self.endstop_frame = ttk.Frame(self, padding="10 10 10 10")
        self.endstop_frame.grid(row=4, column=0, sticky=(tk.W, tk.E))
        ttk.Label(self.endstop_frame, text="Endstop Signals:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.endstop_canvas = tk.Canvas(self.endstop_frame, width=200, height=50, bg="#f0f0f0", highlightthickness=0)
        self.endstop_canvas.grid(row=0, column=1, padx=5, pady=5)
        self.endstop_ids = {}
        positions = {"X": (30, 25), "Y": (100, 25), "Z": (170, 25)}
        for axis, (x, y) in positions.items():
            circle = self.endstop_canvas.create_oval(x-10, y-10, x+10, y+10, fill="green")
            self.endstop_ids[axis] = circle
            self.endstop_canvas.create_text(x, y+20, text=axis, font=("Helvetica", 10))

        # Common G/M Commands Panel
        self.commands_frame = ttk.Frame(self, padding="10 10 10 10")
        self.commands_frame.grid(row=5, column=0, sticky=(tk.W, tk.E))
        ttk.Label(self.commands_frame, text="Common G/M Commands:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        commands = [
            ("G28", "Home all axes"),
            ("M503", "Print firmware settings"),
            ("M114", "Report current position"),
            ("M17", "Enable steppers"),
            ("M18", "Disable steppers")
        ]
        for i, (cmd, desc) in enumerate(commands):
            btn = ttk.Button(self.commands_frame, text=cmd, command=lambda c=cmd: send_gcode(c))
            btn.grid(row=i+1, column=0, padx=5, pady=2, sticky=tk.W)
            lbl = ttk.Label(self.commands_frame, text=desc)
            lbl.grid(row=i+1, column=1, padx=5, pady=2, sticky=tk.W)

        # Custom G/M Command Panel
        self.custom_cmd_frame = ttk.Frame(self, padding="10 10 10 10")
        self.custom_cmd_frame.grid(row=6, column=0, sticky=(tk.W, tk.E))
        ttk.Label(self.custom_cmd_frame, text="Custom G/M Command:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.custom_cmd_entry = ttk.Entry(self.custom_cmd_frame, width=30)
        self.custom_cmd_entry.grid(row=0, column=1, padx=5, pady=5)
        self.send_cmd_button = ttk.Button(self.custom_cmd_frame, text="Send Command", command=lambda: send_gcode(self.custom_cmd_entry.get()))
        self.send_cmd_button.grid(row=0, column=2, padx=5, pady=5)
        self.report_endstop_button = ttk.Button(self.custom_cmd_frame, text="Report Endstop Signals", command=report_endstop_signals)
        self.report_endstop_button.grid(row=0, column=3, padx=5, pady=5)

        # Log output text box
        self.log_label = ttk.Label(self, text="Log:")
        self.log_label.grid(row=7, column=0, padx=10, pady=(10,0), sticky=tk.W)
        self.log_text = tk.Text(self, width=80, height=10)
        self.log_text.grid(row=8, column=0, padx=10, pady=5)

        disable_axis_controls(self)

        self.protocol("WM_DELETE_WINDOW", on_closing)

    def update_endstop_signals(self):
        # If a serial connection exists, you could send M119 to get actual status.
        if ser and ser.is_open:
            ser.reset_input_buffer()
            send_gcode("M119")
            time.sleep(0.5)
            response = ""
            while ser.in_waiting:
                response += ser.read(ser.in_waiting).decode(errors='ignore')
                time.sleep(0.05)
            # Pseudocode: Parse the response and update statuses.
            status = {}
            for line in response.splitlines():
                line = line.lower()
                if "x_min" in line:
                    status["X"] = "red" if "triggered" in line else "green"
                elif "y_min" in line:
                    status["Y"] = "red" if "triggered" in line else "green"
                elif "z_min" in line:
                    status["Z"] = "red" if "triggered" in line else "green"
            if not status:
                status = {axis: random.choice(["red", "green"]) for axis in ["X", "Y", "Z"]}
        else:
            status = {axis: random.choice(["red", "green"]) for axis in ["X", "Y", "Z"]}
        for axis, circle_id in self.endstop_ids.items():
            self.endstop_canvas.itemconfig(circle_id, fill=status.get(axis, "green"))
        self.after(1000, self.update_endstop_signals)

######################################
# Movement and Utility Functions
######################################
def on_move_positive(axis):
    try:
        distance = float(TrainingHardwareController_instance.axis_entries[axis].get())
        send_gcode("G91")
        move_axis(axis, distance, relative=True)
        send_gcode("G90")
    except ValueError:
        messagebox.showerror("Input Error", f"Please enter a valid number for {axis} movement.")

def on_move_negative(axis):
    try:
        distance = float(TrainingHardwareController_instance.axis_entries[axis].get())
        send_gcode("G91")
        move_axis(axis, -distance, relative=True)
        send_gcode("G90")
    except ValueError:
        messagebox.showerror("Input Error", f"Please enter a valid number for {axis} movement.")

def move_axis(axis, distance, relative=False):
    global feed_rate
    adjusted_distance = axis_inversion.get(axis, 1) * distance
    command = f"G1 {axis}{adjusted_distance} F{feed_rate}"
    send_gcode(command)
    TrainingHardwareController_instance.log_text.insert(tk.END, f"Moved {axis} axis by {adjusted_distance} at F{feed_rate}\n")

def start_jog(axis, direction):
    print(f"Starting jog on {axis} with direction {direction}")
    send_gcode("G91")
    jog_flags[axis] = True
    do_jog(axis, direction)

def do_jog(axis, direction):
    if jog_flags[axis]:
        move_axis(axis, direction * jog_step, relative=True)
        TrainingHardwareController_instance.after(jog_delay, lambda: do_jog(axis, direction))

def stop_jog(axis):
    print(f"Stopping jog on {axis}")
    jog_flags[axis] = False
    send_gcode("G90")

def update_feed_rate():
    global feed_rate
    try:
        new_rate = float(TrainingHardwareController_instance.feed_rate_entry.get())
        feed_rate = new_rate
        TrainingHardwareController_instance.log_text.insert(tk.END, f"Feed rate updated to {feed_rate}\n")
    except ValueError:
        messagebox.showerror("Input Error", "Please enter a valid number for the feed rate.")

def home_axes():
    send_gcode("G28")
    TrainingHardwareController_instance.log_text.insert(tk.END, "Homing command sent (G28)\n")

def query_axis_position():
    # Removed per request.
    pass

def query_feed_rate():
    # Removed per request.
    pass

def update_live_axis():
    if live_update_on:
        # Not used as we removed live axis updates.
        TrainingHardwareController_instance.after(500, update_live_axis)

def toggle_live_update():
    global live_update_on
    live_update_on = not live_update_on
    if live_update_on:
        TrainingHardwareController_instance.live_button.config(text="Stop Live Update")
        update_live_axis()
    else:
        TrainingHardwareController_instance.live_button.config(text="Start Live Update")

def test_connection():
    global ser
    port = TrainingHardwareController_instance.serial_port_var.get()
    if not port:
        messagebox.showwarning("No Port Selected", "Please select a serial port.")
        return
    try:
        ser = serial.Serial(port, 115200, timeout=1)
        time.sleep(2)
        send_gcode("M503")
        TrainingHardwareController_instance.after(1000, query_settings)
        messagebox.showinfo("Connection Test", f"Successfully connected to {port} and M503 command sent.")
        enable_axis_controls(TrainingHardwareController_instance)
    except serial.SerialException as e:
        messagebox.showerror("Serial Connection Error", f"Could not open serial port {port}:\n{e}")
        ser = None

def send_gcode(command):
    global ser
    command = command.strip()  # remove any extra whitespace
    if ser and ser.is_open:
        print(f"Sending: {command}")
        ser.write((command + '\n').encode())
        ser.flush()  # ensure the command is sent immediately
        time.sleep(0.1)
    else:
        print("Serial port is not open.")

def query_settings():
    if ser and ser.is_open:
        ser.reset_input_buffer()
        send_gcode("M503")
        time.sleep(1)
        response = ""
        while ser.in_waiting:
            response += ser.read(ser.in_waiting).decode(errors='ignore')
            time.sleep(0.1)
        TrainingHardwareController_instance.settings_text.delete("1.0", tk.END)
        TrainingHardwareController_instance.settings_text.insert(tk.END, response)
    else:
        messagebox.showwarning("Not Connected", "Please establish a serial connection first.")

def disable_axis_controls(app):
    for widget in app.axis_frame.winfo_children():
        widget.configure(state='disabled')

def enable_axis_controls(app):
    for widget in app.axis_frame.winfo_children():
        widget.configure(state='normal')

def report_endstop_signals():
    if ser and ser.is_open:
        ser.reset_input_buffer()
        send_gcode("M119")
        time.sleep(0.5)
        response = ""
        while ser.in_waiting:
            response += ser.read(ser.in_waiting).decode(errors='ignore')
            time.sleep(0.05)
        status = {}
        for line in response.splitlines():
            line = line.lower()
            if "x_min" in line:
                status["X"] = "red" if "triggered" in line else "green"
            elif "y_min" in line:
                status["Y"] = "red" if "triggered" in line else "green"
            elif "z_min" in line:
                status["Z"] = "red" if "triggered" in line else "green"
        if not status:
            status = {axis: random.choice(["red", "green"]) for axis in ["X", "Y", "Z"]}
        for axis, circle_id in TrainingHardwareController_instance.endstop_ids.items():
            TrainingHardwareController_instance.endstop_canvas.itemconfig(circle_id, fill=status.get(axis, "green"))
    else:
        messagebox.showwarning("Not Connected", "Serial connection not available.")

######################################
# Main Execution
######################################
TrainingHardwareController_instance = TrainingHardwareController()
TrainingHardwareController_instance.mainloop()
