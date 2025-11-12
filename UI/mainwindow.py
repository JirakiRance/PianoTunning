# This Python file uses the following encoding: utf-8
import sys

from PySide6.QtWidgets import QApplication, QMainWindow,QFileDialog,QListWidget,QListWidgetItem,QInputDialog,QMessageBox,QDialog


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

from PySide6.QtCore import QFile,QStandardPaths,QDir,QTimer
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import  QPushButton, QLabel,QFileDialog,QLineEdit,QProgressBar
from PySide6.QtWidgets import QSizePolicy,QComboBox,QDial,QSlider
from PySide6.QtGui import QAction,QActionGroup
import numpy as np
from datetime import datetime
from typing import Dict,Any

# 导入音频检测模块
try:
    from AudioDetector import AudioDetector, PitchDetectionAlgorithm,PitchResult,RealtimeData,AnalysisProgress,MusicalAnalysisResult
    AUDIO_MODULES_AVAILABLE = True
except ImportError as e:
    import traceback
    traceback.print_exc()
    print(f"导入音频模块失败: {e}")
    AUDIO_MODULES_AVAILABLE = False

# 频谱绘制模块
try:
    from SpectrumWidget import SpectrumWidget
    SPECTRUM_WIDGET_AVAILABLE = True
except ImportError as e:
    print(f"导入 SpectrumWidget 失败: {e}")
    SPECTRUM_WIDGET_AVAILABLE = False

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

# 导入调整面板绘图组件
# try:
#     from TuningDialWidget import TuningDialWidget
#     TUNING_DIAL_AVAILABLE = True
# except ImportError as e:
#     print(f"导入 TuningDialWidget 失败: {e}")
#     TUNING_DIAL_AVAILABLE = False
# try:
#     from TuningInputWidget import TuningInputWidget
#     TUNING_INPUT_WIDGHET_AVAILABLE = True
# except ImportError as e:
#     print(f"导入 TuningInputWidget 失败: {e}")
#     TUNING_INPUT_WIDGHET_AVAILABLE = False

# 导入RightMechanicsPanel
try:
    from RightMechanicsPanel import RightMechanicsPanel
    RIGHT_PANEL_AVAILABLE = True
except ImportError as e:
    import traceback
    traceback.print_exc()
    print(f"导入 RightMechanicsPanel 失败: {e}")
    RIGHT_PANEL_AVAILABLE = False

from MechanicsEngine import MechanicsEngine

# 导入配置管理器和数据管理器
try:
    from ConfigManager import ConfigManager
    from StringCSVManager import StringCSVManager
    MANAGER_AVAILABLE = True
except ImportError as e:
    print(f"导入管理器失败: {e}")
    MANAGER_AVAILABLE = False

# 导入钢琴配置 Widget
try:
    from PianoConfigWidget import PianoConfigWidget
    PIANO_CONFIG_WIDGET_AVAILABLE = True
except ImportError as e:
    print(f"导入 PianoConfigWidget 失败: {e}")
    import traceback
    traceback.print_exc()
    PIANO_CONFIG_WIDGET_AVAILABLE = False

# 导入摩擦模型配置 Widget
try:
    from FrictionConfigWidget import FrictionConfigWidget
    FRICTION_CONFIG_WIDGET_AVAILABLE = True
except ImportError as e:
    print(f"导入 FrictionConfigWidget 失败: {e}")
    FRICTION_CONFIG_WIDGET_AVAILABLE = False

try:
    from MechanicalEngine import MechanicalEngine
    MECHANICAL_ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"导入 MechanicalEngine 失败: {e}")
    MECHANICAL_ENGINE_AVAILABLE = False

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
    # pitch_detected = Signal(PitchResult)
    pitch_detected = Signal(RealtimeData)

