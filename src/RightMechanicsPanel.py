from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from PySide6.QtCore import Qt, QRectF, QPointF, Signal,QElapsedTimer,QTimer
import math
from MechanicsEngine import MechanicsEngine
from TuningDialWidget2 import TuningDialWidget2
from PianoGenerator import PianoKey
from StringCSVManager import StringCSVManager
from typing import Dict,Any


class RightMechanicsPanel(QWidget):
    """
    ------------------------------
    钢琴调律辅助系统 - 力学调整模块（速度驱动版）
    ------------------------------
    架构：
        [TuningDial]     —— 扇形频率指示仪
        [ParameterPanel] —— 当前频率、张力、音分偏差
        [MouseAdjustBoard] —— 鼠标输入控制 v_user = dD/dt
    """

    def __init__(self, parent=None,k_d=50):
        super().__init__(parent)

        # ========== 初始化物理引擎 ==========
        self.mechanics = MechanicsEngine(k_d=k_d)

        # 当前目标频率（可扩展为音高选择器）
        self.target_freq = 440.0
        self.current_state = {}

        # ========== 子部件 ==========
        #self.dial = TuningDial(self)
        self.dial = TuningDialWidget2()
        self.dial.set_range(100)
        self.params = ParameterPanel(self)
        self.board = MouseAdjustBoard(self)
        self.board.velocityChanged.connect(self.apply_velocity)

        # ========== 布局 ==========
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.dial)
        layout.addWidget(self.params)
        layout.addWidget(self.board)
        self.setLayout(layout)


    # ===================================================
    #   MainWindow -> Panel (输入接口)
    # ===================================================


    def set_target_key(self,db_manager:StringCSVManager, new_key:PianoKey):
        """设置目标频率，供 MainWindow 调用"""
        self.target_freq = new_key.frequency
        self.dial.target_freq = new_key.frequency

        string_param=db_manager.get_string_parameters_by_id(new_key.key_id)
        self.mechanics.L=string_param.get("length",self.mechanics.L)
        self.mechanics.mu=string_param.get("density",self.mechanics.mu)
        self.mechanics.set_initial_state_by_frequency(new_key.frequency)


        # 强制用新目标频率更新一次 UI
        self.apply_velocity(0.0) # 使用当前速度(可能为0)驱动一次更新

    def set_current_frequency(self, freq: float):
        """设置目标频率，供 MainWindow 调用"""
        # self.apply_velocity(0.0)

        # 提前计算theta，必须做！！
        self.mechanics.set_initial_state_by_frequency(freq)

        state = self.mechanics.update( v_user=0.0,dt=0.01)
        self.current_state = state
        tension = state["tension"]

        # 计算音分偏差
        cents = 0.0
        if freq > 0:
            cents = 1200 * math.log2(freq / self.target_freq)
        # 更新
        self.dial.set_frequencies(freq,self.target_freq)
        self.params.update_values(
            freq=freq,
            target=self.target_freq,
            cents=cents,
            tension=tension,
            theta=self.mechanics.theta,
            velocity=0.0,
            torque_apply=0.0,
            k_d=self.mechanics.k_d
        )

        self.update()

    def set_params(self, new_params: Dict[str, Any]):
        self.apply_velocity(0.0)
        self.mechanics.update( v_user=0.0,dt=0.01)

        self.mechanics.update_physical_params(new_params)

        self.apply_velocity(0.0)
        self.mechanics.update( v_user=0.0,dt=0.01)

        self.update()


    # ===================================================
    #     力学联动逻辑
    # ===================================================
    def apply_velocity(self, v_user: float):
        """
        鼠标调整板发出速度输入 v_user（m/s）
        传递给 MechanicsEngine，并实时更新 UI
        """
        state = self.mechanics.update(v_user=v_user, dt=0.01)
        self.current_state = state

        freq = state["frequency"]
        tension = state["tension"]

        # 计算音分偏差
        cents = 0.0
        if freq > 0:
            cents = 1200 * math.log2(freq / self.target_freq)

        # 更新子部件
        self.dial.set_cents(cents)

        # 3.1. 修正：更新 TuningDialWidget2 (使用频率和目标频率)
        self.dial.set_frequencies(freq, self.target_freq)

        # # 3.2. 更新 ParameterPanel
        # drive_gain = getattr(self.mechanics, 'drive_gain', 5000)

        self.params.update_values(
            freq=freq,
            target=self.target_freq,
            cents=cents,
            tension=tension,
            theta=self.mechanics.theta,
            velocity=v_user,
            torque_apply=v_user * self.mechanics.k_d,
            k_d=self.mechanics.k_d
        )

        self.update()


# ===============================================================
# 扇形频率偏差指示仪
# ===============================================================

