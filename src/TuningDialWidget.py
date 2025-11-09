# TuningDialWidget.py (新文件)
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QDial, QSlider, QSizePolicy
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath
from PySide6.QtCore import Qt, QPoint, QRectF
import numpy as np

class TuningDialWidget(QWidget):
    """
    音分偏差与弦轴角度可视化仪表盘 (推杆替代品)。
    显示音分刻度、当前指针和弦轴角度。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cents_deviation = 0.0  # -50 到 +50 cents
        self.theta_degrees = 0.0    # 弦轴总转动角度 (度)
        self.setMinimumSize(250, 300)

    def set_values(self, cents: float, theta_degrees: float):
        """更新音分偏差和弦轴角度"""
        self.cents_deviation = cents
        self.theta_degrees = theta_degrees
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        W = self.width()
        H = self.height()
        center = QPoint(W // 2, H // 2)
        radius = min(W, H) // 2 - 20

        # 1. 绘制背景和刻度
        painter.setBrush(QColor(44, 62, 80)) # 深色背景
        painter.drawRect(self.rect())
        painter.setPen(QColor(127, 140, 141)) # 灰色边框

        # 2. 绘制音分刻度盘 (±50 cents)
        dial_radius = radius * 0.8

        # A. 绘制彩色区域 (红-黄-绿)
        rect = QRectF(center.x() - dial_radius, center.y() - dial_radius, 2 * dial_radius, 2 * dial_radius)

        # 颜色定义 (±2: 绿, ±10: 黄, >±10: 红)
        self._draw_arc(painter, center, dial_radius, 135, 90, QColor(231, 76, 60)) # 红色 (左 -10 to -50)
        self._draw_arc(painter, center, dial_radius, 90, 45, QColor(241, 196, 15)) # 黄色 (左 -10 to -2)
        self._draw_arc(painter, center, dial_radius, 45, 10, QColor(46, 204, 113)) # 绿色 (中心 -2 to +2)
        self._draw_arc(painter, center, dial_radius, 35, 45, QColor(241, 196, 15)) # 黄色 (右 +2 to +10)
        self._draw_arc(painter, center, dial_radius, 80, 135, QColor(231, 76, 60)) # 红色 (右 +10 to +50)

        # B. 绘制刻度和数字
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Arial", 10)
        painter.setFont(font)

        for deg, text in [(135, "-50"), (90, "-10"), (45, "-2"), (0, "0"), (-45, "+2"), (-90, "+10"), (-135, "+50")]:
            self._draw_tick(painter, center, dial_radius, deg, text)

        # 3. 绘制指针 (音分偏差)
        # 将 cents_deviation (-50 to +50) 映射到角度 (135 deg to -135 deg)
        clamped_cents = np.clip(self.cents_deviation, -50, 50)

        # 角度范围: 270度 (135 到 -135)
        # 0 cents = 0 deg
        # +50 cents = -135 deg
        # -50 cents = +135 deg

        # 映射函数：angle = - (cents / 50) * 135 (简化)
        # 实际映射：135 - (clamped_cents + 50) * 2.7
        angle = 135 - (clamped_cents + 50) * 2.7

        painter.save()
        painter.translate(center)
        painter.rotate(angle)

        # 指针
        painter.setPen(QPen(QColor(255, 0, 0), 2))
        painter.drawLine(0, 0, 0, -dial_radius + 5)
        painter.restore()

        # 4. 绘制中心读数
        painter.setPen(QColor(255, 255, 255))
        font.setPointSize(18)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRectF(center.x() - radius, center.y() + radius * 0.1, 2 * radius, radius * 0.3),
                         Qt.AlignCenter, f"{self.cents_deviation:+.1f} CENTS")

        # 5. 绘制弦轴角度 (底部)
        font.setPointSize(10)
        font.setBold(False)
        painter.setFont(font)
        painter.drawText(QRectF(0, H - 30, W, 30),
                         Qt.AlignCenter, f"角度: {self.theta_degrees:.2f}°")


    def _draw_arc(self, painter, center, radius, start_angle_map, end_angle_map, color):
        """辅助函数：绘制彩色圆弧"""

        start_angle = (start_angle_map + 90) * 16 # 映射到 Qt 角度 (0=3 o'clock, CCW)
        span_angle = (end_angle_map - start_angle_map) * 16

        painter.setPen(Qt.NoPen)
        painter.setBrush(color)

        # 绘制扇形
        rect = QRectF(center.x() - radius, center.y() - radius, 2 * radius, 2 * radius)
        painter.drawPie(rect, start_angle, span_angle)


    def _draw_tick(self, painter, center, radius, deg, text):
        """辅助函数：绘制刻度线和标签"""
        # 将刻度线从圆周缩进一点
        tick_radius = radius - 5

        painter.save()
        painter.translate(center)
        painter.rotate(-deg) # 旋转到刻度位置 (负号修正方向)

        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawLine(0, -radius, 0, -tick_radius)

        painter.restore()

        # 绘制标签
        font = QFont("Arial", 8)
        painter.setFont(font)
        label_radius = radius + 5

        angle_rad = np.radians(deg)
        x = center.x() + label_radius * np.cos(angle_rad + np.radians(90)) # 90度修正，使0度在顶部
        y = center.y() + label_radius * np.sin(angle_rad + np.radians(90))

        painter.drawText(int(x - 20), int(y - 10), 40, 20, Qt.AlignCenter, text)
