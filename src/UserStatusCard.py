from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QGridLayout, QProgressBar, QPushButton, QTextEdit, QDialog,QSizePolicy
)
from PySide6.QtGui import QFont, QColor, QPalette,QTextCursor
from PySide6.QtCore import Qt

class UserStatusCard(QFrame):
    """
    用户态系统状态卡片：
    显示：
        - 输入设备
        - 分析模式
        - 音高算法
        - 当前目标
        - 当前频率
        - 音分偏差
        - 置信度
        - 文件分析进度（仅文件分析时显示/变色）
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("UserStatusCard")
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setMinimumHeight(200)

        # 外观样式（卡片风）
        self.setStyleSheet("""
        QFrame#UserStatusCard {
            background-color: #f7f8fa;
            border: 1px solid #d0d7de;
            border-radius: 8px;
        }
        QLabel.status-title {
            font-size: 13px;
            font-weight: 600;
            color: #1f2328;
        }
        QLabel.status-key {
            color: #6e7781;
        }
        QLabel.status-value {
            color: #24292f;
            font-weight: 500;
        }
        QLabel.status-message {
            color: #57606a;
        }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # 标题
        title_label = QLabel("系统状态概览")
        title_label.setProperty("class", "status-title")
        title_label.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        main_layout.addWidget(title_label)

        # 信息表格（左键名，右数值）
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(4)

        def make_key_label(text: str) -> QLabel:
            lab = QLabel(text)
            lab.setProperty("class", "status-key")
            lab.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            return lab

        def make_value_label(text: str = "--") -> QLabel:
            lab = QLabel(text)
            lab.setProperty("class", "status-value")
            lab.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            return lab

        row = 0
        grid.addWidget(make_key_label("输入设备:"), row, 0)
        self.lbl_input_device = make_value_label("默认输入设备")
        grid.addWidget(self.lbl_input_device, row, 1)

        row += 1
        grid.addWidget(make_key_label("分析模式:"), row, 0)
        self.lbl_mode = make_value_label("实时分析")
        grid.addWidget(self.lbl_mode, row, 1)

        row += 1
        grid.addWidget(make_key_label("音高算法:"), row, 0)
        self.lbl_algorithm = make_value_label("--")
        grid.addWidget(self.lbl_algorithm, row, 1)

        row += 1
        grid.addWidget(make_key_label("当前目标:"), row, 0)
        self.lbl_target = make_value_label("A4 (440.00 Hz)")
        grid.addWidget(self.lbl_target, row, 1)

        row += 1
        grid.addWidget(make_key_label("当前频率:"), row, 0)
        self.lbl_current_freq = make_value_label("-- Hz")
        grid.addWidget(self.lbl_current_freq, row, 1)

        row += 1
        grid.addWidget(make_key_label("音分偏差:"), row, 0)
        self.lbl_cents = make_value_label("-- cents")
        grid.addWidget(self.lbl_cents, row, 1)

        row += 1
        grid.addWidget(make_key_label("置信度:"), row, 0)
        self.lbl_confidence = make_value_label("--")
        grid.addWidget(self.lbl_confidence, row, 1)

        main_layout.addLayout(grid)

        # 状态消息（短文本）
        self.lbl_status_msg = QLabel("状态: 等待开始")
        self.lbl_status_msg.setProperty("class", "status-message")
        self.lbl_status_msg.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # === 加入宽度限制，防止把左面板撑宽 ===
        self.lbl_status_msg.setWordWrap(True)              # 自动换行
        self.lbl_status_msg.setMaximumWidth(240)           # ⭐ 根据左侧面板宽度调整
        self.lbl_status_msg.setMinimumWidth(200)           # 保持布局稳定
        self.lbl_status_msg.setSizePolicy(
           QSizePolicy.Preferred,
           QSizePolicy.Minimum
        )
        # ============================================

        main_layout.addWidget(self.lbl_status_msg)

        # 底部进度条（默认灰色，仅文件分析时显示&变色）
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("文件分析进度: %p%")
        self.progress_bar.setVisible(False)  # 初始隐藏

        # 默认灰色样式
        self._inactive_style = """
        QProgressBar {
            border: 1px solid #d0d7de;
            border-radius: 4px;
            background: #f0f1f3;
            text-align: center;
            font-size: 10px;
        }
        QProgressBar::chunk {
            background-color: #c8ccd1;
        }
        """
        # 激活时样式（蓝色）
        self._active_style = """
        QProgressBar {
            border: 1px solid #409EFF;
            border-radius: 4px;
            background: #ecf5ff;
            text-align: center;
            font-size: 10px;
        }
        QProgressBar::chunk {
            background-color: #409EFF;
        }
        """
        self.progress_bar.setStyleSheet(self._inactive_style)

        main_layout.addWidget(self.progress_bar)

    # ========= 对外接口（给 MainWindow 调用）=========

    def set_input_device(self, name: str):
        self.lbl_input_device.setText(name or "默认输入设备")

    def set_mode(self, text: str):
        self.lbl_mode.setText(text)

    def set_algorithm(self, algo_str: str):
        self.lbl_algorithm.setText(algo_str)

    def set_target(self, note_name: str, freq: float):
        if freq is not None:
            self.lbl_target.setText(f"{note_name} ({freq:.2f} Hz)")
        else:
            self.lbl_target.setText(note_name)

    def update_realtime(self, freq: float, target_freq: float, cents: float, confidence: float):
        if freq is not None:
            self.lbl_current_freq.setText(f"{freq:.2f} Hz")
        else:
            self.lbl_current_freq.setText("-- Hz")

        if cents is not None:
            self.lbl_cents.setText(f"{cents:+.2f} cents")
        else:
            self.lbl_cents.setText("-- cents")

        if confidence is not None:
            self.lbl_confidence.setText(f"{confidence:.2f}")
        else:
            self.lbl_confidence.setText("--")

    def set_status_message(self, message: str):
        self.lbl_status_msg.setText(f"状态: {message}")

    def set_progress_active(self, active: bool):
        if active:
            self.progress_bar.setStyleSheet(self._active_style)
        else:
            self.progress_bar.setStyleSheet(self._inactive_style)
            self.progress_bar.setValue(0)

    def show_progress(self, visible: bool):
        self.progress_bar.setVisible(visible)



