# from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLineEdit,
#                               QPushButton, QGroupBox, QHBoxLayout, QLabel,
#                               QMessageBox, QDoubleSpinBox, QSizePolicy, QDialog)
# from PySide6.QtCore import Qt, Signal
# from typing import Dict, Any

# class FrictionConfigWidget(QWidget):
#     """摩擦模型参数配置界面"""
#     # 信号：当配置参数被保存时发出
#     config_saved = Signal(dict)

#     def __init__(self, current_params: Dict[str, Any], parent=None):
#         """
#         :param current_params: 包含当前所有摩擦参数的字典。
#         """
#         super().__init__(parent)
#         self.setWindowTitle("摩擦模型配置 (限幅摩擦)")
#         self.current_params = current_params
#         self._setup_ui()

#     def _setup_ui(self):
#         main_layout = QVBoxLayout(self)
#         main_layout.setSpacing(15)

#         model_group = QGroupBox("限幅摩擦模型参数")
#         form_layout = QFormLayout(model_group)

#         # 1. 初始静摩擦极限 τ_fric_limit_0 (N·m)
#         self.input_fric_limit_0 = self._create_double_spin_box(
#             self.current_params.get('mech_fric_limit_0', 0.1), -1000.0, 1000.0, 4)
#         form_layout.addRow(QLabel("初始静摩擦极限 τ_0 (N·m):"), self.input_fric_limit_0)

#         # 2. 静摩擦增长系数 α (N·m/rad)
#         self.input_alpha = self._create_double_spin_box(
#             self.current_params.get('mech_alpha', 0.05), 0.0,1000.0, 4)
#         form_layout.addRow(QLabel("静摩擦增长系数 α (N·m/rad):"), self.input_alpha)

#         # 3. 动摩擦扭矩 τ_kinetic (N·m)
#         self.input_kinetic = self._create_double_spin_box(
#             self.current_params.get('mech_kinetic', 0.08), 0.0, 1000.0, 4)
#         form_layout.addRow(QLabel("动摩擦扭矩 τ_kinetic (N·m):"), self.input_kinetic)

#         # 4. 粘性摩擦系数 σ (N·m·s/rad)
#         self.input_sigma = self._create_double_spin_box(
#             self.current_params.get('mech_sigma', 0.001), 0.0, 1.0, 5)
#         form_layout.addRow(QLabel("粘性摩擦系数 σ (N·m·s/rad):"), self.input_sigma)

#         main_layout.addWidget(model_group)

#         # 5. 控制按钮
#         button_layout = QHBoxLayout()
#         self.btn_save = QPushButton("保存配置")
#         self.btn_cancel = QPushButton("取消")

#         self.btn_save.clicked.connect(self._save_config)
#         self.btn_cancel.clicked.connect(self._cancel_and_exit)

#         button_layout.addStretch(1)
#         button_layout.addWidget(self.btn_save)
#         button_layout.addWidget(self.btn_cancel)

#         main_layout.addLayout(button_layout)
#         self.setLayout(main_layout)
#         self.setFixedSize(self.sizeHint()) # 固定窗口大小

#     def _create_double_spin_box(self, value, minimum, maximum, decimals=3):
#         """创建 QDoubleSpinBox 的辅助函数"""
#         spinbox = QDoubleSpinBox()
#         spinbox.setRange(minimum, maximum)
#         spinbox.setDecimals(decimals)
#         spinbox.setValue(value)
#         spinbox.setSingleStep((maximum - minimum) / 100) # 步进值
#         spinbox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
#         return spinbox

#     def _save_config(self):
#         """收集参数，发出信号并关闭窗口"""
#         new_params = {
#             'mech_fric_limit_0': self.input_fric_limit_0.value(),
#             'mech_alpha': self.input_alpha.value(),
#             'mech_kinetic': self.input_kinetic.value(),
#             'mech_sigma': self.input_sigma.value()
#         }

#         self.config_saved.emit(new_params)
#         if self.parent():
#              self.parent().accept() # 关闭对话框

#     def _cancel_and_exit(self):
#         """取消操作，关闭父级对话框"""
#         if self.parent():
#              self.parent().reject() # 告诉父级 Dialog 数据未保存


from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLineEdit,
                              QPushButton, QGroupBox, QHBoxLayout, QLabel,
                              QMessageBox, QDoubleSpinBox, QSizePolicy, QDialog)
from PySide6.QtCore import Qt, Signal
from typing import Dict, Any

class FrictionConfigWidget(QWidget):
    """摩擦模型参数配置界面（静/动摩擦联动模型）"""
    config_saved = Signal(dict)

    def __init__(self, current_params: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setWindowTitle("摩擦模型配置")
        self.current_params = current_params
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        model_group = QGroupBox("摩擦模型参数")
        form_layout = QFormLayout(model_group)

        # 1. 初始静摩擦极限 τ₀（可为负值）
        self.input_fric_limit_0 = self._create_double_spin_box(
            self.current_params.get('mech_fric_limit_0', -10.0), -1000.0, 1000.0, 4)
        form_layout.addRow(QLabel("初始静摩擦极限 τ₀ (N·m)："), self.input_fric_limit_0)

        # 2. 静摩擦增长系数 α
        self.input_alpha = self._create_double_spin_box(
            self.current_params.get('mech_alpha', 0.05), 0.0, 1000.0, 4)
        form_layout.addRow(QLabel("静摩擦增长系数 α (N·m/rad)："), self.input_alpha)

        # 3. 动静摩擦比例 γ（0.3 ~ 1 常见）
        self.input_gamma = self._create_double_spin_box(
            self.current_params.get('mech_gamma', 0.9), 0.01, 1.0, 3)
        form_layout.addRow(QLabel("动静摩擦比例 γ："), self.input_gamma)

        # 4. 粘性阻尼系数 σ
        self.input_sigma = self._create_double_spin_box(
            self.current_params.get('mech_sigma', 0.001), 0.0, 1.0, 5)
        form_layout.addRow(QLabel("粘性摩擦系数 σ (N·m·s/rad)："), self.input_sigma)

        main_layout.addWidget(model_group)

        # 保存/取消按钮
        button_layout = QHBoxLayout()
        self.btn_save = QPushButton("保存配置")
        self.btn_cancel = QPushButton("取消")

        self.btn_save.clicked.connect(self._save_config)
        self.btn_cancel.clicked.connect(self._cancel_and_exit)

        button_layout.addStretch(1)
        button_layout.addWidget(self.btn_save)
        button_layout.addWidget(self.btn_cancel)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        self.setFixedSize(self.sizeHint())  # 固定大小

    def _create_double_spin_box(self, value, minimum, maximum, decimals=3):
        spinbox = QDoubleSpinBox()
        spinbox.setRange(minimum, maximum)
        spinbox.setDecimals(decimals)
        spinbox.setValue(value)
        spinbox.setSingleStep((maximum - minimum) / 200)
        spinbox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        return spinbox

    def _save_config(self):
        new_params = {
            'mech_fric_limit_0': self.input_fric_limit_0.value(),
            'mech_alpha': self.input_alpha.value(),
            'mech_gamma': self.input_gamma.value(),
            'mech_sigma': self.input_sigma.value()
        }

        self.config_saved.emit(new_params)
        if self.parent():
            self.parent().accept()

    def _cancel_and_exit(self):
        if self.parent():
            self.parent().reject()
