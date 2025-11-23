# RandomTuningDialog.py
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QDialog, QWidget, QLabel, QPushButton, QComboBox,
    QVBoxLayout, QHBoxLayout, QGroupBox, QSpacerItem,
    QSizePolicy
)
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Qt

import random

from RightMechanicsPanel import RightMechanicsPanel
from PianoGenerator import PianoGenerator, PianoKey

try:
    from AudioEngine import AudioEngine  # 仅用于类型提示，不强制
except ImportError:  # 打包/运行失败也无所谓
    AudioEngine = None  # type: ignore


class RandomTuningDialog(QDialog):
    """
    随机调音练习子窗口
    ---------------------------------------
    - 左侧：练习控制区
        * 当前目标音符
        * 频率显示
        * 范围选择
        * 播放标准音
        * 下一题
        * 记为正确 / 简单得分统计
        * 提示信息

    - 右侧：完整 RightMechanicsPanel
        * 和主界面一样的力学调音面板
    """

    def __init__(
        self,
        piano: PianoGenerator,
        audio_engine=None,
        parent: QWidget | None = None
    ):
        super().__init__(parent)

        self.piano: PianoGenerator = piano
        self.audio_engine = audio_engine  # AudioEngine 实例（可为 None）

        # 统计
        self.total_count = 0
        self.correct_count = 0

        # 当前目标键
        self.current_key: PianoKey | None = None

        # 预设范围（通过 MIDI 号）
        # A0(21) ~ B2(47); C3(48)~B4(71); C5(72)~C8(108)
        self.range_presets = {
            "全键盘 (A0 - C8)": (21, 108),
            "低音区 (A0 - B2)": (21, 47),
            "中音区 (C3 - B4)": (48, 71),
            "高音区 (C5 - C8)": (72, 108),
        }

        self._build_ui()
        self.setWindowTitle("随机调音练习")
        self.resize(300, 650)

        self.mechanics_panel.apply_velocity(0.0,False)
        self.mechanics_panel.dial.set_range(50)

        # 启动第一题
        self.next_question()

    # ======================================================
    # UI 构建
    # ======================================================
    def _build_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(12)

        # ===== 左侧控制区 =====
        control_widget = QWidget(self)
        control_layout = QVBoxLayout(control_widget)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(10)

        # --- 当前目标信息 ---
        info_group = QGroupBox("当前目标", control_widget)
        info_layout = QVBoxLayout(info_group)
        info_layout.setContentsMargins(8, 8, 8, 8)
        info_layout.setSpacing(6)

        self.label_note = QLabel("音符：-", info_group)
        self.label_note.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        self.label_note.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.label_freq = QLabel("频率：- Hz", info_group)
        self.label_freq.setFont(QFont("Consolas", 12))
        self.label_freq.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.label_range = QLabel("范围：-", info_group)
        self.label_range.setFont(QFont("Microsoft YaHei", 10))
        self.label_range.setStyleSheet("color: #bbbbbb;")

        info_layout.addWidget(self.label_note)
        info_layout.addWidget(self.label_freq)
        info_layout.addWidget(self.label_range)

        # --- 范围选择 ---
        range_group = QGroupBox("随机范围", control_widget)
        range_layout = QVBoxLayout(range_group)
        range_layout.setContentsMargins(8, 8, 8, 8)
        range_layout.setSpacing(6)

        self.combo_range = QComboBox(range_group)
        for name in self.range_presets.keys():
            self.combo_range.addItem(name)
        self.combo_range.setCurrentIndex(1)  # 默认中间某个，比如低音区/中音区都行

        range_layout.addWidget(self.combo_range)

        # --- 按钮区 ---
        btn_group = QGroupBox("练习控制", control_widget)
        btn_layout = QVBoxLayout(btn_group)
        btn_layout.setContentsMargins(8, 8, 8, 8)
        btn_layout.setSpacing(6)

        self.btn_play = QPushButton("播放标准音", btn_group)
        self.btn_next = QPushButton("下一题 ▶", btn_group)
        self.btn_mark_correct = QPushButton("记为调准 ✅", btn_group)
        self.btn_hint = QPushButton("显示提示", btn_group)

        self.btn_play.setMinimumHeight(32)
        self.btn_next.setMinimumHeight(32)
        self.btn_mark_correct.setMinimumHeight(32)
        self.btn_hint.setMinimumHeight(28)

        btn_layout.addWidget(self.btn_play)
        btn_layout.addWidget(self.btn_next)
        btn_layout.addWidget(self.btn_mark_correct)
        btn_layout.addWidget(self.btn_hint)

        # --- 成绩 & 提示 ---
        status_group = QGroupBox("练习状态", control_widget)
        status_layout = QVBoxLayout(status_group)
        status_layout.setContentsMargins(8, 8, 8, 8)
        status_layout.setSpacing(6)

        self.label_score = QLabel("已完成：0 题，记为正确：0 题", status_group)
        self.label_score.setFont(QFont("Microsoft YaHei", 9))
        self.label_score.setStyleSheet("color: #dddddd;")

        self.label_hint = QLabel("", status_group)
        self.label_hint.setWordWrap(True)
        self.label_hint.setFont(QFont("Microsoft YaHei", 9))
        self.label_hint.setStyleSheet("color: #ffcc66;")  # 暖黄色，作为提示色

        status_layout.addWidget(self.label_score)
        status_layout.addWidget(self.label_hint)

        # 左侧整体布局
        control_layout.addWidget(info_group)
        control_layout.addWidget(range_group)
        control_layout.addWidget(btn_group)
        control_layout.addWidget(status_group)
        control_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # ===== 右侧：力学调音面板 =====
        self.mechanics_panel = RightMechanicsPanel(self)

        # --- 总布局组合 ---
        main_layout.addWidget(control_widget, stretch=0)
        main_layout.addWidget(self.mechanics_panel, stretch=1)

        # 连接信号
        self.btn_play.clicked.connect(self._on_play_clicked)
        self.btn_next.clicked.connect(self._on_next_clicked)
        self.btn_mark_correct.clicked.connect(self._on_mark_correct_clicked)
        self.btn_hint.clicked.connect(self._on_hint_clicked)

    # ======================================================
    # 逻辑：出题 & 随机选键
    # ======================================================
    def _pick_random_key(self) -> PianoKey | None:
        """根据当前范围预设随机挑一个键"""
        range_name = self.combo_range.currentText()
        midi_min, midi_max = self.range_presets.get(range_name, (21, 108))

        candidates = [
            key for key in self.piano.keys.values()
            if midi_min <= key.midi_number <= midi_max
        ]

        if not candidates:
            return None

        return random.choice(candidates)

    def next_question(self):
        """刷新出新的一题"""
        key = self._pick_random_key()
        if key is None:
            self.label_note.setText("音符：-")
            self.label_freq.setText("频率：- Hz")
            self.label_hint.setText("当前范围内没有可用的琴键。")
            return

        self.current_key = key
        self.total_count += 1

        # 更新左侧文本
        self.label_note.setText(f"音符：{key.note_name}")
        self.label_freq.setText(f"频率：{key.frequency:.2f} Hz")
        self.label_range.setText(self.combo_range.currentText())

        # 更新 RightMechanicsPanel 的目标频率（让表盘围绕当前键）
        try:
            self.mechanics_panel.target_freq = key.frequency
        except Exception:
            # 如果后续 RightMechanicsPanel 改了接口，这里也不至于崩
            pass

        self._update_score_label()
        self.label_hint.setText("")  # 清空提示

    # ======================================================
    # 按钮回调
    # ======================================================
    def _on_play_clicked(self):
        """播放当前目标键的标准音"""
        if self.current_key is None:
            return

        # 优先走 AudioEngine.sf2 / sample
        if self.audio_engine is not None and hasattr(self.audio_engine, "play_note"):
            try:
                self.audio_engine.play_note(self.current_key.note_name, velocity=0.9, duration=2.0)
            except Exception as e:
                print(f"[RandomTuningDialog] AudioEngine 播放失败: {e}")
        else:
            # 兜底：用 PianoGenerator 内置的简易正弦波
            try:
                self.piano.play_key_frequency(self.current_key.key_id, duration=1.5, volume=0.4)
            except Exception as e:
                print(f"[RandomTuningDialog] PianoGenerator 播放失败: {e}")

    def _on_next_clicked(self):
        self.next_question()

    def _on_mark_correct_clicked(self):
        """用户自我标记：这一题我已经调好了"""
        if self.current_key is None:
            return
        self.correct_count += 1
        self._update_score_label()

    def _on_hint_clicked(self):
        """显示/刷新提示"""
        if self.current_key is None:
            self.label_hint.setText("当前没有目标音符。")
            return

        key = self.current_key
        text = (
            f"提示：当前目标是 {key.note_name}（{key.frequency:.2f} Hz）。\n"
            f"建议：先多听几遍标准音，再通过右侧扭矩板缓慢调整，"
            f"让频率指针稳定在 ±1 音分以内。"
        )
        self.label_hint.setText(text)

    # ======================================================
    # 辅助
    # ======================================================
    def _update_score_label(self):
        self.label_score.setText(
            f"已完成：{self.total_count} 题，记为正确：{self.correct_count} 题"
        )
