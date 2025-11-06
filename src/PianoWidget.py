# This Python file uses the following encoding: utf-8
from PySide6.QtWidgets import QWidget,QSizePolicy
from PySide6.QtGui import QPainter, QColor, QMouseEvent
from PySide6.QtCore import Qt, Signal, QObject, QRectF
from typing import Dict, Optional, List, Tuple

from PianoGenerator import KeyColor


# ----------------- 信号定义 -----------------
class PianoSignals(QObject):
    """用于发出交互事件的信号"""
    key_clicked = Signal(str)  # 发出被点击的音名 (e.g., "A4")

# ----------------- 钢琴绘图组件 -----------------
class PianoWidget(QWidget):
    """Keyscape风格88键钢琴绘图组件"""
    # 声明自定义信号
    key_clicked = Signal(str)

    def __init__(self, piano_generator, parent=None):
        super().__init__(parent)
        self.piano_generator = piano_generator
        self.target_note_name: Optional[str] = None
        self.detected_note_name: Optional[str] = None # 用于实时反馈音高

        # 尺寸参数（适配组件大小）
        self.key_scale_factor = 1.0
        self.white_key_width_scaled = 0.0
        self.white_key_height_scaled = 0.0
        self.key_rects: Dict[str, QRectF] = {} # 存储键的绘制区域

        # 允许接收鼠标点击事件
        self.setMouseTracking(False)
        self.setMinimumHeight(150)
        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding # QSizePolicy 需在主文件中导入
        )


    def resizeEvent(self, event):
        """窗口大小改变时重新计算键的尺寸和位置"""
        self._calculate_key_dimensions()
        super().resizeEvent(event)

    def set_piano_generator(self, new_generator):
        """
        接收新的 PianoGenerator 实例并更新内部状态。
        这是解决 UI 引用滞后问题的关键。
        """
        self.piano_generator = new_generator
        # 1. 重新计算所有键的绘制区域 (因为新的生成器可能有不同的音名)
        self._calculate_key_dimensions()
        # 2. 清除旧的高亮状态
        self.clear_highlights()
        # 3. 强制重绘
        self.update()


    def clear_highlights(self):
        """清除所有高亮状态"""
        self.target_note_name = None
        self.detected_note_name = None
        self.update()

    def _calculate_key_dimensions(self):
        """根据当前组件尺寸计算键的实际绘制尺寸"""
        if not self.piano_generator:
            return

        # 1. 确定整体缩放因子
        total_white_keys = self.piano_generator.get_key_count()[0]

        # 绘制区域宽度
        widget_width = self.width() - 10 # 留出一点边距
        widget_height = self.height() - 10 # 留出一点边距

        # 白键绘制宽度: 组件宽度 / 白键总数
        self.white_key_width_scaled = widget_width / total_white_keys
        self.white_key_height_scaled = widget_height

        # 计算黑键尺寸
        black_key_width = self.white_key_width_scaled * 0.6
        black_key_height = self.white_key_height_scaled * 0.65

        self.key_rects.clear()

        white_key_index = 0

        # 2. 遍历所有键计算绘制区域 (QRectF)
        for key_id in sorted(self.piano_generator.keys.keys()):
            key_data = self.piano_generator.keys[key_id]

            if key_data.color == KeyColor.WHITE:
                x = white_key_index * self.white_key_width_scaled
                y = 0.0
                rect = QRectF(x, y, self.white_key_width_scaled, self.white_key_height_scaled)
                self.key_rects[key_data.note_name] = rect
                white_key_index += 1

            elif key_data.color == KeyColor.BLACK:
                # 定位黑键。使用白键的索引，并进行偏移
                # 找到该黑键前一个白键的索引（因为黑键画在两个白键之间）
                midi_before = key_data.midi_number - 1
                key_before = self.piano_generator.get_key_by_midi(midi_before)
                if key_before and key_before.color == KeyColor.WHITE:
                    # 找到前一个白键的索引
                    key_index_before = [k.note_name for k in self.piano_generator.keys.values()
                                        if k.color == KeyColor.WHITE and k.midi_number < key_data.midi_number].index(key_before.note_name)

                    # 绘制位置在白键中间偏右一点 (0.5 - 0.25 = 0.25)
                    x_base = key_index_before * self.white_key_width_scaled
                    x = x_base + self.white_key_width_scaled - black_key_width / 2.0

                    y = 0.0
                    rect = QRectF(x, y, black_key_width, black_key_height)
                    self.key_rects[key_data.note_name] = rect


    def paintEvent(self, event):
        """绘制钢琴键盘"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self.piano_generator:
            # 绘制提示信息，确保用户知道原因
            painter.setPen(QColor(255, 0, 0))
            painter.drawText(self.rect(), Qt.AlignCenter, "钢琴数据加载失败，请检查 PianoGenerator 模块")
            return

        # 1. 绘制白键 (先绘制白键作为背景)
        white_keys_to_draw = [k for k in self.piano_generator.keys.values() if k.color == KeyColor.WHITE]
        for key_data in white_keys_to_draw:
            rect = self.key_rects.get(key_data.note_name)
            if rect:
                # 默认颜色
                color = QColor(250, 250, 250)
                # 实时反馈高亮 (黄色)
                if key_data.note_name == self.detected_note_name:
                    color = QColor(255, 230, 100)
                # 目标键高亮 (绿色) - 优先级低于实时反馈
                elif key_data.note_name == self.target_note_name:
                    color = QColor(60, 180, 75)

                painter.fillRect(rect, color)
                painter.drawRect(rect)

                # # 绘制音名 C/F/A
                # if key_data.note_name.startswith('C') or key_data.note_name.startswith('F') or key_data.note_name.startswith('A'):
                #     painter.setPen(QColor(50, 50, 50))
                #     # 绘制在底部
                #     painter.drawText(rect.adjusted(0, rect.height() - 20, 0, 0),
                #                      Qt.AlignCenter, key_data.note_name)
                # 绘制音名 C
                if key_data.note_name.startswith('C'):
                    painter.setPen(QColor(50, 50, 50))
                    # 绘制在底部
                    painter.drawText(rect.adjusted(0, rect.height() - 20, 0, 0),
                                     Qt.AlignCenter, key_data.note_name)


        # 2. 绘制黑键 (后绘制黑键，覆盖在白键上方)
        black_keys_to_draw = [k for k in self.piano_generator.keys.values() if k.color == KeyColor.BLACK]
        for key_data in black_keys_to_draw:
            rect = self.key_rects.get(key_data.note_name)
            if rect:
                # 默认颜色
                color = QColor(25, 25, 25)
                # 实时反馈高亮 (黄色)
                if key_data.note_name == self.detected_note_name:
                    color = QColor(255, 230, 100)
                # 目标键高亮 (绿色)
                elif key_data.note_name == self.target_note_name:
                    color = QColor(60, 180, 75)

                painter.fillRect(rect, color)
                painter.setPen(QColor(100, 100, 100))
                painter.drawRect(rect)

    def mousePressEvent(self, event: QMouseEvent):
        """处理鼠标点击事件，用于选择目标键"""
        if not self.piano_generator:
            return
        if event.button() == Qt.LeftButton:
            pos = event.pos()

            # 必须先检查黑键（因为它在视觉上覆盖了白键的一部分）
            keys_to_check = sorted(self.piano_generator.keys.values(), key=lambda k: k.color == KeyColor.BLACK, reverse=True)

            for key_data in keys_to_check:
                rect = self.key_rects.get(key_data.note_name)
                if rect and rect.contains(pos):
                    # 找到被点击的键
                    self.target_note_name = key_data.note_name
                    self.key_clicked.emit(key_data.note_name)
                    self.update() # 触发重绘以高亮新目标
                    break

# --- 公共设置方法 ---

    def set_target_note(self, note_name: str):
        """设置调律目标键并触发重绘"""
        self.target_note_name = note_name
        self.update()

    def set_detected_note(self, note_name: str):
        """设置实时检测到的音高并触发重绘"""
        self.detected_note_name = note_name
        self.update()
