# This Python file uses the following encoding: utf-8
from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtGui import QPainter, QColor, QPen,QPainterPath
from PySide6.QtCore import Qt, QPointF
import numpy as np


class SpectrumWidget(QWidget):
    """实时频谱和波形可视化组件"""
    def __init__(self, sample_rate, parent=None):
        super().__init__(parent)
        self.audio_frame = np.array([])
        self.sample_rate = sample_rate
        self.setMinimumHeight(300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.is_full_file = False

    def update_frame(self, audio_frame: np.ndarray,is_full_file: bool = False):
        """接收新音频帧并触发重绘"""
        self.audio_frame = audio_frame
        self.is_full_file = is_full_file # <-- 存储模式
        self.update() # 触发 paintEvent

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        width = self.width()
        height = self.height()

        # 背景
        painter.fillRect(self.rect(), QColor("#2c3e50"))

        if len(self.audio_frame) == 0:
            painter.setPen(QColor(255, 255, 255, 100))
            painter.drawText(self.rect(), Qt.AlignCenter, "等待音频输入...")
            return

        # --- 1. 绘制波形 (上半部分) ---
        wave_height = height * 0.45
        wave_offset = height * 0.05

        if len(self.audio_frame) > 0:
            # 缩放波形数据到 [0, wave_height] 范围
            scaled_data = (self.audio_frame + 1) / 2 * wave_height

            points = []
            for i, val in enumerate(scaled_data):
                x = i * width / len(self.audio_frame)
                y = wave_height - val + wave_offset
                points.append(QPointF(x, y))

            painter.setPen(QPen(QColor("#3498db"), 1.5))
            if points:
                # 绘制波形线
                path = QPainterPath()
                path.moveTo(points[0])
                for point in points[1:]:
                    path.lineTo(point)
                painter.drawPath(path)

            #painter.setPen(QPen(QColor("#3498db", 100), 1))
            base_color = QColor("#3498db")
            base_color.setAlpha(100) # 设置透明度为 100 (0-255)
            painter.setPen(QPen(base_color, 1))
            painter.drawLine(0, wave_height/2 + wave_offset, width, wave_height/2 + wave_offset) # 中线

        # --- 2. 绘制频谱 (下半部分) ---
        spec_height = height * 0.45
        spec_offset = height * 0.55

        try:
            # 快速FFT计算
            fft_data = np.abs(np.fft.rfft(self.audio_frame * np.hanning(len(self.audio_frame))))
            freqs = np.fft.rfftfreq(len(self.audio_frame), 1.0 / self.sample_rate)

            # 频率显示范围：0Hz 到 5000Hz (钢琴范围)
            max_freq_to_show = 5000
            valid_bins = np.where(freqs <= max_freq_to_show)[0]
            fft_data = fft_data[valid_bins]
            freqs = freqs[valid_bins]

            if len(fft_data) > 0:
                # 幅值归一化 (对数缩放，增强低幅度细节)
                fft_log = 20 * np.log10(fft_data + 1e-6)
                max_db = np.max(fft_log)
                min_db = max_db - 80 # 80dB 动态范围

                # 缩放到 [0, spec_height]
                scaled_fft = np.clip((fft_log - min_db) / (max_db - min_db), 0, 1) * spec_height

                # 绘制频谱柱
                bar_width = width / len(scaled_fft)

                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor("#e67e22")) # 橙色

                for i, val in enumerate(scaled_fft):
                    x = i * bar_width
                    # y 从底部开始画
                    y = height - val - spec_offset
                    painter.drawRect(x, spec_offset + spec_height - val, bar_width, val)

        except Exception:
            # 忽略 FFT 错误
            pass
