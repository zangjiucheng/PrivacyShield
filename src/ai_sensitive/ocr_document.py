from typing import Optional, List

import cv2
import numpy as np
import pytesseract
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans

from .schema import Word, Line, Paragraph

from setting import ocr_config, debug_flag


class OCRDocument:
    def __init__(
        self,
        image_path: str,
        line_threshold: int = None,
        paragraph_threshold: int = None,
        languages: Optional[str] = "eng",
    ):
        self.image_path = image_path  # Path to the image
        self.image = cv2.imread(image_path)  # Load the image using OpenCV
        self.gray_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        self.sensitive_block_image = self.image.copy()
        self.paragraphs = []  # List to store paragraphs
        self.languages = languages  # Default language for OCR

        # Perform OCR and automatically determine line and paragraph thresholds
        if line_threshold == None or paragraph_threshold == None:
            self.line_threshold, self.paragraph_threshold = (
                self._auto_adjust_thresholds()
            )

        print(
            f"Line Threshold: {self.line_threshold}, Paragraph Threshold: {self.paragraph_threshold}"
        )
        self._perform_ocr(self.line_threshold, self.paragraph_threshold)
        if debug_flag:
            self.plot_three_graphs()

    def _auto_adjust_thresholds(self):
        """Automatically determine optimal line and paragraph thresholds based on OCR data."""
        data = pytesseract.image_to_data(
            self.image,
            lang=self.languages,
            output_type=pytesseract.Output.DICT,
            config=ocr_config,
        )

        # Calculate vertical distances between adjacent words
        word_y_coords = [
            data["top"][i] for i in range(len(data["text"])) if data["text"][i].strip()
        ]
        word_distances = [
            abs(word_y_coords[i] - word_y_coords[i - 1])
            for i in range(1, len(word_y_coords))
            if abs(word_y_coords[i] - word_y_coords[i - 1]) != 0
        ]

        # print(f"Word Distances: {word_y_coords}")

        # Calculate vertical distances between lines for paragraph threshold
        line_distances = self._calculate_line_distances(data)

        # print(f"Line Distances: {line_distances}")

        # Use KMeans clustering to separate line breaks from regular word spacing
        if len(word_distances) > 1:
            word_distances_reshaped = np.array(word_distances).reshape(-1, 1)
            kmeans_words = KMeans(n_clusters=5, random_state=0).fit(
                word_distances_reshaped
            )
            line_cluster_centers = sorted(kmeans_words.cluster_centers_.flatten())
            # print(f"Cluster Line Centers: {line_cluster_centers}")
            line_threshold = line_cluster_centers[
                1
            ]  # Smaller cluster center for line threshold
        else:
            line_threshold = 10  # Default if clustering isn't feasible

        # Use clustering to separate paragraph breaks from regular line spacing
        if len(line_distances) > 1:
            # Reshape distances for clustering and apply k-means with 2 clusters
            line_distances_reshaped = np.array(line_distances).reshape(-1, 1)
            kmeans = KMeans(n_clusters=3, random_state=0).fit(line_distances_reshaped)
            cluster_centers = sorted(kmeans.cluster_centers_.flatten())
            print(f"Cluster Paragraph Centers: {cluster_centers}")
            # Choose the larger cluster center as the paragraph threshold
            paragraph_threshold = (
                cluster_centers[1] if len(cluster_centers) > 1 else cluster_centers[0]
            )
        else:
            paragraph_threshold = 20

        return int(line_threshold), int(paragraph_threshold)

    def _calculate_line_distances(self, data):
        """Calculate vertical distances between adjacent lines in OCR data."""
        # Collect lines based on y-coordinates of words
        line_y_coords = []
        current_line_y = None

        for i in range(len(data["text"])):
            text = data["text"][i].strip()
            if text:
                y = data["top"][i]
                if current_line_y is None or abs(y - current_line_y) > 5:
                    # New line detected based on y-coordinate jump
                    line_y_coords.append(y)
                    current_line_y = y

        # Calculate distances between each pair of adjacent line y-coordinates
        line_distances = [
            abs(line_y_coords[i] - line_y_coords[i - 1])
            for i in range(1, len(line_y_coords))
        ]
        return line_distances

    def _perform_ocr(self, line_threshold: int, paragraph_threshold: int):
        # Perform OCR on the image
        data = pytesseract.image_to_data(
            self.gray_image, lang=self.languages, output_type=pytesseract.Output.DICT
        )

        # Group words into lines and lines into paragraphs
        lines = self._group_words_into_lines(data, line_threshold)
        self.paragraphs = self._group_lines_into_paragraphs(lines, paragraph_threshold)

    def _group_words_into_lines(self, data, line_threshold: int) -> List[Line]:
        """Groups words detected by OCR into lines based on their vertical position."""
        lines = []
        current_line = Line()
        previous_y = None

        for i in range(len(data["text"])):
            text = data["text"][i].strip()
            if text:  # Ensure the text is not empty
                x, y, w, h = (
                    data["left"][i],
                    data["top"][i],
                    data["width"][i],
                    data["height"][i],
                )
                word = Word(text, x, y, w, h)

                # Check if this word should start a new line based on the y-coordinate
                if previous_y is not None and abs(y - previous_y) > line_threshold:
                    # Start a new line if y-coordinate difference is too large
                    lines.append(current_line)
                    current_line = Line()

                # Add the word to the current line
                current_line.add_word(word)
                previous_y = y

        # Add the last line if not empty
        if current_line.words:
            lines.append(current_line)

        return lines

    def _group_lines_into_paragraphs(
        self, lines: List[Line], paragraph_threshold: int
    ) -> List[Paragraph]:
        """Groups lines into paragraphs based on their vertical distance."""
        paragraphs = []
        current_paragraph = Paragraph()
        previous_y = None

        for line in lines:
            # Calculate the average y position of words in the line
            avg_y = sum(word.y for word in line.words) / len(line.words)

            # Check if the line should start a new paragraph
            if previous_y is not None and abs(avg_y - previous_y) > paragraph_threshold:
                # Start a new paragraph if vertical distance is too large
                paragraphs.append(current_paragraph)
                current_paragraph = Paragraph()

            # Add line to the current paragraph
            current_paragraph.add_line(line)
            previous_y = avg_y

        # Add the last paragraph if not empty
        if current_paragraph.lines:
            paragraphs.append(current_paragraph)

        return paragraphs

    def _plot_words(self, word_plot=True):
        """Plots the OCR results showing bounding boxes around each word."""
        image_rgb = self.image.copy()

        # Loop over paragraphs, lines, and words to plot bounding boxes
        for paragraph in self.paragraphs:
            for line in paragraph.lines:
                for word in line.words:
                    x, y, w, h = word.x, word.y, word.width, word.height
                    # Draw rectangle around each word
                    cv2.rectangle(image_rgb, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    if word_plot:
                        # Add the detected text to the image
                        plt.text(
                            x,
                            y - 5,
                            word.text,
                            fontsize=12,
                            color="blue",
                            weight="bold",
                        )
        return image_rgb

    def _plot_lines(self):
        """Plots the OCR results showing bounding boxes around each line."""
        image_rgb = self.image.copy()

        for paragraph in self.paragraphs:
            for line in paragraph.lines:
                x_min = min(word.x for word in line.words)
                y_min = min(word.y for word in line.words)
                x_max = max(word.x + word.width for word in line.words)
                y_max = max(word.y + word.height for word in line.words)

                cv2.rectangle(
                    image_rgb, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2
                )  # Blue box for lines

        return image_rgb

    def _plot_paragraphs(self):
        """Plots the OCR results showing bounding boxes around each paragraph."""
        image_rgb = self.image.copy()

        for paragraph in self.paragraphs:
            x_min = min(word.x for line in paragraph.lines for word in line.words)
            y_min = min(word.y for line in paragraph.lines for word in line.words)
            x_max = max(
                word.x + word.width for line in paragraph.lines for word in line.words
            )
            y_max = max(
                word.y + word.height for line in paragraph.lines for word in line.words
            )

            cv2.rectangle(
                image_rgb, (x_min, y_min), (x_max, y_max), (0, 0, 255), 2
            )  # Red box for paragraphs

        return image_rgb

    def plot_three_graphs(self):
        fig, axs = plt.subplots(1, 3, figsize=(36, 12))

        # Plot words
        image_rgb_words = self._plot_words(False)

        axs[0].imshow(image_rgb_words)
        axs[0].axis("off")
        axs[0].set_title("Words Grouping")

        # Plot lines
        image_rgb_lines = self._plot_lines()

        axs[1].imshow(image_rgb_lines)
        axs[1].axis("off")
        axs[1].set_title("Line Grouping")

        # Plot paragraphs
        image_rgb_paragraphs = self._plot_paragraphs()

        axs[2].imshow(image_rgb_paragraphs)
        axs[2].axis("off")
        axs[2].set_title("Paragraph Grouping")

        plt.show()

    def get_text(self):
        # Concatenate all paragraphs' texts to form the document's text
        return "\n\n".join(paragraph.get_text() for paragraph in self.paragraphs)

    def __repr__(self):
        return (
            f"OCRDocument(image_path='{self.image_path}', paragraphs={self.paragraphs})"
        )
