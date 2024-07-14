import json
import os
import sys
import shutil
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
import threading
import pyautogui
import time
import ctypes

def setup_logging():
    if not os.path.exists('logs'):
        os.makedirs('logs')

    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    if os.path.exists('logs/app.log'):
        shutil.move('logs/app.log', f'logs/app_{current_time}.log')

    return open('logs/app.log', 'w')

log_file = setup_logging()

def log_with_timestamp(message):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    log_message = f"[{timestamp}] {message}"
    print(log_message)
    log_file.write(log_message + '\n')
    log_file.flush()

def load_config():
    default_config = {
        "window": {
            "size": '347x300'
        },
        "TARGET_MINUTES": '7',  # Default target minutes
        "CLICK_INTERVAL": '15'
        
    }

    try:
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)

        for key, value in default_config.items():
            if key not in config:
                config[key] = value

        with open('config.json', 'w') as config_file:
            json.dump(config, config_file, indent=4)

    except FileNotFoundError:
        log_with_timestamp("Config file not found. Creating default config.")
        config = default_config
        with open('config.json', 'w') as config_file:
            json.dump(config, config_file, indent=4)

    return config

def get_current_time():
    current_time = datetime.now()
    return current_time.strftime('%H:%M:%S:%f').split(':')
    
def resource_path(relative_path):
    """ Get the absolute path to a resource, works for both development and PyInstaller. """
    try:
        base_path = sys._MEIPASS  # Used when running as a bundled exe
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class AutoClickerApp:
    def __init__(self, master):
        # Show disclaimer
        self.master = master
        self.config = load_config()
        self.apply_config()
        
        # Load and set the icon
        self.icon = tk.PhotoImage(file=resource_path('main.png'))
        self.master.iconphoto(True, self.icon)
        
        self.TARGET_MINUTES = self.config['TARGET_MINUTES']
        self.CLICK_INTERVAL = self.config['CLICK_INTERVAL']
        
        # Create a validation function for digit-only input
        # self.validate_digit_input = master.register(self.validate_digits)

        # Add Entry for TARGET_MINUTES
        self.minutes_label = ttk.Label(master, text="Target Minutes:")
        self.minutes_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.minutes_entry = ttk.Entry(master)
        self.minutes_entry.insert(0, self.TARGET_MINUTES)  # Set initial value
        self.minutes_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # Add Entry for CLICK_INTERVAL below TARGET_MINUTES
        self.interval_label = ttk.Label(master, text="Click Interval (seconds):")
        self.interval_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.interval_entry = ttk.Entry(master)
        self.interval_entry.insert(0, str(self.CLICK_INTERVAL))  # Set initial value
        self.interval_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        # Apply Button for both entries
        self.apply_button = ttk.Button(master, text="Apply", command=self.apply_settings)
        self.apply_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.toggle_button = ttk.Button(master, text="Enable Clicking", command=self.toggle_clicking)
        self.toggle_button.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.last_click_label = ttk.Label(master, text="Last Click: N/A")
        self.last_click_label.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.time_label = ttk.Label(master, text="")
        self.time_label.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.reload_button = ttk.Button(master, text="Reload Config", command=self.reload_config)
        self.reload_button.grid(row=6, column=0, padx=10, pady=10, sticky="ew")

        self.quit_button = ttk.Button(master, text="Quit", command=self.quit)
        self.quit_button.grid(row=6, column=1, padx=10, pady=10, sticky="ew")


        
        style = ttk.Style()
        style.theme_use('clam')

        # Define colors
        primary_color = "#1DB954"  
        secondary_color = "#191414"  
        text_color = "#FFFFFF"  

        # Configure the styles
        style.configure('TLabel', background=secondary_color, foreground=text_color)
        style.configure('TButton', background=primary_color, foreground=text_color)
        style.configure('TEntry', fieldbackground='#FFFFFF', background=secondary_color, foreground='#000000')
        style.map('TButton', background=[('active', primary_color), ('!disabled', primary_color)])

        # Apply background color to the main window
        self.master.configure(background=secondary_color)

        # Apply the theme to each widget
        self.minutes_label.configure(style='TLabel')
        self.minutes_entry.configure(style='TEntry')
        self.toggle_button.configure(style='TButton')
        self.last_click_label.configure(style='TLabel')
        self.time_label.configure(style='TLabel')
        self.reload_button.configure(style='TButton')
        self.quit_button.configure(style='TButton')

        self.update_time()  # Initial time display
        self.clicking_enabled = False
        self.running = True

        master.grid_rowconfigure(0, weight=1)
        master.grid_rowconfigure(1, weight=1)
        master.grid_rowconfigure(2, weight=1)
        master.grid_rowconfigure(3, weight=1)
        master.grid_rowconfigure(4, weight=1)
        master.grid_rowconfigure(5, weight=1)
        master.grid_columnconfigure(0, weight=1)
        master.grid_columnconfigure(1, weight=1)
        
        self.show_disclaimer()

    def apply_config(self):
        window_config = self.config['window']
        self.master.title("Echomancing")
        #self.master.geometry("260x275")
        self.master.geometry(window_config['size'])
        self.master.attributes('-topmost', True)  # Set window to always on top
        
    def show_disclaimer(self):
        disclaimer_text = (
            "By using our software, you acknowledge that there is a risk of being banned from Wuthering Wave. "
            "We are not responsible for any bans or penalties that may occur as a result of using our software. "
            "Use at your own risk."
        )
        response = messagebox.askyesno("Disclaimer", disclaimer_text)
        if not response:
            self.quit()  

    def reload_config(self):
        log_with_timestamp("Reloading config...")
        new_config = load_config()  # Load new config

        # Check if TARGET_MINUTES has changed
        if new_config['TARGET_MINUTES'] != self.config['TARGET_MINUTES']:
            log_with_timestamp(f"Updating TARGET_MINUTES from {self.config['TARGET_MINUTES']} to {new_config['TARGET_MINUTES']}")
            self.TARGET_MINUTES = new_config['TARGET_MINUTES']
            self.config['TARGET_MINUTES'] = self.TARGET_MINUTES  # Update stored config

        self.apply_config()  # Apply any other window changes if needed
        log_with_timestamp("Config reloaded")
        


    def update_time(self):
        current_time = get_current_time()
        self.time_label.config(text=f"Current Time: {current_time}")
        self.master.after(1000, self.update_time)

    def update_last_click(self, time):
        self.last_click_label.config(text=f"Last Click: {time}")

    def toggle_clicking(self):
        self.clicking_enabled = not self.clicking_enabled
        state = "enabled" if self.clicking_enabled else "disabled"
        self.toggle_button.config(text=f"{state.title()} Clicking")
        log_with_timestamp(f"Clicking {state}")
        
    #def validate_digits(self, new_value):
        """ Validate input to allow only digits. """
        #if new_value == "" or new_value.isdigit():
            #return True
        #return False
        
    def apply_settings(self):
        """ Update TARGET_MINUTES and CLICK_INTERVAL from the entry fields. """
        new_minutes = self.minutes_entry.get().strip()  # Get and strip any extra whitespace
        new_interval = self.interval_entry.get().strip()  # Get and strip any extra whitespace

        if new_minutes:
            log_with_timestamp(f"Updating TARGET_MINUTES to {new_minutes}")
            self.TARGET_MINUTES = new_minutes
            self.config['TARGET_MINUTES'] = new_minutes  # Update stored config

        if new_interval:
            try:
                new_interval_value = int(new_interval)
                log_with_timestamp(f"Updating CLICK_INTERVAL to {new_interval_value}")
                self.CLICK_INTERVAL = new_interval_value
                self.config['CLICK_INTERVAL'] = self.CLICK_INTERVAL  # Update stored config
            except ValueError:
                log_with_timestamp(f"Invalid CLICK_INTERVAL value: {new_interval}")

        log_with_timestamp("Settings applied")


    def quit(self):
        self.running = False
        self.master.after(100, self.master.quit)

