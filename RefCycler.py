import os, sys
import threading
import time
from PIL import Image, ImageTk
import customtkinter as ctk
from tkinter import filedialog, messagebox

from aux_func import *

class ImageCyclerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Image Cycler")
        self.geometry("1174x768")  # Increased width by 150 pixels#
        
        if hasattr(sys, '_MEIPASS'):
            icon_path = os.path.join(sys._MEIPASS, 'app_icon.ico')
        else:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_icon.ico')

        self.iconbitmap(icon_path)  # Set the icon here

        self.attributes("-topmost", True)  # Set the window to always be on top

        # Initialize variables
        self.image_list = []
        self.current_image_index = 0
        self.cycle_interval = 3  # Default cycle interval in seconds
        self.images_per_board = 3  # Default number of images per mood board
        self.selected_folder = None
        self.zoom_factor = 1.0
        self.image_origin = (0, 0)
        self.drag_start = None
        self.current_image = None

        self.stop_event = threading.Event()  # Event to signal stopping of the thread

        # Create and place widgets in a grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)
        self.grid_columnconfigure(4, weight=1)
        self.grid_columnconfigure(5, weight=1)
        self.grid_columnconfigure(6, weight=1)
        self.grid_columnconfigure(7, weight=1)

        self.folder_button = ctk.CTkButton(self, text="Select Folder", command=self.select_folder)
        self.folder_button.grid(row=0, column=0, padx=20, pady=20, sticky="ew")

        self.interval_label = ctk.CTkLabel(self, text="Seconds :")
        self.interval_label.grid(row=0, column=1, padx=20, pady=10, sticky="w")

        self.interval_entry = ctk.CTkEntry(self, width=100)
        self.interval_entry.insert(0, "3")
        self.interval_entry.grid(row=0, column=2, padx=20, pady=10, sticky="w")

        self.images_per_board_label = ctk.CTkLabel(self, text="Images per board:")
        self.images_per_board_label.grid(row=0, column=3, padx=20, pady=10, sticky="w")

        self.images_per_board_entry = ctk.CTkEntry(self, width=100)
        self.images_per_board_entry.insert(0, "3")
        self.images_per_board_entry.grid(row=0, column=4, padx=20, pady=10, sticky="w")

        self.folder_selection_label = ctk.CTkLabel(self, text="Select Subfolder:")
        self.folder_selection_label.grid(row=1, column=0, padx=20, pady=10, sticky="w")

        self.folder_selection = ctk.CTkComboBox(self, values=[""])
        self.folder_selection.grid(row=1, column=1, columnspan=2, padx=20, pady=10, sticky="ew")
        self.folder_selection.bind("<<ComboboxSelected>>", self.update_selected_folder)

        self.save_button = ctk.CTkButton(self, text="Save", command=self.save_settings)
        self.save_button.grid(row=0, column=5, padx=20, pady=20, sticky="ew")

        self.cycle_switch = ctk.CTkSwitch(self, text="Cycle", command=self.toggle_cycling)
        self.cycle_switch.grid(row=1, column=3, padx=20, pady=20, sticky="ew")
        
        self.canvas = ctk.CTkCanvas(self, background="black")
        self.canvas.grid(row=2, column=0, columnspan=8, padx=20, pady=20, sticky="nsew")
        self.rowconfigure(2, weight=1)  # Make the canvas row stretch with window resize

        self.bind("<Left>", self.show_previous_image)
        self.bind("<Right>", self.show_next_image)
        self.canvas.bind("<MouseWheel>", self.zoom_image)
        self.bind("<space>", self.reset_zoom)
        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag_image)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drag)

        # Bind Enter key to save settings
        self.bind("<Return>", lambda event: self.save_settings())

        # Start the image cycling in a separate thread
        self.cycling_thread = threading.Thread(target=self.cycle_images, daemon=True)
        self.cycling_thread.start()

    def toggle_cycling(self):
        if self.cycle_switch.get() == 1:  # Switch is ON
            self.stop_event.clear()
            self.cycling_thread = threading.Thread(target=self.cycle_images, daemon=True)
            self.cycling_thread.start()
            self.cycle_switch.configure(text="Stop")
        else:  # Switch is OFF
            self.stop_event.set()
            self.cycle_switch.configure(text="Cycle")

    def stop_cycling(self):
        self.stop_event.set()

    def select_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.subfolders = [f.path for f in os.scandir(folder_path) if f.is_dir()]
            self.folder_selection.configure(values=[os.path.basename(f) for f in self.subfolders])
            self.current_image_index = 0
            if self.subfolders:
                self.folder_selection.set(os.path.basename(self.subfolders[0]))
                self.update_selected_folder()
            else:
                messagebox.showerror("Error", "No subfolders found in the selected folder")
        else:
            messagebox.showinfo("Info", "No folder selected")

    def update_selected_folder(self, event=None):
        selection = self.folder_selection.get()
        if selection:
            selected_path = [f for f in self.subfolders if os.path.basename(f) == selection]
            if selected_path:
                self.selected_folder = selected_path[0]
                self.image_list = [os.path.join(self.selected_folder, f) for f in os.listdir(self.selected_folder) if f.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'bmp'))]
                self.current_image_index = 0  # Reset the image index
                print(f"Selected folder: {self.selected_folder}, Number of images: {len(self.image_list)}")
                if self.image_list:
                    self.update_image()
                else:
                    messagebox.showerror("Error", "No images found in the selected subfolder")
        else:
            self.selected_folder = None

    def save_settings(self):
        try:
            self.cycle_interval = int(self.interval_entry.get())
        except ValueError:
            self.cycle_interval = 3  # Default value if invalid

        try:
            self.images_per_board = int(self.images_per_board_entry.get())
        except ValueError:
            self.images_per_board = 3  # Default value if invalid

        # Ensure the folder selection is respected
        self.update_selected_folder()

        print(f"Settings saved: Cycle Interval = {self.cycle_interval}, Images per board = {self.images_per_board}, Selected Folder = {self.selected_folder}")
        self.update_image()

    def update_image(self):
        if not self.image_list:
            return
        
        # Select the batch of images for the current mood board
        start_index = self.current_image_index
        end_index = start_index + self.images_per_board
        images_to_display = self.image_list[start_index:end_index]

        # Create the mood board image using bin packing
        mood_board_img = self.create_mood_board(images_to_display)

        # Resize to fit the UI while maintaining aspect ratio
        self.display_image(mood_board_img)

    def create_mood_board(self, images):
        # Load images
        opened_images = load_images(images)

        # Define the bin dimensions (you can adjust these values)
        bin_width = 4096    
        bin_height = 4096

        # Apply bin packing
        bins = bin_packing(opened_images, bin_width, bin_height)

        # Create packed image from bins
        packed_images = create_packed_image(bins)
        
        # Assuming one packed image for simplicity
        return packed_images[0] if packed_images else Image.new('RGBA', (bin_width, bin_height), (255, 255, 255, 0))

    def cycle_images(self):
        while not self.stop_event.is_set():
            if self.image_list:
                self.current_image_index = (self.current_image_index + self.images_per_board) % len(self.image_list)
                self.update_image()
            time.sleep(self.cycle_interval)

    def show_previous_image(self, event):
        if not self.image_list:
            return
        
        self.current_image_index = (self.current_image_index - self.images_per_board) % len(self.image_list)
        self.update_image()

    def show_next_image(self, event):
        if not self.image_list:
            return
        
        self.current_image_index = (self.current_image_index + self.images_per_board) % len(self.image_list)
        self.update_image()

    def zoom_image(self, event):
        # Calculate zoom factor
        if event.delta > 0:
            self.zoom_factor *= 1.1
        elif event.delta < 0:
            self.zoom_factor /= 1.1

        # Resize the image
        self.display_image(self.current_image)

    def reset_zoom(self, event):
        self.zoom_factor = 1.0
        self.image_origin = (0, 0)
        self.display_image(self.current_image)

    def start_drag(self, event):
        self.drag_start = (event.x, event.y)

    def drag_image(self, event):
        if self.drag_start and self.current_image:
            dx = event.x - self.drag_start[0]
            dy = event.y - self.drag_start[1]
            self.image_origin = (self.image_origin[0] + dx, self.image_origin[1] + dy)
            self.drag_start = (event.x, event.y)
            self.display_image(self.current_image)

    def stop_drag(self, event):
        self.drag_start = None

    def display_image(self, img):
        if img is None:
            return

        self.current_image = img.copy()

        # Resize the image according to the zoom factor
        width, height = img.size
        new_width = int(width * self.zoom_factor)
        new_height = int(height * self.zoom_factor)
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Create a blank image to place the resized image
        display_img = Image.new("RGBA", (self.canvas.winfo_width(), self.canvas.winfo_height()), (0, 0, 0, 0))
        display_img.paste(resized_img, (int(self.image_origin[0]), int(self.image_origin[1])))

        # Convert to ImageTk for display
        tk_img = ImageTk.PhotoImage(display_img)
        self.canvas.create_image(0, 0, anchor="nw", image=tk_img)
        self.canvas.image = tk_img

    def focus_app(self):
        self.lift()
        self.focus_force()

if __name__ == "__main__":
    app = ImageCyclerApp()
    app.mainloop()
