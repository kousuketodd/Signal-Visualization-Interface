import customtkinter as ctk
from serial_interface import SerialInterface
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import input_validation as iv
import os
import pandas as pd
import time
import threading

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

ANGLE_DEFAULT = 0
CYCLES_DEFAULT = 0
PULSES_DEFAULT = 0
RESOLUTION_DEFAULT = 60
X_LIM_DEFAULT = (0, 100)
Y_LIM_DEFAULT = (0, 100)

# GUI Pages
class MainMenuPage(ctk.CTkFrame):
    def __init__(self, master, show_single_channel, show_multi_channel):
        super().__init__(master)
        self.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(self, text="Main Menu", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=40)

        icon_frame = ctk.CTkFrame(self)
        icon_frame.pack(pady=20)

        single_btn = ctk.CTkButton(icon_frame, text="Single Channel", width=200, height=100, command=show_single_channel)
        single_btn.grid(row=0, column=0, padx=20)

        multi_btn = ctk.CTkButton(icon_frame, text="Multi-Channel", width=200, height=100, command=show_multi_channel)
        multi_btn.grid(row=0, column=1, padx=20)

class MultiChannelPage(ctk.CTkFrame):
    def __init__(self, master, go_back):
        super().__init__(master)
        self.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(self, text="Multi-Channel Mode", font=ctk.CTkFont(size=20)).pack(pady=20)
        ctk.CTkButton(self, text="Back to Main Menu", command=go_back).pack(pady=10)