#==================== 主窗口 ========================
class MainWindow(QMainWindow):
    def __init__(self):
        # 0. UI 基础设置
        super().__init__()
        self.right_panel=None

        # 0.5 参数配置
        self.config_manager = ConfigManager(project_root)
        self.config_data = self.config_manager.load_config()
        # A. 力学参数
        self.mech_I = self.config_data.get('mech_I', 0.0001)    # 转动惯量 I (kg·m²)
        self.mech_r = self.config_data.get('mech_r', 0.005)     # 弦轴半径 r (m)
        self.mech_k = self.config_data.get('mech_k', 500000.0)  # 琴弦劲度系数 k (N/m) (用于张力/角度转换)
        self.mech_Kd = self.config_data.get('mech_Kd', 0.5)     # 施力敏感度 K_D (N·m·s/rad)
        # 摩擦模型参数 (保持默认值或从配置加载)
        self.mech_friction_model = self.config_data.get('mech_friction_model', "Limit_Friction")# 默认模型
        self.mech_fric_limit_0 = self.config_data.get('mech_fric_limit_0', 0.1) # 初始静摩擦极限 τ_fric_limit_0 (N·m)
        self.mech_alpha = self.config_data.get('mech_alpha', 0.05)          # 静摩擦增长系数 α (N·m/rad)
        self.mech_kinetic = self.config_data.get('mech_kinetic', 0.08)      # 动摩擦扭矩 τ_kinetic (N·m)
        self.mech_sigma = self.config_data.get('mech_sigma', 0.001)         # 粘性摩擦系数 σ (N·m·s/rad)
        # B. CSV Manager 路径
        self.db_manager = None
        if StringCSVManager:
            initial_db_path = self.config_data.get('db_file_path')
            self.db_manager = StringCSVManager(file_path=initial_db_path)
            print(f"CSV 管理器已初始化，文件路径: {self.db_manager.get_connected_path()}")
        # ---------------------------
        # C. MechanicalEngine 实例化 (依赖 A 的参数)
        self.mechanical_engine = None
        if MECHANICAL_ENGINE_AVAILABLE:
            self.mechanical_engine = MechanicalEngine(dt=1/60)
            # 收集所有全局力学参数并更新引擎
            all_mech_params = {k: getattr(self, k) for k in self.config_data.keys() if k.startswith('mech_')}
            self.mechanical_engine.update_physical_params(all_mech_params)

        # 1.控件
        # 用于缓存状态消息的静态列表
        self._status_message_cache = []
        # 存储分析完需要删除的文件路径
        self.temp_files_to_delete = []
        # 保存分析结果的控制
        self.settings_auto_prompt_save = True
        # 默认开启保存录音文件
        self.settings_save_recording_file = True
        # 录音时长设置声明
        self.max_recording_time_options = [5, 10, 20] # 选项：5s, 10s, 20s
        self.settings_max_recording_time = 10         # 默认值 10s
        # 音名系统设置声明,默认使用降号b系统
        self.settings_accidental_type = AccidentalType.FLAT

        # # 1.5 --- RK4 驱动状态和计时器 (必须在 connect_signals 前实例化) ---
        # self.user_input_ddt = 0.0
        # self.user_input_torque = 0.0
        # self.is_simulating = False
        # self.last_analysis_freq = None

        # self.tuning_loop_timer = QTimer(self) # <-- QTimer 实例化
        # self.tuning_loop_timer.timeout.connect(self._run_tuning_simulation)
        # self.tuning_loop_timer.setInterval(int(1000 / 60))
        # -----------------------------------------------------------------


        # 2. 声明数据模型和核心模块实例 (在 setup_ui 调用前完成)
        self.audio_detector = None     # 存储 AudioDetector 实例
        self.pitch_signal = PitchSignal() # 音高信号实例
        self.piano_generator = None    # PianoGenerator 实例
        self.target_key: Optional[PianoKey] = None # 当前调律的目标键
        self.default_target_note_name = "A4"
        self.current_analysis_folder: Optional[str] = None  # 新增文件系统属性

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

    # 处理参数文件路径更新
    def _handle_db_config_update(self, new_file_path: str):
        """接收 PianoConfigWidget 发出的文件路径更改信号"""
        # CSV Manager 实例本身没有变，只是内部的 file_path 变了，这里更新状态即可。
        self.update_status(f"琴弦数据文件已更新为: {new_file_path}")
        # 这里不需要重新加载 self.db_manager，因为它已是引用。


    def _post_ui_init_status_update(self):
        """在UI创建完成后，统一初始化状态显示"""
        # # 初始化状态显示 - 钢琴系统
        # if self.target_key:
        #     self.set_target_note(self.target_key.note_name)
        #     self.update_status(f"参数预览 - 目标频率: {self.target_key.note_name} ({self.target_key.frequency:.1f}Hz)")
        # else:
        #     self.update_status("目标音高: 待配置 (钢琴系统初始化失败)")

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

        # 初始化状态显示 - 钢琴系统
        if self.target_key:
            self.set_target_note(self.target_key.note_name)
            self.update_status(f"参数预览 - 目标频率: {self.target_key.note_name} ({self.target_key.frequency:.1f}Hz)")
        else:
            self.update_status("目标音高: 待配置 (钢琴系统初始化失败)")
        # # --- 修正：强制刷新 UI 状态 ---
        QApplication.processEvents() # 强制处理所有挂起的重绘事件
        # # ------------------------------------


    # 初始化音频系统
    def init_audio_system(self):
        """初始化 AudioDetector 实例和连接回调"""
        if AUDIO_MODULES_AVAILABLE:
            try:
                # 获取默认录音输出路径
                output_dir = self._get_default_recording_path()
                # 使用默认参数初始化 AudioDetector
                self.audio_detector = AudioDetector(
                    sample_rate=44100,
                    frame_length=8192,
                    hop_length=512,
                    # 可以根据配置界面选择输入设备，这里先用默认设备2
                    input_device=2,
                    pitch_algorithm=PitchDetectionAlgorithm.AUTOCORR, # 默认使用AUTOCORR,有一定准确度，且响应极快
                    output_dir=output_dir
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
        # right_panel = self.create_right_panel()
        right_panel = RightMechanicsPanel()
        self.right_panel=right_panel
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

        self.mode_realtime = QRadioButton("\t实时分析")
        self.mode_file = QRadioButton("\t文件分析")
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
        # btn_layout.addWidget(self.pause_btn) 暂停功能不提供了

        record_layout.addLayout(btn_layout)

        # 时长显示
        self.duration_label = QLabel("⏱ 时长: 00:00")
        record_layout.addWidget(self.duration_label)

        # --- 新增：进度条 ---
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False) # 默认隐藏
        self.progress_bar.setFormat("分析进度: %p%")
        record_layout.addWidget(self.progress_bar)
        # ------------------

        # 文件系统 (文件模式) 旧的文件系统，用QTextEdit占位置
    #     self.file_group = QGroupBox("文件系统")
    #     file_layout = QVBoxLayout(self.file_group)

    #     # 新增：文件选择按钮
    #     self.select_file_btn = QPushButton("📂 选择音频文件并分析")
    #     file_layout.addWidget(self.select_file_btn)

    #     self.file_list = QTextEdit()
    #     self.file_list.setMaximumHeight(120)
    #     self.file_list.setPlainText("""📁 最近文件
    # • recording1.wav
    # • piano_A4.wav
    # • test_audio.mp3

    # 📁 录音记录
    # • 2024-01-15.wav
    # • session_1.wav""")
    #     self.file_list.setReadOnly(True)

    #     file_layout.addWidget(self.file_list)
        # 文件系统 (文件模式)
        self.file_group = QGroupBox("文件分析系统")
        file_layout = QVBoxLayout(self.file_group)
        # 1. 文件夹路径显示和选择按钮
        # folder_layout = QHBoxLayout()
        # self.select_folder_btn = QPushButton("📂 选择文件夹")
        # self.folder_path_label = QLabel("当前目录: 未选择")
        # self.folder_path_label.setTextInteractionFlags(Qt.TextSelectableByMouse) # 路径可复制
        # folder_layout.addWidget(self.select_folder_btn)
        # folder_layout.addWidget(self.folder_path_label)
        # file_layout.addLayout(folder_layout)
        # --- 1. 文件夹路径输入框和选择按钮 ---
        folder_path_layout = QHBoxLayout()
        self.select_folder_btn = QPushButton("📂 更改目录")

        # 使用 QLineEdit 显示绝对路径
        self.folder_path_edit = QLineEdit()
        self.folder_path_edit.setReadOnly(True) # 不允许手动编辑

        folder_path_layout.addWidget(self.folder_path_edit,5)
        folder_path_layout.addWidget(self.select_folder_btn,2)
        file_layout.addLayout(folder_path_layout)

        # 2. 文件列表 (QListWidget)
        self.file_list_widget = QListWidget()
        self.file_list_widget.setMinimumHeight(120)
        file_layout.addWidget(self.file_list_widget)

        # 3. 开始分析按钮
        self.start_analysis_btn = QPushButton("▶ 开始文件分析")
        self.start_analysis_btn.setEnabled(False) # 默认禁用，直到选中文件
        # 移除旧的 self.select_file_btn ,添加新的start_analysis_btn
        file_layout.addWidget(self.start_analysis_btn)



        # 初始隐藏文件系统
        self.file_group.setVisible(False)

        # --- 初始设置默认路径 ---
        self._set_default_analysis_folder()
        # ------------------------

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
        layout.setStretchFactor(self.file_group, 3)
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

        # 占位置用的测试Label
        # self.spectrum_display = QLabel("实时频谱显示区域\n(频率波形可视化)")
        # self.spectrum_display.setAlignment(Qt.AlignCenter)
        # self.spectrum_display.setStyleSheet("""
        #     background-color: #2c3e50;
        #     color: white;
        #     padding: 50px;
        #     border: 2px solid #34495e;
        #     border-radius: 8px;
        #     font-size: 14px;
        # """)
        # self.spectrum_display.setMinimumHeight(300)
        # 替换 QLabel 为 SpectrumWidget
        if SPECTRUM_WIDGET_AVAILABLE and self.audio_detector:
            self.spectrum_widget = SpectrumWidget(self.audio_detector.sample_rate)
            self.spectrum_display = self.spectrum_widget # 保持名称兼容，但指向 widget
        else:
            self.spectrum_display = QLabel("实时频谱显示区域\n(SpectrumWidget不可用)")
            self.spectrum_display.setAlignment(Qt.AlignCenter)

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


    # RightMechanicsPanel
    #def create_right_panel(self):



    # 旧的粗糙面板
    # def create_right_panel(self):
    #     """创建右边面板 - 纯粹的力学调整"""
    #     panel = QWidget()
    #     layout = QVBoxLayout(panel)
    #     layout.setSpacing(10)

    #     # 力学调整器
    #     adjust_group = QGroupBox("力学调整")
    #     adjust_layout = QVBoxLayout(adjust_group)

    #     # 推杆模拟 - 更大的显示
    #     slider_layout = QVBoxLayout()
    #     # 先用QLabel占位置
    #     self.slider_display = QLabel("🎚️ 精密推杆调节器\n\n← 偏低 | 准确 | 偏高 →")
    #     self.slider_display.setAlignment(Qt.AlignCenter)
    #     self.slider_display.setStyleSheet("""
    #         background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    #             stop:0 #e74c3c, stop:0.4 #f39c12, stop:0.5 #27ae60,
    #             stop:0.6 #f39c12, stop:1 #e74c3c);
    #         color: white;
    #         padding: 120px 20px;
    #         border: 2px solid #7f8c8d;
    #         border-radius: 10px;
    #         font-weight: bold;
    #         font-size: 14px;
    #     """)
    #     self.slider_display.setMinimumHeight(250)
    #     # if TUNING_DIAL_AVAILABLE:
    #     #     self.tuning_inputwidget_widget = TuningDialWidget()
    #     #     # 兼容性命名，确保 _update_slider_display 可以调用
    #     #     self.slider_display = self.tuning_inputwidget_widget
    #     # else:
    #     #     self.slider_display = QLabel("🎚️ 精密推杆调节器\n(Dial Widget不可用)")

    #     slider_layout.addWidget(self.slider_display)

    #     # # 旋钮区域，占位置
    #     knob_layout = QHBoxLayout()

    #     coarse_knob = QLabel("🔘 粗调\n(±10音分)")
    #     coarse_knob.setAlignment(Qt.AlignCenter)
    #     coarse_knob.setStyleSheet("""
    #         background-color: #95a5a6;
    #         padding: 40px 20px;
    #         border-radius: 60px;
    #         border: 2px solid #7f8c8d;
    #         font-weight: bold;
    #         min-width: 100px;
    #         font-size: 12px;
    #     """)

    #     fine_knob = QLabel("🔘 微调\n(±1音分)")
    #     fine_knob.setAlignment(Qt.AlignCenter)
    #     fine_knob.setStyleSheet("""
    #         background-color: #95a5a6;
    #         padding: 30px 15px;
    #         border-radius: 50px;
    #         border: 2px solid #7f8c8d;
    #         font-weight: bold;
    #         min-width: 90px;
    #         font-size: 12px;
    #     """)
    #     # --- 旋钮区域 (使用 QDial/QLabel 模拟，保持之前的 QDial 逻辑) ---
    #     # knob_layout = QHBoxLayout()

    #     # # 模拟 QDial
    #     # self.coarse_knob = QDial()
    #     # self.fine_knob = QDial()
    #     # self.coarse_knob.setRange(-100, 100)
    #     # self.fine_knob.setRange(-20, 20)
    #     # self.coarse_knob.setNotchesVisible(True)
    #     # self.fine_knob.setNotchesVisible(True)

    #     # # knob_layout.addWidget(coarse_knob)
    #     # # knob_layout.addWidget(fine_knob)
    #     # knob_layout.addWidget(self.coarse_knob)
    #     # knob_layout.addWidget(self.fine_knob)

    #     # adjust_layout.addLayout(slider_layout)
    #     # adjust_layout.addLayout(knob_layout)
    #     # adjust_layout.setStretchFactor(slider_layout,7)
    #     # adjust_layout.setStretchFactor(knob_layout,3)

    #     # # 让力学调整组扩展到整个右边面板高度
    #     layout.addWidget(adjust_group)
    #     layout.setStretchFactor(adjust_group,1)

    #     # 1. 旋钮 (QDial) - 模拟微调或精细控制
    #     self.fine_knob = QDial()
    #     self.fine_knob.setRange(-20, 20) # 较小的范围
    #     self.fine_knob.setNotchesVisible(True)

    #     # # 2. 推杆 (QSlider) - 模拟粗调或快速调整
    #     self.coarse_slider = QSlider(Qt.Vertical) # 垂直推杆
    #     self.coarse_slider.setRange(-100, 100) # 较大的范围
    #     self.coarse_slider.setTickPosition(QSlider.TicksBothSides)

    #     # # 将输入控件放入布局
    #     knob_layout.addWidget(QLabel("旋钮 (微调)"), 1)
    #     knob_layout.addWidget(self.fine_knob, 3)
    #     knob_layout.addWidget(QLabel("推杆 (粗调)"), 1)
    #     knob_layout.addWidget(self.coarse_slider, 3) # QSlider 占更多空间

    #     # 连接信号 (在 connect_signals 中完成)

    #     adjust_layout.addLayout(slider_layout, 7)
    #     adjust_layout.addLayout(knob_layout, 3)

    #     layout.addWidget(adjust_group)

    #     return panel
    # def create_right_panel(self):
    #     """创建右边面板 - 纯粹的力学调整 (最终版本)"""
    #     panel = QWidget()
    #     layout = QVBoxLayout(panel)
    #     layout.setSpacing(10)

    #     # 力学调整器
    #     adjust_group = QGroupBox("力学调整")
    #     adjust_layout = QVBoxLayout(adjust_group)

    #     # --- 1. 输出/显示区域 (TuningDialWidget) ---
    #     slider_layout = QVBoxLayout()

    #     if TUNING_DIAL_AVAILABLE:
    #         self.tuning_inputwidget_widget = TuningDialWidget()
    #         # 使用 tuning_inputwidget_widget 作为 slider_display 的实际内容
    #         self.slider_display = self.tuning_inputwidget_widget
    #     else:
    #         # 回退到 QLabel
    #         self.slider_display = QLabel("🎚️ 精密推杆调节器\n(Dial Widget不可用)")
    #         self.slider_display.setAlignment(Qt.AlignCenter)
    #         self.slider_display.setMinimumHeight(250)

    #     slider_layout.addWidget(self.slider_display)

    #     # --- 2. 输入区域 (单旋钮 + 推杆) ---
    #     input_container = QWidget()
    #     knob_layout = QHBoxLayout(input_container)

    #     # a. 微调旋钮 (QDial)
    #     self.fine_knob = QDial()
    #     self.fine_knob.setRange(-20, 20)
    #     self.fine_knob.setNotchesVisible(True)

    #     # b. 粗调推杆 (QSlider)
    #     self.coarse_slider = QSlider(Qt.Vertical)
    #     self.coarse_slider.setRange(-100, 100)
    #     self.coarse_slider.setTickPosition(QSlider.TicksBothSides)

    #     # 将输入控件放入布局
    #     knob_layout.addWidget(QLabel("旋钮 (微调)\n输入"), 1)
    #     knob_layout.addWidget(self.fine_knob, 3)
    #     knob_layout.addWidget(QLabel("推杆 (粗调)\n输入"), 1)
    #     knob_layout.addWidget(self.coarse_slider, 3)

    #     # --- 3. 布局集成 ---
    #     adjust_layout.addLayout(slider_layout, 6) # 较大的显示区域
    #     adjust_layout.addWidget(input_container, 4) # 输入区域

    #     # 让力学调整组扩展到整个右边面板高度
    #     layout.addWidget(adjust_group)
    #     layout.setStretchFactor(adjust_group, 1)

    #     # (连接信号在 connect_signals 中完成)
    #     return panel
    # def create_right_panel(self):
    #     """创建右边面板 - 纯粹的力学调整 (最终集成版本)"""
    #     panel = QWidget()
    #     layout = QVBoxLayout(panel)
    #     layout.setSpacing(10)

    #     # 力学调整器 GroupBox
    #     adjust_group = QGroupBox("力学调整")
    #     adjust_layout = QVBoxLayout(adjust_group)

    #     # --- 1. 输出/显示区域 (TUNING_INPUT_WIDGHET_AVAILABLE) ---
    #     slider_layout = QVBoxLayout()

    #     # 使用 TUNING_INPUT_WIDGHET_AVAILABLE (美化后的仪表盘)
    #     if TUNING_INPUT_WIDGHET_AVAILABLE:
    #         self.tuning_inputwidget_widget = TuningInputWidget()
    #         # 兼容性命名：用于 _update_slider_display 接收参数
    #         self.slider_display = self.tuning_inputwidget_widget
    #     else:
    #         # 回退到 QLabel
    #         self.slider_display = QLabel("🎚️ 精密推杆调节器\n(Dial Widget不可用)")
    #         self.slider_display.setAlignment(Qt.AlignCenter)
    #         self.slider_display.setMinimumHeight(250)

    #     slider_layout.addWidget(self.slider_display)

    #     # --- 2. 输入区域 (TuningInputWidget - 单旋钮 + 推杆) ---

    #     # 引入 TuningInputWidget (它包含了旋钮、推杆和联动逻辑)
    #     if hasattr(self, 'tuning_input_widget'):
    #         # 如果之前已经初始化，则使用已有的实例
    #         input_widget = self.tuning_input_widget
    #     else:
    #         # 否则，创建一个新实例（此逻辑应在 __init__ 中完成，这里只是安全回退）
    #         # 由于我们已在 _open_piano_config_dialog 之后移除了复杂控件，我们直接在 __init__ 之后声明
    #         input_widget = TuningInputWidget()

    #     self.tuning_input_widget = input_widget

    #     adjust_layout.addLayout(slider_layout, 6) # 较大的显示区域
    #     adjust_layout.addWidget(self.tuning_input_widget, 4) # 输入区域

    #     # --- 连接信号 (在 connect_signals 中完成) ---

    #     # 让力学调整组扩展到整个右边面板高度
    #     layout.addWidget(adjust_group)
    #     layout.setStretchFactor(adjust_group, 1)

    #     return panel

    # ===================================================
    #   MainWindow -> Panel (数据发送函数)
    # ===================================================
    def inform_right_target(self, target_freq: float):
        """设置调律的目标频率，并通知 RightMechanicsPanel。"""
        if hasattr(self, 'right_panel'):
            self.right_panel.set_target_frequency(target_freq)
            # 示例：更新主窗口状态
            # self.update_status(f"目标频率已设置为: {target_freq:.2f} Hz")
    def inform_right_current(self, current_freq: float):
        """设置调律的目标频率，并通知 RightMechanicsPanel。"""
        if hasattr(self, 'right_panel'):
            self.right_panel.set_current_frequency(current_freq)
            # 示例：更新主窗口状态
            # self.update_status(f"目标频率已设置为: {target_freq:.2f} Hz")
    def inform_right_params(self,I:float,r:float,k:float,k_d:float):
        if hasattr(self, 'right_panel'):
            self.right_panel.set_params(I=I,r=r,k=k,k_d=k_d)


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

        # # 编辑菜单
        # edit_menu = menubar.addMenu("✏️ 编辑(&E)")
        # edit_menu.addAction("⭐ 参数预设")
        # edit_menu.addAction("📋 复制数据")
        # edit_menu.addAction("🧹 清空记录")

        # # 视图菜单
        # view_menu = menubar.addMenu("👁️ 视图(&V)")
        # view_menu.addAction("📈 频谱显示选项")
        # view_menu.addAction("🎹 钢琴窗主题")
        # view_menu.addAction("🎨 界面主题")
        # view_menu.addSeparator()
        # view_menu.addAction("🖥️ 全屏模式")

        # # 工具菜单
        # tools_menu = menubar.addMenu("🛠️ 工具(&T)")
        # tools_menu.addAction("🎧 音频设备配置")
        # tools_menu.addAction("🔊 参考音生成器")
        # tools_menu.addAction("⚖️ 频率校准工具")
        # tools_menu.addAction("📁 批量文件分析")

        # --- 新增：参数菜单 ---
        params_menu = menubar.addMenu("⚙️ 参数(&P)")

        # 1. 钢琴参数配置
        self.action_piano_config = QAction("🎹 钢琴物理参数配置", self)
        self.action_piano_config.triggered.connect(self._open_piano_config_dialog)
        params_menu.addAction(self.action_piano_config)

        # 2. 摩擦模型配置
        self.action_friction_config = QAction("⚖️ 摩擦模型配置", self)
        self.action_friction_config.triggered.connect(self._open_friction_config_dialog)
        params_menu.addAction(self.action_friction_config)

        # 3. 施力敏感度 (K_D)
        self.action_kd_config = QAction("💪 施力敏感度 (K_D) 设置", self)
        self.action_kd_config.triggered.connect(self._open_kd_config_dialog)
        params_menu.addAction(self.action_kd_config)
        # ------------------------

        # 设置菜单
        settings_menu = menubar.addMenu("⚙️ 设置(&S)")

        # 分析摘要保存
        self.action_toggle_save_prompt = QAction("分析完成保存分析摘要", self)
        self.action_toggle_save_prompt.setCheckable(True)
        self.action_toggle_save_prompt.setChecked(self.settings_auto_prompt_save)
        self.action_toggle_save_prompt.triggered.connect(self._toggle_save_prompt_setting) # <-- 连接到正确的提示方法
        # 录音文件保存
        self.action_toggle_save_recording = QAction("分析完成保存录音文件", self)
        self.action_toggle_save_recording.setCheckable(True)
        self.action_toggle_save_recording.setChecked(self.settings_save_recording_file)
        self.action_toggle_save_recording.triggered.connect(self._toggle_save_recording_setting)

        # --- 最大录音时长子菜单 ---
        max_time_menu = settings_menu.addMenu("最大录音时长")
        # QActionGroup 确保只有一个选项被选中
        self.max_time_action_group = QActionGroup(self)
        self.max_time_action_group.setExclusive(True)

        for time_s in self.max_recording_time_options:
            action = QAction(f"{time_s} 秒", self, checkable=True)
            action.setData(time_s) # 将秒数存储在 QAction 的 Data 属性中

            if time_s == self.settings_max_recording_time:
                action.setChecked(True)

            self.max_time_action_group.addAction(action)
            max_time_menu.addAction(action)

        # 连接 QActionGroup 的 triggered 信号来处理选择变化
        self.max_time_action_group.triggered.connect(self._set_max_recording_time)
        # ----------------------------------------------------

        # --- 音名系统设置子菜单 ---
        accidental_menu = settings_menu.addMenu("音名系统设置")
        # QActionGroup 确保只有一个选项被选中
        self.accidental_action_group = QActionGroup(self)
        self.accidental_action_group.setExclusive(True)

        # 1. 升号选项
        self.action_sharp = QAction("升号 (#) 系统", self, checkable=True)
        self.action_sharp.setData(AccidentalType.SHARP)
        if self.settings_accidental_type == AccidentalType.SHARP:
            self.action_sharp.setChecked(True)

        # 2. 降号选项
        self.action_flat = QAction("降号 (b) 系统", self, checkable=True)
        self.action_flat.setData(AccidentalType.FLAT)
        if self.settings_accidental_type == AccidentalType.FLAT:
            self.action_flat.setChecked(True)

        # 添加到组和菜单
        self.accidental_action_group.addAction(self.action_sharp)
        self.accidental_action_group.addAction(self.action_flat)
        accidental_menu.addAction(self.action_sharp)
        accidental_menu.addAction(self.action_flat)

        # 连接 triggered 信号
        self.accidental_action_group.triggered.connect(self._set_accidental_type)
        # ----------------------------------------------------


        # 添加分隔线，区分不同类别的设置.其上为选择项，其下为直接设置项
        settings_menu.addSeparator()

        # 加入设置
        settings_menu.addAction(self.action_toggle_save_recording)
        settings_menu.addAction(self.action_toggle_save_prompt)

        # settings_menu.addAction("🎹 钢琴数据库管理")
        # settings_menu.addAction("🎻 琴弦密度配置")
        # settings_menu.addAction("🎵 音名系统设置")
        # settings_menu.addAction("🎶 钢琴窗音色配置")
        # settings_menu.addSeparator()
        # settings_menu.addAction("🔧 高级音频设置")

        # 帮助菜单
        help_menu = menubar.addMenu("❓ 帮助(&H)")
        help_menu.addAction("📖 用户手册")
        help_menu.addAction("🔍 算法说明")
        help_menu.addAction("⌨️ 快捷键列表")
        help_menu.addSeparator()
        help_menu.addAction("ℹ️ 关于")



    def _open_piano_config_dialog(self):
        """打开钢琴物理参数配置对话框"""
        if not PIANO_CONFIG_WIDGET_AVAILABLE:
            QMessageBox.critical(self, "错误", "钢琴配置模块未找到。")
            return

        # 收集当前参数
        current_params = {
            'mech_I': self.mech_I,
            'mech_r': self.mech_r,
            'mech_k': self.mech_k,
        }

        # 使用 QDialog 来承载 PianoConfigWidget
        dialog = QDialog(self)
        config_widget = PianoConfigWidget(current_params,self.db_manager, dialog)

        # 连接信号：当 widget 发出保存信号时，执行更新逻辑
        config_widget.config_saved.connect(self._update_global_physics_params)
        # 连接信号: 参数文件路径更改信号
        config_widget.config_saved.connect(self._update_global_physics_params)
        config_widget.db_config_updated.connect(self._handle_db_config_update)

        dialog.setLayout(QVBoxLayout(dialog))
        dialog.layout().addWidget(config_widget)
        dialog.setWindowTitle(config_widget.windowTitle())
        dialog.setModal(True) # 设置为模态对话框


        # 绝对绝对绝对绝对不要注释下面这个handle_dialog_close，不然取消和x就关不了了
        # # --- 拦截 QDialog 的关闭事件 ---
        def handle_dialog_close(allowed: bool):
            """处理来自 PianoConfigWidget 的关闭请求信号"""
            if allowed:
                print("allow to close")
                dialog.accept() # 允许关闭对话框
            # 否则不执行任何操作，对话框保持打开

        config_widget.request_close.connect(handle_dialog_close)

        # 拦截 QDialog 自身的关闭按钮 (X 按钮)
        def dialog_close_handler(event):
            """拦截对话框的 X 按钮点击"""
            event.ignore() # 默认阻止关闭
            config_widget.request_close_action() # 触发 Widget 的校验逻辑

        dialog.closeEvent = dialog_close_handler


        # 3. 让按钮连接到父级对话框的关闭请求
        config_widget.btn_cancel.clicked.disconnect() # 断开旧连接
        config_widget.btn_cancel.clicked.connect(config_widget.request_close_action) # 取消按钮也触发校验

        dialog.exec()

    def _update_global_physics_params(self, new_params: Dict[str, Any]):
        """接收任何配置窗口发出的信号，更新内部参数并持久化"""
        try:
            # 1. 更新实例变量 (仅更新传入的参数)
            self.mech_I = new_params.get('mech_I', self.mech_I)
            self.mech_r = new_params.get('mech_r', self.mech_r)
            self.mech_k = new_params.get('mech_k', self.mech_k)
            self.mech_Kd = new_params.get('mech_Kd', self.mech_Kd)
            # 摩擦参数
            self.mech_fric_limit_0 = new_params.get('mech_fric_limit_0', self.mech_fric_limit_0)
            self.mech_alpha = new_params.get('mech_alpha', self.mech_alpha)
            self.mech_kinetic = new_params.get('mech_kinetic', self.mech_kinetic)
            self.mech_sigma = new_params.get('mech_sigma', self.mech_sigma)

            # 更新 StringCSVManager 的文件路径
            new_db_path = new_params.get('db_file_path')
            if new_db_path and self.db_manager:
                self.db_manager.file_path = new_db_path
                self.db_manager._initialize_file() # 确保新路径下的文件被初始化/校验
            # --------------------------------------------------

            # 2. 更新集中配置数据 (MainWindow 持有最终状态)
            self.config_data.update(new_params)
            # 3. 执行持久化
            self.config_manager.save_config(self.config_data)

            self.update_status("物理参数已更新并保存。")

            # TODO: 未来需要通知 MechanicalEngine 模块更新这些参数
            # if self.mechanical_engine:
            #     self.mechanical_engine.update_parameters(new_params)

            self.inform_right_params(self.mech_I,self.mech_r,self.mech_k,self.mech_Kd)

        except Exception as e:
            self.update_status(f"更新参数失败: {e}")
            QMessageBox.critical(self, "更新错误", f"更新钢琴参数失败:\n{e}")
    # 占位置用
    # def _open_friction_config_dialog(self):
    #     """打开摩擦模型配置对话框（包括模型选择和参数）"""
    #     # --- 核心逻辑说明 ---
    #     # 这个对话框需要一个 QComboBox 来选择模型 (目前只有 Limit_Friction)
    #     # 还需要输入框来配置 τ_fric_limit_0, α, τ_kinetic, σ。
    #     # ---
    #     self.update_status("等待实现：打开摩擦模型配置对话框。")
    #     msg = (f"当前模型: {self.mech_friction_model}\n"
    #            f"初始静摩擦 τ_fric_limit_0: {self.mech_fric_limit_0} N·m\n"
    #            f"摩擦增长系数 α: {self.mech_alpha}\n"
    #            f"动摩擦扭矩 τ_kinetic: {self.mech_kinetic} N·m\n"
    #            f"粘性摩擦系数 σ: {self.mech_sigma}")
    #     QMessageBox.information(self, "摩擦模型配置", msg)
    def _open_friction_config_dialog(self):
        """打开摩擦模型配置对话框"""
        if not FRICTION_CONFIG_WIDGET_AVAILABLE:
            QMessageBox.critical(self, "错误", "摩擦配置模块未找到。")
            return

        # 收集当前摩擦参数
        current_params = {
            'mech_fric_limit_0': self.mech_fric_limit_0,
            'mech_alpha': self.mech_alpha,
            'mech_kinetic': self.mech_kinetic,
            'mech_sigma': self.mech_sigma,
        }

        dialog = QDialog(self)
        friction_widget = FrictionConfigWidget(current_params, dialog)

        # 连接信号：统一连接到更新全局参数的槽函数
        friction_widget.config_saved.connect(self._update_global_physics_params)

        dialog.setLayout(QVBoxLayout(dialog))
        dialog.layout().addWidget(friction_widget)
        dialog.setWindowTitle(friction_widget.windowTitle())
        dialog.setModal(True)
        dialog.exec()


    def _open_kd_config_dialog(self):
        """打开施力敏感度 K_D 配置对话框"""
        # --- 核心逻辑说明 ---
        # 这是一个简单的配置，可以使用 QInputDialog 或小型对话框
        # ---
        self.update_status("等待实现：打开施力敏感度 (K_D) 设置对话框。")
        current_Kd = self.mech_Kd
        new_Kd, ok = QInputDialog.getDouble(
            self,
            "施力敏感度 (K_D) 设置",
            "设置虚拟力敏感度 K_D (建议 0.1 - 2.0):",
            current_Kd,
            decimals=3
            # decimals=3,
            # min=-10.0,
            # max=10.0
        )
        if ok:
            self.mech_Kd = new_Kd
            self.update_status(f"施力敏感度 K_D 已更新为: {new_Kd}")
            self.inform_right_params(I=self.mech_I,r=self.mech_r,k=self.mech_k,k_d=new_Kd)



        # def _set_accidental_type(self, action: QAction):
    #     """处理音名系统（升降号）的选择"""
    #     new_type = action.data()
    #     if new_type != self.settings_accidental_type:
    #         self.settings_accidental_type = new_type
    #         # 重新初始化钢琴系统以应用新的音名命名规则
    #         self.init_piano_system()
    #         # 更新状态栏
    #         type_str = "升号 (#)" if new_type == AccidentalType.SHARP else "降号 (b)"
    #         self.update_status(f"音名系统已切换到 {type_str}。")
    #         if hasattr(self, 'piano_window'):
    #              self.piano_window.update_note_labels(self.piano_generator)

    def _set_accidental_type(self, action: QAction):
        """处理音名系统（升降号）的选择，并刷新UI"""
        new_type = action.data()
        if new_type != self.settings_accidental_type:
            self.settings_accidental_type = new_type
            # 1. 重新初始化钢琴系统以应用新的音名命名规则
            self.init_piano_system()
            # 2. 刷新 UI 组件
            if self.piano_generator:
                # --- A. 刷新 QComboBox (音名选择框) ---
                if hasattr(self, 'note_selector'):
                    self.note_selector.blockSignals(True) # 阻止信号，避免在填充时触发不必要的 set_target_note
                    self.note_selector.clear()
                    # 重新获取并填充所有 88 个键的音名
                    note_names = sorted(self.piano_generator.export_key_frequencies().keys(),
                                        key=lambda n: self.piano_generator.get_key_by_note_name(n).midi_number)
                    self.note_selector.addItems(note_names)
                    # 重新选择当前调律目标（例如，如果目标是 A4，保持选中 A4）
                    if self.target_key:
                        self.note_selector.setCurrentText(self.target_key.note_name)
                        self.set_target_note(self.target_key.note_name)
                    # self.note_selector.setCurrentText(self.default_target_note_name)
                    self.note_selector.blockSignals(False) # 恢复信号
                # --- B. 刷新 PianoWidget (钢琴窗) ---
                if hasattr(self, 'piano_widget'):
                    # 强制 PianoWidget 重新绘制整个键盘
                    self.piano_widget.update()
            # 3. 更新状态栏
            type_str = "升号 (#)" if new_type == AccidentalType.SHARP else "降号 (b)"
            self.update_status(f"音名系统已切换到 {type_str}。")


    # 处理最大录音时长选择的方法
    def _set_max_recording_time(self, action: QAction):
        """处理用户在菜单中选择的最大录音时长"""
        selected_time = action.data()
        self.settings_max_recording_time = selected_time
        self.update_status(f"最大录音时长已设置为 {selected_time} 秒。")

    def _toggle_save_prompt_setting(self):
            """切换分析完成后是否弹出保存对话框的设置"""
            self.settings_auto_prompt_save = self.action_toggle_save_prompt.isChecked()
            state = "开启" if self.settings_auto_prompt_save else "关闭"
            self.update_status(f"分析完成弹出保存提示功能已{state}")
    def _toggle_save_recording_setting(self):
            """切换实时分析时是否保存录音文件的设置"""
            self.settings_save_recording_file = self.action_toggle_save_recording.isChecked()
            state = "开启" if self.settings_save_recording_file else "关闭"
            self.update_status(f"实时分析保存录音文件功能已{state}")

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
        # # 文件分析按钮
        # if hasattr(self, 'select_file_btn'):
        #     self.select_file_btn.clicked.connect(self.on_analyse_file_clicked)
        # 文件分析系统连接
        self.select_folder_btn.clicked.connect(self.on_select_folder_clicked)
        # 列表项选中时，启用分析按钮
        self.file_list_widget.itemSelectionChanged.connect(self.on_file_selection_changed)
        self.start_analysis_btn.clicked.connect(self.on_start_file_analysis_clicked)
        # 实时模式下，禁用暂停按钮
        self.pause_btn.setEnabled(False) # 实时录音/处理线程模型下，暂停逻辑较复杂，先禁用

        # 钢琴逻辑
        if PIANO_MODULES_AVAILABLE:
            # 1. 连接 QComboBox 改变事件
            self.note_selector.currentTextChanged.connect(self.on_note_selector_changed)

            # 2. 连接 PianoWidget 鼠标点击事件
            self.piano_widget.key_clicked.connect(self.on_note_selector_changed) # 鼠标点击也使用相同的槽函数

        # 力学调整器
        # if hasattr(self, 'coarse_knob'):
        #     self.coarse_knob.valueChanged.connect(self._update_coarse_input)
        # if hasattr(self, 'fine_knob'):
        #     self.fine_knob.valueChanged.connect(self._update_fine_input)
        # if hasattr(self, 'coarse_slider'):
        #     # 推杆连接到处理粗调的方法
        #     self.coarse_slider.valueChanged.connect(self._update_coarse_slider_input)
        # if hasattr(self, 'fine_knob'):
        #     # 旋钮连接到处理微调的方法
        #     self.fine_knob.valueChanged.connect(self._update_fine_knob_input)
        # --- 力学调整器连接 ---
        # 连接 TuningInputWidget 的输入信号到驱动逻辑
        # if hasattr(self, 'tuning_input_widget'):
        #     self.tuning_input_widget.input_changed.connect(self._handle_input_change)
        #     self.tuning_input_widget.drag_started.connect(self._start_simulation_session)
        #     self.tuning_input_widget.drag_ended.connect(self._end_simulation_session)
        # # ----------------------

    def _get_default_recording_path(self) -> str:
        """获取项目默认的录音/分析文件夹路径：工作路径/recordings"""
        # 获取当前文件所在目录的上级目录 (项目根目录)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)

        # 目标路径：[Project_Root]/recordings
        default_path = os.path.join(project_root, 'recordings')

        # 确保目录存在
        if not os.path.exists(default_path):
            try:
                os.makedirs(default_path)
            except Exception as e:
                # 如果创建失败，使用用户文档目录作为备用
                print(f"创建默认目录失败: {e}. 使用文档目录备用。")
                default_path = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)

        return default_path

    def _set_default_analysis_folder(self):
        """设置默认分析文件夹路径，更新 UI 并加载文件列表"""
        default_folder = self._get_default_recording_path()
        self.current_analysis_folder = default_folder

        # 更新 QLineEdit
        if hasattr(self, 'folder_path_edit'):
            self.folder_path_edit.setText(default_folder)

        self.update_file_list(default_folder)
        self.update_status(f"文件分析默认目录已加载：{default_folder}")

    # 为了绘制频谱，这段就注释了
    # def on_analyse_file_clicked(self):
    #     """处理文件分析模式下的文件选择和分析"""
    #     if not self.audio_detector or not self.piano_generator:
    #         self.update_status("错误：音频或钢琴模块未初始化")
    #         return
    #     # 弹出文件选择对话框
    #     file_dialog = QFileDialog(self, "选择音频文件", os.getcwd(), "音频文件 (*.wav *.mp3 *.flac)")
    #     if file_dialog.exec():
    #         file_path = file_dialog.selectedFiles()[0]
    #         self.update_status(f"开始分析文件: {os.path.basename(file_path)}")
    #         # 获取当前目标频率
    #         current_target_freq = self.target_key.frequency if self.target_key else None
    #         # 执行同步文件分析
    #         analysis_result = self.audio_detector.analyse_audio_file(
    #             file_path=file_path,
    #             target_frequency=current_target_freq
    #         )
    #         if analysis_result:
    #             self.update_status(f"文件分析完成。主导频率: {analysis_result.dominant_frequency:.1f} Hz")

    #             # --- 关键：文件分析结果可视化 ---
    #             # 为了绘制频谱，我们需要整个音频文件的FFT，或者在分析时就将分帧数据缓存。
    #             # 由于 AudioDetector.analyse_audio_file 仅返回统计结果，我们不能直接获得帧数据。
    #             # 暂时：仅显示最终结果，并提示用户切换到实时模式查看波形。

    #             # TODO: (未来优化) 修改 AudioDetector.analyse_audio_file，让其返回处理后的波形/频谱帧数据列表。

    #             # 临时处理：更新状态和推杆（使用平均偏差）
    #             mean_cents = np.mean([r.cents_deviation for r in analysis_result.pitch_results if r.cents_deviation is not None])
    #             self._update_slider_display(mean_cents)
    #         else:
    #             self.update_status("文件分析失败。")
    # on_analyse_file_clicked改名为on_start_file_analysis_clicked
    # def on_analyse_file_clicked(self):
    #     """
    #     处理文件分析模式下的文件选择和分析。
    #     分析完成后，显示整体波形图和平均音分偏差。
    #     """
    #     if not self.audio_detector or not self.piano_generator:
    #         self.update_status("错误：音频或钢琴模块未初始化")
    #         return

    #     # 弹出文件选择对话框
    #     file_dialog = QFileDialog(self, "选择音频文件", os.getcwd(), "音频文件 (*.wav *.mp3 *.flac)")
    #     if file_dialog.exec():
    #         file_path = file_dialog.selectedFiles()[0]
    #         self.update_status(f"开始分析文件: {os.path.basename(file_path)}")

    #         # 获取当前目标频率
    #         current_target_freq = self.target_key.frequency if self.target_key else None

    #         # 执行同步文件分析
    #         analysis_result = self.audio_detector.analyse_audio_file(
    #             file_path=file_path,
    #             target_frequency=current_target_freq
    #         )

    #         if analysis_result:
    #             # 1. 更新状态信息
    #             self.update_status(f"文件分析完成。主导频率: {analysis_result.dominant_frequency:.1f} Hz")

    #             # 2. 更新推杆显示（使用平均偏差）
    #             # 排除 None 值后计算平均音分偏差
    #             cents_values = [r.cents_deviation for r in analysis_result.pitch_results if r.cents_deviation is not None]
    #             if cents_values:
    #                 mean_cents = np.mean(cents_values)
    #                 self._update_slider_display(mean_cents)
    #             else:
    #                 self._update_slider_display(0.0) # 无有效检测结果，偏差设为0

    #             # 3. 绘制整体波形图 (文件分析的核心可视化)
    #             if hasattr(self, 'spectrum_widget') and analysis_result.full_audio_data is not None:
    #                 # 传入完整的音频数据，并标记为整体图模式 (is_full_file=True)
    #                 self.spectrum_widget.update_frame(analysis_result.full_audio_data, is_full_file=True)
    #             else:
    #                 self.update_status("警告：无法绘制整体波形，SpectrumWidget或数据缺失。")
    #         else:
    #             self.update_status("文件分析失败。")

    def progress_update_callback(self, progress: AnalysisProgress):
        """接收 AudioDetector 发送的进度信息并更新 QProgressBar"""

        if hasattr(self, 'progress_bar'):
            percentage = int(progress.progress_percentage)
            self.progress_bar.setValue(percentage)

            # 更新状态栏显示当前分析算法和剩余时间
            status_msg = (f"分析中: {progress.current_algorithm} | "
                          f"进度: {percentage:.1f}% | "
                          f"剩余: {progress.estimated_remaining_time:.1f}s")
            self.update_status(status_msg)

            # 强制 Qt 处理事件，确保进度条实时更新
            QApplication.processEvents()


    def on_start_file_analysis_clicked(self):
        """
        处理文件分析模式下的文件选择和分析。
        分析完成后，显示整体波形图和平均音分偏差。
        """
        if not self.audio_detector or not self.piano_generator:
            self.update_status("错误：音频或钢琴模块未初始化")
            return

        selected_items = self.file_list_widget.selectedItems()
        if not selected_items or not hasattr(self, 'current_analysis_folder'):
            self.update_status("请先选择一个文件并确保已选择文件夹。")
            return
        # 构造完整文件路径
        selected_file_name = selected_items[0].text()
        file_path = os.path.join(self.current_analysis_folder, selected_file_name)

        self.update_status(f"开始分析文件: {selected_file_name}")

        # --- 进度和按钮控制开始 ---
        self.start_analysis_btn.setEnabled(False) # 禁用开始按钮，防止重复点击
        self.select_folder_btn.setEnabled(False) # 禁用更改目录
        self.mode_realtime.setEnabled(False) # <--- 禁用实时模式按钮
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True) # 显示进度条
        self.audio_detector.set_progress_callback(self.progress_update_callback) # 设置进度回调
        # ---------------------------

        # 获取当前目标频率
        current_target_freq = self.target_key.frequency if self.target_key else None
        start_time = time.time() # <-- 记录开始时间
        try:
            # 执行同步文件分析
            analysis_result = self.audio_detector.analyse_audio_file(
                file_path=file_path,
                target_frequency=current_target_freq
            )
            total_analysis_time = time.time() - start_time # <-- 计算总耗时

            # if file_dialog.exec():
            #     file_path = file_dialog.selectedFiles()[0]
            #     self.update_status(f"开始分析文件: {os.path.basename(file_path)}")

            #     # 获取当前目标频率
            #     current_target_freq = self.target_key.frequency if self.target_key else None

            #     # 执行同步文件分析
            #     analysis_result = self.audio_detector.analyse_audio_file(
            #         file_path=file_path,
            #         target_frequency=current_target_freq
            #     )

            if analysis_result:
                self.last_analysis_freq = analysis_result.dominant_frequency
                # 1. 更新状态信息
                self.update_status(f"文件分析完成。主导频率: {analysis_result.dominant_frequency:.1f} Hz")

                # 2. 通知调整面板（使用平均偏差）
                # 排除 None 值后计算平均音分偏差
                cents_values = [r.cents_deviation for r in analysis_result.pitch_results if r.cents_deviation is not None]
                if cents_values:
                    mean_cents = np.mean(cents_values)
                    # self._update_slider_display(mean_cents)
                    self.inform_right_current(analysis_result.dominant_frequency)
                else:
                    # self._update_slider_display(0.0) # 无有效检测结果，偏差设为0
                    uuuu=1+2

                # 3. 绘制整体波形图 (文件分析的核心可视化)
                if hasattr(self, 'spectrum_widget') and analysis_result.full_audio_data is not None:
                    # 传入完整的音频数据，并标记为整体图模式 (is_full_file=True)
                    self.spectrum_widget.update_frame(analysis_result.full_audio_data, is_full_file=True)
                else:
                    self.update_status("警告：无法绘制整体波形，SpectrumWidget或数据缺失。")
                # --- 调用后分析结果保存的处理逻辑 ---
                self._handle_post_analysis(analysis_result, file_path, total_analysis_time) # <-- 传递耗时
                # ----------------------
            else:
                self.update_status("文件分析失败。")
        except Exception as e:
            self.update_status(f"分析过程中发生错误: {e}")
        finally:
            # --- 进度和按钮控制结束 ---
            self.audio_detector.set_progress_callback(None) # 清除回调
            self.progress_bar.setVisible(False) # 隐藏进度条
            self.progress_bar.setValue(0)
            self.start_analysis_btn.setEnabled(True) # 恢复开始按钮
            self.select_folder_btn.setEnabled(True) # 恢复更改目录
            self.mode_realtime.setEnabled(True) # <--- 恢复实时模式按钮

    def on_select_folder_clicked(self):
        """打开文件夹对话框，选择分析目录，并填充文件列表"""
        # 使用 QFileDialog.getExistingDirectory()
        # folder_path = QFileDialog.getExistingDirectory(self, "选择包含音频文件的文件夹", os.getcwd())
        folder_path = QFileDialog.getExistingDirectory(self, "选择包含音频文件的文件夹", self.current_analysis_folder or os.getcwd())

        if folder_path:
            self.current_analysis_folder = folder_path
            # self.folder_path_label.setText(f"当前目录: {os.path.basename(folder_path)}")
            # 更新 QLineEdit
            if hasattr(self, 'folder_path_edit'):
                self.folder_path_edit.setText(folder_path)

            self.file_list_widget.clear()
            self.update_file_list(folder_path)
            self.update_status(f"已加载文件夹: {os.path.basename(folder_path)}")
        else:
            self.update_status("未选择文件夹。")

    def update_file_list(self, folder_path: str):
        """根据文件夹路径，筛选音频文件并填充 QListWidget"""
        audio_extensions = ('.wav', '.mp3', '.flac', '.aiff', '.ogg') # 识别的音频扩展名
        self.file_list_widget.clear()

        try:
            for item_name in os.listdir(folder_path):
                if item_name.lower().endswith(audio_extensions):
                    # 仅添加文件名
                    QListWidgetItem(item_name, self.file_list_widget)
        except Exception as e:
            self.update_status(f"读取文件列表失败: {e}")

    def on_file_selection_changed(self):
        """文件选择状态改变时，更新开始分析按钮的状态"""
        # 只要有选中项，就启用分析按钮
        is_selected = len(self.file_list_widget.selectedItems()) > 0
        self.start_analysis_btn.setEnabled(is_selected)

    def on_mode_changed(self):
        """模式切换"""
        if self.mode_realtime.isChecked():
            self.record_group.setVisible(True)
            self.file_group.setVisible(False)
            self.update_status("切换到实时分析模式")
            # 清除频谱显示
            if hasattr(self, 'spectrum_widget'):
                self.spectrum_widget.update_frame(np.array([]))
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
        # 获取当前目标频率
        current_target_freq = self.target_key.frequency if self.target_key else None

        # 获取当前的录音保存设置
        save_file_setting = self.settings_save_recording_file # <-- 读取设置状态

        # 定义一个包装函数，在音频线程中发射信号
        # def real_time_pitch_callback(result: PitchResult):
        #     # 这是一个在 AudioDetector 内部线程中运行的回调
        #     self.pitch_signal.pitch_detected.emit(result)
        def real_time_pitch_callback(realtime_data: RealtimeData):
            self.pitch_signal.pitch_detected.emit(realtime_data) # 传递 RealtimeData
        # 业务逻辑
        if self.audio_detector.start_realtime_analysis(pitch_callback=real_time_pitch_callback,
                                                        save_recording=save_file_setting,
                                                        target_frequency=current_target_freq):
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            # self.pause_btn.setEnabled(True) # 先禁用暂停
            self.mode_file.setEnabled(False) # <--- 禁用文件模式按钮
            # 启动计时器
            self.record_start_time = time.time()
            self.record_timer.start(1000) # 每秒更新一次
            self.update_status("实时分析启动成功，录音进行中...")
        else:
            self.update_status("实时分析启动失败")


    # 现在已经将实时录音模式的分析改成录音结束后绘制频谱了
    # def on_stop_recording(self):
    #     """停止录音"""
    #     if not self.audio_detector:
    #         return
    #     # 保存文件
    #     recording_file = self.audio_detector.stop_realtime_analysis()
    #     self.record_timer.stop()
    #     self.duration_label.setText("⏱ 时长: 00:00")
    #     # 按钮
    #     self.start_btn.setEnabled(True)
    #     self.stop_btn.setEnabled(False)
    #     self.pause_btn.setEnabled(False)
    #     # 后处理
    #     if recording_file:
    #         self.update_status(f"录音已停止。文件已保存: {os.path.basename(recording_file)}")
    #     else:
    #         self.update_status("录音已停止。未保存文件或停止失败")

    def on_stop_recording(self):
        """停止录音，并触发分析（如果当前是实时模式）"""
        if not self.audio_detector:
            return

        # 0. 禁用所有控制按钮，防止重复点击
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(False) # 立即禁用 STOP 按钮
        self.pause_btn.setEnabled(False)

        # 1. 停止录音线程和流，并获取录音文件路径
        recording_file = self.audio_detector.stop_realtime_analysis()

        self.record_timer.stop()
        self.duration_label.setText("⏱ 时长: 00:00")

        # self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)

        # # 2. 如果成功录制了文件，则立即分析
        # if recording_file:
        #     self.update_status(f"录音已停止。文件已保存: {os.path.basename(recording_file)}。正在进行分析...")

        #     # 自动进行文件分析（复用 on_analyse_file_clicked 的核心逻辑）
        #     self._auto_analyse_recording(recording_file)

        # else:
        #     self.update_status("录音已停止。未保存文件或停止失败")
        # self.start_btn.setEnabled(True) # 恢复start
        # # 恢复 RadioButton 状态
        # self.mode_file.setEnabled(True)
        # self.mode_realtime.setEnabled(True)

        # 2. 始终执行分析，并记录是否需要删除
        if recording_file:
            self.update_status(f"录音已停止。文件已保存: {os.path.basename(recording_file)}。正在进行分析...")

            # 如果设置是关闭的，将文件添加到待删除列表
            if not self.settings_save_recording_file:
                self.temp_files_to_delete.append(recording_file)

            # 自动进行文件分析
            self._auto_analyse_recording(recording_file)

        else:
            self.update_status("录音已停止。未保存文件或停止失败")
        self.start_btn.setEnabled(True) # 恢复 START 按钮
        # 恢复 RadioButton 状态
        if hasattr(self, 'mode_file'):
            self.mode_file.setEnabled(True)
        if hasattr(self, 'mode_realtime'):
            self.mode_realtime.setEnabled(True)

    def _clean_up_temp_files(self):
        """分析完成后，删除临时文件列表中的文件"""
        files_removed = 0
        for file_path in self.temp_files_to_delete:
            try:
                os.remove(file_path)
                files_removed += 1
            except Exception as e:
                print(f"删除文件失败 {file_path}: {e}")

        if files_removed > 0:
            self.update_status(f"已清理 {files_removed} 个临时录音文件。")

        self.temp_files_to_delete.clear()

    def _auto_analyse_recording(self, file_path: str):
        """
        录音结束后自动执行文件分析和整体绘制。
        这个方法与 on_analyse_file_clicked 的核心逻辑相同，但输入源是固定的。
        """

        if not self.audio_detector or not self.piano_generator:
            self.update_status("错误：音频或钢琴模块未初始化")
            return

        # --- 进度控制开始 ---
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True) # 显示进度条
        self.audio_detector.set_progress_callback(self.progress_update_callback) # 设置进度回调
        # --------------------

        # 确保当前目标频率
        current_target_freq = self.target_key.frequency if self.target_key else None

        start_time = time.time() # <-- 记录开始时间
        # 执行同步文件分析
        analysis_result = self.audio_detector.analyse_audio_file(
            file_path=file_path,
            target_frequency=current_target_freq
        )
        total_analysis_time = time.time() - start_time # <-- 计算总耗时
        try:
            if analysis_result:
                # 1. 更新状态信息
                self.last_analysis_freq = analysis_result.dominant_frequency
                self.update_status(f"分析完成。主导频率: {analysis_result.dominant_frequency:.1f} Hz")

                # 2. 通知调整面板（使用平均偏差）
                cents_values = [r.cents_deviation for r in analysis_result.pitch_results if r.cents_deviation is not None]
                if cents_values:
                    mean_cents = np.mean(cents_values)
                    # self._update_slider_display(mean_cents)
                    self.inform_right_current(analysis_result.dominant_frequency)

                else:
                    # self._update_slider_display(0.0)
                    uuuu=1+2

                # 3. 绘制整体波形图
                if hasattr(self, 'spectrum_widget') and analysis_result.full_audio_data is not None:
                    self.spectrum_widget.update_frame(analysis_result.full_audio_data, is_full_file=True)
                else:
                    self.update_status("警告：无法绘制整体波形，SpectrumWidget或数据缺失。")
                # --- 调用后保存分析结果的处理逻辑 ---
                self._handle_post_analysis(analysis_result, file_path, total_analysis_time) # <-- 传递耗时
                # ----------------------
            else:
                self.update_status("自动文件分析失败。")
        except Exception as e:
            self.update_status(f"分析过程中发生错误: {e}")
        finally:
            # --- 进度控制结束 ---
            self.audio_detector.set_progress_callback(None) # 清除回调
            self.progress_bar.setVisible(False) # 隐藏进度条
            self.progress_bar.setValue(0)
            # 确保主按钮恢复（已在 on_stop_recording 中处理，但这里再次确认）
            self.start_btn.setEnabled(True)
            # 清理文件
            self._clean_up_temp_files()

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

    def on_pitch_detected_update_ui(self, result: RealtimeData):
        """
        接收到实时音高结果，在主线程中安全地更新 UI。
        这是连接音频模块和用户界面的核心。
        """
        # 修改：从 RealtimeData 中解包 PitchResult 和 audio_frame
        result = realtime_data.pitch_result
        audio_frame = realtime_data.audio_frame

        # 1. 计算音分偏差
        cents = result.cents_deviation if result.cents_deviation is not None else 0.0

        # 2. 更新状态显示
        status_message = (f"频率: {result.frequency:.1f} Hz "
                          f"| 目标: {result.target_frequency:.1f} Hz "
                          f"| 偏差: {cents:+.2f} 音分 "
                          f"| 置信度: {result.confidence:.2f}")
        self.update_status(status_message)

        # 3. 更新精密推杆显示 (slider_display)
        # self._update_slider_display(cents)

        # 4.  更新频谱波图
        # audio_frame = realtime_data.audio_frame
        if hasattr(self, 'spectrum_widget'):
            # 将实时帧数据传递给 SpectrumWidget 进行绘制
            # self.spectrum_widget.update_frame(audio_frame)
            # 传入实时帧数据，标记为实时模式
            self.spectrum_widget.update_frame(audio_frame, is_full_file=False)
        # 5.更新钢琴键盘高亮
        if self.piano_generator and result.confidence > 0.6: # 仅在高置信度时高亮
            closest_key = self.piano_generator.find_closest_key(result.frequency)
            self.piano_widget.set_detected_note(closest_key.note_name)
        else:
            self.piano_widget.set_detected_note(None) # 没有有效检测时取消高亮

    def _update_slider_display(self, cents_deviation: float,theta_degrees:float=0.0):
        """根据音分偏差更新推杆的颜色和提示文字"""
        # if TUNING_DIAL_AVAILABLE and hasattr(self, 'tuning_inputwidget_widget'):
        if TUNING_INPUT_WIDGHET_AVAILABLE and hasattr(self, 'tuning_inputwidget_widget'):
            # 驱动新的 Dial Widget
            self.tuning_inputwidget_widget.set_values(cents_deviation, theta_degrees)
            return
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
            # --- 新增功能：达到最大录音时长时自动停止 ---
            if elapsed_time >= self.settings_max_recording_time:
                self.record_timer.stop()
                self.update_status(f"达到最大时长 ({self.settings_max_recording_time} 秒)，自动停止录音。")
                self.on_stop_recording() # 自动触发停止逻辑
                return
            # ----------------------------------------------
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



    # def _generate_analysis_summary(self,
    #                                    result: MusicalAnalysisResult,
    #                                    total_analysis_time: float) -> str: # <-- 增加耗时参数
    #     """根据分析结果生成摘要文本"""
    #     if not result:
    #         return "分析结果为空。"

    #     summary = f"--- 钢琴调律分析报告 ---\n"
    #     summary += f"分析文件: {os.path.basename(result.file_path)}\n"
    #     summary += f"文件时长: {result.duration:.2f} 秒\n"
    #     summary += f"采样率: {result.sample_rate} Hz\n"
    #     summary += f"分析帧数: {len(result.pitch_results)} 帧\n"
    #     summary += f"总分析耗时 (s): {total_analysis_time:.3f} 秒\n" # <-- 使用传入的耗时
    #     summary += f"-----------------------------------\n"

    #     # 主要指标
    #     summary += f"主要音高分析:\n"
    #     summary += f"  主导频率 (Hz): {result.dominant_frequency:.2f} Hz\n"

    #     # 获取目标音高信息
    #     if self.target_key:
    #         target_note_name = self.target_key.note_name
    #         target_freq = self.target_key.frequency
    #         summary += f"  目标音高: {target_note_name} ({target_freq:.2f} Hz)\n"

    #     # 计算平均偏差
    #     cents_values = [p.cents_deviation for p in result.pitch_results if p.cents_deviation is not None]
    #     mean_cents = np.mean(cents_values) if cents_values else None

    #     if mean_cents is not None:
    #         summary += f"  平均偏差 (音分): {mean_cents:.2f} Cents\n"
    #         summary += f"  调音质量: {result.tuning_quality:.3f}\n"
    #     else:
    #         summary += f"调律指标: 无法计算 (目标频率缺失或无有效检测)\n"

    #     summary += f"音高稳定性: {result.stability:.3f}\n"

    #     summary += f"-----------------------------------\n"

    #     # 统计信息
    #     confidence_values = [p.confidence for p in result.pitch_results]

    #     if cents_values:
    #         summary += f"统计数据:\n"
    #         summary += f"  - 最大偏差: {np.max(cents_values):.2f} Cents\n"
    #         summary += f"  - 最小偏差: {np.min(cents_values):.2f} Cents\n"
    #         summary += f"  - 标准差: {np.std(cents_values):.2f} Cents\n"

    #     if confidence_values:
    #         summary += f"  - 平均置信度: {np.mean(confidence_values):.3f}\n"

    #     # 增加算法信息（从 AudioDetector 的打印输出中获取，需要 AnalysisTiming）
    #     # 假设 AnalysisTiming 被自动计算并存储在 AudioDetector 内部

    #     # 为简化，暂时不包含 AnalysisTiming 的详细信息，但可以在未来版本中添加。

    #     summary += f"-----------------------------------\n"
    #     summary += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    #     return summary

    def _generate_analysis_summary(self,
                                   result: MusicalAnalysisResult,
                                   total_analysis_time: float) -> str:
        """
        根据分析结果生成摘要文本。
        这个方法从 MusicalAnalysisResult 中提取数据，并格式化输出。
        """
        if not result:
            return "分析结果为空。"

        # --- 确保 target_key 存在且已设置 ---
        target_key_info = ""
        if self.target_key:
            target_note_name = self.target_key.note_name
            target_freq = self.target_key.frequency
            target_key_info = f"  目标音高: {target_note_name} ({target_freq:.2f} Hz)\n"

        # --- 计算统计数据 ---
        cents_values = [p.cents_deviation for p in result.pitch_results if p.cents_deviation is not None]
        confidence_values = [p.confidence for p in result.pitch_results]
        mean_cents = np.mean(cents_values) if cents_values else None

        # --- 开始生成摘要 ---
        summary = f"--- 钢琴调律分析报告 ---\n"
        summary += f"分析文件: {os.path.basename(result.file_path)}\n"
        summary += f"文件时长: {result.duration:.2f} 秒\n"
        summary += f"采样率: {result.sample_rate} Hz\n"
        summary += f"分析帧数: {len(result.pitch_results)} 帧\n"
        summary += f"总分析耗时 (s): {total_analysis_time:.3f} 秒\n"
        summary += f"-----------------------------------\n"

        # 主要指标
        summary += f"主要音高分析:\n"
        summary += f"  主导频率 (Hz): {result.dominant_frequency:.2f} Hz\n"
        summary += target_key_info

        # 调律指标
        if mean_cents is not None:
            summary += f"  平均偏差 (音分): {mean_cents:.2f} Cents\n"
            summary += f"  调音质量: {result.tuning_quality:.3f}\n"
        else:
            summary += f"调律指标: 无法计算 (目标频率缺失或无有效检测)\n"

        summary += f"音高稳定性: {result.stability:.3f}\n"

        summary += f"-----------------------------------\n"

        # 统计信息
        if cents_values:
            summary += f"统计数据:\n"
            summary += f"  - 最大偏差: {np.max(cents_values):.2f} Cents\n"
            summary += f"  - 最小偏差: {np.min(cents_values):.2f} Cents\n"
            summary += f"  - 标准差: {np.std(cents_values):.2f} Cents\n"

        if confidence_values:
            summary += f"  - 平均置信度: {np.mean(confidence_values):.3f}\n"

        summary += f"-----------------------------------\n"
        summary += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        return summary

    def _save_analysis_summary(self, result: MusicalAnalysisResult, default_filename: str, total_analysis_time: float):
        """弹出文件保存对话框，将分析摘要保存为 TXT 文件"""

        # 调用摘要生成器
        summary_text = self._generate_analysis_summary(result, total_analysis_time)

        # 默认保存路径
        default_folder = self.current_analysis_folder if hasattr(self, 'current_analysis_folder') else os.getcwd()
        default_path = os.path.join(default_folder, default_filename)

        # 弹出保存对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存分析结果摘要",
            default_path,
            "文本文件 (*.txt);;所有文件 (*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(summary_text)
                self.update_status(f"分析摘要已成功保存到: {os.path.basename(file_path)}")
            except Exception as e:
                self.update_status(f"保存文件失败: {e}")
                QMessageBox.critical(self, "保存错误", f"保存分析结果摘要失败:\n{e}")

    # def _handle_post_analysis(self, analysis_result: MusicalAnalysisResult, file_path: str, total_analysis_time: float):
    #     """处理分析完成后续逻辑：提示保存摘要"""

    #     if not analysis_result:
    #         return

    #     if self.settings_auto_prompt_save:
    #         # 默认文件名: 原始文件名_Analysis_YYYYMMDD_HHMMSS.txt
    #         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    #         original_name = os.path.splitext(os.path.basename(file_path))[0]
    #         default_filename = f"{original_name}_Analysis_{timestamp}.txt"

    #         # 询问用户是否保存
    #         reply = QMessageBox.question(
    #             self,
    #             "保存分析结果",
    #             f"文件分析已完成。\n是否保存分析摘要？",
    #             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    #             QMessageBox.StandardButton.Yes
    #         )

    #         if reply == QMessageBox.StandardButton.Yes:
    #             self._save_analysis_summary(analysis_result, default_filename, total_analysis_time)

    def _handle_post_analysis(self, analysis_result: MusicalAnalysisResult, file_path: str, total_analysis_time: float):
        """处理分析完成后续逻辑：根据设置，弹出保存对话框让用户指定路径"""

        if not analysis_result:
            return

        # 1. 检查设置：用户是否允许/需要保存提示
        if self.settings_auto_prompt_save:
            # 默认文件名: 原始文件名_Analysis_YYYYMMDD_HHMMSS.txt
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_name = os.path.splitext(os.path.basename(file_path))[0]
            default_filename = f"{original_name}_Analysis_{timestamp}.txt"

            self.update_status("分析完成。等待用户指定保存路径...")

            # 2. 调用 _save_analysis_summary，该方法内部会弹出 QFileDialog
            #    并等待用户手动选择保存路径。
            self._save_analysis_summary(analysis_result, default_filename, total_analysis_time)
        else:
            self.update_status("分析完成。用户设置：不自动弹出保存提示。")

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
                    accidental_type=self.settings_accidental_type
                )

                # # 2. 设置目标键参数 (只设置数据，不操作 UI)
                self.target_key = self.piano_generator.get_key_by_note_name(self.default_target_note_name)
                # 2. 修正：将新的生成器实例传递给 PianoWidget
                # 假设 self.piano_widget 已经创建且有一个 set_piano_generator 方法
                if hasattr(self, 'piano_widget') and hasattr(self.piano_widget, 'set_piano_generator'):
                     self.piano_widget.set_piano_generator(self.piano_generator)

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
            # 通知调整面板
            self.inform_right_target(new_key.frequency)
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


    # 关闭事件
    def closeEvent(self, event):
        """
        在主窗口关闭前执行的事件，用于持久化保存配置到 config.json。
        """
        try:
            # 1. 确保将 StringCSVManager 的当前路径也保存到 config_data 中
            # 这是一个额外的安全网，防止用户在配置窗口外切换了文件。
            if self.db_manager:
                self.config_data['db_file_path'] = self.db_manager.get_connected_path()

            # 2. 持久化保存所有配置数据
            success = self.config_manager.save_config(self.config_data)

            if success:
                print("程序退出时，配置已成功保存到 config.json。")
            else:
                # 即使保存失败，也应该允许程序退出
                print("程序退出时，配置保存失败。")

            # 3. 允许窗口关闭
            event.accept()

        except Exception as e:
            print(f"退出时保存配置发生错误: {e}")
            # 即使发生异常，也应该允许程序退出
            event.accept()

