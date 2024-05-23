import sys
import os
import base64
import threading
from io import BytesIO
from PIL import ImageGrab, Image
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit, QFileDialog, QMessageBox, QRubberBand
from PyQt5.QtCore import QRect, QPoint, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPixmap
from openai import OpenAI
from dotenv import load_dotenv


# Load the .env file
load_dotenv()

# Read the API key from the environment variable
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

system_message = """
ROLE: You are a world-class art director, visual critic, and designer.
"""
user_message = """
TASK: Your job is to provide constructive and actionable feedback on artwork. Focus on relevant aspects of the artwork and provide clear, concise critique. Use examples to illustrate your suggestions.
INSTRUCTIONS: Use bullet points and follow this structure:

Initial Remark: What it sees and a positive overall remark.
Full Feedback: A list of 3-5 bullet points of the most important elements to fix about the image to improve it.
Final Closing Thoughts: Visual interpretation of where it thinks the artwork should go.
EXAMPLES:
...
---
Provide feedback on the image below.
"""

class ScreenshotWidget(QWidget):
    screenshot_taken = pyqtSignal(QPixmap)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setWindowState(Qt.WindowFullScreen)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)

    def mousePressEvent(self, event):
        self.start_point = event.pos()
        self.rubber_band.setGeometry(QRect(self.start_point, QSize()))
        self.rubber_band.show()

    def mouseMoveEvent(self, event):
        self.rubber_band.setGeometry(QRect(self.start_point, event.pos()).normalized())

    def mouseReleaseEvent(self, event):
        self.end_point = event.pos()
        screenshot = ImageGrab.grab(bbox=(self.start_point.x(), self.start_point.y(), self.end_point.x(), self.end_point.y()))
        screenshot_qt = QPixmap.fromImage(ImageQt(screenshot))
        self.screenshot_taken.emit(screenshot_qt)
        self.close()


class ImageCritiqueApp(QWidget):

    critique_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Image Critique App')
        self.setGeometry(100, 100, 800, 600)

        self.layout = QVBoxLayout()

        self.screenshot_button = QPushButton('Take Screenshot', self)
        self.screenshot_button.clicked.connect(self.initiate_screenshot)
        self.layout.addWidget(self.screenshot_button)

        self.critique_label = QLabel('Artistic Critique:', self)
        self.layout.addWidget(self.critique_label)

        self.critique_text = QTextEdit(self)
        self.critique_text.setReadOnly(True)
        self.layout.addWidget(self.critique_text)

        self.setLayout(self.layout)

        self.critique_signal.connect(self.display_critique)

    @pyqtSlot()
    def initiate_screenshot(self):
        self.screenshot_widget = ScreenshotWidget()
        self.screenshot_widget.screenshot_taken.connect(self.process_screenshot)
        self.screenshot_widget.show()

    @pyqtSlot(QPixmap)
    def process_screenshot(self, screenshot):
        screenshot_path = "screenshot.png"
        screenshot.save(screenshot_path)
        threading.Thread(target=self.get_artistic_critique, args=(screenshot_path,)).start()

    def get_artistic_critique(self, screenshot_path):
        try:
            with open(screenshot_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message + f"\n![Screenshot](data:image/png;base64,{base64_image})"}
            ]

            response = client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                max_tokens=500
            )

            if response and response.choices and len(response.choices) > 0:
                critique = response.choices[0].message.content
                self.critique_signal.emit(critique)
            else:
                self.critique_signal.emit("No critique generated.")
        except Exception as e:
            self.critique_signal.emit(f"Error getting artistic critique: {e}")

    @pyqtSlot(str)
    def display_critique(self, critique):
        self.critique_text.setPlainText(critique)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ImageCritiqueApp()
    ex.show()
    sys.exit(app.exec_())
