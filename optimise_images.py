import os
import OpenEXR
import Imath
import numpy as np
from PIL import Image
import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk

class ImageResizerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Image Resizer")
        self.geometry("400x400")
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico")
        self.iconbitmap(icon_path)

        # Initialize variables
        self.input_folder_path = ""
        self.output_folder_path = ""
        self.scale_factor = 0.25  # Default scale factor
        self.output_format = "PNG"

        # Create and place widgets
        self.select_input_folder_button = ctk.CTkButton(self, text="Select Input Folder", command=self.select_input_folder)
        self.select_input_folder_button.pack(pady=10)

        self.select_output_folder_button = ctk.CTkButton(self, text="Select Output Folder", command=self.select_output_folder)
        self.select_output_folder_button.pack(pady=10)

        self.scale_label = ctk.CTkLabel(self, text="Scale Factor:")
        self.scale_label.pack(pady=5)

        self.scale_entry = ctk.CTkEntry(self, width=200)
        self.scale_entry.insert(0, "0.5")
        self.scale_entry.pack(pady=5)

        self.format_label = ctk.CTkLabel(self, text="Output Format:")
        self.format_label.pack(pady=5)

        self.format_combobox = ctk.CTkComboBox(self, values=["JPEG", "PNG"], command=self.set_output_format)
        self.format_combobox.set(self.output_format)
        self.format_combobox.pack(pady=5)

        self.progress = ttk.Progressbar(self, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=10)

        self.start_button = ctk.CTkButton(self, text="Start Resizing", command=self.start_resizing)
        self.start_button.pack(pady=10)

    def select_input_folder(self):
        self.input_folder_path = filedialog.askdirectory()
        if self.input_folder_path:
            print(f"Selected input folder: {self.input_folder_path}")
        else:
            messagebox.showinfo("Info", "No input folder selected")

    def select_output_folder(self):
        self.output_folder_path = filedialog.askdirectory()
        if self.output_folder_path:
            print(f"Selected output folder: {self.output_folder_path}")
        else:
            messagebox.showinfo("Info", "No output folder selected")

    def set_output_format(self, choice):
        self.output_format = choice

    def start_resizing(self):
        try:
            self.scale_factor = float(self.scale_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid scale factor. Please enter a valid number.")
            return

        if not self.input_folder_path:
            messagebox.showerror("Error", "No input folder selected. Please select an input folder first.")
            return

        if not self.output_folder_path:
            messagebox.showerror("Error", "No output folder selected. Please select an output folder first.")
            return

        self.resize_images_in_folder(self.input_folder_path, self.output_folder_path, self.scale_factor, self.output_format)
        messagebox.showinfo("Success", "Images resized successfully.")

    def resize_images_in_folder(self, input_folder, output_folder, scale_factor, output_format):
        files = [f for f in os.listdir(input_folder) if f.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'bmp', 'exr'))]
        self.progress["maximum"] = len(files)
        for idx, filename in enumerate(files):
            file_path = os.path.join(input_folder, filename)
            try:
                if filename.lower().endswith('exr'):
                    img = self.open_exr(file_path)
                else:
                    img = Image.open(file_path)

                new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
                resized_img = img.resize(new_size, Image.LANCZOS)

                # Convert to RGB if image has an alpha channel
                if resized_img.mode == 'RGBA':
                    resized_img = resized_img.convert('RGB')

                new_filename = os.path.splitext(filename)[0] + f".{output_format.lower()}"
                new_file_path = os.path.join(output_folder, new_filename)

                if output_format == "JPEG":
                    resized_img.save(new_file_path, "JPEG", quality=85)
                elif output_format == "PNG":
                    resized_img.save(new_file_path, "PNG", compress_level=6)

            except Exception as e:
                print(f"Error processing file {file_path}: {e}")
                continue

            self.progress["value"] = idx + 1
            self.update_idletasks()

    def open_exr(self, file_path):
        exr_file = OpenEXR.InputFile(file_path)
        header = exr_file.header()
        dw = header['dataWindow']
        width = dw.max.x - dw.min.x + 1
        height = dw.max.y - dw.min.y + 1

        channels = ['R', 'G', 'B']
        img_array = np.zeros((height, width, len(channels)), dtype=np.float32)

        for i, channel in enumerate(channels):
            if channel in header['channels']:
                ch_str = exr_file.channel(channel, Imath.PixelType(Imath.PixelType.FLOAT))
                ch = np.frombuffer(ch_str, dtype=np.float32)
                if ch.size == width * height:
                    img_array[:, :, i] = ch.reshape((height, width))
                else:
                    raise ValueError(f"Channel {channel} size mismatch: {ch.size} vs {width * height}")

        img_array = np.clip(img_array * 255.0, 0, 255).astype(np.uint8)
        img = Image.fromarray(img_array, 'RGB')
        return img

if __name__ == "__main__":
    app = ImageResizerApp()
    app.mainloop()
