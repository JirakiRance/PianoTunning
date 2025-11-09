from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QDial, QSlider, QLabel, QSizePolicy
from PySide6.QtCore import Qt, Signal,QEvent
import numpy as np

class TuningInputWidget(QWidget):
    """双向联动输入控件：旋钮和推杆"""

    # 信号：当用户输入改变时，发出归一化的输入值 (-1.0 to 1.0)
    input_changed = Signal(float)

    # 信号：当用户开始拖动时发出 (左键按下)
    drag_started = Signal()

    # 信号：当用户停止拖动时发出 (左键松开)
    drag_ended = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_norm_input = 0.0 # 归一化后的输入值 (-1.0 to 1.0)
        self._is_left_button_down = False
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        input_container = QWidget()
        knob_layout = QHBoxLayout(input_container)

        # 1. 微调旋钮 (QDial)
        self.fine_knob = QDial()
        self.fine_knob.setRange(-20, 20)
        self.fine_knob.setNotchesVisible(True)

        # 2. 粗调推杆 (QSlider)
        self.coarse_slider = QSlider(Qt.Vertical)
        self.coarse_slider.setRange(-100, 100)
        self.coarse_slider.setTickPosition(QSlider.TicksBothSides)

        knob_layout.addWidget(QLabel("旋钮\n(等价输入)"), 1)
        knob_layout.addWidget(self.fine_knob, 3)
        knob_layout.addWidget(QLabel("推杆\n(等价输入)"), 1)
        knob_layout.addWidget(self.coarse_slider, 3)

        main_layout.addWidget(input_container)

        # 连接：实现双向联动
        self.fine_knob.valueChanged.connect(self._handle_knob_change)
        self.coarse_slider.valueChanged.connect(self._handle_slider_change)

        # 鼠标事件 (用于拖拽启动/停止模拟)
        self.setMouseTracking(True)
        self.installEventFilter(self) # 需要安装事件过滤器

    def _handle_knob_change(self, value):
        """处理旋钮输入，更新推杆"""
        self.current_norm_input = value / 20.0
        self._block_and_set(self.coarse_slider, int(self.current_norm_input * 100))
        self.input_changed.emit(self.current_norm_input)

    def _handle_slider_change(self, value):
        """处理推杆输入，更新旋钮"""
        self.current_norm_input = value / 100.0
        self._block_and_set(self.fine_knob, int(self.current_norm_input * 20))
        self.input_changed.emit(self.current_norm_input)

    def _block_and_set(self, widget, value):
        """辅助函数：阻断信号并设置值"""
        widget.blockSignals(True)
        widget.setValue(value)
        widget.blockSignals(False)

    # --- 鼠标事件拦截 (实现左键按住运行) ---
    def eventFilter(self, source, event):
        """拦截鼠标事件，用于启动/停止拖拽"""

        if source == self:
            # 检查左键按下
            # --- 关键修正：使用 QEvent.MouseButtonPress ---
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                if self.rect().contains(event.pos()):
                    self._is_left_button_down = True
                    self.drag_started.emit() # 启动模拟

            # 检查左键释放
            # --- 关键修正：使用 QEvent.MouseButtonRelease ---
            elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                if self._is_left_button_down: # 确保是从拖动状态释放
                    self._is_left_button_down = False
                    self.drag_ended.emit() # 停止模拟

        # 忽略所有其他事件 (MouseMove, Resize, Paint, etc.)
        return super().eventFilter(source, event)
