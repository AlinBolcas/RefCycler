import os
import threading
import time
from PIL import Image
import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk

class Bin:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.remaining_width = width
        self.remaining_height = height
        self.current_x = 0
        self.current_y = 0
        self.max_row_height = 0
        self.images = []

    def can_place_image(self, img_width, img_height):
        if img_width > self.remaining_width:
            if img_height + self.max_row_height > self.height:
                return False
            self.current_x = 0
            self.current_y += self.max_row_height
            self.remaining_width = self.width
            self.max_row_height = 0
        return img_width <= self.remaining_width and self.current_y + img_height <= self.height

    def place_image(self, img, position):
        self.images.append((img, position))
        self.remaining_width -= img.width
        self.current_x += img.width
        if img.height > self.max_row_height:
            self.max_row_height = img.height

    def is_empty(self):
        return len(self.images) == 0

def load_images(image_paths):
    images = []
    for path in image_paths:
        img = Image.open(path)
        images.append(img)
    return images

def bin_packing(images, bin_width, bin_height):
    bins = []

    for img in images:
        placed = False
        for bin in bins:
            if bin.can_place_image(img.width, img.height):
                bin.place_image(img, (bin.current_x, bin.current_y))
                placed = True
                break
        if not placed:
            new_bin = Bin(bin_width, bin_height)
            new_bin.place_image(img, (0, 0))
            bins.append(new_bin)

    return bins

def create_packed_image(bins):
    packed_images = []
    for bin in bins:
        if not bin.is_empty():
            max_width = max(img.width + pos[0] for img, pos in bin.images)
            max_height = max(img.height + pos[1] for img, pos in bin.images)
            packed_image = Image.new('RGBA', (max_width, max_height), (255, 255, 255, 0))
            for img, position in bin.images:
                packed_image.paste(img, position)
            packed_images.append(packed_image)
    return packed_images

class ImageCyclerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Image Cycler")
        self.geometry("1024x768")
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico")
        self.iconbitmap(icon_path)  # Set the icon here

        self.attributes("-topmost", True)  # Set the window to always be on top

        # Initialize variables
        self.image_list = []
        self.current_image_index = 0
        self.cycle_interval = 3  # Default cycle interval in seconds
        self.images_per_board = 3  # Default number of images per mood board
        self.selected_folder = None
        
        # Create and place widgets in a grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)
        
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
        
        self.image_label = ctk.CTkLabel(self, text="")
        self.image_label.grid(row=2, column=0, columnspan=6, padx=20, pady=20, sticky="nsew")
        
        self.bind("<Left>", self.show_previous_image)
        self.bind("<Right>", self.show_next_image)

        # Bind the Enter key to the save_settings method
        self.bind('<Return>', lambda event: self.save_settings())
        
        # Start the image cycling in a separate thread
        self.cycling_thread = threading.Thread(target=self.cycle_images, daemon=True)
        self.cycling_thread.start()

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
        max_width, max_height = self.winfo_width(), self.winfo_height()
        mood_board_img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        
        # Convert to CTkImage for HighDPI support
        ctk_img = ctk.CTkImage(dark_image=mood_board_img, size=(mood_board_img.width, mood_board_img.height))
        self.image_label.configure(image=ctk_img)
        self.image_label.image = ctk_img

    def create_mood_board(self, images):
        # Load images
        opened_images = load_images(images)

        # Define the bin dimensions (you can adjust these values)
        bin_width = 1024
        bin_height = 1024

        # Apply bin packing
        bins = bin_packing(opened_images, bin_width, bin_height)

        # Create packed image from bins
        packed_images = create_packed_image(bins)
        
        # Assuming one packed image for simplicity
        return packed_images[0] if packed_images else Image.new('RGBA', (bin_width, bin_height), (255, 255, 255, 0))

    def cycle_images(self):
        while True:
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

if __name__ == "__main__":
    app = ImageCyclerApp()
    app.mainloop()
