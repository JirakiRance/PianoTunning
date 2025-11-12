# from PySide6.QtWidgets import QWidget
# from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont
# from PySide6.QtCore import Qt, QPointF, QTimer
# import math


# class TuningDialWidget2(QWidget):
#     """
#     扇形音高指示仪 (Dial Gauge)
#     -------------------------------------
#     - 类似万用表指针仪表
#     - 中心频率为目标频率
#     - 左右 ±range_cents 表示音分偏差
#     - 动态指针指示当前频率偏差
#     """

#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.current_freq = 440.0
#         self.target_freq = 440.0
#         self.range_cents = 50.0  # ±范围 (音分)
#         self.current_angle = 0.0
#         self.display_angle = 0.0  # 用于平滑动画

#         # 外观设置
#         self.arc_span_deg = 120     # 扇形总角度
#         self.pointer_color = QColor(200, 60, 60)
#         self.bg_color = QColor(245, 245, 250)
#         self.tick_color = QColor(120, 120, 140)
#         self.label_color = QColor(70, 70, 90)

#         # 平滑动画计时器
#         self.smooth_timer = QTimer(self)
#         self.smooth_timer.timeout.connect(self._update_smooth)
#         self.smooth_timer.start(16)  # 60Hz刷新

#     # ======================== 外部接口 ========================

#     def set_frequencies(self, current_freq: float, target_freq: float):
#         """设置当前和目标频率"""
#         self.current_freq = max(1e-6, current_freq)
#         self.target_freq = max(1e-6, target_freq)

#         # 计算音分偏差 Δcents
#         delta_cents = 1200.0 * math.log2(self.current_freq / self.target_freq)
#         delta_cents = max(-self.range_cents, min(self.range_cents, delta_cents))

#         # 映射到角度（左负右正）
#         self.current_angle = (delta_cents / self.range_cents) * (self.arc_span_deg / 2)
#         self.update()

#     def set_range(self, range_cents: float):
#         """设置扇形显示的量程范围（单位：音分）"""
#         self.range_cents = max(10.0, range_cents)
#         self.update()

#     # ======================== 平滑更新 ========================

#     def _update_smooth(self):
#         """指针角度平滑插值"""
#         diff = self.current_angle - self.display_angle
#         self.display_angle += diff * 0.15  # 趋近系数（越小越稳）
#         self.update()

#     # ======================== 绘制部分 ========================

#     def paintEvent(self, event):
#         painter = QPainter(self)
#         painter.setRenderHint(QPainter.RenderHint.Antialiasing)
#         rect = self.rect()
#         center = rect.center()

#         # 半径区域
#         radius = min(rect.width(), rect.height()) * 0.45
#         arc_rect = rect.center().x() - radius, rect.center().y() - radius, 2 * radius, 2 * radius

#         # 背景
#         painter.fillRect(rect, self.bg_color)

#         # 绘制扇形刻度
#         self._draw_scale(painter, center, radius)

#         # 绘制指针
#         self._draw_pointer(painter, center, radius)

#         # 绘制标签
#         self._draw_labels(painter, center, radius)

#     def _draw_scale(self, painter, center, radius):
#         """绘制弧形刻度线"""
#         painter.save()
#         painter.translate(center)
#         painter.rotate(-self.arc_span_deg / 2)
#         num_ticks = 10
#         tick_len = 10

#         for i in range(num_ticks + 1):
#             angle = i * (self.arc_span_deg / num_ticks)
#             painter.save()
#             painter.rotate(angle)
#             painter.setPen(QPen(self.tick_color, 2))
#             painter.drawLine(0, -radius + 8, 0, -radius + 8 + tick_len)
#             painter.restore()
#         painter.restore()

#         # 绘制弧形边界
#         painter.setPen(QPen(QColor(180, 180, 200), 3))
#         painter.drawArc(
#             rect=self.rect().adjusted(10, 10, -10, -10),
#             startAngle=int((90 + self.arc_span_deg / 2) * 16),
#             spanAngle=int(-self.arc_span_deg * 16)
#         )

#     def _draw_pointer(self, painter, center, radius):
#         """绘制指针"""
#         painter.save()
#         painter.translate(center)
#         painter.rotate(self.display_angle)
#         painter.setPen(QPen(self.pointer_color, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
#         painter.drawLine(0, 0, 0, -radius * 0.8)
#         painter.restore()

#         # 中心圆
#         painter.setBrush(self.pointer_color)
#         painter.setPen(Qt.PenStyle.NoPen)
#         painter.drawEllipse(center, 6, 6)

