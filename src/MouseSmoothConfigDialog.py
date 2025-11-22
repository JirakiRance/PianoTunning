

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QDoubleSpinBox,
    QLabel, QPushButton, QHBoxLayout
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt


class MouseSmoothConfigDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("鼠标控制平滑设置")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)

        # ---------------------------------------------------------
        # ⭐ 用户提示说明（自动换行，不撑 UI）
        # ---------------------------------------------------------
        help_label = QLabel(
            "鼠标控制板的灵敏度和平滑可通过以下参数调整：\n\n"
            "● 死区（deadzone）\n"
            "    鼠标微小抖动会被忽略，小数值 = 更灵敏，大数值 = 更稳重。\n\n"
            "● 平滑因子（alpha）\n"
            "    控制速度信号的平滑程度。\n"
            "    小（0.1）= 更稳更慢，大（0.5）= 更灵敏但可能抖动。\n\n"
            "● 像素→速度比例（scale）\n"
            "    影响鼠标移动转换为调音速度的强弱。\n"
            "    大（0.003）= 鼠标轻轻移动就很快调音，小 = 细腻但需要更大鼠标位移。\n\n"
            "● 松手衰减时间（decay_tau）\n"
            "    松开鼠标后，速度逐渐减到 0 的时间常数。\n"
            "    大值 = 更慢停下，更柔和，小值 = 立即停止，响应快。\n\n"
            "建议：如果调音时感觉方向反、停不下来或太跳，可以调低 scale 或提高 alpha。\n"
        )
        help_label.setWordWrap(True)
        help_label.setAlignment(Qt.AlignLeft)
        help_label.setFont(QFont("Microsoft YaHei", 9))
        layout.addWidget(help_label)

        # ---------------------------------------------------------
        # 参数表单
        # ---------------------------------------------------------
        form = QFormLayout()

        self.in_deadzone = QDoubleSpinBox()
        self.in_deadzone.setRange(0, 5)
        self.in_deadzone.setDecimals(2)
        self.in_deadzone.setValue(config["mouse_deadzone"])
        form.addRow("死区 deadzone (px):", self.in_deadzone)

        self.in_alpha = QDoubleSpinBox()
        self.in_alpha.setRange(0, 1)
        self.in_alpha.setSingleStep(0.05)
        self.in_alpha.setDecimals(2)
        self.in_alpha.setValue(config["mouse_alpha"])
        form.addRow("平滑因子 alpha:", self.in_alpha)

        self.in_scale = QDoubleSpinBox()
        self.in_scale.setRange(0.0001, 0.01)
        self.in_scale.setDecimals(5)
        self.in_scale.setSingleStep(0.0001)
        self.in_scale.setValue(config["mouse_scale"])
        form.addRow("像素→速度比例 scale:", self.in_scale)

        self.in_decay_tau = QDoubleSpinBox()
        self.in_decay_tau.setRange(0.0001, 0.5)
        self.in_decay_tau.setDecimals(4)
        self.in_decay_tau.setValue(config["mouse_decay_tau"])
        form.addRow("松手衰减 decay_tau (s):", self.in_decay_tau)

        layout.addLayout(form)

        # ---------------------------------------------------------
        # 按钮
        # ---------------------------------------------------------
        buttons = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")

        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)

        layout.addLayout(buttons)
