# interaction_manager.py
import pygame
import math
import time
from typing import Dict, Any, Callable, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum


class InteractionMode(Enum):
    SLIDER = "slider"  # 拉条直接调整
    KNOB_DRAG = "knob_drag"  # 旋钮拖拽（左键单击后移动，释放结束）
    KNOB_WHEEL = "knob_wheel"  # 旋钮滚轮（悬停时）
    MOUSE_MOVE = "mouse_move"  # 鼠标移动（左键单击后移动，释放结束）
    KEY_PRESS = "key_press"  # 键盘长按


@dataclass
class InteractionState:
    """交互状态"""
    displacement: float = 100.0
    angle: float = 0.0
    is_dragging: bool = False
    drag_start_angle: float = 0.0
    drag_start_pos: Tuple[int, int] = (0, 0)
    drag_start_displacement: float = 100.0
    mouse_over_knob: bool = False
    key_held: Optional[int] = None
    key_hold_start_time: float = 0.0
    mouse_in_control_area: bool = False


class InteractionManager:
    """完整的交互管理器"""

    def __init__(self, mechanics_engine, screen_width: int = 1000, screen_height: int = 700):
        self.mechanics = mechanics_engine
        self.screen_width = screen_width
        self.screen_height = screen_height

        # 交互状态
        self.state = InteractionState()
        self.current_mode = InteractionMode.SLIDER

        # 旋钮参数
        self.knob_radius = 60
        self.knob_center = (250, 200)

        # 鼠标移动控制区域
        self.mouse_control_rect = pygame.Rect(600, 150, 300, 300)

        # 拉条参数
        self.slider_rect = pygame.Rect(150, 400, 600, 40)
        self.slider_knob_width = 20

        # 交互参数
        self.angle_sensitivity = 0.02
        self.scroll_sensitivity = 0.5
        self.mouse_move_sensitivity = 0.8
        self.key_press_initial_delay = 0.5  # 长按初始延迟（秒）
        self.key_press_repeat_rate = 0.1  # 长按重复速率（秒）

        # 位移范围
        self.min_displacement = 50.0
        self.max_displacement = 200.0
        self.angle_range = math.pi * 3  # 1.5圈

        # 回调函数
        self.on_displacement_change: Optional[Callable[[float], None]] = None
        self.on_interaction_start: Optional[Callable[[], None]] = None
        self.on_interaction_end: Optional[Callable[[], None]] = None

        # 初始化Pygame
        pygame.init()
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("钢琴调律交互模拟")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        # 计算角度到位移的转换
        self._calculate_conversion_ratios()

    def _calculate_conversion_ratios(self):
        """计算转换比率"""
        self.angle_to_displacement_ratio = (self.max_displacement - self.min_displacement) / self.angle_range

    def angle_to_displacement(self, angle: float) -> float:
        """角度转位移"""
        normalized_angle = (angle + self.angle_range / 2) / self.angle_range
        displacement = self.min_displacement + normalized_angle * (self.max_displacement - self.min_displacement)
        return max(self.min_displacement, min(self.max_displacement, displacement))

    def displacement_to_angle(self, displacement: float) -> float:
        """位移转角度"""
        normalized_displacement = (displacement - self.min_displacement) / (
                    self.max_displacement - self.min_displacement)
        angle = -self.angle_range / 2 + normalized_displacement * self.angle_range
        return angle

    # ===== 模式1: 拉条直接调整 =====
    def handle_slider_click(self, mouse_pos: Tuple[int, int]):
        """处理拉条点击"""
        if self.slider_rect.collidepoint(mouse_pos):
            # 计算新的位移值
            relative_x = mouse_pos[0] - self.slider_rect.left
            percentage = relative_x / self.slider_rect.width
            new_displacement = self.min_displacement + percentage * (self.max_displacement - self.min_displacement)
            self.set_displacement_direct(new_displacement)
            return True
        return False

    # ===== 模式2: 旋钮拖拽（左键单击后移动，释放结束）=====
    def start_knob_drag(self, mouse_pos: Tuple[int, int]):
        """开始旋钮拖拽"""
        if self._is_point_in_knob(mouse_pos):
            self.state.is_dragging = True
            self.state.drag_start_angle = self.state.angle

            # 计算初始鼠标角度
            dx = mouse_pos[0] - self.knob_center[0]
            dy = mouse_pos[1] - self.knob_center[1]
            self.drag_start_mouse_angle = math.atan2(dy, dx)

            if self.on_interaction_start:
                self.on_interaction_start()
            return True
        return False

    def update_knob_drag(self, mouse_pos: Tuple[int, int]):
        """更新旋钮拖拽"""
        if not self.state.is_dragging:
            return

        # 计算当前鼠标角度
        dx = mouse_pos[0] - self.knob_center[0]
        dy = mouse_pos[1] - self.knob_center[1]
        current_mouse_angle = math.atan2(dy, dx)

        # 计算角度变化
        angle_delta = current_mouse_angle - self.drag_start_mouse_angle
        new_angle = self.state.drag_start_angle + angle_delta * self.angle_sensitivity

        self._update_from_angle(new_angle)

    # ===== 模式3: 旋钮滚轮（悬停时）=====
    def handle_knob_wheel(self, scroll_delta: float):
        """处理旋钮滚轮"""
        if self.state.mouse_over_knob:
            angle_delta = scroll_delta * self.scroll_sensitivity
            new_angle = self.state.angle + angle_delta
            self._update_from_angle(new_angle)

    # ===== 模式4: 鼠标移动（左键单击后移动，释放结束）=====
    def start_mouse_move(self, mouse_pos: Tuple[int, int]):
        """开始鼠标移动控制"""
        if self.mouse_control_rect.collidepoint(mouse_pos):
            self.state.is_dragging = True
            self.state.drag_start_pos = mouse_pos
            self.state.drag_start_displacement = self.state.displacement

            if self.on_interaction_start:
                self.on_interaction_start()
            return True
        return False

    def update_mouse_move(self, mouse_pos: Tuple[int, int]):
        """更新鼠标移动控制"""
        if not self.state.is_dragging:
            return

        # 计算鼠标移动距离
        dx = mouse_pos[0] - self.state.drag_start_pos[0]
        dy = mouse_pos[1] - self.state.drag_start_pos[1]

        # 使用移动距离调整位移（水平和垂直都有效）
        move_distance = math.sqrt(dx * dx + dy * dy)
        if abs(dx) > abs(dy):
            # 主要水平移动
            delta = dx * self.mouse_move_sensitivity
        else:
            # 主要垂直移动
            delta = -dy * self.mouse_move_sensitivity

        new_displacement = self.state.drag_start_displacement + delta
        self.set_displacement_direct(new_displacement)

    def end_drag(self):
        """结束所有拖拽操作"""
        if self.state.is_dragging:
            self.state.is_dragging = False
            if self.on_interaction_end:
                self.on_interaction_end()

    # ===== 模式5: 键盘长按 =====
    def start_key_press(self, key: int):
        """开始键盘长按"""
        self.state.key_held = key
        self.state.key_hold_start_time = time.time()
        self._handle_key_press_immediate(key)

    def update_key_press(self):
        """更新键盘长按（重复触发）"""
        if self.state.key_held is None:
            return

        current_time = time.time()
        hold_duration = current_time - self.state.key_hold_start_time

        if hold_duration > self.key_press_initial_delay:
            # 初始延迟后开始重复
            repeat_count = int((hold_duration - self.key_press_initial_delay) / self.key_press_repeat_rate)
            if repeat_count > self._last_repeat_count:
                self._handle_key_press_immediate(self.state.key_held)
                self._last_repeat_count = repeat_count

    def end_key_press(self):
        """结束键盘长按"""
        self.state.key_held = None
        self._last_repeat_count = 0

    def _handle_key_press_immediate(self, key: int):
        """立即处理按键"""
        if key == pygame.K_UP:
            self.set_displacement_direct(self.state.displacement + 2.0)
        elif key == pygame.K_DOWN:
            self.set_displacement_direct(self.state.displacement - 2.0)
        elif key == pygame.K_LEFT:
            new_angle = self.state.angle - 0.1
            self._update_from_angle(new_angle)
        elif key == pygame.K_RIGHT:
            new_angle = self.state.angle + 0.1
            self._update_from_angle(new_angle)

    # ===== 通用方法 =====
    def set_displacement_direct(self, new_displacement: float):
        """直接设置位移"""
        old_value = self.state.displacement
        self.state.displacement = max(self.min_displacement, min(self.max_displacement, new_displacement))
        self.state.angle = self.displacement_to_angle(self.state.displacement)
        self._update_mechanics()

        if self.on_displacement_change and abs(old_value - new_displacement) > 0.001:
            self.on_displacement_change(self.state.displacement)

    def _update_from_angle(self, new_angle: float):
        """从角度更新"""
        old_displacement = self.state.displacement
        self.state.angle = new_angle
        self.state.displacement = self.angle_to_displacement(new_angle)
        self._update_mechanics()

        if self.on_displacement_change and abs(old_displacement - self.state.displacement) > 0.001:
            self.on_displacement_change(self.state.displacement)

    def _update_mechanics(self):
        """更新力学引擎"""
        self.mechanics.set_displacement(self.state.displacement)
        self.mechanics.set_velocity(0.0)

    def _is_point_in_knob(self, point: Tuple[int, int]) -> bool:
        """检查点是否在旋钮内"""
        dx = point[0] - self.knob_center[0]
        dy = point[1] - self.knob_center[1]
        distance = math.sqrt(dx * dx + dy * dy)
        return distance <= self.knob_radius

    # ===== 主事件处理 =====
    def handle_events(self):
        """处理所有事件"""
        mouse_pos = pygame.mouse.get_pos()

        # 更新悬停状态
        self.state.mouse_over_knob = self._is_point_in_knob(mouse_pos)
        self.state.mouse_in_control_area = self.mouse_control_rect.collidepoint(mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键
                    # 尝试旋钮拖拽
                    if self.start_knob_drag(event.pos):
                        self.current_mode = InteractionMode.KNOB_DRAG
                    # 尝试鼠标移动控制
                    elif self.start_mouse_move(event.pos):
                        self.current_mode = InteractionMode.MOUSE_MOVE
                    # 尝试拉条点击
                    elif self.handle_slider_click(event.pos):
                        self.current_mode = InteractionMode.SLIDER

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # 左键释放
                    self.end_drag()

            elif event.type == pygame.MOUSEMOTION:
                if self.state.is_dragging:
                    if self.current_mode == InteractionMode.KNOB_DRAG:
                        self.update_knob_drag(event.pos)
                    elif self.current_mode == InteractionMode.MOUSE_MOVE:
                        self.update_mouse_move(event.pos)

            elif event.type == pygame.MOUSEWHEEL:
                if self.state.mouse_over_knob:
                    self.current_mode = InteractionMode.KNOB_WHEEL
                    self.handle_knob_wheel(event.y)

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                    self.current_mode = InteractionMode.KEY_PRESS
                    self.start_key_press(event.key)
                elif event.key == pygame.K_r:  # 重置
                    self.set_displacement_direct(100.0)
                elif event.key == pygame.K_1:  # 切换到拉条模式
                    self.current_mode = InteractionMode.SLIDER
                elif event.key == pygame.K_2:  # 切换到旋钮模式
                    self.current_mode = InteractionMode.KNOB_DRAG
                elif event.key == pygame.K_3:  # 切换到鼠标移动模式
                    self.current_mode = InteractionMode.MOUSE_MOVE

            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                    self.end_key_press()

        # 更新长按键
        self.update_key_press()

        return True

    # ===== 渲染界面 =====
    def draw_interface(self):
        """绘制完整界面"""
        self.screen.fill((240, 240, 240))

        # 绘制旋钮
        self._draw_knob()

        # 绘制鼠标移动控制区域
        self._draw_mouse_control_area()

        # 绘制拉条
        self._draw_slider()

        # 绘制信息显示
        self._draw_info_panel()

        # 绘制操作说明
        self._draw_instructions()

        pygame.display.flip()

    def _draw_knob(self):
        """绘制旋钮"""
        # 旋钮背景
        color = (180, 180, 220) if self.state.mouse_over_knob else (150, 150, 180)
        pygame.draw.circle(self.screen, color, self.knob_center, self.knob_radius)
        pygame.draw.circle(self.screen, (200, 200, 220), self.knob_center, self.knob_radius - 8)

        # 旋钮指针
        pointer_length = self.knob_radius - 15
        end_x = self.knob_center[0] + math.cos(self.state.angle) * pointer_length
        end_y = self.knob_center[1] + math.sin(self.state.angle) * pointer_length

        pygame.draw.line(self.screen, (255, 50, 50), self.knob_center, (end_x, end_y), 6)
        pygame.draw.circle(self.screen, (50, 50, 50), self.knob_center, 6)

        # 旋钮标签
        label = self.small_font.render("旋钮控制", True, (0, 0, 0))
        self.screen.blit(label, (self.knob_center[0] - 30, self.knob_center[1] + self.knob_radius + 10))

    def _draw_mouse_control_area(self):
        """绘制鼠标移动控制区域"""
        color = (180, 220, 180) if self.state.mouse_in_control_area else (150, 180, 150)
        pygame.draw.rect(self.screen, color, self.mouse_control_rect, border_radius=10)
        pygame.draw.rect(self.screen, (100, 140, 100), self.mouse_control_rect, 3, border_radius=10)

        # 绘制十字指引
        center_x = self.mouse_control_rect.centerx
        center_y = self.mouse_control_rect.centery
        pygame.draw.line(self.screen, (80, 80, 80), (center_x - 40, center_y), (center_x + 40, center_y), 2)
        pygame.draw.line(self.screen, (80, 80, 80), (center_x, center_y - 40), (center_x, center_y + 40), 2)

        label = self.small_font.render("鼠标移动控制区", True, (0, 0, 0))
        self.screen.blit(label, (self.mouse_control_rect.centerx - 50, self.mouse_control_rect.bottom + 10))

    def _draw_slider(self):
        """绘制拉条"""
        # 拉条轨道
        pygame.draw.rect(self.screen, (200, 200, 200), self.slider_rect, border_radius=5)
        pygame.draw.rect(self.screen, (100, 100, 100), self.slider_rect, 2, border_radius=5)

        # 拉条滑块
        slider_range = self.slider_rect.width - self.slider_knob_width
        slider_pos = (self.state.displacement - self.min_displacement) / (self.max_displacement - self.min_displacement)
        knob_x = self.slider_rect.left + int(slider_pos * slider_range)
        knob_rect = pygame.Rect(knob_x, self.slider_rect.top - 5, self.slider_knob_width, self.slider_rect.height + 10)

        pygame.draw.rect(self.screen, (70, 130, 230), knob_rect, border_radius=3)
        pygame.draw.rect(self.screen, (30, 80, 180), knob_rect, 2, border_radius=3)

        label = self.small_font.render("位移拉条", True, (0, 0, 0))
        self.screen.blit(label, (self.slider_rect.centerx - 30, self.slider_rect.bottom + 10))

    def _draw_info_panel(self):
        """绘制信息面板"""
        info_y = 500
        texts = [
            f"当前模式: {self.current_mode.value}",
            f"虚拟位移: {self.state.displacement:.1f}",
            f"旋钮角度: {math.degrees(self.state.angle):.1f}°",
            f"弦张力: {self.mechanics.get_tension():.1f} N",
            f"预测频率: {self.mechanics.predict_frequency(0.125, 0.001):.1f} Hz"
        ]

        for i, text in enumerate(texts):
            surface = self.font.render(text, True, (0, 0, 0))
            self.screen.blit(surface, (50, info_y + i * 40))

    def _draw_instructions(self):
        """绘制操作说明"""
        instructions = [
            "操作说明:",
            "1. 拉条控制: 点击拉条直接设置位移",
            "2. 旋钮拖拽: 左键拖拽旋钮旋转",
            "3. 旋钮滚轮: 鼠标悬停时使用滚轮",
            "4. 鼠标移动: 在绿色区域左键拖拽移动",
            "5. 键盘长按: ↑↓←→键持续调整",
            "R键: 重置位移 | 1/2/3键: 切换模式"
        ]

        for i, line in enumerate(instructions):
            surface = self.small_font.render(line, True, (60, 60, 60))
            self.screen.blit(surface, (600, 500 + i * 25))

    def run(self):
        """运行交互系统"""
        running = True
        self._last_repeat_count = 0

        print("启动交互系统...")
        print("5种交互模式:")
        print("  1. 拉条直接调整 (点击拉条)")
        print("  2. 旋钮拖拽 (左键单击旋钮后移动)")
        print("  3. 旋钮滚轮 (鼠标悬停旋钮时滚轮)")
        print("  4. 鼠标移动 (在绿色区域左键单击后移动)")
        print("  5. 键盘长按 (方向键长按持续调整)")
        print("按1/2/3键切换模式，R键重置")

        while running:
            running = self.handle_events()
            self.draw_interface()
            self.clock.tick(60)

        pygame.quit()


# 测试代码
if __name__ == "__main__":
    from MechanicsEngine import SimplePianoMechanics

    mechanics = SimplePianoMechanics()
    mechanics.set_calibration(C0=0.25)

    manager = InteractionManager(mechanics)


    def on_change(new_value):
        print(f"位移更新: {new_value:.1f}")


    manager.on_displacement_change = on_change
    manager.run()