# RefCycler

RefCycler is a Python application for cycling through images in a selected folder and its subfolders, displaying them in a mood board format. The application supports zooming, panning, and dynamic resizing of the window.

## Features

- Cycle through images in a selected folder and its subfolders.
- Display multiple images in a mood board format using bin packing.
- Zoom in and out with the mouse wheel, centered around the image.
- Click and drag within the canvas to pan the image.
- Reset zoom and image position with the space bar.
- Dynamically resize the canvas to fit the window size.
- Always on top window functionality.

## Requirements

- Python 3.6+
- CustomTkinter
- Pillow

## Installation

1. Clone the repository:
    ```
    git clone git@github.com:AlinBolcas/RefCycler.git
    cd RefCycler
    ```

2. Create a virtual environment and activate it:
    ```
    python -m venv myenv
    myenv\Scripts\activate  # On Windows
    source myenv/bin/activate  # On macOS/Linux
    ```

3. Install the required packages:
    ```
    pip install -r requirements.txt
    ```

4. Run the application:
    ```
    python RefCycler.py
    ```

## Usage

1. Click "Select Folder" to choose the main folder containing your images.
2. Choose a subfolder from the dropdown menu.
3. Set the cycle interval (in seconds) and the number of images per board.
4. Click "Save" to apply the settings.
5. Use the left and right arrow keys to manually cycle through the images.
6. Use the mouse wheel to zoom in and out, and click and drag to pan the image within the canvas.
7. Press the space bar to reset the zoom and image position.

## Building Executable

To build the executable for Windows, use the following command:
```
pyinstaller --onefile --windowed --icon=app_icon.ico RefCycler.py
```

This will create a standalone executable in the `dist` folder.

## License

This project is licensed under the MIT License.
"""

