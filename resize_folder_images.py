import os
from PIL import Image
import customtkinter as ctk
from tkinter import filedialog, messagebox

class ImageResizerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Image Resizer")
        self.geometry("400x200")
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico")
        self.iconbitmap(icon_path)

        # Initialize variables
        self.folder_path = ""
        self.scale_factor = 0.25  # Default scale factor

        # Create and place widgets
        self.select_folder_button = ctk.CTkButton(self, text="Select Folder", command=self.select_folder)
        self.select_folder_button.pack(pady=10)

        self.scale_label = ctk.CTkLabel(self, text="Scale Factor:")
        self.scale_label.pack(pady=5)

        self.scale_entry = ctk.CTkEntry(self, width=200)
        self.scale_entry.insert(0, "0.25")
        self.scale_entry.pack(pady=5)

        self.start_button = ctk.CTkButton(self, text="Start Resizing", command=self.start_resizing)
        self.start_button.pack(pady=10)

    def select_folder(self):
        self.folder_path = filedialog.askdirectory()
        if self.folder_path:
            print(f"Selected folder: {self.folder_path}")
            # messagebox.showinfo("Selected Folder", f"Selected folder: {self.folder_path}")
        else:
            messagebox.showinfo("Info", "No folder selected")

    def start_resizing(self):
        try:
            self.scale_factor = float(self.scale_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid scale factor. Please enter a valid number.")
            return

        if not self.folder_path:
            messagebox.showerror("Error", "No folder selected. Please select a folder first.")
            return

        self.resize_images_in_folder(self.folder_path, self.scale_factor)
        messagebox.showinfo("Success", "Images resized successfully.")

    def resize_images_in_folder(self, folder_path, scale_factor):
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'bmp')):
                file_path = os.path.join(folder_path, filename)
                with Image.open(file_path) as img:
                    new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
                    resized_img = img.resize(new_size, Image.LANCZOS)

                    # Convert to RGB if image has an alpha channel
                    if resized_img.mode == 'RGBA':
                        resized_img = resized_img.convert('RGB')

                    new_filename = os.path.splitext(filename)[0] + "_resized.jpg"
                    new_file_path = os.path.join(folder_path, new_filename)
                    resized_img.save(new_file_path, "JPEG")

if __name__ == "__main__":
    app = ImageResizerApp()
    app.mainloop()
