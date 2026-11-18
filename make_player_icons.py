# -*- coding: utf-8 -*-
"""Build the sidebar player badges from the supplied brand screenshots.

Crops each icon out of its screenshot background, applies a rounded-corner
mask, and writes assets/kugou-logo*.png + assets/netease-logo*.png.
"""
import os
import sys

from PySide6.QtCore import QRect, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath
from PySide6.QtWidgets import QApplication

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'assets')

SOURCES = {
    'netease-logo': r'C:\Users\Administrator\.workbuddy\clipboard-images\clipboard-2026-11-18T01-32-54-093Z-8ef61aed.png',
    'kugou-logo': r'C:\Users\Administrator\.workbuddy\clipboard-images\clipboard-2026-11-18T01-32-54-097Z-efdd5c70.png',
}


def _bg_color(img):
    """Average colour of the four corners = screenshot background."""
    w, h = img.width(), img.height()
    pts = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    cols = [img.pixelColor(x, y) for x, y in pts]
    return QColor(sum(c.red() for c in cols) // 4,
                  sum(c.green() for c in cols) // 4,
                  sum(c.blue() for c in cols) // 4)


def _bbox(img, bg):
    w, h = img.width(), img.height()
    left, top, right, bottom = w, h, -1, -1
    for y in range(h):
        for x in range(w):
            c = img.pixelColor(x, y)
            dist = (abs(c.red() - bg.red()) + abs(c.green() - bg.green())
                    + abs(c.blue() - bg.blue()))
            if dist > 60:
                left, right = min(left, x), max(right, x)
                top, bottom = min(top, y), max(bottom, y)
    if right < 0:
        return QRect(0, 0, w, h)
    return QRect(left, top, right - left + 1, bottom - top + 1)


def _square_padded(img, rect):
    """Crop `rect`, then pad to a square on a transparent canvas."""
    crop = img.copy(rect)
    side = max(crop.width(), crop.height())
    canvas = QImage(side, side, QImage.Format.Format_ARGB32)
    canvas.fill(Qt.GlobalColor.transparent)
    p = QPainter(canvas)
    p.drawImage((side - crop.width()) // 2, (side - crop.height()) // 2, crop)
    p.end()
    return canvas


def _round_mask(img, radius_ratio=0.235):
    s = img.width()
    out = QImage(s, s, QImage.Format.Format_ARGB32)
    out.fill(Qt.GlobalColor.transparent)
    p = QPainter(out)
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, s, s), s * radius_ratio, s * radius_ratio)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setClipPath(path)
    p.drawImage(0, 0, img)
    p.end()
    return out


def build(name, src):
    img = QImage(src)
    if img.isNull():
        raise SystemExit('missing source: %s' % src)
    bg = _bg_color(img)
    box = _bbox(img, bg)
    print('%s: src=%dx%d bbox=%s' % (name, img.width(), img.height(),
                                     (box.x(), box.y(), box.width(), box.height())))
    square = _square_padded(img, box)
    rounded = _round_mask(square)
    # Downscale first to kill screenshot noise, then upscale for the icon sizes.
    clean = rounded.scaled(96, 96, Qt.AspectRatioMode.IgnoreAspectRatio,
                          Qt.TransformationMode.SmoothTransformation)
    for size in (128, 64, 32):
        out = clean.scaled(size, size, Qt.AspectRatioMode.IgnoreAspectRatio,
                           Qt.TransformationMode.SmoothTransformation)
        out.save(os.path.join(OUT, '%s-%d.png' % (name, size)))
    clean.scaled(64, 64, Qt.AspectRatioMode.IgnoreAspectRatio,
                 Qt.TransformationMode.SmoothTransformation).save(
        os.path.join(OUT, name + '.png'))
    print('  ->', name)


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    os.makedirs(OUT, exist_ok=True)
    for name, src in SOURCES.items():
        build(name, src)
    del app


if __name__ == '__main__':
    main()
