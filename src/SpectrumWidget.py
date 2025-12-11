

from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath, QFont
from PySide6.QtCore import Qt, QPoint
import numpy as np


class SpectrumWidget(QWidget):
    def __init__(self, sample_rate, parent=None):
        super().__init__(parent)
        self.sample_rate = sample_rate

        self.audio_frame = np.array([])
        self.dominant_freq = None
        self.is_full_file = False

        self.setMinimumHeight(350)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    # 外部调用：更新音频帧
    def update_frame(self, audio_frame, dominant_freq=None, is_full_file=False):
        """
        audio_frame   : 最新音频数据
        dominant_freq : 主峰（来自 PitchDetector）
        is_full_file  : 是否绘制完整频谱（文件分析模式）
        """
        self.audio_frame = audio_frame.astype(np.float32)
        self.dominant_freq = dominant_freq
        self.is_full_file = is_full_file
        self.update()

    # ==================================================
    # paintEvent 主绘制
    # ==================================================
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        W = self.width()
        H = self.height()

        # 背景
        painter.fillRect(self.rect(), QColor("#1a1a1a"))

        # 无数据
        if len(self.audio_frame) == 0:
            painter.setPen(QColor(200, 200, 200))
            painter.drawText(self.rect(), Qt.AlignCenter, "等待音频输入…")
            return

        # 上波形区
        H_wave = int(H * 0.45)
        gap = int(H * 0.04)
        H_spec_start = H_wave + gap

        self._draw_waveform(painter, 0, H_wave, W)
        self._draw_spectrum(painter, H_spec_start, H, W)

    # ==================================================
    # 波形绘制（上半部分）
    # ==================================================
    def _draw_waveform(self, painter, y0, H_wave, W):
        data = self.audio_frame
        L = len(data)

        # 标题
        painter.setPen(QColor(220, 220, 220))
        painter.setFont(QFont("Microsoft Yahei", 10))
        painter.drawText(20, y0 + 20, "Waveform")

        # 归一化
        data_norm = data / (np.max(np.abs(data)) + 1e-6)
        y_vals = y0 + H_wave / 2 - data_norm * (H_wave / 2 - 5)

        # 中线
        painter.setPen(QPen(QColor(120, 120, 120), 1))
        painter.drawLine(0, int(y0 + H_wave / 2), W, int(y0 + H_wave / 2))

        # 波形路径
        path = QPainterPath()
        step = max(1, L // W)
        path.moveTo(0, y_vals[0])

        for i in range(1, L, step):
            x = i * W / L
            path.lineTo(x, y_vals[i])

        painter.setPen(QPen(QColor("#4aa3ff"), 2))
        painter.drawPath(path)

    # ==================================================
    # 对数频谱绘制（下半部分）
    # ==================================================
    def _draw_spectrum(self, painter, y0, y_bottom, W):
        audio = self.audio_frame
        sr = self.sample_rate
        H = y_bottom - y0

        # 标题
        painter.setPen(QColor(220, 220, 220))
        painter.drawText(20, y0 + 20, "Spectrum")

        if len(audio) == 0:
            return

        # FFT 长度
        NFFT = 8192 if self.is_full_file else 4096
        NFFT = min(len(audio), NFFT)

        window = np.hanning(NFFT)
        fft = np.abs(np.fft.rfft(audio[:NFFT] * window))
        freqs = np.fft.rfftfreq(NFFT, 1 / sr)

        # ---------------------------
        # frequency range 20–5000 Hz
        # ---------------------------
        f_lo, f_hi = 20, 5000
        mask = (freqs >= f_lo) & (freqs <= f_hi)
        freqs = freqs[mask]
        mags = fft[mask]

        mags_db = 20 * np.log10(mags + 1e-6)
        mags_db = np.clip(mags_db, -80, 0)

        # ================
        # 对数轴映射
        # ================
        log_min = np.log10(f_lo)
        log_max = np.log10(f_hi)

        def f_to_x(f):
            return int((np.log10(f) - log_min) / (log_max - log_min) * W)

        def db_to_y(db):
            return y0 + (1 - (db + 80) / 80) * (H - 20)

        # ======================
        # dB 网格
        # ======================
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        for db in [-80, -60, -40, -20, 0]:
            yy = db_to_y(db)
            painter.drawLine(0, yy, W, yy)
            painter.drawText(5, yy - 2, f"{db} dB")

        # ======================
        # 频率刻度（对数等距）
        # ======================
        freq_ticks = [20, 50, 100, 200, 400, 800, 1600, 3200, 5000]
        for f in freq_ticks:
            x = f_to_x(f)
            painter.drawLine(x, y0, x, y_bottom)
            painter.drawText(x + 2, y0 + 15, f"{f}")

        # ======================
        # 频谱折线
        # ======================
        path = QPainterPath()
        path.moveTo(f_to_x(freqs[0]), db_to_y(mags_db[0]))

        for f, db in zip(freqs[1:], mags_db[1:]):
            path.lineTo(f_to_x(f), db_to_y(db))

        painter.setPen(QPen(QColor("#ff9900"), 2))
        painter.drawPath(path)

        # ======================
        # 主峰标注（dominant_freq）
        # ======================
        if self.dominant_freq and (f_lo <= self.dominant_freq <= f_hi):
            px = f_to_x(self.dominant_freq)

            # 找到此频率对应的能量
            peak_idx = np.argmin(np.abs(freqs - self.dominant_freq))
            py = db_to_y(mags_db[peak_idx])

            # 半透明竖线（不遮挡曲线）
            painter.setPen(QPen(QColor(255, 230, 0, 100), 2))
            painter.drawLine(px, y0, px, y_bottom - 10)

            # 圆点：淡色填充 + 清晰描边
            painter.setBrush(QColor(255, 230, 0, 90))      # 半透明填充
            painter.setPen(QPen(QColor(255, 230, 0, 180), 2))  # 边缘稍亮
            painter.drawEllipse(QPoint(px, py), 4, 4)      # 适当缩小避免遮挡

            # 数字标注（淡色）
            painter.setPen(QColor(255, 230, 0, 180))
            painter.drawText(px + 8, py - 8, f"{self.dominant_freq:.1f} Hz")

