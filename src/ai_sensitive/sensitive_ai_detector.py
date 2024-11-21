from typing import List, Tuple

from .sensitive_info_utils import detect_sensitive_information, load_model
from .ocr_document import OCRDocument
from .schema import Paragraph

from setting import debug_flag


class SensitiveAIDetector:
    def __init__(self, ocr: OCRDocument):
        self.ocr: OCRDocument = ocr

    def get_sensitive_info(self) -> None:
        print("Detecting sensitive information...")
        paragraphs = self.ocr.paragraphs

        sensitive_info = []

        ai_model = load_model()
        for paragraph in paragraphs:
            sensitive_info.extend(
                detect_sensitive_information(ai_model, paragraph.get_text())
            )

        return sensitive_info

    def back_locate_sensitive_info(
        self, paragraphs: List[Paragraph], sensitive_info: List[str]
    ) -> List[Tuple[int, int, int, int]]:
        coordinates = []
        for paragraph in paragraphs:
            for info in sensitive_info:
                if info in paragraph.get_text():
                    for line in paragraph.lines:
                        for word in line.words:
                            for info_word in info.split():
                                if info_word in word.text:
                                    coordinate = (
                                        word.x,
                                        word.y,
                                        word.width,
                                        word.height,
                                    )
                                    coordinates.append(coordinate)
                                    if debug_flag:
                                        print(f"Sensitive Info: {info}")
                                        print(f"Coordinates: {coordinate}")
                                        print("\n")

        return coordinates

    def process(self, sensitive_info: List[str]) -> None:
        return self.back_locate_sensitive_info(self.ocr.paragraphs, sensitive_info)
