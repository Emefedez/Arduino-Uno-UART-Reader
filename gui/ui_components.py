import customtkinter as ctk
from tkinter import ttk
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from serial_handler import SerialHandler
import datetime
import collections

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Arduino Serial Monitor")
        self.geometry("1100x700")
        
        self.serial = SerialHandler()
        self.serial.on_message = self.on_message
        self.serial.on_status = self.on_status
        self.serial.on_log = self.log_message
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.create_sidebar()
        self.create_main_view()
        
        # Data storage
        self.analog_data = collections.defaultdict(lambda: collections.deque(maxlen=100))
        
    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="Arduino Monitor", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Connection
        self.port_option = ctk.CTkOptionMenu(self.sidebar, values=self.serial.get_ports())
        self.port_option.grid(row=1, column=0, padx=20, pady=10)
        
        self.refresh_btn = ctk.CTkButton(self.sidebar, text="Refresh Ports", command=self.refresh_ports)
        self.refresh_btn.grid(row=2, column=0, padx=20, pady=5)
        
        self.connect_btn = ctk.CTkButton(self.sidebar, text="Connect", command=self.toggle_connection)
        self.connect_btn.grid(row=3, column=0, padx=20, pady=10)
        
        # Pin Selection
        self.pin_label = ctk.CTkLabel(self.sidebar, text="Pin Selection", anchor="w")
        self.pin_label.grid(row=4, column=0, padx=20, pady=(20, 0))
        
        self.pin_scroll = ctk.CTkScrollableFrame(self.sidebar, height=200)
        self.pin_scroll.grid(row=5, column=0, padx=20, pady=5, sticky="ew")
        
        self.pin_vars = {}
        # Digital 0-13
        for i in range(14):
            var = ctk.BooleanVar(value=False)
            chk = ctk.CTkCheckBox(self.pin_scroll, text=f"D{i}", variable=var)
            chk.pack(anchor="w", pady=2)
            self.pin_vars[f"D{i}"] = var
            
        # Analog A0-A5
        for i in range(6):
            var = ctk.BooleanVar(value=False)
            chk = ctk.CTkCheckBox(self.pin_scroll, text=f"A{i}", variable=var)
            chk.pack(anchor="w", pady=2)
            self.pin_vars[f"A{i}"] = var
            
        self.apply_btn = ctk.CTkButton(self.sidebar, text="Apply Config", command=self.apply_config)
        self.apply_btn.grid(row=6, column=0, padx=20, pady=10)
        
        self.detect_btn = ctk.CTkButton(self.sidebar, text="Detect All", command=self.detect_all)
        self.detect_btn.grid(row=7, column=0, padx=20, pady=5)

    def create_main_view(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        self.tab_monitor = self.tabview.add("Monitor")
        self.tab_pins = self.tabview.add("Pins")
        self.tab_graph = self.tabview.add("Graph")
        
        # --- Monitor Tab ---
        self.tab_monitor.grid_columnconfigure(0, weight=1)
        self.tab_monitor.grid_rowconfigure(0, weight=1)
        
        # History Table (using Treeview)
        self.tree_frame = ctk.CTkFrame(self.tab_monitor)
        self.tree_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        columns = ("timestamp", "origin", "data")
        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show="headings")
        self.tree.heading("timestamp", text="Time")
        self.tree.heading("origin", text="Origin")
        self.tree.heading("data", text="Data")
        self.tree.column("timestamp", width=100)
        self.tree.column("origin", width=100)
        self.tree.column("data", width=400)
        self.tree.pack(fill="both", expand=True)
        
        # Input
        self.input_entry = ctk.CTkEntry(self.tab_monitor, placeholder_text="Send command...")
        self.input_entry.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self.input_entry.bind("<Return>", self.send_command)
        
        # --- Pins Tab ---
        self.pin_view = PinVisualizer(self.tab_pins)
        self.pin_view.pack(fill="both", expand=True)
        
        # --- Graph Tab ---
        self.graph_view = GraphVisualizer(self.tab_graph)
        self.graph_view.pack(fill="both", expand=True)

    def refresh_ports(self):
        self.port_option.configure(values=self.serial.get_ports())
        
    def toggle_connection(self):
        if self.serial.is_running:
            self.serial.disconnect()
            self.connect_btn.configure(text="Connect", fg_color="#1f538d") # Blue
        else:
            port = self.port_option.get()
            if self.serial.connect(port):
                self.connect_btn.configure(text="Disconnect", fg_color="red")
                
    def send_command(self, event=None):
        text = self.input_entry.get()
        if text:
            self.serial.send(text)
            self.input_entry.delete(0, "end")
            
    def apply_config(self):
        d_pins = [i for i in range(14) if self.pin_vars[f"D{i}"].get()]
        a_pins = [i for i in range(6) if self.pin_vars[f"A{i}"].get()]
        self.serial.send_config(d_pins, a_pins)
        
        # Update Visualizers
        self.pin_view.update_layout(d_pins, a_pins)
        self.graph_view.update_layout(a_pins)
        
    def detect_all(self):
        # Enable all checkboxes
        for var in self.pin_vars.values():
            var.set(True)
        self.apply_config()
        
    def log_message(self, msg):
        print(f"[LOG] {msg}")
        
    def on_message(self, origin, data):
        ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.tree.insert("", 0, values=(ts, origin, data))
        
    def on_status(self, status):
        # Update Pin View
        self.pin_view.update_status(status)
        
        # Update Graph Data
        for k, v in status.items():
            if k.startswith("A"):
                self.analog_data[k].append(v)
        self.graph_view.update_data(self.analog_data)

