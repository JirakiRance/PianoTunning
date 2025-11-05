# This Python file uses the following encoding: utf-8
import sys

from PySide6.QtWidgets import QApplication, QMainWindow

# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from ui_form import Ui_MainWindow


# 以上为qt系统生成

import os
# 添加src文件夹到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root=os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
sys.path.append(src_path)

from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import  QPushButton, QLabel
from PySide6.QtWidgets import QSizePolicy,QComboBox

# 导入音频检测模块
try:
    from AudioDetector import AudioDetector, PitchDetectionAlgorithm,PitchResult
    AUDIO_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"导入音频模块失败: {e}")
    AUDIO_MODULES_AVAILABLE = False

# 导入钢琴生成器模块
try:
    from PianoGenerator import PianoGenerator, AccidentalType, PianoKey, KeyColor
    PIANO_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"导入钢琴模块失败: {e}")
    PIANO_MODULES_AVAILABLE = False

# 导入钢琴绘图组件
try:
    from PianoWidget import PianoWidget
except ImportError as e:
    print(f"导入 PianoWidget 失败: {e}")

import sys
import os
import time
import numpy as np
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QRadioButton, QGroupBox,
                              QButtonGroup, QTextEdit, QProgressBar,QSystemTrayIcon)
from PySide6.QtCore import Qt, QTimer,QObject, Signal
from PySide6.QtGui import QFont, QPalette, QColor,QIcon


# ==================== 音高信号类 ====================
class PitchSignal(QObject):
    """用于从工作线程向主线程传递音高结果的信号"""
    pitch_detected = Signal(PitchResult)

