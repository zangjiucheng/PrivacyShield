from PIL import Image

class ImageTools:
    def __init__(self, image_path):
        self.image = Image.open(image_path)
        self.process_image = self.image.copy()

    # def draw_rectangle(self, coordinates, outline="red", width=2):
    #     for coord in coordinates:
    #         self.process_image.rectangle(coord, outline=outline, width=width)

    def fill_rectangle(self, coordinates, fill="black"):
        for coord in coordinates:
            x, y, w, h = coord
            fill_color = Image.new("RGB", (w, h), fill)
            self.process_image.paste(fill_color, (x, y, x + w, y + h))

    def draw_block(self, coordinates):
        self.process_image = self.image.copy()
        self.fill_rectangle(coordinates)

    def get_processed_image(self):
        return self.process_image

    def show_processed_image(self):
        self.process_image.show()

    def save_processed_image(self, path):
        self.process_image.save(path.split(".")[0] + "_processed." + path.split(".")[1])

    def save_image(self, path):
        self.image.save(path)

    def show_image(self):
        self.image.show()
