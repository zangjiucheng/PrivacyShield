import sys
import os

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QFileDialog,
    QVBoxLayout,
    QPushButton,
    QWidget,
    QHBoxLayout,
)
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt, QThread, Signal, QObject, Slot
import cv2

from tools.basic_info import BasicInfo

class Worker(QObject):
    finished = Signal()  # Signal to indicate the worker has finished
    error = Signal(str)  # Signal for error handling (optional)

    def __init__(self, function):
        super().__init__()
        self.function = function

    def run(self):
        try:
            self.function()
        except Exception as e:
            self.error.emit(str(e))  # Emit error signal if an exception occurs
        self.finished.emit()  # Emit finished signal when done

class ImageBlocker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Blocker")
        self.setGeometry(100, 100, 800, 600)

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 300)
        self.image_path = None
        self.basic_info = None
        self.image = None
        self.rectangles = []
        self.start_point = None

        load_button = QPushButton("Load Image")
        load_button.clicked.connect(self.load_image)

        save_button = QPushButton("Save Image")
        save_button.clicked.connect(self.save_image)

        clear_button = QPushButton("Clear Blocks")
        clear_button.clicked.connect(self.clear_blocks)

        self.ai_detector_button = QPushButton("AI Detector")
        self.ai_detector_button.clicked.connect(lambda: self._start_worker(self.ai_detector))
        button_layout = QHBoxLayout()
        button_layout.addWidget(load_button)
        button_layout.addWidget(save_button)
        button_layout.addWidget(clear_button)
        button_layout.addWidget(self.ai_detector_button)

        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def _convert_cv2_to_qpixmap(self, cv2_image):
        """
        Convert an OpenCV image to QPixmap.
        :param cv2_image: The OpenCV image to convert.
        :return: QPixmap representation of the image.
        """
        # Convert BGR to RGB (OpenCV uses BGR by default)
        cv2_image_rgb = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)

        # Get image dimensions
        height, width, channel = cv2_image_rgb.shape

        # Create a QImage from the RGB array
        bytes_per_line = channel * width
        q_image = QImage(
            cv2_image_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888
        )

        # Convert QImage to QPixmap
        q_pixmap = QPixmap.fromImage(q_image)

        return q_pixmap

    def _convert_pillow_to_qpixmap(self, pillow_image):
        """
        Convert a Pillow image to QPixmap.
        :param pillow_image: The Pillow image to convert.
        :return: QPixmap representation of the image.
        """
        # Convert Pillow image to RGB if not already
        if pillow_image.mode != "RGB":
            pillow_image = pillow_image.convert("RGB")

        # Get image size and data
        width, height = pillow_image.size
        data = pillow_image.tobytes("raw", "RGB")

        # Create a QImage from the Pillow image data
        q_image = QImage(data, width, height, QImage.Format_RGB888)

        # Convert QImage to QPixmap
        q_pixmap = QPixmap.fromImage(q_image)

        return q_pixmap
    
    def _start_worker(self, function):
        self.thread = QThread()  # Create a new thread
        self.worker = Worker(function)  # Create the worker and pass the function
        self.worker.moveToThread(self.thread)  # Move the worker to the thread

        print("Starting worker")
        # Connect signals and slots
        self.thread.started.connect(self.worker.run)  # Start the worker
        self.worker.finished.connect(self.thread.quit)  # Stop the thread when done
        self.worker.finished.connect(self.worker.deleteLater)  # Clean up the worker
        self.thread.finished.connect(self.thread.deleteLater)  # Clean up the thread
        self.worker.error.connect(self._handle_error)  # Handle any errors (optional)

        # Start the thread
        self.thread.start()
    
    def _handle_error(self, error_message):
        print(f"Error: {error_message}")  # Handle any errors here

    @Slot()
    def ai_detector(self):
        try:
            self.ai_detector_button.setEnabled(False)
            if self.image_path:
                self.basic_info = BasicInfo(self.image_path)
                self.basic_info.ai_detector()
                self.update_image()
                self.display_scaled_image()
        finally:
            self.ai_detector_button.setEnabled(True)

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.image_path = file_path
            self.basic_info = BasicInfo(self.image_path)
            # self.image = self._convert_pillow_to_qpixmap(self.basic_info.image_tools.image)
            self.image = QPixmap(self.image_path)
            self.display_scaled_image()

    def save_image(self):
        if self.image:
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Image",
                "",
                "PNG Files (*.png);;JPG Files (*.jpg);;BMP Files (*.bmp)",
            )
            if save_path:
                self.basic_info.image_tools.save_processed_image(save_path)

    def clear_blocks(self):
        self.basic_info.sensitive_coordinates = []
        self.basic_info.update_block()
        self.image = QPixmap(self.image_path)
        self.display_scaled_image()

    # def mousePressEvent(self, event):
    #     if event.button() == Qt.LeftButton and self.image:
    #         self.start_point = event.pos()

    # def mouseReleaseEvent(self, event):
    #     if event.button() == Qt.LeftButton and self.image and self.start_point:
    #         end_point = event.pos()
    #         rect = QRect(self.start_point - self.image_label.pos(), end_point - self.image_label.pos())
    #         self.rectangles.append(rect)
    #         self.update_image()
    #         self.start_point = None

    def update_image(self):
        if self.basic_info:
            self.basic_info.update_block()
            self.image = self._convert_pillow_to_qpixmap(
                self.basic_info.image_tools.process_image
            )

    def display_scaled_image(self):
        if self.image:
            scaled_image = self.image.scaled(
                self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_image)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.display_scaled_image()


def load_stylesheet():
    stylesheet_path = os.path.join(os.path.dirname(__file__), "ui", "styles.qss")
    with open(stylesheet_path, "r") as f:
        return f.read()


def run():
    app = QApplication(sys.argv)
    stylesheet = load_stylesheet()
    app.setStyleSheet(stylesheet)  # Apply the QSS
    window = ImageBlocker()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