def main():
    log_with_timestamp("Starting main function")

    root = tk.Tk()
    app = AutoClickerApp(root)

    last_click_time = None
    next_check = time.perf_counter() + 1  # Check every second

    log_with_timestamp("Entering main loop")
    
    TARGET_MINUTES = app.config["TARGET_MINUTES"]  # Load from config
    
    def click():
        ctypes.windll.user32.mouse_event(2, 0, 0, 0, 0)  # Mouse down
        ctypes.windll.user32.mouse_event(4, 0, 0, 0, 0)  # Mouse up

    def clicker_loop():
        nonlocal last_click_time, next_check
        while app.running:
            current = time.perf_counter()
            if current >= next_check:
                try:
                    time_parts = get_current_time()
                    
                    if time_parts:
                        h, m, s, ms = time_parts
                        ms = int(time_parts[3]) // 1000  # Convert microseconds to milliseconds
                        
                        # Check if the minutes contain '7'
                        if app.TARGET_MINUTES in m and app.clicking_enabled:
                            # Check if seconds are 0, 15, 30, or 45
                            if int(s) % app.CLICK_INTERVAL == 0 or ms <= 50:
                                click()  # Perform click
                                click_time = f"{h}:{m}:{s}:{ms}"
                                log_with_timestamp(f"Clicked at {click_time}")
                                app.update_last_click(click_time)

                except Exception as e:
                    if app.running:
                        log_with_timestamp(f"Error in clicker loop: {e}")
                    break

                next_check = current + 1  # Check every second
                
            time.sleep(0.0001)  # Sleep briefly to reduce CPU usage

    clicker_thread = threading.Thread(target=clicker_loop, daemon=True)
    clicker_thread.start()

    root.mainloop()

    app.running = False
    time.sleep(0.2)
    log_file.close()

if __name__ == "__main__":
    main()
