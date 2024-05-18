import os
import threading
import time
from PIL import Image
import customtkinter as ctk
from tkinter import filedialog, messagebox

class ImageCyclerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Image Cycler")
        self.geometry("800x600")
        
        # Initialize variables
        self.image_list = []
        self.current_image_index = 0
        self.cycle_interval = 3  # Default cycle interval in seconds
        
        # Create and place widgets in a grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self.folder_button = ctk.CTkButton(self, text="Select Folder", command=self.select_folder)
        self.folder_button.grid(row=0, column=0, padx=20, pady=20, sticky="ew")

        self.interval_label = ctk.CTkLabel(self, text="Seconds (seconds):")
        self.interval_label.grid(row=0, column=1, padx=20, pady=10, sticky="w")

        self.interval_entry = ctk.CTkEntry(self, width=100)
        self.interval_entry.insert(0, "3")
        self.interval_entry.grid(row=0, column=2, padx=20, pady=10, sticky="w")
        
        self.image_label = ctk.CTkLabel(self, text="")
        self.image_label.grid(row=1, column=0, columnspan=3, padx=20, pady=20)

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

    def update_image(self):
        if not self.image_list:
            return
        
        image_path = self.image_list[self.current_image_index]
        img = Image.open(image_path)
        
        # Calculate the new size maintaining aspect ratio
        max_width, max_height = 800, 600
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        
        # Convert to CTkImage for HighDPI support
        ctk_img = ctk.CTkImage(dark_image=img, size=(img.width, img.height))
        self.image_label.configure(image=ctk_img)
        self.image_label.image = ctk_img

    def cycle_images(self):
        while True:
            if self.image_list:
                self.current_image_index = (self.current_image_index + 1) % len(self.image_list)
                self.update_image()
            try:
                self.cycle_interval = int(self.interval_entry.get())
            except ValueError:
                self.cycle_interval = 3  # Default value if invalid
            time.sleep(self.cycle_interval)

    def show_previous_image(self, event):
        if not self.image_list:
            return
        
        self.current_image_index = (self.current_image_index - 1) % len(self.image_list)
        self.update_image()

    def show_next_image(self, event):
        if not self.image_list:
            return
        
        self.current_image_index = (self.current_image_index + 1) % len(self.image_list)
        self.update_image()

if __name__ == "__main__":
    app = ImageCyclerApp()
    app.mainloop()