class TuningDial(QWidget):
    """
    扇形音高偏差指示仪：
    以目标频率为中心，显示 ±range_cents 范围内的音分偏差。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_cents = 0.0
        self.range_cents = 100.0
        self.setMinimumHeight(220)

    def set_cents(self, value: float):
        self.current_cents = max(-self.range_cents, min(self.range_cents, value))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w // 2, h - 30
        r = min(w, h * 0.8) // 2

        # 扇形刻度
        painter.setPen(QPen(QColor(200, 200, 210), 2))
        for i in range(-60, 61, 5):
            angle = math.radians(180 + i)
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            painter.drawLine(QPointF(cx, cy), QPointF(x, y))

        # 指针
        norm = max(-1.0, min(1.0, self.current_cents / self.range_cents))
        pointer_angle = math.radians(180 + norm * 60)
        px = cx + r * 0.9 * math.cos(pointer_angle)
        py = cy + r * 0.9 * math.sin(pointer_angle)

        painter.setPen(QPen(QColor(255, 80, 80), 5))
        painter.drawLine(QPointF(cx, cy), QPointF(px, py))

        # 文字说明
        painter.setFont(QFont("Microsoft YaHei", 10))
        painter.setPen(QColor(80, 80, 80))
        painter.drawText(QRectF(0, h - 25, w, 25),
                         Qt.AlignmentFlag.AlignCenter, "音高偏差 (cents)")


# ===============================================================
# 参数显示面板
# ===============================================================

class ParameterPanel(QFrame):
    """显示当前频率、张力、音分偏差、输入速度、施加扭矩等"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.values = {}
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setMinimumHeight(150)

    def update_values(self, freq, target, cents, tension,theta, velocity,torque_apply,k_d):
        self.values = {
            "当前频率": f"{freq:.2f} Hz",
            "目标频率": f"{target:.2f} Hz",
            "音分偏差": f"{cents:+.1f} cents",
            "弦张力": f"{tension:.2f} N",
            "螺丝角度": f"{theta:.2f} rad",
            "输入速度": f"{velocity:+.4f} m/s",
            "施加扭矩": f"{torque_apply:+.2f} Nm",
            "当前k_d": f"{k_d} "
        }
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setFont(QFont("Microsoft YaHei", 10))
        y = 25
        for k, v in self.values.items():
            painter.setPen(QColor(60, 60, 60))
            painter.drawText(20, y, k)
            painter.setPen(QColor(40, 40, 160))
            painter.drawText(140, y, v)
            y += 25





class MouseAdjustBoard(QFrame):
    """
    鼠标速度控制板（带平滑与稳定机制）
    -------------------------------------------------
    特性：
        ✅ 左键按下才启用控制
        ✅ 鼠标移动速度 → v_user (dD/dt)
        ✅ 鼠标静止自动归零
        ✅ 松手平滑衰减到 0
        ✅ 抖动滤波 + 死区阈值 + EMA 平滑
    """
    velocityChanged = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setMinimumHeight(200)

        # 状态控制
        self.dragging = False
        self.last_y = 0.0
        self.last_time = QElapsedTimer()
        self.v_user = 0.0
        self.v_filtered = 0.0

        # 平滑参数
        self.alpha = 0.25       # EMA平滑系数
        self.deadzone = 0.2     # 像素死区
        self.max_dt = 0.25      # 最大时间间隔 (s)
        self.scale = 0.001      # 像素→速度比例 (m/s per pixel)
        self.decay_tau = 0.02    # 松手衰减时间常数 (s)

        # 衰减计时器（平滑归零）
        self.decay_timer = QTimer()
        self.decay_timer.timeout.connect(self._decay_to_zero)
        self.decay_timer.setInterval(16)  # 60FPS更新

    # ===================================================
    # 鼠标事件
    # ===================================================

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.last_y = event.position().y()
            self.last_time.start()
            self.v_user = 0.0
            self.v_filtered = 0.0
            self.velocityChanged.emit(0.0)
            self.decay_timer.stop()
        event.accept()

    def mouseMoveEvent(self, event):
        if not self.dragging:
            return

        current_y = event.position().y()
        elapsed_ms = self.last_time.elapsed()
        self.last_time.restart()

        if elapsed_ms <= 0:
            return

        dt = elapsed_ms / 1000.0
        dy = self.last_y - current_y

        # ===================== 核心：速度估算 =====================
        if abs(dy) < self.deadzone or dt > self.max_dt:
            v_est = 0.0
        else:
            v_est = dy * self.scale / dt

        # EMA 平滑
        self.v_filtered = self.alpha * v_est + (1 - self.alpha) * self.v_filtered
        self.v_user = self.v_filtered

        # 更新状态
        self.last_y = current_y
        self.velocityChanged.emit(self.v_user)
        self.update()

        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            # 启动平滑衰减
            self.decay_timer.start()
        event.accept()

    def leaveEvent(self, event):
        if self.dragging:
            self.dragging = False
            self.decay_timer.start()
        event.accept()

    # ===================================================
    # 平滑衰减逻辑（松手后速度逐步回零）
    # ===================================================

    def _decay_to_zero(self):
        dt = 0.016  # 60fps
        decay_factor = math.exp(-dt / self.decay_tau)
        self.v_filtered *= decay_factor
        if abs(self.v_filtered) < 1e-4:
            self.v_filtered = 0.0
            self.v_user = 0.0
            self.decay_timer.stop()
        else:
            self.v_user = self.v_filtered
        self.velocityChanged.emit(self.v_user)
        self.update()

    # ===================================================
    # 绘制部分
    # ===================================================

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(10, 10, -10, -10)

        # 背景框
        painter.setBrush(QBrush(QColor(240, 240, 245)))
        painter.setPen(QPen(QColor(160, 160, 180), 2))
        painter.drawRoundedRect(rect, 8, 8)

        # 标题
        painter.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        painter.setPen(QColor(50, 50, 70))
        painter.drawText(rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
                         "鼠标速度控制板")

        # 红点位置（速度方向可视化）
        cx = rect.center().x()
        cy = rect.center().y()
        offset = max(-60, min(60, -self.v_user * 200))
        painter.setBrush(QBrush(QColor(220, 80, 80)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy + offset), 10, 10)

        # 显示当前速度
        painter.setFont(QFont("Microsoft YaHei", 9))
        painter.setPen(QColor(100, 100, 120))
        painter.drawText(rect.adjusted(0, 140, 0, 0),
                         Qt.AlignmentFlag.AlignHCenter,
                         f"v_user = {self.v_user:+.4f} m/s")



