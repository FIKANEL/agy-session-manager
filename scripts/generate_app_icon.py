"""
scripts/generate_app_icon.py
Generates official multi-resolution icon.ico and icon.png for Agy Session Manager.
Brand DNA: Linear x Raycast (Deep canvas #090a0f, Indigo glow #5e6ad2 -> #818cf8, Terminal Bolt glyph).
"""
import os
import sys
from PIL import Image

# Use PySide6 to draw vector graphics cleanly with high-DPI anti-aliasing
from PySide6.QtGui import (
    QImage, QPainter, QColor, QPen, QBrush, QLinearGradient, QPainterPath
)
from PySide6.QtCore import Qt, QRectF, QPointF


def render_icon_base(size=512) -> Image.Image:
    qimg = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    qimg.fill(Qt.GlobalColor.transparent)

    painter = QPainter(qimg)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    scale = size / 512.0
    margin = 32 * scale
    rect = QRectF(margin, margin, size - 2 * margin, size - 2 * margin)
    corner_radius = 96 * scale

    # Outer squircle / background
    bg_path = QPainterPath()
    bg_path.addRoundedRect(rect, corner_radius, corner_radius)

    # Dark background gradient
    bg_grad = QLinearGradient(0, 0, size, size)
    bg_grad.setColorAt(0.0, QColor("#14151f"))
    bg_grad.setColorAt(0.6, QColor("#0d0e14"))
    bg_grad.setColorAt(1.0, QColor("#08090d"))
    painter.fillPath(bg_path, bg_grad)

    # 1px hairline border with top-left highlight
    border_grad = QLinearGradient(0, 0, 0, size)
    border_grad.setColorAt(0.0, QColor(129, 140, 248, 120))  # subtle lavender highlight
    border_grad.setColorAt(0.5, QColor(42, 45, 58, 180))
    border_grad.setColorAt(1.0, QColor(25, 27, 35, 120))

    pen = QPen(border_grad, 3.0 * scale)
    painter.strokePath(bg_path, pen)

    # Inner terminal / lightning glyph
    # Bolt / Command Chevron shape in center
    bolt_path = QPainterPath()
    # Coords relative to 512 canvas
    pts = [
        QPointF(275 * scale, 110 * scale),
        QPointF(185 * scale, 265 * scale),
        QPointF(255 * scale, 265 * scale),
        QPointF(230 * scale, 402 * scale),
        QPointF(335 * scale, 240 * scale),
        QPointF(265 * scale, 240 * scale),
    ]
    bolt_path.moveTo(pts[0])
    for pt in pts[1:]:
        bolt_path.lineTo(pt)
    bolt_path.closeSubpath()

    # Glyph gradient: Electric Indigo to Lavender
    glyph_grad = QLinearGradient(180 * scale, 110 * scale, 340 * scale, 400 * scale)
    glyph_grad.setColorAt(0.0, QColor("#818cf8"))   # Lavender blue
    glyph_grad.setColorAt(0.5, QColor("#5e6ad2"))   # Signature Linear indigo
    glyph_grad.setColorAt(1.0, QColor("#4338ca"))   # Deep electric violet

    painter.fillPath(bolt_path, glyph_grad)

    # Subtle inner bolt shine
    shine_pen = QPen(QColor(255, 255, 255, 160), 2.0 * scale)
    painter.strokePath(bolt_path, shine_pen)

    # Terminal prompt chevron on lower left (<_ or >_)
    chev_path = QPainterPath()
    chev_path.moveTo(140 * scale, 335 * scale)
    chev_path.lineTo(165 * scale, 355 * scale)
    chev_path.lineTo(140 * scale, 375 * scale)

    chev_pen = QPen(QColor("#a6abb8"), 4.0 * scale, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    painter.strokePath(chev_path, chev_pen)

    painter.end()

    # Convert QImage to PIL Image
    qimg = qimg.convertToFormat(QImage.Format.Format_RGBA8888)
    width = qimg.width()
    height = qimg.height()
    bytes_per_line = qimg.bytesPerLine()
    ptr = qimg.bits()
    raw_bytes = bytes(ptr)

    pil_img = Image.frombytes("RGBA", (width, height), raw_bytes, "raw", "RGBA", bytes_per_line, 1)
    return pil_img


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets_dir = os.path.join(repo_root, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    print("Rendering vector icon base (512x512)...")
    base_img = render_icon_base(512)

    # Save high-res PNG
    png_path = os.path.join(assets_dir, "icon.png")
    base_img.save(png_path, format="PNG")
    print(f"Saved: {png_path}")

    # Generate multi-resolution Windows ICO
    ico_path = os.path.join(assets_dir, "icon.ico")
    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (24, 24), (16, 16)]
    base_img.save(ico_path, format="ICO", sizes=icon_sizes)
    print(f"Saved multi-res ICO ({len(icon_sizes)} sizes): {ico_path}")


if __name__ == "__main__":
    main()
