
from PIL import Image, ImageTk, ImageGrab, ImageEnhance
import customtkinter as ctk
import base64

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

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
    print(f"Encoded image length: {len(encoded_image)}")  # Debugging print statement
    return encoded_image


class ScreenRegionSelector(ctk.CTk):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.attributes("-fullscreen", True)
        self.attributes("-alpha", 0.3)  # Slightly transparent window
        self.canvas = ctk.CTkCanvas(self, cursor="cross", bg="black")
        self.canvas.pack(fill=ctk.BOTH, expand=True)
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.bind("<Map>", self.on_map)  # Bind the Map event to focus the window
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.selected_region = None

    def on_map(self, event):
        self.focus_force()  # Force focus on the window

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='white')
        # print(f"Button pressed at ({self.start_x}, {self.start_y})")

    def on_mouse_drag(self, event):
        if self.rect:
            self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)
        # print(f"Mouse dragged to ({event.x}, {event.y})")

    def on_button_release(self, event):
        end_x = event.x
        end_y = event.y
        # print(f"Button released at ({end_x}, {end_y})")
        self.selected_region = (self.start_x, self.start_y, end_x, end_y)
        self.capture_and_save(self.start_x, self.start_y, end_x, end_y)
        self.parent.region_selected = True  # Ensure flag is set
        self.destroy()

    def capture_and_save(self, start_x, start_y, end_x, end_y):
        left = min(start_x, end_x)
        top = min(start_y, end_y)
        right = max(start_x, end_x)
        bottom = max(start_y, end_y)

        screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
        screenshot_path = "screenshot.png"
        screenshot.save(screenshot_path)
        print(f"Cropped screenshot saved as {screenshot_path}")
        return screenshot_path




class ConversationBuffer:
    def __init__(self, max_tokens=100000):
        self.max_tokens = max_tokens
        self.buffer = []
        self.token_count = 0

    def _tokenize(self, message):
        # Simple tokenization based on whitespace. Adjust as needed for more accurate token counting.
        return len(message.split())

    def add_message(self, role, message):
        tokens = self._tokenize(message)
        self.buffer.append((role, message, tokens))
        self.token_count += tokens
        self.trim_buffer()

    def trim_buffer(self):
        while self.token_count > self.max_tokens:
            role, message, tokens = self.buffer.pop(0)
            self.token_count -= tokens

    def get_conversation(self):
        return "\n".join(f"{role}: {message}" for role, message, tokens in self.buffer)
