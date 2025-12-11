
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox,
    QPushButton, QFileDialog, QMessageBox, QComboBox, QProgressDialog
)
from PySide6.QtCore import Qt
import numpy as np
import csv

from RightMechanicsPanel import RightMechanicsPanel   # 用于 set_target_key
from PianoGenerator import PianoKey

class ExportRepairTimeDialog(QDialog):
    """
    导出修复时间（增强版）
    支持：
        - 单键导出（二位格式）
        - 批量导出
        - 键位选择
    """

    def __init__(self, piano_generator, main_right_panel,current_key_id,db_manager, parent=None):
        super().__init__(parent)

        # 主界面正在使用的 MechanicsEngine（当前键）
        self.main_right_panel = main_right_panel
        self.mechanics = main_right_panel.mechanics

        # 键盘
        self.piano = piano_generator   # PianoGenerator
        self.current_key_id=current_key_id
        self.db_manager=db_manager

        # 隐藏版 right_mech，用来切换键位、计算
        self.hidden_panel = RightMechanicsPanel(None)
        self.hidden_panel.setVisible(False)

        self.setWindowTitle("导出修复时间")
        self.setMinimumWidth(450)

        self._build_ui()

    # --------------------------------------------------------
    # 构建 UI
    # --------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)

        # -------------------------------
        # 键位选择
        # -------------------------------
        hkey = QHBoxLayout()
        hkey.addWidget(QLabel("选择键位："))

        self.combo_key = QComboBox()
        for key_id, key in self.piano.keys.items():
            self.combo_key.addItem(f"{key.note_name} ({key_id})", key_id)

        # 默认同步到主界面当前键
        current_id = self.current_key_id
        idx = self.combo_key.findData(current_id)
        if idx >= 0:
            self.combo_key.setCurrentIndex(idx)

        hkey.addWidget(self.combo_key)
        layout.addLayout(hkey)

        # -------------------------------
        # 力矩
        # -------------------------------
        h_torque = QHBoxLayout()
        h_torque.addWidget(QLabel("预定义力矩 (N·m):"))
        self.spin_torque = QDoubleSpinBox()
        self.spin_torque.setRange(0.01, 10000000)
        self.spin_torque.setValue(self.main_right_panel.predefined_force)
        self.spin_torque.setDecimals(4)
        h_torque.addWidget(self.spin_torque)
        layout.addLayout(h_torque)

        # -------------------------------
        # 范围 + 步长
        # -------------------------------
        h_range = QHBoxLayout()
        h_range.addWidget(QLabel("音分范围 ±cent:"))
        self.spin_range = QDoubleSpinBox()
        self.spin_range.setRange(0.1, 20.0)
        self.spin_range.setValue(10.0)
        self.spin_range.setDecimals(2)
        h_range.addWidget(self.spin_range)
        layout.addLayout(h_range)

        h_step = QHBoxLayout()
        h_step.addWidget(QLabel("步长 (cent):"))
        self.spin_step = QDoubleSpinBox()
        self.spin_step.setRange(0.1, 5.0)
        self.spin_step.setValue(0.5)
        self.spin_step.setDecimals(3)
        h_step.addWidget(self.spin_step)
        layout.addLayout(h_step)

        # -------------------------------
        # dt + 最大模拟时间
        # -------------------------------
        h_dt = QHBoxLayout()
        h_dt.addWidget(QLabel("时间步长 dt (s):"))
        self.spin_dt = QDoubleSpinBox()
        self.spin_dt.setRange(0.001, 0.1)
        self.spin_dt.setValue(self.mechanics.repair_simulation_dt)
        self.spin_dt.setDecimals(5)
        h_dt.addWidget(self.spin_dt)
        layout.addLayout(h_dt)

        h_maxt = QHBoxLayout()
        h_maxt.addWidget(QLabel("最大模拟时间 (s):"))
        self.spin_maxtime = QDoubleSpinBox()
        self.spin_maxtime.setRange(5.0, 20000.0)
        self.spin_maxtime.setValue(self.mechanics.max_repair_time)
        self.spin_maxtime.setDecimals(1)
        h_maxt.addWidget(self.spin_maxtime)
        layout.addLayout(h_maxt)

        # -------------------------------
        # 按钮
        # -------------------------------
        btn_single = QPushButton("导出单键")
        btn_single.clicked.connect(self.export_single_csv)

        btn_multi = QPushButton("批量导出")
        btn_multi.clicked.connect(self.export_multi_csv)

        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(self.close)

        h_btn = QHBoxLayout()
        h_btn.addWidget(btn_single)
        h_btn.addWidget(btn_multi)
        h_btn.addWidget(btn_close)

        layout.addLayout(h_btn)

    # --------------------------------------------------------
    # 单键计算
    # --------------------------------------------------------
    def compute_one_key(self, key_id):
        """
        返回二维: [cent], [repair_time]
        """
        # 同步 mechanics 参数
        self.hidden_panel.mechanics.copy_from(self.mechanics)

        # 切键
        self.hidden_panel.set_target_key(self.db_manager,self.piano.get_key_by_midi(key_id+self.piano.start_midi))

        mech = self.hidden_panel.mechanics

        mech.repair_simulation_dt = self.spin_dt.value()
        mech.max_repair_time = self.spin_maxtime.value()

        max_torque = self.spin_torque.value()
        self.hidden_panel.predefined_force=self.spin_torque.value()
        cent_range = self.spin_range.value()
        step = self.spin_step.value()

        cents_list = np.arange(-cent_range, cent_range + step, step)

        f0 = self.hidden_panel.target_freq
        if f0 <= 0:
            return None, None

        times = []
        for c in cents_list:
            f_bias = f0 * (2 ** (c / 1200))
            self.hidden_panel.set_current_frequency(f_bias)
            theta_target = mech.calculate_theta_for_frequency(f0)
            t = mech.calculate_repair_time(theta_target, max_torque)
            times.append(t)

        return cents_list, times

    # --------------------------------------------------------
    # 单键导出 —— 二维格式
    # --------------------------------------------------------
    def export_single_csv(self):
        key_id = self.combo_key.currentData()
        key_name = self.piano.keys[key_id].note_name

        cents_list, times = self.compute_one_key(key_id)
        if cents_list is None:
            QMessageBox.warning(self, "错误", "无法计算（频率为0）")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "保存 CSV", f"repair_{key_name}_{self.hidden_panel.predefined_force}Nm.csv", "CSV Files (*.csv)"
        )
        if not path:
            return

        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["cent", key_name])
            for c, t in zip(cents_list, times):
                w.writerow([c, t])

        QMessageBox.information(self, "完成", f"单键{self.piano.keys[self.combo_key.itemData(self.combo_key.currentIndex())].note_name}已导出：\n{path}")

    # --------------------------------------------------------
    # 批量导出（二维表）
    # --------------------------------------------------------
    def export_multi_csv(self):
        start_idx = self.combo_key.currentIndex()
        #start_key_id = self.combo_key.itemData(start_idx)
        start_key_id=0
        self.hidden_panel.predefined_force=self.spin_torque.value()
        self.mechanics.repair_simulation_dt=self.spin_dt.value()
        self.mechanics.max_repair_time=self.spin_maxtime.value()

        # 准备路径
        path, _ = QFileDialog.getSaveFileName(
            self, "保存二维 CSV", f"repair_all_keys_{self.hidden_panel.predefined_force}Nm.csv", "CSV Files (*.csv)"
        )
        if not path:
            return

        # 音分点
        cent_range = self.spin_range.value()
        step = self.spin_step.value()
        cents_list = np.arange(-cent_range, cent_range + step, step)

        # 进度条
        prog = QProgressDialog("计算中，请稍候...", "取消", 0, 88 - start_key_id, self)
        prog.setWindowModality(Qt.WindowModal)
        prog.setMinimumDuration(0)

        # 写入
        with open(path, "w", newline="") as f:
            w = csv.writer(f)

            # 表头
            header = ["cent"]
            for key_id in range(start_key_id, 88):
                header.append(self.piano.keys[key_id].note_name)
            w.writerow(header)

            # 初始化二维表（行 = cents）
            rows = {c: [c] + [None] * (88 - start_key_id) for c in cents_list}

            progress = 0
            for key_id in range(start_key_id, 88):
                if prog.wasCanceled():
                    break

                cents, times = self.compute_one_key(key_id)
                if cents is None:
                    continue

                # 写入行
                for i, c in enumerate(cents):
                    rows[c][1 + (key_id - start_key_id)] = times[i]

                progress += 1
                prog.setValue(progress)

            # 输出
            for c in cents_list:
                w.writerow(rows[c])

        prog.close()
        QMessageBox.information(self, "完成", f"批量修复时间已导出：\n{path}")