# ===========================  核心模拟  ==================================

    # def _update_coarse_slider_input(self, value):
    #     """处理粗调推杆输入 (驱动力学模拟)"""
    #     # coarse_slider 范围 [-100, 100]。映射到 [-1.0, 1.0] 的归一化值。
    #     coarse_norm_val = value / 100.0
    #     self.coarse_input_val = coarse_norm_val

    #     # 计算总输入：粗调权重高 (例如 1.5 扭矩系数)
    #     self.user_input_ddt = self.coarse_input_val * 1.5 + self.fine_input_val * 0.15

    #     self._check_and_start_simulation()

    # def _update_fine_knob_input(self, value):
    #     """处理微调旋钮输入 (驱动力学模拟)"""
    #     # fine_knob 范围 [-20, 20]。映射到 [-1.0, 1.0] 的归一化值。
    #     fine_norm_val = value / 20.0
    #     self.fine_input_val = fine_norm_val

    #     # 计算总输入：微调权重低 (例如 0.15 扭矩系数)
    #     self.user_input_ddt = self.coarse_input_val * 1.5 + self.fine_input_val * 0.15

    #     self._check_and_start_simulation()

    # def _check_and_start_simulation(self):
    #     """检查启动前置条件 (音频分析结果) 并启动/停止 RK4 模拟循环"""
    #     if not self.mechanical_engine or not self.target_key:
    #          return

    #     # 1. 检查音频分析前置条件 (必须有初始频率 f_current)
    #     if self.last_analysis_freq is None:
    #         self.update_status("警告：请先执行音频分析以获得初始频率，才能启动调律模拟。")
    #         return

    #     # 2. 启动模拟逻辑 (用户输入非零)
    #     if abs(self.user_input_ddt) > 1e-4: # 用户输入非零

    #         if not self.tuning_loop_timer.isActive():
    #             # 首次启动：使用最近的分析结果初始化引擎
    #             current_freq = self.last_analysis_freq

    #             # 初始化力学引擎 (获取 L, μ 并设置 θ_initial)
    #             self.on_start_tuning_simulation(current_freq)

    #             # 启动 RK4 计时器
    #             self.tuning_loop_timer.start(int(self.mechanical_engine.dt * 1000))
    #             self.update_status("力学模拟已启动，响应调整...")

    #     # 3. 停止模拟逻辑 (输入归零)
    #     elif abs(self.user_input_ddt) <= 1e-4 and self.tuning_loop_timer.isActive():
    #         self.tuning_loop_timer.stop()
    #         self.mechanical_engine.state.omega = 0.0
    #         self.update_status("模拟停止，张力稳定。")



    # def on_start_tuning_simulation(self, current_freq: float):
    #     """
    #     [架构核心] 初始化力学引擎，加载 L/mu，并设置模拟的起始状态。
    #     """
    #     if not self.mechanical_engine or not self.target_key or not self.db_manager:
    #         self.update_status("错误: 力学引擎核心依赖缺失，无法启动调律模拟。")
    #         return

    #     # 1. 从 CSV 读取当前目标键的 L 和 μ
    #     key_id_to_find = self.target_key.key_id

    #     # 假设 csv_manager 有一个方法能按 key_id 查找参数
    #     string_params = self.db_manager.get_string_parameters_by_id(key_id_to_find)

    #     if not string_params:
    #         self.update_status(f"错误: 琴弦数据 (ID {key_id_to_find}, {self.target_key.note_name}) 在 CSV 文件中缺失。请检查钢琴参数。")
    #         return

    #     # 2. 准备初始化参数
    #     try:
    #         L = string_params['length']
    #         mu = string_params['density']
    #         target_freq = self.target_key.frequency # 从 PianoGenerator 获取
    #     except KeyError:
    #          self.update_status("致命错误: CSV 文件字段缺失或数据类型错误。请检查文件。")
    #          return

    #     # 3. 初始化力学引擎 (设置 F_initial, theta_initial)
    #     self.mechanical_engine.initialize_tuning(
    #         current_freq=current_freq,
    #         target_freq=target_freq,
    #         target_key_L=L,
    #         target_key_mu=mu
    #     )
    #     self.update_status(f"调律会话已就绪。初始频率: {current_freq:.1f}Hz。")

    # def _run_tuning_simulation(self):
    #     """
    #     RK4 模拟主循环：每 dt 步进一次，驱动力学引擎。
    #     """
    #     if not self.mechanical_engine or not self.target_key or not self.audio_detector:
    #         if self.tuning_loop_timer.isActive():
    #              self.tuning_loop_timer.stop()
    #         self.update_status("错误：力学模拟核心依赖缺失，已停止。")
    #         return

    #     # 1. 计算用户输入的总扭矩 (τ_input = user_input_ddt * Kd)
    #     tau_input = self.user_input_ddt * self.mechanical_engine.Kd

    #     # 2. 执行 RK4 步进
    #     new_state = self.mechanical_engine.step_rk4(tau_input)

    #     # 3. 获取新的频率和音分偏差
    #     new_freq = self.mechanical_engine.get_current_frequency()
    #     target_freq = self.target_key.frequency
    #     cents_deviation = self.audio_detector.calculate_cents_deviation(new_freq, target_freq)

    #     # 4. 获取角度 (转换为度)
    #     theta_degrees = np.degrees(new_state.theta)

    #     # 5. 更新 UI 显示 (使用 TuningDialWidget)
    #     self._update_slider_display(cents_deviation, theta_degrees)

    #     # 6. 更新状态信息
    #     status_msg = (f"模拟运行 | 角度: {theta_degrees:.2f}° "
    #                   f"| 张力: {new_state.string_tension:.1f} N "
    #                   f"| 偏差: {cents_deviation:+.2f} 音分")
    #     self.update_status(status_msg)

    #     # 7. 检查停止条件 (静止)
    #     if abs(new_state.omega) < self.mechanical_engine.epsilon and abs(self.user_input_ddt) < 1e-4:
    #         self.tuning_loop_timer.stop()
    #         self.mechanical_engine.state.omega = 0.0
    #         self.update_status(f"模拟静止，张力稳定。最终偏差: {cents_deviation:+.2f} Cents")


    #=================================以上为废案，不要了===================================
    # def _handle_input_change(self, normalized_input: float):
    #     """接收归一化输入，计算 dD/dt"""
    #     # 假设最大扭矩输入对应归一化输入 1.0，使用 2.0 作为最大 dD/dt
    #     self.user_input_ddt = normalized_input * 2.0
    #     self.user_input_torque = self.user_input_ddt * self.mechanical_engine.Kd

    #     # 如果模拟已经在运行，改变输入值即可。

    # def _start_simulation_session(self):
    #     """启动调律模拟会话 (在鼠标左键按下时触发)"""
    #     if self.is_simulating: return

    #     # 1. 检查启动前置条件 (音频分析结果)
    #     if self.last_analysis_freq is None:
    #         self.update_status("警告：请先执行音频分析以获得初始频率，才能启动调律模拟。")
    #         return

    #     # 2. 初始化力学引擎状态
    #     self.on_start_tuning_simulation(self.last_analysis_freq)

    #     # 3. 启动 RK4 计时器 (现在是事件驱动的步进)
    #     self.is_simulating = True
    #     self.simulation_timer.start() # 计时器开始，将持续调用 _step_simulation
    #     self.update_status("调律模拟会话已启动，等待调整...")

    # def _end_simulation_session(self):
    #     """结束调律模拟会话 (在鼠标左键松开时触发)"""
    #     self.simulation_timer.stop()
    #     self.is_simulating = False
    #     self.user_input_ddt = 0.0 # 清零输入

    #     # 确保力学引擎状态静止
    #     if self.mechanical_engine:
    #         self.mechanical_engine.state.omega = 0.0

    #     self.update_status("调律模拟会话结束，张力锁定。")

    # def _step_simulation(self):
    #     """RK4 模拟步进方法 (由 QTimer 触发)"""
    #     if not self.mechanical_engine or not self.target_key:
    #          return

    #     # 1. 执行 RK4 步进
    #     new_state = self.mechanical_engine.step_rk4(self.user_input_torque)

    #     # 2. 获取频率和音分偏差
    #     new_freq = self.mechanical_engine.get_current_frequency()
    #     target_freq = self.target_key.frequency
    #     cents_deviation = self.audio_detector.calculate_cents_deviation(new_freq, target_freq)

    #     # 3. UI 反馈
    #     theta_degrees = np.degrees(new_state.theta)
    #     self._update_slider_display(cents_deviation, theta_degrees)

    #     # 4. 更新状态信息
    #     status_msg = (f"模拟运行 | 角度: {theta_degrees:.2f}° "
    #                   f"| 力矩: {self.user_input_torque:.4f} N·m "
    #                   f"| 偏差: {cents_deviation:+.2f} 音分")
    #     self.update_status(status_msg)

    #     # 5. 检查物理静止 (即使在拖动中，如果内部摩擦锁死，RK4 也会反映出来)
    #     if abs(new_state.omega) < self.mechanical_engine.epsilon and abs(self.user_input_ddt) < 1e-4:
    #         self._end_simulation_session() # 物理静止，结束会话

    # def _run_tuning_simulation(self):
    #     """
    #     RK4 模拟主循环：每 dt 步进一次，驱动力学引擎。
    #     该方法是 self.tuning_loop_timer 的槽函数。
    #     """
    #     if not self.mechanical_engine or not self.target_key or not self.audio_detector:
    #         # 如果核心组件丢失，停止计时器并返回
    #         if self.tuning_loop_timer.isActive():
    #              self.tuning_loop_timer.stop()
    #         self.update_status("错误：力学模拟核心依赖缺失，已停止。")
    #         return

    #     # 1. 执行 RK4 步进
    #     # tau_input = user_input_ddt * Kd
    #     tau_input = self.user_input_ddt * self.mechanical_engine.Kd

    #     new_state = self.mechanical_engine.step_rk4(tau_input)

    #     # 2. 获取新的频率和音分偏差
    #     new_freq = self.mechanical_engine.get_current_frequency()
    #     target_freq = self.target_key.frequency

    #     # 确保 audio_detector 实例存在，否则无法计算音分
    #     cents_deviation = self.audio_detector.calculate_cents_deviation(new_freq, target_freq)

    #     # 3. 获取角度 (转换为度)
    #     theta_degrees = np.degrees(new_state.theta)

    #     # 4. 更新 UI 显示 (使用 TuningDialWidget)
    #     self._update_slider_display(cents_deviation, theta_degrees)

    #     # 5. 更新状态信息
    #     status_msg = (f"模拟运行 | 角度Δθ: {theta_degrees:.2f}° "
    #                   f"| 张力F: {new_state.string_tension:.1f} N "
    #                   f"| 偏差: {cents_deviation:+.2f} 音分")
    #     self.update_status(status_msg)

    #     # 6. 检查停止条件 (静止)
    #     # 只有在角速度低于阈值且用户没有输入，才停止计时器。
    #     if abs(new_state.omega) < self.mechanical_engine.epsilon and abs(self.user_input_ddt) < 1e-4:
    #         self.tuning_loop_timer.stop()
    #         self.mechanical_engine.state.omega = 0.0
    #         self.update_status(f"模拟静止，张力稳定。最终偏差: {cents_deviation:+.2f} Cents")