#==================== 主窗口 ========================
class MainWindow(QMainWindow):
    def __init__(self):
        # 这个构造有点问题，注释掉
        # # UI
        # super().__init__()
        # # self.setup_ui()
        # # self.setup_menu_bar()
        # # self.connect_signals()
        # # 音频模块初始化
        # self.audio_detector = None  # 存储 AudioDetector 实例
        # self.pitch_signal = PitchSignal() # 音高信号实例
        # self.init_audio_system() # 初始化音频系统

        # # 录音计时器模块
        # self.record_timer = QTimer(self)
        # self.record_timer.timeout.connect(self.update_duration)
        # self.record_start_time = 0
        # self.is_paused = False # 暂停状态

        # # 钢琴窗模块
        # # --- 钢琴和调律目标参数 ---
        # self.piano_generator = None
        # self.init_piano_system() # 初始化钢琴系统
        # self.target_key: Optional[PianoKey] = None # 当前调律的目标键
        # # 默认目标键：A4
        # self.default_target_note_name = "A4"
        # self.update_status(f"参数预览 - 目标频率: {self.target_key.note_name} ({self.target_key.frequency:.1f}Hz)")

        # # UI
        # self.setup_ui()
        # self.setup_menu_bar()
        # self.connect_signals()

        # 1. UI 基础设置
        super().__init__()

        # 用于缓存状态消息的静态列表
        self._status_message_cache = []

        # 2. 声明数据模型和核心模块实例 (在 setup_ui 调用前完成)
        self.audio_detector = None     # 存储 AudioDetector 实例
        self.pitch_signal = PitchSignal() # 音高信号实例
        self.piano_generator = None    # PianoGenerator 实例
        self.target_key: Optional[PianoKey] = None # 当前调律的目标键
        self.default_target_note_name = "A4"

        # 3. 初始化核心系统 (只声明，不进行状态更新)
        # 注意：这里调用 init_audio_system 和 init_piano_system 时，它们内部的 update_status 仍会失败。
        # 需要暂时修改这两个 init 方法，使其在调用 update_status 前检查 self.status_display 是否存在。
        self.init_piano_system()
        self.init_audio_system()

        # 4. UI 设置
        self.setup_ui()
        self.setup_menu_bar()
        self.connect_signals()

        # 5. UI 后续操作 (录音计时器等)
        self.record_timer = QTimer(self)
        self.record_timer.timeout.connect(self.update_duration)
        self.record_start_time = 0
        self.is_paused = False

        # 6. 最终状态初始化 (在这里统一刷新状态，取代之前分散的 update_status 调用)
        self._post_ui_init_status_update()



    def _post_ui_init_status_update(self):
        """在UI创建完成后，统一初始化状态显示"""
        # 初始化状态显示 - 钢琴系统
        if self.target_key:
            self.set_target_note(self.target_key.note_name)
            self.update_status(f"参数预览 - 目标频率: {self.target_key.note_name} ({self.target_key.frequency:.1f}Hz)")
        else:
            self.update_status("目标音高: 待配置 (钢琴系统初始化失败)")

        # 初始化状态显示 - 音频系统 (重播 init_audio_system 中的状态信息)
        if self.audio_detector:
            self.update_status(f"音频系统初始化成功，算法：{self.audio_detector.get_current_algorithm().value}")
        else:
            self.update_status("音频模块不可用或初始化失败")

        # 钢琴系统状态
        if self.piano_generator:
            self.update_status(f"钢琴系统初始化成功，88键，A4={self.piano_generator.base_frequency}Hz")
        else:
            self.update_status("钢琴模块不可用或初始化失败")


    # 初始化音频系统
    def init_audio_system(self):
        """初始化 AudioDetector 实例和连接回调"""
        if AUDIO_MODULES_AVAILABLE:
            try:
                # 使用默认参数初始化 AudioDetector
                self.audio_detector = AudioDetector(
                    sample_rate=44100,
                    frame_length=8192,
                    hop_length=512,
                    # 可以根据配置界面选择输入设备，这里先用默认设备2
                    input_device=2,
                    pitch_algorithm=PitchDetectionAlgorithm.AUTOCORR # 默认使用AUTOCORR,有一定准确度，且响应极快
                )
                self.update_status("音频系统初始化成功，算法：AUTOCORR")

                # 连接自定义信号到主线程槽函数
                self.pitch_signal.pitch_detected.connect(self.on_pitch_detected_update_ui)

            except Exception as e:
                self.update_status(f"音频系统初始化失败: {e}")
                self.audio_detector = None
        else:
            self.update_status("音频模块不可用，请检查依赖库")

    def setup_ui(self):
        """设置主界面"""
        self.setWindowTitle("千椻")
        self.setWindowIcon(QIcon("E:/Resources/images/acgs/NanoAlice01.png"))
        self.setGeometry(100, 100, 1400, 900)
        # 设置系统托盘图标
        if QSystemTrayIcon.isSystemTrayAvailable():
            print("系统支持托盘图标")
            self.tray_icon = QSystemTrayIcon(QIcon("E:/Resources/images/acgs/NanoAlice01.png"), self)
            self.tray_icon.show()
            print("托盘图标已显示")
        else:
            print("系统不支持托盘图标")
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 左边面板 (25%)
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 2)

        # 中间区域 (50%)
        center_panel = self.create_center_panel()
        main_layout.addWidget(center_panel, 5)

        # 右边面板 (25%)
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, 2)

        # 设置所有面板都扩展到最大高度
        main_layout.setAlignment(Qt.AlignBottom)


    def create_left_panel(self):
        """创建左边面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)

        # 模式选择
        mode_group = QGroupBox("分析模式")
        mode_layout = QVBoxLayout(mode_group)

        self.mode_realtime = QRadioButton("● 实时分析")
        self.mode_file = QRadioButton("○ 文件分析")
        self.mode_realtime.setChecked(True)

        mode_layout.addWidget(self.mode_realtime)
        mode_layout.addWidget(self.mode_file)

        # 录音控制 (实时模式)
        self.record_group = QGroupBox("录音控制")
        record_layout = QVBoxLayout(self.record_group)

        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("● 开始录音")
        self.stop_btn = QPushButton("■ 停止")
        self.pause_btn = QPushButton("⏸ 暂停")

        self.stop_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.pause_btn)

        record_layout.addLayout(btn_layout)

        # 时长显示
        self.duration_label = QLabel("⏱ 时长: 00:00")
        record_layout.addWidget(self.duration_label)

        # 文件系统 (文件模式)
        self.file_group = QGroupBox("文件系统")
        file_layout = QVBoxLayout(self.file_group)

        self.file_list = QTextEdit()
        self.file_list.setMaximumHeight(120)
        self.file_list.setPlainText("""📁 最近文件
    • recording1.wav
    • piano_A4.wav
    • test_audio.mp3

    📁 录音记录
    • 2024-01-15.wav
    • session_1.wav""")
        self.file_list.setReadOnly(True)

        file_layout.addWidget(self.file_list)

        # 初始隐藏文件系统
        self.file_group.setVisible(False)

        # 状态信息
        status_group = QGroupBox("系统状态")
        status_layout = QVBoxLayout(status_group)

        self.status_display = QTextEdit()
        self.status_display.setMaximumHeight(200)
        self.status_display.setPlainText("""📊 当前状态
