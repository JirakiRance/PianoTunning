# 旧版已经从注释移除

from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath, QFont
from PySide6.QtCore import Qt, QPointF
import numpy as np

class SpectrumWidget(QWidget):
    """
    专业版波形 + 频谱显示（用户可读性增强）
    ---------------------------------------------------
    上半部分：Waveform（带标题、中线）
    下半部分：Spectrum（频率刻度 + dB刻度 + 主峰标注）
    """
    def __init__(self, sample_rate, parent=None):
        super().__init__(parent)
        self.sample_rate = sample_rate
        self.audio_frame = np.array([])
        self.setMinimumHeight(350)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    # 外部调用 —— 更新音频帧
    def update_frame(self, audio_frame,is_full_file:bool=False):
        self.audio_frame = audio_frame.astype(np.float32)
        self.update()

    # ======================================================
    # 主绘图函数
    # ======================================================
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        W = self.width()
        H = self.height()

        # 背景
        painter.fillRect(self.rect(), QColor("#1a1a1a"))

        if len(self.audio_frame) == 0:
            painter.setPen(QColor(200, 200, 200))
            painter.drawText(self.rect(), Qt.AlignCenter, "等待音频输入…")
            return

        # 区域划分
        H_wave = H * 0.45
        gap = H * 0.05
        H_spec_start = H_wave + gap
        H_spec = H - H_spec_start

        # 绘制波形
        self._draw_waveform(painter, 0, H_wave, W)

        # 绘制频谱
        self._draw_spectrum(painter, H_spec_start, H, W)

    # ======================================================
    # 波形绘制（上半部分）
    # ======================================================
    def _draw_waveform(self, painter, y0, H_wave, W):
        data = self.audio_frame
        L = len(data)

        # 标题
        painter.setPen(QColor(220, 220, 220))
        painter.setFont(QFont("Microsoft Yahei", 10))
        painter.drawText(10, int(y0 + 20), "Waveform")

        # 归一化
        data_norm = data / (np.max(np.abs(data)) + 1e-6)
        y_vals = y0 + H_wave/2 - data_norm * (H_wave/2 - 5)

        # 中线
        painter.setPen(QPen(QColor(120, 120, 120), 1))
        painter.drawLine(0, int(y0 + H_wave/2), W, int(y0 + H_wave/2))

        # 绘制波形线
        path = QPainterPath()
        path.moveTo(0, y_vals[0])

        step = max(1, L // W)

        for i in range(1, L, step):
            x = i * W / L
            path.lineTo(x, y_vals[i])

        painter.setPen(QPen(QColor("#4aa3ff"), 2))
        painter.drawPath(path)

    # ======================================================
    # 频谱绘制（下半部分）
    # ======================================================
    def _draw_spectrum(self, painter, y0, y_bottom, W):
        audio = self.audio_frame
        sr = self.sample_rate
        H = y_bottom - y0

        # 标题
        painter.setPen(QColor(220, 220, 220))
        painter.setFont(QFont("Microsoft Yahei", 10))
        painter.drawText(10, int(y0 + 20), "Spectrum")

        # FFT
        NFFT = min(len(audio), 4096)
        window = np.hanning(NFFT)
        fft = np.abs(np.fft.rfft(audio[:NFFT] * window))
        freqs = np.fft.rfftfreq(NFFT, 1/sr)

        # 限制 20–5000Hz
        mask = (freqs >= 20) & (freqs <= 5000)
        freqs = freqs[mask]
        mags = fft[mask]

        mags_db = 20 * np.log10(mags + 1e-6)
        mags_db = np.clip(mags_db, -80, 0)

        # 坐标变换
        def f_to_x(f):
            return int((np.log10(f) - np.log10(20)) / (np.log10(5000) - np.log10(20)) * W)

        def db_to_y(db):
            return y0 + (1 - (db + 80) / 80) * (H - 15)

        # ------------------------
        # dB 网格
        # ------------------------
        painter.setPen(QPen(QColor(70, 70, 70), 1))
        for db in [0, -20, -40, -60, -80]:
            yy = db_to_y(db)
            painter.drawLine(0, yy, W, yy)
            painter.setPen(QColor(140, 140, 140))
            painter.drawText(5, yy - 2, f"{db} dB")
            painter.setPen(QPen(QColor(70, 70, 70), 1))

        # ------------------------
        # 频率网格
        # ------------------------
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        for f in [100, 200, 400, 800, 1600, 3200]:
            xx = f_to_x(f)
            painter.drawLine(xx, y0, xx, y_bottom)
            painter.setPen(QColor(160, 160, 160))
            painter.drawText(xx + 2, y0 + 15, f"{f}")
            painter.setPen(QPen(QColor(60, 60, 60), 1))

        # ------------------------
        # 绘制柱形谱
        # ------------------------
        painter.setPen(Qt.NoPen)
        for f, db in zip(freqs, mags_db):
            x = f_to_x(f)
            h = (1 - (db + 80) / 80) * (H - 15)
            painter.setBrush(QColor(255, 150, 30, 220))
            painter.drawRect(x, y_bottom - h, 2, h)

        # ------------------------
        # 主峰标注（最有用）
        # ------------------------
        # peak_idx = np.argmax(mags_db)
        # f_peak = freqs[peak_idx]
        # db_peak = mags_db[peak_idx]

        # px = f_to_x(f_peak)
        # py = db_to_y(db_peak)

        # painter.setPen(QPen(QColor(255, 200, 0), 2))
        # painter.drawLine(px - 5, py, px + 5, py)
        # painter.drawLine(px, py - 5, px, py + 5)

        # painter.setFont(QFont("Microsoft Yahei", 10))
        # painter.drawText(px + 8, py - 8, f"{int(f_peak)} Hz")

