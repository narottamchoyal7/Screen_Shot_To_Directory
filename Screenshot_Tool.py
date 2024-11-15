import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Canvas
import pyautogui
import os
import threading
import time
import mss
import mss.tools
from pynput import keyboard
from PIL import Image

# Define constants for key mappings
screenshot_shortcut = keyboard.Key.insert
region_shortcut = keyboard.Key.home
save_exit_shortcut = keyboard.Key.end

# Initialize variables
img_count = 1
currently_pressed = set()
screenshot_dir = "Class/Session-"
interval = 0  # Default interval in seconds

# Create directories
def create_dirs():
    if not os.path.exists(screenshot_dir):
        os.makedirs(screenshot_dir)

# Get the next available screenshot number
def get_next_screenshot_number():
    global img_count
    files = os.listdir(screenshot_dir)
    if not files:
        img_count = 1
    else:
        numbers = [int(f.split('.')[0]) for f in files if f.endswith('.png')]
        img_count = max(numbers) + 1 if numbers else 1

class ScreenshotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Screenshot Tool Created By Narottam  Choyal")
        self.root.geometry("430x230")

        # Styling
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Arial", 10), padding=5, relief="raised")

        # Main frame
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Canvas with scrollbars
        self.canvas = Canvas(self.main_frame)
        self.scroll_y = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.scroll_x = ttk.Scrollbar(self.main_frame, orient="horizontal", command=self.canvas.xview)

        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Label
        self.label = ttk.Label(self.scrollable_frame, text="Screenshot Tool")
        self.label.grid(row=0, column=0, columnspan=3, pady=10)

        # Buttons
        self.start_button = ttk.Button(self.scrollable_frame, text="Start Screenshots", command=self.start_taking_screenshots)
        self.start_button.grid(row=2, column=0, padx=5, pady=5)

        self.stop_button = ttk.Button(self.scrollable_frame, text="Stop Screenshots", command=self.stop_taking_screenshots, state=tk.DISABLED)
        self.stop_button.grid(row=3, column=0, columnspan=3, pady=10)

        self.interval_label = ttk.Label(self.scrollable_frame, text="Screenshot Interval (seconds):")
        self.interval_label.grid(row=4, column=0, padx=5, pady=5)

        self.interval_entry = ttk.Entry(self.scrollable_frame)
        self.interval_entry.grid(row=4, column=1, padx=5, pady=5)
        self.interval_entry.insert(0, str(interval))  # Default interval is 3 seconds

        self.set_interval_button = ttk.Button(self.scrollable_frame, text="Set Interval", command=self.set_interval)
        self.set_interval_button.grid(row=4, column=2, padx=5, pady=5)

        # Instructions
        self.instructions = ttk.Label(self.scrollable_frame, text="Instructions:\n1. Start taking screenshots.\n2. Press Homekey for Region.\n3. Press InsertKey for Full Screen.\n4. Press EndKey to save and exit.")
        self.instructions.grid(row=5, column=0, columnspan=3, pady=10)

        self.running = False
        self.last_screenshot_path = None  # Store the last screenshot path

        # Start listening for key presses
        self.listener = keyboard.Listener(on_press=self.on_key_press)
        self.listener.start()

    def update_button_states(self, normal):
        state = tk.NORMAL if normal else tk.DISABLED
        self.start_button.config(state=state)

    def start_taking_screenshots(self):
        create_dirs()
        get_next_screenshot_number()

        self.running = True
        self.update_button_states(normal=False)
        self.stop_button.config(state=tk.NORMAL)

        threading.Thread(target=self.take_screenshots).start()

    def stop_taking_screenshots(self):
        self.running = False
        self.stop_button.config(state=tk.DISABLED)
        self.update_button_states(normal=True)

    def take_screenshots(self):
        while self.running:
            self.capture_full_screenshot()
            time.sleep(int(self.interval_entry.get()))  # Adjust the interval as needed

        messagebox.showinfo("Stopped", "Stopped taking screenshots.")

    def on_key_press(self, key):
        if key == region_shortcut:
            self.select_region()
        elif key == screenshot_shortcut:
            self.capture_full_screenshot()
        elif key == save_exit_shortcut:
            self.save_and_exit()

    def select_region(self):
        self.root.attributes("-topmost", False)

        def on_mouse_press(event):
            nonlocal start_x, start_y, rect_id
            start_x, start_y = event.x, event.y
            rect_id = canvas.create_rectangle(start_x, start_y, start_x, start_y, outline="Beige", width=2)

        def on_mouse_drag(event):
            if rect_id:
                canvas.coords(rect_id, start_x, start_y, event.x, event.y)

        def on_mouse_release(event):
            nonlocal start_x, start_y
            x1, y1 = min(start_x, event.y), min(start_y, event.x)
            x2, y2 = max(start_x, event.x), max(start_y, event.y)
            root_region.destroy()
            self.capture_screenshot(x1, y1, x2, y2)

        root_region = tk.Toplevel(self.root)
        root_region.title("Select Region")
        root_region.attributes("-topmost", True)
        root_region.geometry(f"{pyautogui.size()[0]}x{pyautogui.size()[1]}+0+0")
        root_region.config(bg="gray")
        root_region.attributes("-alpha", 0.3)
        root_region.attributes("-fullscreen", True)
        root_region.bind("<Escape>", lambda e: root_region.destroy())

        canvas = Canvas(root_region, cursor="cross", bg="gray", highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)

        start_x = start_y = None
        rect_id = None

        canvas.bind("<Button-1>", on_mouse_press)
        canvas.bind("<B1-Motion>", on_mouse_drag)
        canvas.bind("<ButtonRelease-1>", on_mouse_release)

    def capture_full_screenshot(self):
        global img_count
        try:
            create_dirs()  # Ensure directory exists before saving
            screenshot = pyautogui.screenshot()
            screenshot_path = os.path.join(screenshot_dir, f"{img_count:04d}.png")
            screenshot.save(screenshot_path, quality=95)  # Save with high quality
            img_count += 1
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while capturing the full screenshot: {e}")

    def capture_screenshot(self, x1, y1, x2, y2):
        global img_count
        try:
            create_dirs()  # Ensure directory exists before saving
            with mss.mss() as sct:
                monitor = {"top": y1, "left": x1, "width": x2 - x1, "height": y2 - y1}
                sct_img = sct.grab(monitor)
                screenshot_path = os.path.join(screenshot_dir, f"{img_count:04d}.png")
                mss.tools.to_png(sct_img.rgb, sct_img.size, output=screenshot_path)
                img_count += 1
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while capturing the region: {e}")

    def save_and_exit(self):
        if self.running:
            self.stop_taking_screenshots()
        self.listener.stop()
        self.root.destroy()

    def set_interval(self):
        global interval
        try:
            interval = int(self.interval_entry.get())
            messagebox.showinfo("Interval Set", f"Screenshot interval set to {interval} seconds.")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for the interval.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ScreenshotApp(root)
    root.mainloop()