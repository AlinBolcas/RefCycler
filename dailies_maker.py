import customtkinter as ctk
import os
import re
import cv2
from tkinter import filedialog
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import logging
import subprocess


# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to extract version, subject, and task from the filename
def extract_details_from_filename(filename):
    match = re.match(r"^(.*?)_(.*?)_v(\d+)_.*\.\w+$", filename)
    if match:
        subject, task, version = match.groups()
        version = f"v{int(version):03d}"  # Ensure version is always three digits
        return subject, task, version
    return None, None, None

# Function to add text to an image with a custom font
def add_text_to_image(image, text, position, font_size=40, color="white"):
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("sora.ttf", font_size)
    except IOError:
        logging.error("Custom font not found. Using default font.")
        font = ImageFont.load_default()
    draw.text(position, text, font=font, fill=color)
    return image

# Function to process frames and add cover image
def process_frames(input_folder, comment):
    # Get list of frames excluding any existing video files
    frames = sorted([os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.endswith(('.png', '.jpg')) and not re.search(r'\.mov$', f)])
    
    if not frames:
        raise ValueError("No valid frames found in the specified folder.")

    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Get project name from user input
    project = project_entry.get()
    
    # Check for before/after pattern
    before_after_pattern = any(re.search(r'_(before|after)_', os.path.basename(f)) for f in frames)
    new_frames = []

    if before_after_pattern:
        before_frames = [f for f in frames if '_before_' in os.path.basename(f)]
        after_frames = [f for f in frames if '_after_' in os.path.basename(f)]
        frames = [val for pair in zip(before_frames, after_frames) for val in pair]

    # Extract details from the first frame to maintain consistency
    first_frame_name = os.path.basename(frames[0])
    subject, task, version = extract_details_from_filename(first_frame_name)
    if not all([subject, task, version]):
        raise ValueError("Frame filenames do not match the expected pattern.")
    
    # Create cover image
    cover_font_size = 75
    cover_image = Image.open("dailies_cover_logo_04.png")
    x_start = 500  # Starting x position (middle of the frame)
    y_start = 900  # Starting y position
    y_offset = 180  # Space between each line

    cover_image = add_text_to_image(cover_image, f"{project}", (x_start, y_start - 2 * y_offset - 30), font_size=150, color="white")  # Project
    cover_image = add_text_to_image(cover_image, f"Asset: {subject}", (x_start, y_start), font_size=cover_font_size, color="white")  # Asset
    cover_image = add_text_to_image(cover_image, f"Task: {task}", (x_start, y_start + y_offset), font_size=cover_font_size, color="white")  # Task
    cover_image = add_text_to_image(cover_image, f"Date: {date_str}", (x_start, y_start + 2 * y_offset), font_size=cover_font_size, color="white")  # Date
    cover_image = add_text_to_image(cover_image, f"Frame: 1-{len(frames)}", (x_start, y_start + 3 * y_offset), font_size=cover_font_size, color="white")  # Frame range
    cover_image = add_text_to_image(cover_image, f"Note: {comment}", (x_start, y_start + 4 * y_offset), font_size=cover_font_size, color="white")  # Comment

    # Load selected frame
    selected_frame_path = frame_path.get()
    if selected_frame_path:
        selected_frame = Image.open(selected_frame_path).convert("RGBA")
        scale_factor = 0.52
        selected_frame.thumbnail((selected_frame.width * scale_factor, selected_frame.height * scale_factor))  # Resize selected frame

        # Calculate the center of the selected frame
        selected_image_center_x = selected_frame.width // 2
        selected_image_center_y = selected_frame.height // 2

        # Define the target position where you want the center of the selected frame to be
        target_x = cover_image.width - 1100  # Adjust as needed
        target_y = cover_image.height - 1100  # Adjust as needed

        # Calculate the paste position so that the center of the selected frame is at (target_x, target_y)
        paste_position_x = target_x - selected_image_center_x
        paste_position_y = target_y - selected_image_center_y

        # Ensure mask is in the correct mode
        cover_image.paste(selected_frame, (paste_position_x, paste_position_y), selected_frame.split()[3])  # Add to cover

    cover_image.save(os.path.join(input_folder, "cover_image_with_text.png"))

    # Process each frame
    for i, f_path in enumerate(frames):
        frame_number = i + 1
        frame_image = Image.open(f_path)
        
        # Scale frame to match cover image aspect ratio
        frame_image = scale_and_centralize(frame_image, cover_image.size)
        annotated_f_path = os.path.join(input_folder, f"annotated_{frame_number:04d}.png")
        frame_image = add_text_to_image(frame_image, f"Arvolve: {project}", (50, 30), color="white")  # Top left
        frame_image = add_text_to_image(frame_image, f"{subject}_{task}_{version}", (frame_image.width / 2 - 250, 30), color="white")  # Top left
        frame_image = add_text_to_image(frame_image, f"{date_str}", (frame_image.width - 300, 30), color="white")  # Top right
        
        # Add before/after annotation if present
        frame_name = os.path.basename(f_path)
        before_after_match = re.search(r'_(before|after)_', frame_name)
        if before_after_match:
            before_after_text = before_after_match.group(1)
            frame_image = add_text_to_image(frame_image, before_after_text, (frame_image.width / 2 - 100, frame_image.height - 100), color="white")  # Bottom middle
        
        frame_image = add_text_to_image(frame_image, f"{frame_number} ({1}-{len(frames)})", (frame_image.width - 200, frame_image.height - 100), color="white")  # Bottom right
        frame_image.save(annotated_f_path)
        new_frames.append(annotated_f_path)

    return new_frames, subject, task, version

