from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame,QDialog,QHBoxLayout,QPushButton,
                                QSizePolicy,QGroupBox,QRadioButton,QFormLayout,QDoubleSpinBox,
                                QMessageBox)
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from PySide6.QtCore import Qt, QRectF, QPointF, Signal,QElapsedTimer,QTimer
import math
from MechanicsEngine import MechanicsEngine
from TuningDialWidget import TuningDialWidget
from PianoGenerator import PianoKey
from StringCSVManager import StringCSVManager
from typing import Dict,Any
import numpy as np


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

        # 施力模式状态
        self.force_mode = "speed_map"     # 初始模式: 'speed_map' 或 'predefined_force'
        self.predefined_force = 200      # 预定义力矩 (N·m)

        self.tune_done_threshold = 1.0


        # ========== 子部件 ==========
        self.dial = TuningDialWidget()
        self.dial.set_range(100)
        self.params = ParameterPanel(self)
        self.board = MouseAdjustBoard(self)

        # 按钮面板
        self.button_panel = ButtonPanel(self)
        self.button_panel.repairClicked.connect(self._on_repair_clicked)
        self.button_panel.forceModeClicked.connect(self._on_force_mode_clicked)

        # MouseAdjustBoard 发出的速度信号连接到新的施力逻辑
        self.board.velocityChanged.connect(self.apply_velocity)

        # ========== 布局 ==========
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.dial,3.75)
        layout.addWidget(self.params,4)
        layout.addWidget(self.button_panel,0.1)
        layout.addWidget(self.board,2)
        self.setLayout(layout)




    # ===================================================
    # UI 交互槽函数
    # ===================================================


    def _on_repair_clicked(self):
        """
        一键修复（校准）：
        - 计算目标角度 theta_target（用正确公式）
        - 如果 theta_target < 静态松弦阈值（theta_loose），提示用户并自动选择动作：
            - 默认：将 theta 设为阈值 + 小余量，保证稳定
          若阈值无意义（参数不允许松弦），直接设置目标角度。
        - 重置 omega = 0，刷新 UI
        """
        # 1. 计算目标频率对应的角度（使用修正后的 calculate_theta_for_frequency）
        theta_target = self.mechanics.calculate_theta_for_frequency(self.target_freq)

        # 2. 计算静态松弦阈值（如果你的 MechanicsEngine 有类似方法）
        #    如果没有该方法，请参考 MechanicsEngine._compute_theta_loose_threshold 的实现并加上
        theta_loose = None
        # 尝试调用（如果你已按之前建议添加了 _compute_theta_loose_threshold）
        if hasattr(self.mechanics, "_compute_theta_loose_threshold"):
            theta_loose = self.mechanics._compute_theta_loose_threshold()

        # 3. 如果阈值存在且目标在阈值以下，提示用户并自动补偿到阈值上（微小余量）
        if theta_loose is not None:
            if theta_target < theta_loose:
                # 弹出提示，说明原因并将目标调整为阈值+余量
                reply = QMessageBox.question(
                    self, "松弦预警：目标角度低于松弦阈值",
                    ("目标角度对应的 θ 低于静态松弦阈值，"
                     "直接设置会导致螺丝未吃入摩擦区（松弦），修复后无法保持。\n\n"
                     f"目标 θ = {theta_target:.6f} rad\n"
                     f"松弦阈值 θ_loose = {theta_loose:.6f} rad\n\n"
                     "是否将修复角度自动提升到阈值以保证稳定？\n"
                     "（选择 否=仍设为目标θ，可能会被判为松弦）"),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                if reply == QMessageBox.StandardButton.Yes:
                    # 加入微小余量，避免数值边界问题
                    theta_target = theta_loose + max(1e-6, theta_loose * 1e-3)
                # 如果用户选择 No，则保持原目标 theta_target（但可能马上被判为松弦）
        # 4. 强制设置 MechanicsEngine 状态
        self.mechanics.reset(theta=theta_target, omega=0.0)

        # 5. 强制更新 UI（一次完整更新）
        self.apply_velocity(0.0,False)


        QMessageBox.information(self, "校准成功",
                                f"已将弦轴角度校准至目标频率 {self.target_freq:.2f} Hz 对应的角度 ({theta_target:.6f} rad)。")


    def _on_force_mode_clicked(self):
        """槽函数：打开施力方式配置窗口"""
        dialog = ForceModeDialog(
            k_d=self.mechanics.k_d,
            predef_force=self.predefined_force,
            force_mode=self.force_mode,
            parent=self
        )

        if dialog.exec() == QDialog.Accepted:
            config = dialog.get_config()

            # 更新 MechanicsEngine 和 Panel 状态
            self.mechanics.k_d = config["k_d"]
            self.predefined_force = config["predefined_force"]
            self.force_mode = config["force_mode"]

            self.apply_velocity(self.board.v_user) # 用新模式和参数更新一次状态

            mode_name = "速度映射模式" if self.force_mode == "speed_map" else "预定义力模式"
            QMessageBox.information(self, "施力方式更新",
                                    f"施力模式已切换为：{mode_name}。\n驱动增益 k_d: {self.mechanics.k_d:.1f}")


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
        self.apply_velocity(0.0,False) # 使用当前速度(可能为0)驱动一次更新


    def set_current_frequency(self, freq: float):
        """设置目标频率，供 MainWindow 调用"""

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
        self.apply_velocity(0.0,False)

        self.mechanics.update( v_user=0.0,dt=0.01)

        self.mechanics.update_physical_params(new_params)

        self.apply_velocity(0.0,False)

        self.mechanics.update( v_user=0.0,dt=0.01)

        # 更新鼠标设置
        if hasattr(self, "board"):
            self.board.apply_settings(
                deadzone=new_params.get("mouse_deadzone"),
                alpha=new_params.get("mouse_alpha"),
                scale=new_params.get("mouse_scale"),
                decay_tau=new_params.get("mouse_decay_tau")
            )

        # 设置音分指示仪的可调范围
        dial_range = new_params.get("tuning_dial_range_cents")
        if dial_range:
            self.dial.set_range(dial_range)
        # 调律完成阈值
        if "tuning_done_threshold_cents" in new_params:
            self.tune_done_threshold = float(new_params["tuning_done_threshold_cents"])

        self.update()



    # 新版本，有速度映射和预定义力
    def apply_velocity(self, v_user: float,warnings:bool = True):
        """
        鼠标调整板发出速度输入 v_user（m/s）
        根据当前施力模式，将 v_user 转换为 MechanicsEngine 的驱动输入，并实时更新 UI
        """
        # 根据施力模式，决定实际传递给 MechanicsEngine 的 v_user
        if self.force_mode == "predefined_force":
            # 预定义力模式：鼠标速度只用于决定方向和是否静止
            if abs(v_user) < 1e-4:
                # 鼠标静止，输入速度为0
                input_v = 0.0
            else:
                # 鼠标移动，输入速度决定方向，大小由预定义力 F_p / k_d 确定
                # 目的：驱动扭矩 τ_drive ≈ F_p，所以 v_user ≈ F_p / k_d
                sign = np.sign(v_user)
                input_v = sign * (self.predefined_force / self.mechanics.k_d)

            # 施加扭矩的显示值 (简化为预定义力矩)
            torque_display = sign * self.predefined_force if abs(input_v) > 0 else 0.0

        else: # "speed_map" 速度映射模式
            # 默认模式：v_user 直接映射
            input_v = v_user
            # 施加扭矩的显示值 (简化为 k_d * v_user)
            torque_display = input_v * self.mechanics.k_d


        # 1. 执行 MechanicsEngine 更新
        state = self.mechanics.update(v_user=input_v, dt=0.01)
        # ---- 弦松警告（只提示一次） ----
        if warnings and state.get("loose", False):
            if not getattr(self, "_warned_loose", False):
                theta = state["theta"]
                theta_loose = state["theta_loose_threshold"]

                QMessageBox.warning(
                    self, "⚠ 弦松警告",
                    f"当前螺丝角度过小，尚未吃入摩擦区（松弦）。\n\n"
                    f"当前 θ：{theta:.6f} rad\n"
                    f"松弦阈值 θ_loose：{theta_loose:.6f} rad\n\n"
                    f"请轻轻上紧弦轴直到超过松弦阈值。"
                )
                self._warned_loose = True
        else:
            self._warned_loose = False

        # ---- 断弦警告 ----
        if warnings and state.get("broken", False):
            if not getattr(self, "_warned_broken", False):
                T = state["tension"]
                Tmax = state["max_tension"]
                sigma = T / (math.pi * self.mechanics.r * self.mechanics.r)
                sigma_valid = self.mechanics.Sigma_valid

                QMessageBox.critical(
                    self, "⚠ 断弦警告",
                    f"弦张力已超过材料允许极限！\n"
                    f"弦可能已经断裂，请立即停止调节。\n\n"
                    f"当前张力 T：{T:.2f} N\n"
                    f"断弦极限 T_max：{Tmax:.2f} N\n\n"
                    f"当前应力 σ：{sigma:.2f} MPa\n"
                    f"材料允许应力 σ_valid：{sigma_valid:.2f} MPa"
                )
                self._warned_broken = True
        else:
            self._warned_broken = False


        self.current_state = state

        # 2. 更新 UI 显示
        freq = state["frequency"]
        tension = state["tension"]

        # 3. 计算音分偏差
        cents = 0.0
        if freq > 0 and self.target_freq > 0:
            cents = 1200 * math.log2(freq / self.target_freq)

        # 4. 更新子部件
        self.dial.set_frequencies(freq, self.target_freq)

        self.params.update_values(
            freq=freq,
            target=self.target_freq,
            cents=cents,
            tension=tension,
            theta=self.mechanics.theta,
            velocity=v_user, # 保持显示原始鼠标速度
            torque_apply=torque_display, # 显示施加扭矩的简化值
            k_d=self.mechanics.k_d
        )

        self.update()

        # ==============================
        # 🎯 调律完成检测（最简洁）
        # ==============================
        if warnings and abs(cents) <= self.tune_done_threshold:
            if not getattr(self, "_tune_done_reported", False):
                self._tune_done_reported = True

                # 停止输入
                self.board.v_user = 0
                self.board.v_filtered = 0

                # 力学引擎停止
                self.mechanics.update(v_user=0, dt=0.01)

                QMessageBox.information(
                    self, "🎉 调律完成",
                    f"已达到精度要求：±{self.tune_done_threshold} cents\n"
                    f"当前偏差：{cents:+.2f} cents"
                )
        else:
            self._tune_done_reported = False



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

        # # --- 新增：方向反转立即清零 ---
        # if self.v_filtered != 0 and np.sign(v_est) != np.sign(self.v_filtered):
        #     self.v_filtered = 0.0

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

    def apply_settings(self, deadzone=None, alpha=None, scale=None, decay_tau=None):
        if deadzone is not None:
            self.deadzone = float(deadzone)
        if alpha is not None:
            self.alpha = float(alpha)
        if scale is not None:
            self.scale = float(scale)
        if decay_tau is not None:
            self.decay_tau = float(decay_tau)


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



 # ===============================================================
 # 施力方式配置对话框
 # ===============================================================

class ForceModeDialog(QDialog):
    """用于配置施力模式和相关参数的对话框"""
    def __init__(self, k_d: float, predef_force: float, force_mode: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("施力方式配置")

        self.k_d = k_d
        self.predef_force = predef_force
        self.force_mode = force_mode

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # 模式选择
        mode_group = QGroupBox("施力模式选择")
        mode_layout = QVBoxLayout(mode_group)

        self.radio_speed = QRadioButton("速度映射模式 (D_dot → 力矩)")
        self.radio_force = QRadioButton("预定义力模式 (D_dot → ±预定义力矩)")

        mode_layout.addWidget(self.radio_speed)
        mode_layout.addWidget(self.radio_force)

        if self.force_mode == "speed_map":
            self.radio_speed.setChecked(True)
        else:
            self.radio_force.setChecked(True)

        main_layout.addWidget(mode_group)

        # 参数配置
        param_group = QGroupBox("参数配置")
        form_layout = QFormLayout(param_group)

        # 1. k_d 配置
        self.input_k_d = QDoubleSpinBox()
        self.input_k_d.setRange(0.01, 1000.0)
        self.input_k_d.setDecimals(1)
        self.input_k_d.setValue(self.k_d)
        form_layout.addRow(QLabel("驱动增益 k_d (Nm·s/m):"), self.input_k_d)

        # 2. 预定义力配置
        self.input_predef_force = QDoubleSpinBox()
        self.input_predef_force.setRange(0.01, 1000000)
        self.input_predef_force.setDecimals(4)
        self.input_predef_force.setValue(self.predef_force)
        form_layout.addRow(QLabel("预定义力矩 (Nm):"), self.input_predef_force)

        main_layout.addWidget(param_group)

        # 按钮
        button_layout = QHBoxLayout()
        btn_save = QPushButton("确定")
        btn_cancel = QPushButton("取消")

        btn_save.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        button_layout.addStretch(1)
        button_layout.addWidget(btn_save)
        button_layout.addWidget(btn_cancel)

        main_layout.addLayout(button_layout)

    def get_config(self) -> Dict[str, Any]:
        """返回新的配置"""
        new_mode = "speed_map" if self.radio_speed.isChecked() else "predefined_force"
        return {
        "k_d": self.input_k_d.value(),
        "predefined_force": self.input_predef_force.value(),
        "force_mode": new_mode
        }

 # ===============================================================
 # 按钮控制面板
 # ===============================================================

class ButtonPanel(QWidget):
    """包含 一键修复 和 施力方式 按钮的面板"""
    repairClicked = Signal()
    forceModeClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.btn_repair = QPushButton("一键修复 (校准)")
        self.btn_force_mode = QPushButton("施力方式 (配置)")

        self.btn_repair.clicked.connect(self.repairClicked.emit)
        self.btn_force_mode.clicked.connect(self.forceModeClicked.emit)

        # 样式调整
        self.btn_repair.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_force_mode.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout.addWidget(self.btn_repair)
        layout.addWidget(self.btn_force_mode)



