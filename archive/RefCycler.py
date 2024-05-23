import os
import threading
import time
from PIL import Image, ImageTk
import customtkinter as ctk
from tkinter import filedialog, messagebox
import pyautogui

# ADDING STOP BUTTON
# SCREENSHOTTING: either with a button to trigger screenshotting or automatically screenshotting every x seconds
# ADDING LLM with vision gpt4o to write a criticism of the current state of work (based on screenshot)
# TTS to read out the criticism

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

def load_image(inputs: dict) -> dict:
    """Load image from file and encode it as base64."""
    image_path = inputs["image_path"]
  
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    image_base64 = encode_image(image_path)
    return {"image": image_base64}

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
        self.zoom_factor = 1.0
        self.image_origin = (0, 0)
        self.drag_start = None
        self.current_image = None
        
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
        
        self.canvas = ctk.CTkCanvas(self, background="black")
        self.canvas.grid(row=2, column=0, columnspan=6, padx=20, pady=20, sticky="nsew")
        self.rowconfigure(2, weight=1)  # Make the canvas row stretch with window resize

        self.bind("<Left>", self.show_previous_image)
        self.bind("<Right>", self.show_next_image)
        self.canvas.bind("<MouseWheel>", self.zoom_image)
        self.bind("<space>", self.reset_zoom)
        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag_image)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drag)

        # Bind the Enter key to the save_settings method
        self.bind('<Return>', lambda event: self.save_settings())
        
        # Start the image cycling in a separate thread
        self.cycling_thread = threading.Thread(target=self.cycle_images, daemon=True)
        self.cycling_thread.start()

        self.stop_event = threading.Event()  # Event to signal stopping of the thread

        self.stop_button = ctk.CTkButton(self, text="Stop", command=self.stop_cycling)
        self.stop_button.grid(row=0, column=6, padx=20, pady=20, sticky="ew")

        self.screenshot_button = ctk.CTkButton(self, text="Screenshot", command=self.take_screenshot)
        self.screenshot_button.grid(row=0, column=7, padx=20, pady=20, sticky="ew")

        self.screenshot_interval = 10  # Default screenshot interval in seconds
        self.screenshot_thread = threading.Thread(target=self.auto_screenshot, daemon=True)
        self.screenshot_thread.start()

    def take_screenshot(self):
        screenshot = pyautogui.screenshot()
        screenshot.save("screenshot.png")

    def auto_screenshot(self):
        while not self.stop_event.is_set():
            self.take_screenshot()
            time.sleep(self.screenshot_interval)

    def generate_critique(self):
        screenshot = pyautogui.screenshot()
        screenshot.save("screenshot.png")
        with open("screenshot.png", "rb") as img_file:
            image_data = img_file.read()
        response = openai.Image.create(image_data=image_data)
        critique = response.choices[0].text
        print(critique)

    def record_critique(self):
        self.tts_engine.say(self.critique_text)
        self.tts_engine.runAndWait()
    
    def play_critique(self):
        # play the audio
        pass

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

if __name__ == "__main__":
    app = ImageCyclerApp()
    app.mainloop()
