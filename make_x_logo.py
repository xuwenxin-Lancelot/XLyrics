# -*- coding: utf-8 -*-
"""Generate a SpaceX-style X logo (sci-fi deep-blue) using PySide6 only."""
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import (QImage, QPainter, QPen, QBrush, QColor,
                           QLinearGradient, QPainterPath, QPixmap, QPolygonF)
from PySide6.QtCore import Qt, QPointF, QRectF

app = QApplication(sys.argv)


def draw_logo(size):
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setRenderHint(QPainter.TextAntialiasing, True)
    s = float(size)
    cx = cy = s / 2

    def C(hexv, a=255):
        c = QColor(hexv); c.setAlpha(a); return c

    # 深空圆角方底
    bg = QLinearGradient(0, 0, s, s)
    bg.setColorAt(0, C('#0E1B33'))
    bg.setColorAt(1, C('#04070F'))
    p.setBrush(QBrush(bg))
    p.setPen(QPen(C('#12305C', 230), max(1, s * 0.008)))
    margin = s * 0.06
    p.drawRoundedRect(QRectF(margin, margin, s - 2*margin, s - 2*margin), s*0.13, s*0.13)

    # X 主色渐变（金属电光蓝）
    xg = QLinearGradient(0, s * 0.18, 0, s * 0.82)
    xg.setColorAt(0, C('#DCEEFF'))
    xg.setColorAt(0.42, C('#4FB4FF'))
    xg.setColorAt(0.75, C('#1468D8'))
    xg.setColorAt(1, C('#0A3A8C'))

    # 三笔构成 SpaceX 式 X：中央竖杠 + 两条弧形斜臂
    pens = []
    # 斜臂用宽笔描边，带弧度
    arm_w = s * 0.115
    stroke_xg = QPen(QBrush(xg), arm_w, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)

    # 左上 -> 右下（向内弯）
    path1 = QPainterPath()
    path1.moveTo(s * 0.26, s * 0.27)
    path1.cubicTo(QPointF(s*0.52, s*0.40), QPointF(s*0.48, s*0.60), QPointF(s*0.74, s*0.73))
    # 右上 -> 左下（向内弯）
    path2 = QPainterPath()
    path2.moveTo(s * 0.74, s * 0.27)
    path2.cubicTo(QPointF(s*0.48, s*0.40), QPointF(s*0.52, s*0.60), QPointF(s*0.26, s*0.73))

    # 发光底
    glow = QPen(C('#00A8FF', 70), arm_w * 1.55, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(glow)
    p.setBrush(Qt.NoBrush)
    p.drawPath(path1)
    p.drawPath(path2)

    # 斜臂主体
    p.setPen(stroke_xg)
    p.drawPath(path1)
    p.drawPath(path2)

    # 中央竖杠（SpaceX 标志性主干，略带梯形：用多边形）
    stem = QPolygonF([
        QPointF(cx - s*0.055, s*0.18),
        QPointF(cx + s*0.055, s*0.18),
        QPointF(cx + s*0.075, s*0.82),
        QPointF(cx - s*0.075, s*0.82),
    ])
    stem_g = QLinearGradient(0, s*0.18, 0, s*0.82)
    stem_g.setColorAt(0, C('#EAF6FF'))
    stem_g.setColorAt(1, C('#0E4EA8'))
    p.setPen(QPen(C('#00A8FF', 60), s*0.02))
    p.setBrush(QBrush(stem_g))
    p.drawPolygon(stem)

    p.end()
    return img


for sz in (256, 128, 64, 48, 32, 16):
    draw_logo(sz).save(f'assets/x-logo-{sz}.png')
draw_logo(256).save('assets/x-logo.ico', 'ICO')
print('SpaceX 风格 X logo 生成完成')
