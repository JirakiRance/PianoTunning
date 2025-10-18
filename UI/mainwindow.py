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

# 导入音频检测模块
try:
    from AudioDetector import AudioDetector, PitchDetectionAlgorithm, PitchResult
    AUDIO_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"导入音频模块失败: {e}")
    AUDIO_MODULES_AVAILABLE = False



import sys
import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QRadioButton, QGroupBox,
                              QButtonGroup, QTextEdit, QProgressBar,QSystemTrayIcon)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPalette, QColor,QIcon

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_menu_bar()
        self.connect_signals()

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

        self.piano_display = QLabel("Keyscape样式钢琴键盘\n(88键可视化)")
        self.piano_display.setAlignment(Qt.AlignCenter)
        self.piano_display.setStyleSheet("""
            background-color: #34495e;
            color: white;
            padding: 30px;
            border: 2px solid #2c3e50;
            border-radius: 8px;
            font-size: 14px;
        """)
        self.piano_display.setMinimumHeight(200)

        piano_layout.addWidget(self.piano_display)

        layout.addWidget(spectrum_group)
        layout.addWidget(piano_group)
        layout.setStretchFactor(spectrum_group,6)
        layout.setStretchFactor(piano_group,4)

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
        self.mode_realtime.toggled.connect(self.on_mode_changed)
        self.mode_file.toggled.connect(self.on_mode_changed)

        self.start_btn.clicked.connect(self.on_start_recording)
        self.stop_btn.clicked.connect(self.on_stop_recording)
        self.pause_btn.clicked.connect(self.on_pause_recording)

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

    def on_start_recording(self):
        """开始录音"""
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.pause_btn.setEnabled(True)
        self.update_status("录音进行中...")

    def on_stop_recording(self):
        """停止录音"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self.update_status("录音已停止")

    def on_pause_recording(self):
        """暂停录音"""
        self.update_status("录音已暂停")

    def update_status(self, message):
        """更新状态信息"""
        current_text = self.status_display.toPlainText()
        lines = current_text.split('\n')
        if len(lines) > 1:
            lines[1] = f"• 状态: {message}"
            new_text = '\n'.join(lines)
            self.status_display.setPlainText(new_text)