class PinVisualizer(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.indicators = {}
        
    def update_layout(self, d_pins, a_pins):
        for widget in self.winfo_children():
            widget.destroy()
        self.indicators = {}
        
        # Digital
        if d_pins:
            lbl = ctk.CTkLabel(self, text="Digital Pins", font=("Arial", 16, "bold"))
            lbl.pack(pady=10)
            d_frame = ctk.CTkFrame(self)
            d_frame.pack(pady=5)
            for p in d_pins:
                f = ctk.CTkFrame(d_frame, width=60, height=60)
                f.pack(side="left", padx=5)
                l = ctk.CTkLabel(f, text=f"D{p}")
                l.place(relx=0.5, rely=0.3, anchor="center")
                ind = ctk.CTkLabel(f, text="OFF", fg_color="gray", corner_radius=5)
                ind.place(relx=0.5, rely=0.7, anchor="center")
                self.indicators[f"D{p}"] = ind
                
        # Analog
        if a_pins:
            lbl = ctk.CTkLabel(self, text="Analog Pins", font=("Arial", 16, "bold"))
            lbl.pack(pady=10)
            a_frame = ctk.CTkFrame(self)
            a_frame.pack(pady=5)
            for p in a_pins:
                f = ctk.CTkFrame(a_frame, width=80, height=60)
                f.pack(side="left", padx=5)
                l = ctk.CTkLabel(f, text=f"A{p}")
                l.place(relx=0.5, rely=0.3, anchor="center")
                val = ctk.CTkLabel(f, text="0")
                val.place(relx=0.5, rely=0.7, anchor="center")
                self.indicators[f"A{p}"] = val
                
    def update_status(self, status):
        for k, v in status.items():
            if k in self.indicators:
                if k.startswith("D"):
                    color = "green" if v == 1 else "gray"
                    text = "ON" if v == 1 else "OFF"
                    self.indicators[k].configure(fg_color=color, text=text)
                else:
                    self.indicators[k].configure(text=str(v))

class GraphVisualizer(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.figure, self.ax = plt.subplots(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.active_pins = []
        
    def update_layout(self, a_pins):
        self.active_pins = [f"A{p}" for p in a_pins]
        self.ax.clear()
        self.ax.legend(self.active_pins)
        self.canvas.draw()
        
    def update_data(self, data_dict):
        self.ax.clear()
        for pin in self.active_pins:
            if pin in data_dict:
                self.ax.plot(list(data_dict[pin]), label=pin)
        self.ax.legend()
        self.canvas.draw()
