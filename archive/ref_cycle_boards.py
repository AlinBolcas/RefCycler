import os
import threading
import time
from PIL import Image, ImageOps
import customtkinter as ctk
from tkinter import filedialog, messagebox, Tk

class ImageCyclerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Image Cycler")
        self.geometry("800x600")
        self.bind("<Configure>", self.resize_image)

        # Initialize variables
        self.image_list = []
        self.current_image_index = 0
        self.cycle_interval = 3  # Default cycle interval in seconds
        self.batch_size = 1  # Default number of images per mood board

        # Create and place widgets in a grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)

        self.folder_button = ctk.CTkButton(self, text="Select Folder", command=self.select_folder)
        self.folder_button.grid(row=0, column=0, padx=20, pady=20, sticky="ew")

        self.interval_label = ctk.CTkLabel(self, text="Cycle Interval (seconds):")
        self.interval_label.grid(row=0, column=1, padx=20, pady=10, sticky="w")

        self.interval_entry = ctk.CTkEntry(self, width=100)
        self.interval_entry.insert(0, "3")
        self.interval_entry.grid(row=0, column=2, padx=20, pady=10, sticky="w")

        self.batch_label = ctk.CTkLabel(self, text="Images per Mood Board:")
        self.batch_label.grid(row=1, column=0, padx=20, pady=10, sticky="w")

        self.batch_entry = ctk.CTkEntry(self, width=100)
        self.batch_entry.insert(0, "1")
        self.batch_entry.grid(row=1, column=1, padx=20, pady=10, sticky="w")

        self.save_button = ctk.CTkButton(self, text="Save Settings", command=self.save_settings)
        self.save_button.grid(row=1, column=2, padx=20, pady=20, sticky="ew")

        self.image_label = ctk.CTkLabel(self, text="")
        self.image_label.grid(row=2, column=0, columnspan=3, padx=20, pady=20)

        self.bind("<Left>", self.show_previous_image)
        self.bind("<Right>", self.show_next_image)

        # Start the image cycling in a separate thread
        self.cycling_thread = threading.Thread(target=self.cycle_images, daemon=True)
        self.cycling_thread.start()

    def select_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.image_list = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'bmp'))]
            self.current_image_index = 0
            if self.image_list:
                self.update_image()
            else:
                messagebox.showerror("Error", "No images found in the selected folder")
        else:
            messagebox.showinfo("Info", "No folder selected")

    def save_settings(self):
        try:
            self.cycle_interval = int(self.interval_entry.get())
        except ValueError:
            self.cycle_interval = 3  # Default value if invalid
        try:
            self.batch_size = int(self.batch_entry.get())
        except ValueError:
            self.batch_size = 1  # Default value if invalid

    def update_image(self):
        if not self.image_list:
            return

        width, height = self.winfo_width(), self.winfo_height()
        images_to_display = []
        for i in range(self.batch_size):
            index = (self.current_image_index + i) % len(self.image_list)
            image_path = self.image_list[index]
            img = Image.open(image_path)
            img = ImageOps.fit(img, (width // self.batch_size, height), Image.Resampling.LANCZOS)
            images_to_display.append(img)

        if images_to_display:
            combined_image = Image.new('RGB', (width, height))
            for i, img in enumerate(images_to_display):
                combined_image.paste(img, (i * (width // self.batch_size), 0))
            ctk_img = ctk.CTkImage(dark_image=combined_image, size=(width, height))
            self.image_label.configure(image=ctk_img)
            self.image_label.image = ctk_img

    def cycle_images(self):
        while True:
            if self.image_list:
                self.current_image_index = (self.current_image_index + self.batch_size) % len(self.image_list)
                self.update_image()
            time.sleep(self.cycle_interval)

    def show_previous_image(self, event):
        if not self.image_list:
            return
        self.current_image_index = (self.current_image_index - self.batch_size) % len(self.image_list)
        self.update_image()

    def show_next_image(self, event):
        if not self.image_list:
            return
        self.current_image_index = (self.current_image_index + self.batch_size) % len(self.image_list)
        self.update_image()

    def resize_image(self, event):
        self.update_image()

if __name__ == "__main__":
    app = ImageCyclerApp()
    app.mainloop()
