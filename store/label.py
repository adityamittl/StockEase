import labels
import os.path
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFont, stringWidth
from reportlab.graphics import shapes
from reportlab.lib import colors
import random

random.seed(187459)
import io

specs = labels.Specification(210, 297, 2, 8, 90, 25, corner_radius=2)

base_path = os.path.dirname(__file__)

registerFont(TTFont("Judson Bold", os.path.join(base_path, "Judson-Bold.ttf")))


def write_name(label, width, height, name):
    font_size = 17
    text_width = width - 10
    name_width = stringWidth(name, "Judson Bold", font_size)
    while name_width > text_width:
        font_size *= 0.8
        name_width = stringWidth(name, "Judson Bold", font_size)

    s = shapes.String(width / 2.0, 15, name, textAnchor="middle")
    s.fontName = "Judson Bold"
    s.fontSize = font_size
    s.fillColor = colors.black
    label.add(s)


def create_label(names):
    sheet = labels.Sheet(specs, write_name, border=True)
    sheet.add_labels(names)

    buffer = io.BytesIO()
    sheet.save(buffer)
    buffer.seek(0)
    return buffer
