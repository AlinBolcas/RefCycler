from tkinter import Tk, Label, Button, Entry, filedialog, StringVar
from moviepy.editor import VideoFileClip
import threading

def convert_and_speedup(input_video_path, output_video_path, speed_factor=4):
    # Load the video file
    clip = VideoFileClip(input_video_path)
    
    # Speed up the video
    clip = clip.fx(VideoFileClip.speedx, factor=speed_factor)
    
    # Write the output video file
    clip.write_videofile(output_video_path, codec='libx264')

def browse_input_file():
    """ Open a dialog to select the input video file. """
    filename = filedialog.askopenfilename(
        title="Select a video file",
        filetypes=(("Video files", "*.mp4 *.mkv *.avi *.mov"), ("All files", "*.*"))
    )
    input_path.set(filename)

def browse_output_file():
    """ Open a dialog to select the output video file path. """
    filename = filedialog.asksaveasfilename(
        title="Save the video as",
        filetypes=(("MP4 files", "*.mp4"), ("All files", "*.*")),
        defaultextension=".mp4"
    )
    output_path.set(filename)

def convert_video():
    """ Start the video conversion in a separate thread to keep the UI responsive. """ 
    def task():
        input_video_path = input_path.get()
        output_video_path = output_path.get()
        speed_factor = float(speed_factor_var.get())
        
        convert_and_speedup(input_video_path, output_video_path, speed_factor)
        
        # Optional: show a message when conversion is done (this part can be customized)
        print("Conversion completed successfully!")
    
    # Run the conversion in a separate thread to prevent the GUI from freezing
    threading.Thread(target=task).start()

# Create the main window
root = Tk()
root.title("Video Speed-Up Converter")

# Set up the input path field
Label(root, text="Input Video:").grid(row=0, column=0, padx=10, pady=10, sticky='e')
input_path = StringVar()
Entry(root, textvariable=input_path, width=50).grid(row=0, column=1, padx=10, pady=10)
Button(root, text="Browse...", command=browse_input_file).grid(row=0, column=2, padx=10, pady=10)

# Set up the output path field
Label(root, text="Output Video:").grid(row=1, column=0, padx=10, pady=10, sticky='e')
output_path = StringVar()
Entry(root, textvariable=output_path, width=50).grid(row=1, column=1, padx=10, pady=10)
Button(root, text="Browse...", command=browse_output_file).grid(row=1, column=2, padx=10, pady=10)

# Set up the speed factor field
Label(root, text="Speed Factor:").grid(row=2, column=0, padx=10, pady=10, sticky='e')
speed_factor_var = StringVar(value="4")
Entry(root, textvariable=speed_factor_var, width=10).grid(row=2, column=1, padx=10, pady=10, sticky='w')

# Set up the convert button
Button(root, text="Convert Movie", command=convert_video).grid(row=3, column=1, padx=10, pady=10)

# Start the Tkinter event loop
root.mainloop()