#     def _draw_labels(self, painter, center, radius):
#         """绘制文本标签"""
#         painter.setPen(self.label_color)
#         painter.setFont(QFont("Microsoft YaHei", 10))

#         # 当前频率
#         painter.drawText(self.rect(), Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
#                          f"{self.current_freq:.2f} Hz")

#         # 中心标题
#         painter.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
#         painter.drawText(self.rect(), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
#                          "音高偏差指示仪")

#         # 左右端标注 ±音分
#         painter.setFont(QFont("Microsoft YaHei", 9))
#         painter.drawText(self.rect().adjusted(20, 0, 0, 0),
#                          Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
#                          f"-{int(self.range_cents)}¢")
#         painter.drawText(self.rect().adjusted(0, 0, -20, 0),
#                          Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
#                          f"+{int(self.range_cents)}¢")



from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from PySide6.QtCore import Qt, QPointF, QTimer, QRectF
import math

class TuningDialWidget2(QWidget):
    """
    扇形音高指示仪 (Dial Gauge) - 优化版
    -------------------------------------
    - 类似万用表指针仪表
    - 中心频率为目标频率
    - 左右 ±range_cents 表示音分偏差
    - 动态指针指示当前频率偏差
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_freq = 440.0
        self.target_freq = 440.0
        self.range_cents = 50.0  # ±范围 (音分)
        self.current_angle = 0.0
        self.display_angle = 0.0  # 用于平滑动画

        # 外观设置
        self.arc_span_deg = 180     # 扇形总角度 (改为180度，更像万用表)
        self.pointer_color = QColor(255, 0, 0) # 更鲜艳的指针
        self.bg_color = QColor(245, 245, 250)
        self.scale_bg_color = QColor(230, 230, 235) # 仪表盘背景色
        self.tick_color = QColor(120, 120, 140)
        self.label_color = QColor(40, 40, 60)

        # 尺寸策略
        self.setMinimumSize(200, 150)

        # 平滑动画计时器
        self.smooth_timer = QTimer(self)
        self.smooth_timer.timeout.connect(self._update_smooth)
        self.smooth_timer.start(16)  # 60Hz刷新

    # ======================== 外部接口 ========================

    def set_frequencies(self, current_freq: float, target_freq: float):
        """设置当前和目标频率"""
        self.current_freq = max(1e-6, current_freq)
        self.target_freq = max(1e-6, target_freq)

        # 计算音分偏差 Δcents
        delta_cents = 1200.0 * math.log2(self.current_freq / self.target_freq)
        # delta_cents = max(-self.range_cents, min(self.range_cents, delta_cents))
        if abs(delta_cents)>self.range_cents:
            delta_cents=delta_cents/(abs(delta_cents))*self.range_cents

        # # 映射到角度（左负右正）
        # self.current_angle = (delta_cents / self.range_cents) * (self.arc_span_deg / 2)
        # # self.update() # 由定时器触发更新
        self.set_cents(delta_cents) # 调用新方法处理音分和更新

    def set_cents(self, delta_cents: float):
        """
        直接设置音分偏差，用于快速更新指针。
        注意：这不会更新显示的 current_freq 和 target_freq 文本标签。
        """
        # 限制音分偏差在量程内
        delta_cents = max(-self.range_cents, min(self.range_cents, delta_cents))

        # 映射到角度（左负右正）
        self.current_angle = (delta_cents / self.range_cents) * (self.arc_span_deg / 2)
        # 此时无法更新底部的频率显示，所以我们保持 target_freq 不变，
        # 并基于音分偏差计算一个“虚拟”的 current_freq 用于显示
        self.current_freq = self.target_freq * (2 ** (delta_cents / 1200.0))

        self.update()

    def set_range(self, range_cents: float):
        """设置扇形显示的量程范围（单位：音分）"""
        self.range_cents = max(10.0, range_cents)
        self.update()

    # ======================== 平滑更新 ========================

    def _update_smooth(self):
        """指针角度平滑插值"""
        diff = self.current_angle - self.display_angle
        self.display_angle += diff * 0.15  # 趋近系数（越小越稳）
        # 如果接近目标，停止更新，节省资源
        if abs(diff) > 0.01:
             self.update()

    # ======================== 绘制部分 ========================

    # def paintEvent(self, event):
    #     painter = QPainter(self)
    #     painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    #     rect = self.rect()
    #     center = rect.center()

    #     # 计算绘制半径
    #     radius = min(rect.width(), rect.height() * 2) * 0.45

    #     # 绘制背景
    #     painter.fillRect(rect, self.bg_color)

    #     # 绘制扇形背景
    #     self._draw_arc_background(painter, center, radius)

    #     # 绘制刻度线和数字标签 (刻度盘)
    #     self._draw_scale(painter, center, radius)

    #     # 绘制指针
    #     self._draw_pointer(painter, center, radius)

    #     # 绘制文本标签
    #     self._draw_labels(painter, center, radius)

    # def _draw_arc_background(self, painter, center, radius):
    #     """绘制仪表盘的扇形背景"""
    #     painter.save()

    #     # 绘制底色扇形
    #     painter.setBrush(QBrush(self.scale_bg_color))
    #     painter.setPen(Qt.PenStyle.NoPen)

    #     # PySide6/Qt 绘制扇形角度是 1/16 度，从 3点钟方向 (0度) 开始，逆时针为正
    #     # 我们从左边底部开始 (90 + span/2) 逆时针画 span 度
    #     start_angle = int((90 + self.arc_span_deg / 2) * 16)
    #     span_angle = int(-self.arc_span_deg * 16)

    #     # 确保 rect 是 QRectF
    #     arc_rect = QRectF(center.x() - radius, center.y() - radius, 2 * radius, 2 * radius)

    #     painter.drawPie(arc_rect, start_angle, span_angle)

    #     # 绘制弧形边界
    #     painter.setPen(QPen(QColor(180, 180, 200), 3))
    #     painter.setBrush(Qt.BrushStyle.NoBrush)
    #     painter.drawArc(arc_rect, start_angle, span_angle)

    #     painter.restore()

    # def _draw_scale(self, painter, center, radius):
    #     """绘制弧形刻度线和数字标签"""
    #     painter.save()
    #     painter.translate(center)

    #     # 刻度盘起始旋转角度：将扇形中心线对准 Y 轴负方向
    #     painter.rotate(-self.arc_span_deg / 2)

    #     # 刻度设置: 总共100个音分，我们每 10 ¢ 设一个主刻度，每 5 ¢ 设一个副刻度
    #     # 假设 range_cents 是 50.0
    #     num_main_ticks = int(self.range_cents / 10.0) * 2  # 例如 50/10 * 2 = 10个主刻度

    #     main_tick_len = 15
    #     sub_tick_len = 10

    #     # 主副刻度总数
    #     total_ticks = int(self.range_cents / 5.0) * 2 # 例如 50/5 * 2 = 20个刻度

    #     # 每个刻度间隔的角度
    #     angle_per_tick = self.arc_span_deg / total_ticks

    #     font_size = 9

    #     for i in range(total_ticks + 1):
    #         angle = i * angle_per_tick
    #         cents_value = int(i * (self.range_cents / total_ticks * 2) - self.range_cents)

    #         painter.save()
    #         painter.rotate(angle)

    #         # 判断是否为主刻度 (0, ±10, ±20, ±30, ±40, ±50)
    #         is_main_tick = (i % 2 == 0)

    #         # 区分主/副刻度
    #         if is_main_tick:
    #             tick_len = main_tick_len
    #             tick_width = 3
    #             painter.setPen(QPen(QColor(70, 70, 90), tick_width))

    #             # 绘制数字标签（只在主刻度上绘制）
    #             if abs(cents_value) > 0 or i == total_ticks / 2: # 排除中间刻度，中间刻度在_draw_labels中绘制
    #                 painter.setFont(QFont("Microsoft YaHei", font_size, QFont.Weight.Bold))

    #                 # 绘制数字标签的位置，在刻度线外侧
    #                 label_point = QPointF(0, -radius + tick_len + 5)

    #                 # 标签对齐，需要考虑旋转复原
    #                 painter.save()
    #                 painter.rotate(-angle) # 恢复旋转，使文本水平

    #                 # 计算弧度
    #                 rad = math.radians(angle - self.arc_span_deg / 2)

    #                 # 极坐标到笛卡尔坐标的转换，调整文本中心位置
    #                 text_radius = radius - main_tick_len - 10
    #                 x = text_radius * math.sin(rad)
    #                 y = -text_radius * math.cos(rad)

    #                 text_rect = QRectF(center.x() + x - 20, center.y() + y - 10, 40, 20)

    #                 # 为了居中显示，使用 QRectF 和 Flag
    #                 text_value = f"{cents_value}" if cents_value != 0 else "0"

    #                 painter.setPen(self.label_color)
    #                 painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text_value)
    #                 painter.restore()

    #         else:
    #             # 副刻度
    #             tick_len = sub_tick_len
    #             tick_width = 1
    #             painter.setPen(QPen(self.tick_color, tick_width))

    #         # 绘制刻度线
    #         painter.drawLine(0, -radius + 8, 0, -radius + 8 + tick_len)

    #         painter.restore()

    #     painter.restore()

    # def _draw_pointer(self, painter, center, radius):
    #     """绘制指针（更尖锐）"""
    #     painter.save()
    #     painter.translate(center)

    #     # 旋转指针到平滑角度
    #     painter.rotate(self.display_angle)

    #     # 指针路径 (三角形)
    #     pointer_len = radius * 0.9
    #     pointer_width = 6

    #     pointer_path = [
    #         QPointF(0, -pointer_len), # 尖端
    #         QPointF(-pointer_width/2, 0),
    #         QPointF(pointer_width/2, 0),
    #     ]

    #     # 绘制三角形指针
    #     painter.setBrush(QBrush(self.pointer_color))
    #     painter.setPen(QPen(self.pointer_color, 1))
    #     painter.drawConvexPolygon(pointer_path)

    #     # 绘制指针尾巴（从中心向下延伸）
    #     painter.setPen(QPen(self.pointer_color, 2))
    #     painter.drawLine(0, 0, 0, radius * 0.15)

    #     painter.restore()

    #     # 中心圆 (圆钉)
    #     painter.setBrush(QBrush(QColor(0, 0, 0))) # 中心圆钉用黑色
    #     painter.setPen(Qt.PenStyle.NoPen)
    #     painter.drawEllipse(center, 4, 4) # 稍微小一点

    # def _draw_labels(self, painter, center, radius):
    #     """绘制文本标签：当前频率和中心标题"""

    #     # 恢复默认字体和颜色
    #     painter.setPen(self.label_color)

    #     # 当前频率（底部）
    #     painter.setFont(QFont("Microsoft YaHei", 12))
    #     painter.drawText(self.rect().adjusted(0, 0, 0, -10),
    #                      Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
    #                      f"{self.current_freq:.2f} Hz")

    #     # 中心标题（顶部）
    #     painter.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
    #     painter.drawText(self.rect().adjusted(0, 10, 0, 0),
    #                      Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
    #                      "音高偏差指示仪 (¢)")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()

        # 1. 确定半径: 180度仪表盘的半径最大为宽度的一半和高度
        # 使用 95% 的可用空间作为半径，留出边距
        radius = min(rect.width() / 2, rect.height() - 20) * 0.95

        # 2. 确定圆心 (center): 放在底部中央，留出底部10px给频率文本
        center_x = rect.center().x()
        # 圆心Y坐标 = 底部 - 底部留白 (10)
        center_y = rect.bottom() - 10
        center = QPointF(center_x, center_y)

        # 绘制背景
        painter.fillRect(rect, self.bg_color)

        # 绘制扇形背景
        self._draw_arc_background(painter, center, radius)

        # 绘制刻度线和数字标签 (刻度盘)
        self._draw_scale(painter, center, radius)

        # 绘制指针
        self._draw_pointer(painter, center, radius)

        # 绘制文本标签
        self._draw_labels(painter, center, radius)

    def _draw_arc_background(self, painter, center, radius):
        """绘制仪表盘的扇形背景"""
        painter.save()

        # 绘制底色扇形
        painter.setBrush(QBrush(self.scale_bg_color))
        painter.setPen(Qt.PenStyle.NoPen)

        # 180度扇形：从 9点钟方向 (180度) 开始，画 180 度（逆时针为负）
        # Qt 角度是 1/16 度，从 3点钟方向 (0度) 开始，逆时针为正
        # 我们的圆心在底部，所以从 180度开始，逆时针画 -180度（即顺时针画 180度）
        start_angle = int(180 * 16)
        span_angle = int(180 * 16)

        # 确保 rect 是 QRectF
        arc_rect = QRectF(center.x() - radius, center.y() - radius, 2 * radius, 2 * radius)

        painter.drawPie(arc_rect, start_angle, span_angle)

        # 绘制弧形边界
        painter.setPen(QPen(QColor(180, 180, 200), 3))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(arc_rect, start_angle, span_angle)

        painter.restore()

    def _draw_scale(self, painter, center, radius):
        """绘制弧形刻度线和数字标签"""
        painter.save()
        painter.translate(center)

        # 刻度盘起始旋转角度：将扇形最左侧对准 Y 轴负方向
        # 180度仪表盘，起始点在水平线上，所以起始旋转 90 度
        painter.rotate(90)

        # 刻度设置
        # 假设 range_cents 是 50.0，每 10 ¢ 设一个主刻度，每 5 ¢ 设一个副刻度
        total_cents = self.range_cents * 2
        cents_per_tick = 5.0
        total_ticks = int(total_cents / cents_per_tick) # 例如 100/5 = 20个刻度

        main_tick_interval = 10.0 # 主刻度间隔 (10 ¢)

        angle_per_tick = self.arc_span_deg / total_ticks

        main_tick_len = 15
        sub_tick_len = 10
        font_size = 9

        for i in range(total_ticks + 1):
            # i 从 0 到 total_ticks (20)
            angle = i * angle_per_tick
            cents_value = int(i * cents_per_tick - self.range_cents) # 从 -50 到 +50

            painter.save()
            painter.rotate(angle)

            # 判断是否为主刻度 (0, ±10, ±20, ...)
            is_main_tick = (abs(cents_value) % main_tick_interval == 0)

            # 区分主/副刻度
            if is_main_tick:
                tick_len = main_tick_len
                tick_width = 3
                painter.setPen(QPen(QColor(70, 70, 90), tick_width))

                # 绘制数字标签（只在主刻度上绘制）
                if abs(cents_value) <= self.range_cents:
                    painter.setFont(QFont("Microsoft YaHei", font_size, QFont.Weight.Bold))

                    # 标签对齐，需要恢复旋转，使文本水平
                    painter.save()
                    # 恢复旋转，并移动到标签位置
                    painter.rotate(-angle)

                    # 极坐标到笛卡尔坐标的转换，调整文本中心位置
                    # 刻度盘从 180度到 0度（即 90度旋转了 180度）
                    rad = math.radians(angle + 90)

                    text_radius = radius - main_tick_len - 15
                    x = text_radius * math.cos(rad)
                    y = text_radius * math.sin(rad)

                    # 文本矩形 (以 center 移动为基准)
                    text_rect = QRectF(x - 20, y - 10, 40, 20)

                    text_value = f"{cents_value}" if cents_value != 0 else "0"

                    painter.setPen(self.label_color)
                    painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text_value)
                    painter.restore()

            else:
                # 副刻度
                tick_len = sub_tick_len
                tick_width = 1
                painter.setPen(QPen(self.tick_color, tick_width))

            # 绘制刻度线
            # 刻度线从半径内侧开始向外延伸
            painter.drawLine(0, radius, 0, radius - tick_len)

            painter.restore()

        painter.restore()

    def _draw_pointer(self, painter, center, radius):
        """绘制指针（更尖锐）"""
        painter.save()
        painter.translate(center)

        # 旋转指针到平滑角度 (180度仪表盘，指针在 90 度时是垂直向上)
        # painter.rotate(90 + self.display_angle)
        painter.rotate(self.display_angle-90)

        # 指针路径 (三角形)
        pointer_len = radius * 0.9
        pointer_width = 6

        pointer_path = [
            QPointF(pointer_len, 0), # 尖端 (旋转后指向刻度)
            QPointF(0, -pointer_width/2),
            QPointF(0, pointer_width/2),
        ]

        # 绘制三角形指针
        painter.setBrush(QBrush(self.pointer_color))
        painter.setPen(QPen(self.pointer_color, 1))
        painter.drawConvexPolygon(pointer_path)

        # 绘制指针尾巴（从中心向内延伸）
        painter.setPen(QPen(self.pointer_color, 2))
        painter.drawLine(0, 0, -radius * 0.15, 0)

        painter.restore()

        # 中心圆 (圆钉)
        painter.setBrush(QBrush(QColor(0, 0, 0))) # 中心圆钉用黑色
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, 4, 4) # 稍微小一点

    def _draw_labels(self, painter, center, radius):
        """绘制文本标签：当前频率和中心标题"""

        # 恢复默认字体和颜色
        painter.setPen(self.label_color)

        # 当前频率（底部）
        painter.setFont(QFont("Microsoft YaHei", 12))
        # 调整到矩形底部
        painter.drawText(self.rect().adjusted(0, 0, 0, -10),
                         Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
                         f"{self.current_freq:.2f} Hz")

        # 中心标题（顶部）
        painter.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        # 调整到矩形顶部
        painter.drawText(self.rect().adjusted(0, 10, 0, 0),
                         Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
                         "音高偏差指示仪 (¢)")

        # 左右端标注 ±音分
        painter.setFont(QFont("Microsoft YaHei", 9))

        # 左端标注: 位于 center.x() - radius 的位置
        left_text_rect = QRectF(center.x() - radius - 50, center.y() - 15, 45, 30)
        painter.drawText(left_text_rect,
                         Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                         f"-{int(self.range_cents)}¢")

        # 右端标注: 位于 center.x() + radius + 5 的位置
        right_text_rect = QRectF(center.x() + radius + 5, center.y() - 15, 45, 30)
        painter.drawText(right_text_rect,
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                         f"+{int(self.range_cents)}¢")