def scale_and_centralize(image, target_size):
    target_width, target_height = target_size
    width, height = image.size
    
    # Calculate scaling factor to maintain aspect ratio
    scaling_factor = min(target_width / width, target_height / height)
    
    # Scale the image
    new_size = (int(width * scaling_factor), int(height * scaling_factor))
    scaled_image = image.resize(new_size, Image.NEAREST)
    
    # Create new image with target size and paste the scaled image into the center
    new_image = Image.new("RGB", target_size)
    offset = ((target_width - new_size[0]) // 2, (target_height - new_size[1]) // 2)
    new_image.paste(scaled_image, offset)
    
    return new_image

# Function to create video from frames using FFmpeg for lossless quality
def create_video_from_frames(frames, output_path):
    input_folder = os.path.dirname(frames[0])
    cover_image_path = os.path.join(input_folder, "cover_image_with_text.png")

    # Prepare the input argument for FFmpeg as a list
    ffmpeg_input_args = ['ffmpeg', '-f', 'image2pipe', '-i', '-', '-c:v', 'libx264', '-crf', '0', '-preset', 'veryslow', output_path]

    # Use subprocess to pipe the images to FFmpeg
    process = subprocess.Popen(ffmpeg_input_args, stdin=subprocess.PIPE)
    
    # Write the cover image first
    with open(cover_image_path, 'rb') as img_file:
        process.stdin.write(img_file.read())
    
    # Write each frame image
    for frame in frames:
        with open(frame, 'rb') as img_file:
            process.stdin.write(img_file.read())
    
    process.stdin.close()
    process.wait()
    
    # Delete the cover image after video generation
    os.remove(cover_image_path)
    
    # Delete the annotated frames after video generation
    for frame in frames:
        os.remove(frame)

# Tkinter GUI for input
def select_folder():
    folder_selected = filedialog.askdirectory()
    folder_path.set(folder_selected)

def select_frame():
    frame_selected = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg")])
    frame_path.set(frame_selected)

def generate_video():
    input_folder = folder_path.get()
    comment = comment_entry.get()
    project = project_entry.get()  # Get the project name from the entry field
    selected_frame_path = frame_path.get()  # Get the selected frame path from the entry field

    if input_folder and comment and selected_frame_path:
        try:
            frames, subject, task, version = process_frames(input_folder, comment)
            output_filename = f"{subject}_{task}_{version}.mov"
            output_path = os.path.join(input_folder, output_filename)
            if os.path.exists(output_path):
                os.remove(output_path)  # Remove existing video if it exists
            create_video_from_frames(frames, output_path)
            result_label.configure(text="Video generated successfully!")
        except Exception as e:
            logging.error(f"Error generating video: {e}")
            result_label.configure(text="Error generating video. Check log for details.")

# Initialize customtkinter
ctk.set_appearance_mode("dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"

root = ctk.CTk()
root.title("Dailies Video Generator")

folder_path = ctk.StringVar()
frame_path = ctk.StringVar()

ctk.CTkLabel(root, text="Select Frames Folder").pack()
ctk.CTkButton(root, text="Browse", command=select_folder).pack()
ctk.CTkEntry(root, textvariable=folder_path).pack()

ctk.CTkLabel(root, text="Select Frame for Cover").pack()
ctk.CTkButton(root, text="Browse", command=select_frame).pack()
ctk.CTkEntry(root, textvariable=frame_path).pack()

ctk.CTkLabel(root, text="Enter Show Name:").pack()
project_entry = ctk.CTkEntry(root, width=300)
project_entry.pack()

ctk.CTkLabel(root, text="Enter Comment:").pack()
comment_entry = ctk.CTkEntry(root, width=300)
comment_entry.pack()

ctk.CTkButton(root, text="Generate Daily", command=generate_video).pack()
result_label = ctk.CTkLabel(root, text="")
result_label.pack()

root.mainloop()