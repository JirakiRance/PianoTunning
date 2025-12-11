


from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QGroupBox,
    QHBoxLayout, QLabel, QMessageBox, QDoubleSpinBox, QSizePolicy,
    QComboBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal
import numpy as np
import pandas as pd

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from MechanicsEngine import MatCalInterpBuilder


class FrictionConfigWidget(QWidget):
    """摩擦模型配置：线性模型 / 自定义 CSV + 插值"""

    config_saved = Signal(dict)

    def __init__(self, current_params, parent=None):
        super().__init__(parent)
        self.setWindowTitle("摩擦模型配置")

        self.current_params = current_params

        # CSV 数据缓存
        self.theta_arr = None
        self.tau_arr = None
        self.selected_csv_path = None

        # 图像首次不显示
        self.canvas_created = False

        # 创建 UI
        self._setup_ui()

        # 恢复配置
        self._restore_from_previous_config()


    # ============================================================
    # UI 构建
    # ============================================================
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)

        # -------------------------------------------------------
        # 顶部统一摩擦参数（γ、σ） ← 两种模式都需要
        # -------------------------------------------------------
        global_group = QGroupBox("通用摩擦参数")
        global_layout = QFormLayout(global_group)

        self.input_gamma = self._spin(
            self.current_params.get("mech_gamma", 0.9),
            0.01, 1.0, 3
        )
        global_layout.addRow("动静摩擦比 γ：", self.input_gamma)

        self.input_sigma = self._spin(
            self.current_params.get("mech_sigma", 0.001),
            0, 1.0, 5
        )
        global_layout.addRow("粘性阻尼 σ (N·m·s/rad)：", self.input_sigma)

        # -------------------------------------------------------
        # 模型选择
        # -------------------------------------------------------
        mode_group = QGroupBox("摩擦模型选择")
        mode_layout = QFormLayout(mode_group)

        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["线性摩擦模型", "自定义摩擦模型"])
        self.combo_mode.currentIndexChanged.connect(self._mode_changed)
        mode_layout.addRow("选择模式：", self.combo_mode)

        # -------------------------------------------------------
        # 线性模型区 —— 只剩 τ₀ 和 α
        # -------------------------------------------------------
        linear_group = QGroupBox("线性摩擦模型")
        self.linear_group = linear_group
        form = QFormLayout(linear_group)

        self.input_fric_limit_0 = self._spin(
            self.current_params.get("mech_fric_limit_0", -10.0),
            -1000, 0, 4
        )
        form.addRow("静摩擦初值 τ₀：", self.input_fric_limit_0)

        self.input_alpha = self._spin(
            self.current_params.get("mech_alpha", 0.05),
            0, 100, 4
        )
        form.addRow("增长系数 α：", self.input_alpha)

        # -------------------------------------------------------
        # 自定义模型区
        # -------------------------------------------------------
        custom_group = QGroupBox("自定义摩擦模型 (CSV + 插值)")
        self.custom_group = custom_group
        custom_layout = QFormLayout(custom_group)

        # CSV 选择
        self.csv_path_edit = QLineEdit()
        self.csv_path_edit.setReadOnly(True)
        btn_choose = QPushButton("选择 CSV 文件")
        btn_choose.clicked.connect(self._choose_csv)

        h = QHBoxLayout()
        h.addWidget(self.csv_path_edit)
        h.addWidget(btn_choose)
        custom_layout.addRow("CSV 文件：", h)

        # 插值方式
        self.combo_interp = QComboBox()
        self.combo_interp.addItems(["线性插值", "三次样条插值", "牛顿插值"])
        custom_layout.addRow("插值方式：", self.combo_interp)

        # 图像显示区（初始隐藏）
        self.plot_container = QWidget()
        self.plot_container.setVisible(False)
        self.plot_layout = QVBoxLayout(self.plot_container)
        self.plot_layout.setContentsMargins(0, 0, 0, 0)
        custom_layout.addWidget(self.plot_container)

        btn_preview = QPushButton("预览 CSV 数据")
        btn_preview.clicked.connect(self._preview_plot)
        custom_layout.addWidget(btn_preview)

        btn_preview_interp = QPushButton("预览插值曲线")
        btn_preview_interp.clicked.connect(self._preview_interp)
        custom_layout.addWidget(btn_preview_interp)


        # -------------------------------------------------------
        # 保存取消
        # -------------------------------------------------------
        btn_save = QPushButton("保存")
        btn_save.clicked.connect(self._save)

        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self._cancel)

        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        bottom_layout.addWidget(btn_save)
        bottom_layout.addWidget(btn_cancel)

        # -------------------------------------------------------
        # 总布局
        # -------------------------------------------------------
        main_layout.addWidget(global_group)
        main_layout.addWidget(mode_group)
        main_layout.addWidget(linear_group)
        main_layout.addWidget(custom_group)
        main_layout.addLayout(bottom_layout)

        self._mode_changed(0)
        self.setMinimumHeight(350)


    # ============================================================
    def _spin(self, val, mi, ma, dec):
        box = QDoubleSpinBox()
        box.setRange(mi, ma)
        box.setDecimals(dec)
        box.setValue(val)
        box.setSingleStep((ma - mi) / 200)
        return box


    # ============================================================
    # 模式切换
    # ============================================================
    def _mode_changed(self, idx):
        self.linear_group.setVisible(idx == 0)
        self.custom_group.setVisible(idx == 1)


    # ============================================================
    # CSV 选择
    # ============================================================
    def _choose_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择摩擦 CSV 文件", ".", "CSV Files (*.csv)")
        if not path:
            return

        try:
            df = pd.read_csv(path)
            if not {"theta", "tau_fric"}.issubset(df.columns):
                raise Exception("CSV 必须包含列：theta, tau_fric")

            self.theta_arr = df["theta"].astype(float).values
            self.tau_arr = df["tau_fric"].astype(float).values
            self.selected_csv_path = path
            self.csv_path_edit.setText(path)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"CSV 加载失败：\n{e}")


    # ============================================================
    # 图像预览（动态展开）
    # ============================================================
    def _preview_plot(self):
        if self.theta_arr is None:
            QMessageBox.warning(self, "无数据", "请先选择 CSV 文件")
            return

        # 首次创建 Canvas
        if not self.canvas_created:
            self.fig = Figure(figsize=(4, 3), dpi=100)
            self.canvas = FigureCanvas(self.fig)
            self.ax = self.fig.add_subplot(111)

            self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.plot_layout.addWidget(self.canvas)

            self.plot_container.setVisible(True)
            self.canvas_created = True

            # 自动扩展窗口
            self.setMinimumHeight(600)
            self.adjustSize()

        self.ax.clear()
        self.ax.plot(self.theta_arr, self.tau_arr, marker="o")
        self.ax.set_xlabel("θ (rad)")
        self.ax.set_ylabel("τ_fric (N·m)")
        self.ax.grid(True)

        self.fig.tight_layout()
        self.canvas.draw()


    def _preview_interp(self):
        if self.theta_arr is None:
            QMessageBox.warning(self, "无数据", "请先选择 CSV 文件")
            return

        # 创建画布（与 _preview_plot 共用）
        if not self.canvas_created:
            self.fig = Figure(figsize=(4, 3), dpi=100)
            self.canvas = FigureCanvas(self.fig)
            self.ax = self.fig.add_subplot(111)

            self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.plot_layout.addWidget(self.canvas)

            self.plot_container.setVisible(True)
            self.canvas_created = True

            self.setMinimumHeight(600)
            self.adjustSize()

        # 清空图像
        self.ax.clear()

        # -------------------------
        # 1. 绘制原始散点
        # -------------------------
        self.ax.scatter(self.theta_arr, self.tau_arr, color="black", label="CSV")

        # -------------------------
        # 2. 选择插值方法
        # -------------------------
        method = self.combo_interp.currentText()
        if method == "线性插值":
            method_show="linear"
            f, _ = MatCalInterpBuilder.build_linear(self.theta_arr, self.tau_arr)
        elif method == "三次样条插值":
            method_show="cubic"
            f, _ = MatCalInterpBuilder.build_cubic(self.theta_arr, self.tau_arr)
        else:
            method_show="newton"
            f, _ = MatCalInterpBuilder.build_newton(self.theta_arr, self.tau_arr)

        # -------------------------
        # 3. 绘制插值曲线（1000 个点）
        # -------------------------
        xnew = np.linspace(self.theta_arr.min(), self.theta_arr.max(), 1000)
        ynew = np.array([f(x) for x in xnew])

        self.ax.plot(xnew, ynew, color="blue", label=f"{method_show}")

        # -------------------------
        # 4. 图像修饰
        # -------------------------
        self.ax.set_xlabel("θ (rad)")
        self.ax.set_ylabel("τ_fric (N·m)")
        self.ax.grid(True)
        self.ax.legend()

        self.fig.tight_layout()
        self.canvas.draw()



    # ============================================================
    # 保存
    # ============================================================
    def _save(self):
        mode = self.combo_mode.currentIndex()

        # 通用参数
        base = {
            "mech_gamma": self.input_gamma.value(),
            "mech_sigma": self.input_sigma.value(),
        }

        # ----------------- 线性模型 -----------------
        if mode == 0:
            base.update({
                "friction_model": "linear",
                "mech_fric_limit_0": self.input_fric_limit_0.value(),
                "mech_alpha": self.input_alpha.value(),
                "custom_fric_csv_path": None,
                "custom_interp_method": None,
            })
            self.config_saved.emit(base)
            self._close()
            return

        # ----------------- 自定义模型 -----------------
        if not self.selected_csv_path:
            QMessageBox.warning(self, "缺少 CSV 文件", "请选择 CSV 文件")
            return

        method = {
            "线性插值": "linear",
            "三次样条插值": "cubic",
            "牛顿插值": "newton",
        }[self.combo_interp.currentText()]

        base.update({
            "friction_model": "custom",
            "custom_fric_csv_path": self.selected_csv_path,
            "custom_interp_method": method,
            "mech_fric_limit_0": self.input_fric_limit_0.value(),
            "mech_alpha": self.input_alpha.value(),
        })

        self.config_saved.emit(base)
        self._close()


    # ============================================================
    def _cancel(self):
        if self.parent():
            self.parent().reject()

    def _close(self):
        if self.parent():
            self.parent().accept()


    # ============================================================
    # 恢复 UI 初值
    # ============================================================
    def _restore_from_previous_config(self):
        friction_model = self.current_params.get("friction_model", "linear")
        csv_path = self.current_params.get("custom_fric_csv_path")
        interp_method = self.current_params.get("custom_interp_method", "linear")

        # 动静比 & 阻尼（顶层参数）
        self.input_gamma.setValue(self.current_params.get("mech_gamma", 0.9))
        self.input_sigma.setValue(self.current_params.get("mech_sigma", 0.001))

        # 模式
        self.combo_mode.setCurrentIndex(1 if friction_model == "custom" else 0)

        # CSV
        if csv_path:
            self.csv_path_edit.setText(csv_path)
            self.selected_csv_path = csv_path
            try:
                df = pd.read_csv(csv_path)
                self.theta_arr = df["theta"].values
                self.tau_arr = df["tau_fric"].values
            except:
                pass

        # 插值方式
        idx_map = {"linear": 0, "cubic": 1, "newton": 2}
        self.combo_interp.setCurrentIndex(idx_map.get(interp_method, 0))

        # 模式刷新
        self._mode_changed(self.combo_mode.currentIndex())