# class DebugStatusWindow(QDialog):
#     """
#     原来的 QTextEdit 状态窗口，完整迁移到这里，用于调试。
#     文本逻辑沿用你原来的 “替换 • 状态 行” 的规则。
#     """

#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setWindowTitle("调试状态 - 系统日志")
#         self.resize(520, 360)

#         layout = QVBoxLayout(self)
#         self.text_edit = QTextEdit(self)
#         self.text_edit.setReadOnly(True)

#         # 原始状态文本（完全照搬你之前的初始化内容）
#         self.text_edit.setPlainText("""📊 当前状态
# • 模式: 实时分析
# • 状态: 等待开始
# • 设备: 默认麦克风
# • 算法: 自适应

# 💡 调音建议
# • 准备开始音频检测...

# ⚙️ 参数预览
# • 目标频率: A4 (440Hz)
# • 检测算法: 自适应
# • 灵敏度: 中
# • 置信度: --""")

#         layout.addWidget(self.text_edit)

#     def apply_status_update_logic(self, message: str):
#         """
#         完整复刻原来的 _apply_status_update_logic 逻辑，
#         只是把 self.status_display 换成 self.text_edit。
#         """
#         current_text = self.text_edit.toPlainText()
#         lines = current_text.split('\n')

#         found = False
#         for i, line in enumerate(lines):
#             if line.strip().startswith('• 状态:'):
#                 lines[i] = f"• 状态: {message}"
#                 found = True
#                 break

#         if not found:
#             lines.append(f"• 状态: {message}")

#         # 只保留 10 行状态信息（保留你原来的思路）
#         status_lines = [
#             line for line in lines
#             if not line.strip().startswith('• 状态:')
#             and not line.strip().startswith('💡')
#             and not line.strip().startswith('⚙️')
#         ]
#         status_lines.insert(1, f"• 状态: {message}")  # 插入新状态

#         new_text = '\n'.join(status_lines[:10])
#         self.text_edit.setPlainText(new_text)


class DebugStatusWindow(QDialog):
    """
    调试状态窗口（追加日志版本）
    每次更新状态消息时，不再覆盖，而是追加一条日志。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("调试状态 - 系统日志")
        self.resize(520, 360)

        layout = QVBoxLayout(self)
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)

        # 初始内容（可保留）
        self.text_edit.setPlainText("📊 调试日志开始\n")

        layout.addWidget(self.text_edit)

    def append_log(self, message: str):
        """
        追加一条日志
        格式：
            [HH:MM:SS] 内容
        """

        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")

        self.text_edit.append(f"[{timestamp}] {message}")

        # 自动滚动到底部
        # self.text_edit.moveCursor(self.text_edit.textCursor().End)
        # 自动滚动到底部
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.text_edit.setTextCursor(cursor)

    # 兼容旧接口（MainWindow 仍调用 apply_status_update_logic）
    def apply_status_update_logic(self, message: str):
        self.append_log(message)

    def closeEvent(self, event):
        if self.parent() and hasattr(self.parent(), "action_show_debug_status"):
            self.parent().action_show_debug_status.setChecked(False)
        super().closeEvent(event)



