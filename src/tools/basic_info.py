from ai_sensitive.ocr_document import OCRDocument
from ai_sensitive.sensitive_ai_detector import SensitiveAIDetector
from tools.image_tools import ImageTools
from typing import List, Tuple


class BasicInfo:
    def __init__(self, img_path):
        self.img_path: str = img_path

        self.image_tools = ImageTools(self.img_path)
        self.ocr: OCRDocument = None
        self.sensitive_ai_detector: SensitiveAIDetector = None

        self.sensitive_info: List[str] = []
        self.sensitive_coordinates: List[Tuple[int, int, int, int]] = (
            []
        )  # (x, y, width, height)

    def ai_detector(self):
        self.ocr = OCRDocument(self.img_path)
        self.sensitive_ai_detector = SensitiveAIDetector(self.ocr)
        self.sensitive_info = self.sensitive_ai_detector.get_sensitive_info()
        self.sensitive_coordinates.extend(
            self.sensitive_ai_detector.process(self.sensitive_info)
        )
        self.update_block()

    def update_block(self):
        self.image_tools.draw_block(self.sensitive_coordinates)
        
    def plot_ocr(self):
        if self.ocr is None:
            raise Exception("Please run ai_detector first, or set ocr manually.")
        self.ocr.plot_three_graphs()
        
    def plot_blocks(self):
        self.image_tools.show_processed_image()

    def add_sensitive_coordinates(
        self, coordinates: List[int]
    ):  # (x, y, width, height)
        self.sensitive_coordinates.append(coordinates)

    def remove_sensitive_coordinates(self, point: List[int]):  # (x, y)
        for coordinate in self.sensitive_coordinates:
            if point[0] in range(
                coordinate[0], coordinate[0] + coordinate[2]
            ) and point[1] in range(coordinate[1], coordinate[1] + coordinate[3]):
                self.sensitive_coordinates.remove(coordinate)

