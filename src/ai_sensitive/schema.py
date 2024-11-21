from typing import List


class Word:
    def __init__(self, text: str, x: float, y: float, width: float, height: float):
        self.text: str = text
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def __repr__(self):
        return f"Word(text='{self.text}', x={self.x}, y={self.y}, width={self.width}, height={self.height})"


class Line:
    def __init__(self):
        self.words: List[Word] = []  # List to store words in this line

    def add_word(self, word: Word):
        self.words.append(word)

    def get_text(self):
        # Concatenate words to form the line's text
        return " ".join(word.text for word in self.words)

    def __repr__(self):
        return f"Line(words={self.words})"


class Paragraph:
    def __init__(self):
        self.lines: List[Line] = []  # List to store lines in this paragraph

    def add_line(self, line: Line):
        self.lines.append(line)

    def get_text(self):
        # Concatenate line texts to form the paragraph's text
        return " ".join(line.get_text() for line in self.lines)

    def __repr__(self):
        return f"Paragraph(lines={self.lines})"