class SingleChannelPage(ctk.CTkFrame):
    def __init__(self, master, go_back, serial_interface: SerialInterface):
        super().__init__(master)
        self.grid(row=0, column=0, sticky="nsew")

        self.serial_interface = serial_interface
        self.running = False # If true, do not spawn a new thread to read values. If false, clear to spawn thread

        ctk.CTkButton(self, text="Back to Main Menu", command=go_back).grid(row=0, column=0, padx=20, pady=10, sticky="w")

        # Reusing your existing implementation under here
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Top control frame
        control_frame = ctk.CTkFrame(self)
        control_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        control_frame.grid_columnconfigure(0, weight=1)
        control_frame.grid_columnconfigure(1, weight=1)

        # Device config frame
        device_config_frame = ctk.CTkFrame(control_frame)
        device_config_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        device_config_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(device_config_frame, text="Device Angle:").grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.angle_entry = ctk.CTkEntry(device_config_frame, placeholder_text="°")
        self.angle_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(device_config_frame, text="Device Cycles:").grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.cycles_entry = ctk.CTkEntry(device_config_frame, placeholder_text="#")
        self.cycles_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(device_config_frame, text="Device Speed:").grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        self.speed_entry = ctk.CTkEntry(device_config_frame, placeholder_text="RPM")
        self.speed_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        self.enter_btn = ctk.CTkButton(device_config_frame, text="Configure Device", command=self.submit_values)
        self.enter_btn.grid(row=3, column=0, columnspan=2, padx=5, pady=10)

        # Graph config frame
        graph_config_frame = ctk.CTkFrame(control_frame)
        graph_config_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        graph_config_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(graph_config_frame, text="X Limit:").grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.xlim_entry = ctk.CTkEntry(graph_config_frame, placeholder_text="(a,b)")
        self.xlim_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(graph_config_frame, text="Y Limit:").grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.ylim_entry = ctk.CTkEntry(graph_config_frame, placeholder_text="(a,b)")
        self.ylim_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(graph_config_frame, text="Data Rate:").grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        self.resolution_entry = ctk.CTkEntry(graph_config_frame, placeholder_text="Hz")
        self.resolution_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        self.resolution_btn = ctk.CTkButton(graph_config_frame, text="Configure Graph", command=self.submit_graph_data)
        self.resolution_btn.grid(row=3, column=0, columnspan=2, padx=5, pady=10)

        # Monitor frame
        monitor_frame = ctk.CTkFrame(self)
        monitor_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(10, 20))
        monitor_frame.grid_rowconfigure(1, weight=1)
        monitor_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(monitor_frame, text="Live Serial Data", font=ctk.CTkFont(size=16)).grid(row=0, column=0, pady=(10, 5))

        self.fig, self.ax = plt.subplots()
        (self.line,) = self.ax.plot([], [], "bo", lw=2)

        self.ax.set_xlim(0, 100)
        self.ax.set_ylim(0, 100)
        self.ax.set_xlabel("Time Elapsed (s)")
        self.ax.set_ylabel("Resistance (Ω)")
        self.ax.set_title("Resistance vs Time")

        self.canvas = FigureCanvasTkAgg(self.fig, master=monitor_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=1, column=0, pady=10)
        self.x_vals, self.y_vals = [], []

        button_row_frame = ctk.CTkFrame(monitor_frame, fg_color="transparent")
        button_row_frame.grid(row=2, column=0, pady=10)

        self.start_btn = ctk.CTkButton(button_row_frame, text="Start/Resume", command=self.start_serial)
        self.start_btn.grid(row=0, column=0, padx=10)

        self.stop_btn = ctk.CTkButton(button_row_frame, text="Stop", command=self.stop)
        self.stop_btn.grid(row=0, column=1, padx=10)

        self.restart_btn = ctk.CTkButton(button_row_frame, text="Restart", command=self.restart)
        self.restart_btn.grid(row=0, column=2, padx=10)

        self.download_btn = ctk.CTkButton(button_row_frame, text="Download Data", command=self.download_data)
        self.download_btn.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        self.ani = animation.FuncAnimation(self.fig, self.update_plot, interval=1000, cache_frame_data=False)
        

    def submit_values(self):
        '''
        Sends angle, cycle, and pulse data to microcontroller.
        '''
        angle = self.angle_entry.get()
        cycles = self.cycles_entry.get()
        speed = self.speed_entry.get()

        # Check if entries are valid. Empty entries are assigned default values
        angle = iv.check_float(angle, ANGLE_DEFAULT)
        cycles = iv.check_int(cycles, CYCLES_DEFAULT)
        speed = iv.check_float(speed, PULSES_DEFAULT)

        # highlight entry boxes red if entries are invalid. If not, assign default border color
        if angle == None:
            self.angle_entry.configure(border_color="red")
            return
        else:
            self.angle_entry.configure(border_color="gray50")
        if cycles == None:
            self.cycles_entry.configure(border_color="red")
            return
        else:
            self.cycles_entry.configure(border_color="gray50")
        if speed == None:
            self.speed_entry.configure(border_color="red")
            return
        else:
            self.speed_entry.configure(border_color="gray50")

        cmd = f"SET angle={angle} cycles={cycles} speed={speed}"
        if self.serial_interface.ser and self.serial_interface.ser.is_open:
            self.serial_interface.send_command(cmd)


    def submit_graph_data(self):
        '''
        Sends resolution data to microcontroller and reconfigures graph
        '''
        resolution = self.resolution_entry.get()
        xlim = self.xlim_entry.get()
        ylim = self.ylim_entry.get()

        # Check if entries are valid. Empty entries are assigned default values
        resolution = iv.check_int(resolution, RESOLUTION_DEFAULT)
        xlim = iv.check_lim(xlim, X_LIM_DEFAULT)
        ylim = iv.check_lim(ylim, Y_LIM_DEFAULT)

        # highlight entry boxes red if entries are invalid. If not, assign default border color
        if resolution == None:
            self.resolution_entry.configure(border_color="red")
            return
        else:
            self.resolution_entry.configure(border_color="gray50")
        if xlim == None:
            self.xlim_entry.configure(border_color="red")
            return
        else:
            self.xlim_entry.configure(border_color="gray50")
        if ylim == None:
            self.ylim_entry.configure(border_color="red")
            return
        else:
            self.ylim_entry.configure(border_color="gray50")

        self.ax.set_xlim(xlim)
        self.ax.set_ylim(ylim)

        cmd = f"SET resolution={resolution}"
        if self.serial_interface.ser and self.serial_interface.ser.is_open:
            self.serial_interface.send_command(cmd)

        if self.ani:
            self.ani.event_source.stop()
        
        new_interval = 1000/int(resolution)
        self.ani = animation.FuncAnimation(self.fig, self.update_plot, interval=new_interval, cache_frame_data=False)
        self.canvas.draw()

    def download_data(self):
        file_path = ctk.filedialog.asksaveasfilename(
            title="Select a location",
            filetypes=(("CSV Files", "*.csv"), ("All Files", "*.*")),
            initialdir=os.path.expanduser("~")
        )
        
        if file_path[-4:] != '.csv':
            file_path += '.csv'
        
        data = {'strain': self.x_vals, 'pz_response': self.y_vals}
        df = pd.DataFrame(data)

        df.to_csv(file_path, index=False)


    def stop(self):
        '''
        Stops the hardware device.
        '''
        if self.serial_interface.ser and self.serial_interface.ser.is_open:
            self.serial_interface.send_command("STOP")

    def start_serial(self):
        '''
        Initializes the reading of real-time data from the micro-controller
        '''
        if self.serial_interface.ser and self.serial_interface.ser.is_open:
            # so that thread isn't spawned again when user resumes graph
            if self.running == False:
                self.running = True
                threading.Thread(target=self.serial_interface.read_lines(self.get_vals), daemon=True)
            self.serial_interface.send_command("START")

    def restart(self):
        '''
        Clears the graph and restarts the hardware's duty cycle
        '''
        if self.serial_interface.ser and self.serial_interface.ser.is_open:
            self.serial_interface.send_command("RESTART")
            self.x_vals = []
            self.y_vals = []

    def get_vals(self, data: list):
        '''
        A callback function. Extracts x and y data values from received microcontroller data.
        '''
        try:
            x, y = data.split(',')
            self.x_vals.append(int(x))
            self.y_vals.append(int(y))
        except Exception as e:
            print(f"Error parsing data: {e}")


    def update_plot(self, _):
        '''
        Updates graphing data in the GUI.
        '''
        self.line.set_data(self.x_vals, self.y_vals)
        return self.line,

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Signal Visualization Interface")
        self.geometry("1000x800")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.serial_interface = SerialInterface()

        self.main_menu = MainMenuPage(self, self.show_single_channel, self.show_multi_channel)
        self.single_page = SingleChannelPage(self, self.show_main_menu, self.serial_interface)
        self.multi_page = MultiChannelPage(self, self.show_main_menu)

        self.show_main_menu()

    def show_main_menu(self):
        self.main_menu.tkraise()

    def show_single_channel(self):
        threading.Thread(target=self.auto_connect_serial, daemon=True).start()
        self.single_page.tkraise()

    def show_multi_channel(self):
        self.multi_page.tkraise()

    def go_back(self):
        self.clear_window()
        self.serial_interface.disconnect()
        self.show_main_menu()

    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()

    def close(self):
        '''
        Called on the event of closing the GUI.
        '''
        self.clear_window()
        self.serial_interface.disconnect()
        exit()

    def auto_connect_serial(self):
        '''
        Waits for COM4 to be available, then connects and starts reading.
        '''
        while True:
            try:
                self.serial_interface.connect()
                if self.serial_interface.ser and self.serial_interface.ser.is_open:
                    print("Connected to COM4.")
                    break
            except:
                print("Waiting for COM4...")
            time.sleep(1)  # Wait before retrying