• 模式: 实时分析
• 状态: 等待开始
• 设备: 默认麦克风
• 算法: 自适应

💡 调音建议
• 准备开始音频检测...

⚙️ 参数预览
• 目标频率: A4 (440Hz)
• 检测算法: 自适应
• 灵敏度: 中
• 置信度: --""")
        self.status_display.setReadOnly(True)

        status_layout.addWidget(self.status_display)
        layout.addWidget(status_group)

        # 布局管理 - 使用拉伸因子保持固定高度
        layout.addWidget(mode_group)
        layout.addWidget(self.record_group)
        layout.addWidget(self.file_group)
        layout.addWidget(status_group)
        layout.setStretchFactor(mode_group, 1)
        layout.setStretchFactor(self.record_group, 2)
        layout.setStretchFactor(self.file_group, 2)
        layout.setStretchFactor(status_group,4)

        return panel

    def create_center_panel(self):
        """创建中间面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)

        # 频谱波图区域
        spectrum_group = QGroupBox("频谱波图")
        spectrum_layout = QVBoxLayout(spectrum_group)

        self.spectrum_display = QLabel("实时频谱显示区域\n(频率波形可视化)")
        self.spectrum_display.setAlignment(Qt.AlignCenter)
        self.spectrum_display.setStyleSheet("""
            background-color: #2c3e50;
            color: white;
            padding: 50px;
            border: 2px solid #34495e;
            border-radius: 8px;
            font-size: 14px;
        """)
        self.spectrum_display.setMinimumHeight(300)

        spectrum_layout.addWidget(self.spectrum_display)

        # 钢琴键盘区域
        piano_group = QGroupBox("钢琴键盘")
        piano_layout = QVBoxLayout(piano_group)
        # 先用Label占位置测试一下
        # self.piano_display = QLabel("Keyscape样式钢琴键盘\n(88键可视化)")
        # self.piano_display.setAlignment(Qt.AlignCenter)
        # self.piano_display.setStyleSheet("""
        #     background-color: #34495e;
        #     color: white;
        #     padding: 30px;
        #     border: 2px solid #2c3e50;
        #     border-radius: 8px;
        #     font-size: 14px;
        # """)
        # self.piano_display.setMinimumHeight(200)

        # piano_layout.addWidget(self.piano_display)
        # --- 替换原来的 Label 为新的 PianoWidget ---
        self.piano_widget = PianoWidget(self.piano_generator) # 实例化自定义钢琴组件
        self.piano_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 添加目标键选择下拉菜单
        target_select_layout = QHBoxLayout()
        target_select_layout.addWidget(QLabel("选择目标音高:"))

        self.note_selector = QComboBox()
        # 填充 QComboBox
        if self.piano_generator:
            note_names = sorted(self.piano_generator.export_key_frequencies().keys(), key=lambda n: self.piano_generator.get_key_by_note_name(n).midi_number)
            self.note_selector.addItems(note_names)
            # 默认选择 A4
            self.note_selector.setCurrentText(self.default_target_note_name)
            # 确保连接信号在填充后
            self.note_selector.currentTextChanged.connect(self.on_note_selector_changed)
            self.piano_widget.key_clicked.connect(self.on_note_selector_changed)
        else:
            self.note_selector.addItem("钢琴模块加载失败")
            self.note_selector.setEnabled(False) # 加载失败则禁用选择

        target_select_layout.addWidget(self.note_selector)
        target_select_layout.addStretch(1) # 使选择框不占满宽度

        piano_layout.addLayout(target_select_layout)
        piano_layout.addWidget(self.piano_widget) # 替换 self.piano_display

        # --- 结束替换 ---

        layout.addWidget(spectrum_group)
        layout.addWidget(piano_group)
        layout.setStretchFactor(spectrum_group,7)
        layout.setStretchFactor(piano_group,3)

        return panel


    def create_right_panel(self):
        """创建右边面板 - 纯粹的力学调整"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)

        # 力学调整器
        adjust_group = QGroupBox("力学调整")
        adjust_layout = QVBoxLayout(adjust_group)

        # 推杆模拟 - 更大的显示
        slider_layout = QVBoxLayout()
        self.slider_display = QLabel("🎚️ 精密推杆调节器\n\n← 偏低 | 准确 | 偏高 →")
        self.slider_display.setAlignment(Qt.AlignCenter)
        self.slider_display.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #e74c3c, stop:0.4 #f39c12, stop:0.5 #27ae60,
                stop:0.6 #f39c12, stop:1 #e74c3c);
            color: white;
            padding: 120px 20px;
            border: 2px solid #7f8c8d;
            border-radius: 10px;
            font-weight: bold;
            font-size: 14px;
        """)
        self.slider_display.setMinimumHeight(250)

        slider_layout.addWidget(self.slider_display)

        # 旋钮区域
        knob_layout = QHBoxLayout()

        coarse_knob = QLabel("🔘 粗调\n(±10音分)")
        coarse_knob.setAlignment(Qt.AlignCenter)
        coarse_knob.setStyleSheet("""
            background-color: #95a5a6;
            padding: 40px 20px;
            border-radius: 60px;
            border: 2px solid #7f8c8d;
            font-weight: bold;
            min-width: 100px;
            font-size: 12px;
        """)

        fine_knob = QLabel("🔘 微调\n(±1音分)")
        fine_knob.setAlignment(Qt.AlignCenter)
        fine_knob.setStyleSheet("""
            background-color: #95a5a6;
            padding: 30px 15px;
            border-radius: 50px;
            border: 2px solid #7f8c8d;
            font-weight: bold;
            min-width: 90px;
            font-size: 12px;
        """)

        knob_layout.addWidget(coarse_knob)
        knob_layout.addWidget(fine_knob)

        adjust_layout.addLayout(slider_layout)
        adjust_layout.addLayout(knob_layout)
        adjust_layout.setStretchFactor(slider_layout,7)
        adjust_layout.setStretchFactor(knob_layout,3)

        # 让力学调整组扩展到整个右边面板高度
        layout.addWidget(adjust_group)
        layout.setStretchFactor(adjust_group,1)

        return panel

    def setup_menu_bar(self):
        """设置菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("📁 文件(&F)")
        file_menu.addAction("🆕 新建分析")
        file_menu.addAction("📂 打开文件")
        file_menu.addAction("💾 保存结果")
        file_menu.addAction("📊 导出报告")
        file_menu.addSeparator()
        file_menu.addAction("🚪 退出")

        # 编辑菜单
        edit_menu = menubar.addMenu("✏️ 编辑(&E)")
        edit_menu.addAction("⭐ 参数预设")
        edit_menu.addAction("📋 复制数据")
        edit_menu.addAction("🧹 清空记录")

        # 视图菜单
        view_menu = menubar.addMenu("👁️ 视图(&V)")
        view_menu.addAction("📈 频谱显示选项")
        view_menu.addAction("🎹 钢琴窗主题")
        view_menu.addAction("🎨 界面主题")
        view_menu.addSeparator()
        view_menu.addAction("🖥️ 全屏模式")

        # 工具菜单
        tools_menu = menubar.addMenu("🛠️ 工具(&T)")
        tools_menu.addAction("🎧 音频设备配置")
        tools_menu.addAction("🔊 参考音生成器")
        tools_menu.addAction("⚖️ 频率校准工具")
        tools_menu.addAction("📁 批量文件分析")

        # 设置菜单
        settings_menu = menubar.addMenu("⚙️ 设置(&S)")
        settings_menu.addAction("🎹 钢琴数据库管理")
        settings_menu.addAction("🎻 琴弦密度配置")
        settings_menu.addAction("🎵 音名系统设置")
        settings_menu.addAction("🎶 钢琴窗音色配置")
        settings_menu.addSeparator()
        settings_menu.addAction("🔧 高级音频设置")

        # 帮助菜单
        help_menu = menubar.addMenu("❓ 帮助(&H)")
        help_menu.addAction("📖 用户手册")
        help_menu.addAction("🔍 算法说明")
        help_menu.addAction("⌨️ 快捷键列表")
        help_menu.addSeparator()
        help_menu.addAction("ℹ️ 关于")

    def connect_signals(self):
        """连接信号槽"""
        # 模式
        self.mode_realtime.toggled.connect(self.on_mode_changed)
        self.mode_file.toggled.connect(self.on_mode_changed)
        # 音频逻辑
        # 音频按钮
        self.start_btn.clicked.connect(self.on_start_recording)
        self.stop_btn.clicked.connect(self.on_stop_recording)
        self.pause_btn.clicked.connect(self.on_pause_recording)
        # 实时模式下，禁用暂停按钮
        self.pause_btn.setEnabled(False) # 实时录音/处理线程模型下，暂停逻辑较复杂，先禁用

        # 钢琴逻辑
        if PIANO_MODULES_AVAILABLE:
            # 1. 连接 QComboBox 改变事件
            self.note_selector.currentTextChanged.connect(self.on_note_selector_changed)

            # 2. 连接 PianoWidget 鼠标点击事件
            self.piano_widget.key_clicked.connect(self.on_note_selector_changed) # 鼠标点击也使用相同的槽函数


    def on_mode_changed(self):
        """模式切换"""
        if self.mode_realtime.isChecked():
            self.record_group.setVisible(True)
            self.file_group.setVisible(False)
            self.update_status("切换到实时分析模式")
        else:
            self.record_group.setVisible(False)
            self.file_group.setVisible(True)
            self.update_status("切换到文件分析模式")
    # 更新状态信息
    # def update_status(self, message):
    #     """更新状态信息"""
    #     current_text = self.status_display.toPlainText()
    #     lines = current_text.split('\n')
    #     if len(lines) > 1:
    #         lines[1] = f"• 状态: {message}"
    #         new_text = '\n'.join(lines)
    #         self.status_display.setPlainText(new_text)

    def on_start_recording(self):
        """开始录音"""
        if not self.audio_detector:
            self.update_status("错误: 音频检测器未初始化")
            return
        # 定义一个包装函数，在音频线程中发射信号
        def real_time_pitch_callback(result: PitchResult):
            # 这是一个在 AudioDetector 内部线程中运行的回调
            self.pitch_signal.pitch_detected.emit(result)
        # 业务逻辑
        if self.audio_detector.start_realtime_analysis(real_time_pitch_callback, save_recording=True):
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            # self.pause_btn.setEnabled(True) # 先禁用暂停
            # 启动计时器
            self.record_start_time = time.time()
            self.record_timer.start(1000) # 每秒更新一次
            self.update_status("实时分析启动成功，录音进行中...")
        else:
            self.update_status("实时分析启动失败")



    def on_stop_recording(self):
        """停止录音"""
        if not self.audio_detector:
            return
        # 保存文件
        recording_file = self.audio_detector.stop_realtime_analysis()
        self.record_timer.stop()
        self.duration_label.setText("⏱ 时长: 00:00")
        # 按钮
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        # 后处理
        if recording_file:
            self.update_status(f"录音已停止。文件已保存: {os.path.basename(recording_file)}")
        else:
            self.update_status("录音已停止。未保存文件或停止失败")

    def on_pause_recording(self):
        """暂停录音 (暂时简化处理，仅更新状态)"""
        # 实际的音频流和处理线程暂停/继续逻辑较为复杂，
        # 在 `AudioDetector` 中需要更细粒度的控制。
        # 这里仅为 UI 演示。
        # if self.audio_detector and self.audio_detector.is_recording:
        #     # TODO: 实现 AudioDetector 内部的暂停逻辑
        #     self.is_paused = not self.is_paused
        #     if self.is_paused:
        #         self.update_status("录音已暂停")
        #         self.pause_btn.setText("▶ 继续")
        #         self.record_timer.stop()
        #     else:
        #         self.update_status("录音进行中...")
        #         self.pause_btn.setText("⏸ 暂停")
        #         self.record_timer.start(1000)
        pass # 暂时禁用实际逻辑

    def on_pitch_detected_update_ui(self, result: PitchResult):
        """
        接收到实时音高结果，在主线程中安全地更新 UI。
        这是连接音频模块和用户界面的核心。
        """
        # 1. 计算音分偏差
        cents = result.cents_deviation if result.cents_deviation is not None else 0.0

        # 2. 更新状态显示
        status_message = (f"频率: {result.frequency:.1f} Hz "
                          f"| 目标: {result.target_frequency:.1f} Hz "
                          f"| 偏差: {cents:+.2f} 音分 "
                          f"| 置信度: {result.confidence:.2f}")
        self.update_status(status_message)

        # 3. 更新精密推杆显示 (slider_display)
        self._update_slider_display(cents)

        # 4. TODO: 更新频谱波图
        # 5.更新钢琴键盘高亮
        if self.piano_generator and result.confidence > 0.6: # 仅在高置信度时高亮
            closest_key = self.piano_generator.find_closest_key(result.frequency)
            self.piano_widget.set_detected_note(closest_key.note_name)
        else:
            self.piano_widget.set_detected_note(None) # 没有有效检测时取消高亮

    def _update_slider_display(self, cents_deviation: float):
        """根据音分偏差更新推杆的颜色和提示文字"""

        # 颜色渐变: ±2 音分绿色 (精确), ±10 音分黄色 (良好), > ±10 音分红色 (不准)

        # 限制偏差在 [-50, 50] 范围内进行可视化，超出也按极限颜色显示
        cents = np.clip(cents_deviation, -50, 50)

        # 颜色计算（简化版）
        if abs(cents) <= 2.0:
            color = "#27ae60" # 绿色 (准确)
        elif abs(cents) <= 10.0:
            color = "#f39c12" # 黄色 (良好)
        else:
            color = "#e74c3c" # 红色 (不准)

        # 状态文字
        if cents > 10:
            status = "高得太多 (需大幅降张力)"
        elif cents > 2:
            status = "略高 (需微降张力)"
        elif cents < -10:
            status = "低得太多 (需大幅增张力)"
        elif cents < -2:
            status = "略低 (需微增张力)"
        else:
            status = "完美调准 (±2.0音分)"

        # 目标文本
        display_text = f"🎚️ 精密推杆调节器\n\n偏差: {cents:+.2f} 音分\n\n状态: {status}"

        # 更新背景颜色 (仅修改推杆部分，不改变整个渐变)
        style_sheet = f"""
            background-color: {color};
            color: white;
            padding: 120px 20px;
            border: 2px solid #7f8c8d;
            border-radius: 10px;
            font-weight: bold;
            font-size: 14px;
        """
        self.slider_display.setStyleSheet(style_sheet)
        self.slider_display.setText(display_text)

    def update_duration(self):
        """更新录音时长显示"""
        if self.record_start_time > 0 and self.audio_detector and self.audio_detector.is_recording:
            elapsed_time = int(time.time() - self.record_start_time)
            minutes = elapsed_time // 60
            seconds = elapsed_time % 60
            self.duration_label.setText(f"⏱ 时长: {minutes:02d}:{seconds:02d}")


    # 这个更新有点问题，注释掉
    # def update_status(self, message):
    #     """更新状态信息 - 改进: 自动替换'状态'行"""
    #     current_text = self.status_display.toPlainText()
    #     lines = current_text.split('\n')

    #     # 查找包含 '• 状态:' 的行并替换
    #     found = False
    #     for i, line in enumerate(lines):
    #         if line.strip().startswith('• 状态:'):
    #             lines[i] = f"• 状态: {message}"
    #             found = True
    #             break

    #     if not found:
    #          # 如果没找到，追加到末尾
    #         lines.append(f"• 状态: {message}")

    #     # 只保留 10 行状态信息，确保不会太长
    #     status_lines = [line for line in lines if not line.strip().startswith('• 状态:') and not line.strip().startswith('💡') and not line.strip().startswith('⚙️')]
    #     status_lines.insert(1, f"• 状态: {message}") # 插入新状态

    #     new_text = '\n'.join(status_lines[:10])
    #     self.status_display.setPlainText(new_text)
    def update_status(self, message):
        """更新状态信息 - 改进: 自动替换'状态'行"""

        # 如果 self.status_display 尚未创建，则将消息缓存
        if not hasattr(self, 'status_display'):
            self._status_message_cache.append(message)
            return

        # 如果缓存中有消息，先清空缓存并更新
        if self._status_message_cache:
            for cached_msg in self._status_message_cache:
                self._apply_status_update_logic(cached_msg)
            self._status_message_cache.clear()

        # 应用当前消息
        self._apply_status_update_logic(message)

    def _apply_status_update_logic(self, message):
        """实际更新状态文本框的逻辑"""
        current_text = self.status_display.toPlainText()
        lines = current_text.split('\n')

        found = False
        for i, line in enumerate(lines):
            if line.strip().startswith('• 状态:'):
                lines[i] = f"• 状态: {message}"
                found = True
                break

        if not found:
            # 如果没找到，追加到末尾
            lines.append(f"• 状态: {message}")

        # 只保留 10 行状态信息
        status_lines = [line for line in lines if not line.strip().startswith('• 状态:') and not line.strip().startswith('💡') and not line.strip().startswith('⚙️')]
        status_lines.insert(1, f"• 状态: {message}") # 插入新状态

        new_text = '\n'.join(status_lines[:10])
        self.status_display.setPlainText(new_text)

# ======================钢琴系统===================
    def init_piano_system(self):
        # """初始化 PianoGenerator 实例"""
        # if PIANO_MODULES_AVAILABLE:
        #     try:
        #         # 使用默认基频 A4=440Hz 和 降号表示法 初始化
        #         self.piano_generator = PianoGenerator(
        #             base_frequency=440.0,
        #             accidental_type=AccidentalType.FLAT
        #         )
        #         # 设置初始调律目标 A4
        #         self.set_target_note(self.default_target_note_name)

        #         self.update_status(f"钢琴系统初始化成功，88键，A4={self.piano_generator.base_frequency}Hz")
        #     except Exception as e:
        #         import traceback
        #         traceback.print_exc()
        #         self.update_status(f"钢琴系统初始化失败: {e}")
        #         self.piano_generator = None
        # else:
        #     self.update_status("钢琴模块不可用，请检查依赖库")
        """初始化 PianoGenerator 实例和调律参数"""
        if PIANO_MODULES_AVAILABLE:
            try:
                # 1. 初始化 PianoGenerator
                self.piano_generator = PianoGenerator(
                    base_frequency=440.0,
                    accidental_type=AccidentalType.FLAT
                )

                # 2. 设置目标键参数 (只设置数据，不操作 UI)
                self.target_key = self.piano_generator.get_key_by_note_name(self.default_target_note_name)

                # 3. 状态更新 (使用缓存安全的 update_status)
                self.update_status(f"钢琴系统初始化成功，88键，A4={self.piano_generator.base_frequency}Hz")

            except Exception as e:
                # 失败处理
                import traceback
                traceback.print_exc() # 保持打印堆栈，方便未来调试
                self.update_status(f"钢琴系统初始化失败: {e}")
                self.piano_generator = None
                self.target_key = None # 初始化失败，目标键也应为 None
        else:
            self.update_status("钢琴模块不可用，请检查依赖库")
            self.piano_generator = None
            self.target_key = None

    def set_target_note(self, note_name: str):
        """
        设置新的调律目标音高，并更新相关参数。
        """
        if not self.piano_generator:
            return

        new_key = self.piano_generator.get_key_by_note_name(note_name)
        if new_key:
            self.target_key = new_key

            # 更新 AudioDetector 中的目标频率
            self.target_freq = new_key.frequency # 继承自上一步的集成逻辑

            self.update_status(f"目标音高已切换: {new_key.note_name} ({new_key.frequency:.1f}Hz)")
            if hasattr(self, 'piano_widget') and self.piano_widget is not None:
                self.highlight_target_key() # 突出显示目标键
        else:
            self.update_status(f"错误: 未找到音名 {note_name}")

    # 测试用的占位置显示
    # def highlight_target_key(self):
    #     """更新钢琴键盘显示，突出显示目标键"""
    #     if self.target_key:
    #         message = f"Keyscape样式钢琴键盘\n(当前调律目标: {self.target_key.note_name} - {self.target_key.frequency:.1f}Hz 已高亮)"

    #         # 这里是模拟界面更新，实际可能需要 Qt Graphics View
    #         self.piano_display.setStyleSheet(f"""
    #             background-color: #34495e;
    #             color: white;
    #             padding: 30px;
    #             border: 2px solid #27ae60; /* 绿色边框突出显示 */
    #             border-radius: 8px;
    #             font-size: 14px;
    #         """)
    #         self.piano_display.setText(message)

    def on_note_selector_changed(self, note_name: str):
        """
        处理 QComboBox 或 PianoWidget 点击导致的音名变化。
        注意：QComboBox 发送的是 str，PianoWidget.key_clicked 也发送 str。
        """
        # 确保 QComboBox 和 PianoWidget 的显示一致
        if self.note_selector.currentText() != note_name:   # 这个!=有点意思哈，qt真有你的
            self.note_selector.setCurrentText(note_name) # 确保下拉菜单选中

        self.set_target_note(note_name)

        # 如果正在录音，需要重新启动实时分析以应用新的 target_frequency
        if self.audio_detector and self.audio_detector.is_recording:
            self.update_status("正在切换调律目标，准备重启分析...")
            self.on_stop_recording()
            self.on_start_recording()

    def highlight_target_key(self):
        """更新 PianoWidget 突出显示目标键"""
        if hasattr(self, 'piano_widget') and self.piano_widget is not None:
            if self.target_key:
                # 更新自定义 Widget 的目标键
                self.piano_widget.set_target_note(self.target_key.note_name)
                # 更新 Label 模拟显示 (不再需要这个 Label 了，但为保持结构，更新它)
                message = f"Keyscape样式钢琴键盘\n(当前调律目标: {self.target_key.note_name} - {self.target_key.frequency:.1f}Hz 已高亮)"
                # self.piano_display.setText(message) # 不要了旧的 Label 更新

