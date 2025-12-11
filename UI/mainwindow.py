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

# ----------------------------
# 资源定位函数（PyInstaller 必须）
# ----------------------------
def resource_path(relative_path: str):
    """
    在开发环境与 PyInstaller 打包后返回正确的资源路径
    """
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# 添加src文件夹到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root=os.path.dirname(current_dir)
# src_path = os.path.join(project_root, 'src')
# sys.path.append(src_path)
src_path = resource_path("src")  # 修改：使用资源路径
sys.path.append(src_path)


from PySide6.QtCore import QFile,QStandardPaths,QDir,QTimer,QUrl
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import  QPushButton, QLabel,QFileDialog,QLineEdit,QProgressBar
from PySide6.QtWidgets import QSizePolicy,QComboBox,QDial,QSlider
from PySide6.QtGui import QAction,QActionGroup,QDesktopServices
import numpy as np
from datetime import datetime
from typing import Dict,Any
import math
import sounddevice as sd

# 导入音频检测模块
try:
    from AudioDetector import AudioDetector, PitchDetectionAlgorithm,PitchResult,RealtimeData,AnalysisProgress,MusicalAnalysisResult
    AUDIO_MODULES_AVAILABLE = True
except ImportError as e:
    import traceback
    traceback.print_exc()
    print(f"导入音频模块失败: {e}")
    AUDIO_MODULES_AVAILABLE = False

from AudioEngine import AudioEngine,FLUIDSYNTH_AVAILABLE
from ToneLibraryDialog import ToneLibraryDialog
from SampleRateConfigWidget import SampleRateDialog
from UserStatusCard import UserStatusCard,DebugStatusWindow
from MouseSmoothConfigDialog import MouseSmoothConfigDialog
from ExportRepairTimeDialog import ExportRepairTimeDialog
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

# 导入音频输入设备
try:
    from AudioDeviceDialog import AudioDeviceDialog
    AUDIO_DEVICE_DIALOG_AVAILABLE = True
except ImportError as e:
    print(f"导入 AudioDeviceDialog 失败: {e}")
    AUDIO_DEVICE_DIALOG_AVAILABLE = False

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



import sys
import os
import time
import numpy as np
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QRadioButton, QGroupBox,
                              QButtonGroup, QTextEdit, QProgressBar,QSystemTrayIcon)
from PySide6.QtCore import Qt, QTimer,QObject, Signal
from PySide6.QtGui import QFont, QPalette, QColor,QIcon


HELP_FOLDER = "help"  # 项目里 help 文件夹路径

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
        self.mech_k = self.config_data.get('mech_k', 2000.0)  # 琴弦劲度系数 k (N/m) (用于张力/角度转换)
        self.mech_Sigma_valid = self.config_data.get('mech_Sigma_valid',210000)  # 许用应力
        self.mech_Kd = self.config_data.get('mech_Kd', 0.5)     # 施力敏感度 K_D (N·m·s/rad)
        # 摩擦模型参数 (保持默认值或从配置加载)
        self.mech_friction_model = self.config_data.get('mech_friction_model', "Limit_Friction")# 默认模型
        self.mech_fric_limit_0 = self.config_data.get('mech_fric_limit_0', -10.0) # 初始静摩擦极限 τ_fric_limit_0 (N·m)
        self.mech_alpha = self.config_data.get('mech_alpha', 0.05)          # 静摩擦增长系数 α (N·m/rad)
        self.mech_kinetic = self.config_data.get('mech_kinetic', 0.08)      # 动摩擦扭矩 τ_kinetic (N·m)
        self.mech_sigma = self.config_data.get('mech_sigma', 0.001)         # 粘性摩擦系数 σ (N·m·s/rad)
        self.mech_gamma = self.config_data.get('mech_gamma',0.9)            # 动静摩擦转化比
        self.friction_model = self.config_data.get('friction_model',"linear")
        self.custom_fric_csv_path = self.config_data.get('custom_fric_csv_path',None)
        self.custom_interp_method = self.config_data.get('custom_interp_method',None)

        # 步长
        self.repair_simulation_dt=self.config_data.get('repair_simulation_dt',0.01)
        self.max_repair_time = self.config_data.get('max_repair_time',10.0)
        # B. CSV Manager 路径
        self.db_manager = None
        if StringCSVManager:
            initial_db_path = self.config_data.get('db_file_path')
            self.db_manager = StringCSVManager(file_path=initial_db_path)
            print(f"CSV 管理器已初始化，文件路径: {self.db_manager.get_connected_path()}")


        # 1.控件
        # 用于缓存状态消息的静态列表
        self._status_message_cache = []
        # 存储分析完需要删除的文件路径
        self.temp_files_to_delete = []
        # 保存分析结果的控制
        # self.settings_auto_prompt_save = True
        self.settings_auto_prompt_save = self.config_data.get('settings_auto_prompt_save', True)
        # 默认开启保存录音文件
        # self.settings_save_recording_file = True
        self.settings_save_recording_file = self.config_data.get('settings_save_recording_file', True)
        # 录音时长设置声明
        self.max_recording_time_options = [5, 10, 20] # 选项：5s, 10s, 20s
        # self.settings_max_recording_time = 10         # 默认值 10s
        self.settings_max_recording_time = self.config_data.get('settings_max_recording_time', 10)
        # 音名系统设置声明,默认使用降号b系统
        # self.settings_accidental_type = AccidentalType.FLAT
        self.settings_accidental_type = AccidentalType[
            self.config_data.get('settings_accidental_type', 'FLAT')
        ]
        # 默认算法
        #self.settings_pitch_algorithm = PitchDetectionAlgorithm.AUTOCORR
        self.settings_pitch_algorithm = PitchDetectionAlgorithm[
            self.config_data.get('settings_pitch_algorithm', 'AUTOCORR')
        ]
        # 默认基准音
        # self.settings_standard_a4 = 440
        self.settings_standard_a4 = self.config_data.get('settings_standard_a4', 440)

        self.tuning_done_threshold_cents = self.config_data.get('tuning_done_threshold_cents',1.0)
        self.tuning_dial_range_cents = self.config_data.get('tuning_dial_range_cents',100)


        # 2. 声明数据模型和核心模块实例 (在 setup_ui 调用前完成)
        self.audio_detector = None     # 存储 AudioDetector 实例
        self.pitch_signal = PitchSignal() # 音高信号实例
        self.piano_generator = None    # PianoGenerator 实例
        self.target_key: Optional[PianoKey] = None # 当前调律的目标键
        self.default_target_note_name = "A4"
        self.current_analysis_folder: Optional[str] = None  # 新增文件系统属性
        self.audio_engine = None      # 音频生成器



        # 调试状态窗口（旧版系统状态迁移到这里）
        # self.debug_status_window = None  # DebugStatusWindow 实例（按需创建）
        self.debug_status_window = DebugStatusWindow(self)

        # 用户态状态卡片引用（在 create_left_panel 里创建）
        self.status_card = None



        # 3. 初始化核心系统 (只声明，不进行状态更新)
        # 注意：这里调用 init_audio_system 和 init_piano_system 时，它们内部的 update_status 仍会失败。
        # 需要暂时修改这两个 init 方法，使其在调用 update_status 前检查 self.status_display 是否存在。
        self.init_piano_system()
        self.init_audio_system()
        self.init_audio_engine()


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

        print("status_card 是否创建成功:", hasattr(self, "status_card"), type(self.status_card))


    # 处理参数文件路径更新
    def _handle_db_config_update(self, new_file_path: str):
        """接收 PianoConfigWidget 发出的文件路径更改信号"""
        # CSV Manager 实例本身没有变，只是内部的 file_path 变了，这里更新状态即可。
        self.update_status(f"琴弦数据文件已更新为: {new_file_path}")
        # 这里不需要重新加载 self.db_manager，因为它已是引用。


    def _post_ui_init_status_update(self):
        """在UI创建完成后，统一初始化状态显示"""

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

        # 力学引擎
        self.inform_right_params(self.config_data)
        self.inform_right_current(self.target_freq)

        # 初始化 UserStatusCard（用户可见状态卡）
        # self.status_card.set_input_device(self.audio_detector.input_device)
        self.status_card.set_mode("实时分析" if self.mode_realtime.isChecked() else "文件分析")
        self.status_card.set_algorithm(self.audio_detector.get_current_algorithm().value)

        # # --- 修正：强制刷新 UI 状态 ---
        QApplication.processEvents() # 强制处理所有挂起的重绘事件
        # # ------------------------------------


    # def init_audio_engine(self):
    #     try:
    #         from AudioEngine import AudioEngine

    #         self.audio_engine = AudioEngine(
    #             piano_generator=self.piano_generator,
    #             samplerate=44100,
    #             blocksize=512
    #         )

    #         self.audio_engine.set_mode("sine")
    #         self.update_status("音频引擎初始化成功（合成器模式）")

    #     except Exception as e:
    #         import traceback
    #         traceback.print_exc()
    #         self.update_status(f"音频系统初始化失败：{e}")
    #         self.audio_engine = None
    def init_audio_engine(self):
        """初始化发声引擎（合成 + 采样包 + SF2 + SFZ）"""
        try:
            sr = self.config_data.get('audio_sample_rate',48000)

            from AudioEngine import AudioEngine

            self.audio_engine = AudioEngine(
                piano_generator=self.piano_generator,
                samplerate=sr,
                blocksize=512
            )

            # 把 UI 状态输出函数接进去，AudioEngine 内部遇到警告会调它
            # self.audio_engine.set_warning_callback(self.update_status)

            # 默认合成器模式
            self.audio_engine.set_mode("sine")
            self.update_status("音频系统初始化成功（内置合成器模式）")

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.update_status(f"音频系统初始化失败：{e}")
            self.audio_engine = None


    # 初始化音频系统
    def init_audio_system(self):
        """初始化 AudioDetector 实例和连接回调"""
        if AUDIO_MODULES_AVAILABLE:
            try:
                # 获取默认录音输出路径
                output_dir = self._get_default_recording_path()

                # 从配置中获取输入设备，如果没有则使用默认设备
                input_device = self.config_data.get('audio_input_device')
                if input_device is None:
                    # 使用sounddevice的默认输入设备
                    try:
                       input_device = sd.default.device[0]
                    except:
                       input_device = 0

                # 使用默认参数初始化 AudioDetector
                self.audio_detector = AudioDetector(
                    sample_rate=44100,
                    frame_length=8192,
                    hop_length=512,
                    # 可以根据配置界面选择输入设备，这里先用默认设备2
                    input_device=input_device,
                    pitch_algorithm=PitchDetectionAlgorithm.AUTOCORR, # 默认使用AUTOCORR,有一定准确度，且响应极快
                    output_dir=output_dir
                )
                # 获取设备名称用于状态显示
                device_name = self._get_current_device_name(input_device)
                self.update_status("音频系统初始化成功，算法：AUTOCORR")

                # 连接自定义信号到主线程槽函数
                self.pitch_signal.pitch_detected.connect(self.on_pitch_detected_update_ui)

            except Exception as e:
                self.update_status(f"音频系统初始化失败: {e}")
                self.audio_detector = None
        else:
            self.update_status("音频模块不可用，请检查依赖库")

    def _get_current_device_name(self, device_index):
        """获取当前音频设备的名称"""
        try:
            devices = AudioDetector.get_audio_input_devices()
            for device in devices:
                if device['index'] == device_index:
                    return device['name']
            return f"设备 {device_index}"
        except:
            return f"设备 {device_index}"

    def setup_ui(self):
        """设置主界面"""
        self.setWindowTitle("钢琴调律辅助系统")
        #self.setWindowIcon(QIcon("E:/Resources/images/acgs/NanoAlice01.png"))
        self.setWindowIcon(QIcon(":/images/NannoAlice01.png"))
        self.setGeometry(100, 100, 1400, 900)
        # 设置系统托盘图标
        if QSystemTrayIcon.isSystemTrayAvailable():
            print("系统支持托盘图标")
            self.tray_icon = QSystemTrayIcon(QIcon(":/images/NannoAlice01.png"), self)
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
        right_panel = RightMechanicsPanel(parent=self)
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
        # 旧版状态信息，现在已经迁移到视图--调试窗口
#         # 状态信息
#         status_group = QGroupBox("系统状态")
#         status_layout = QVBoxLayout(status_group)

#         self.status_display = QTextEdit()
#         self.status_display.setMaximumHeight(200)
#         self.status_display.setPlainText("""📊 当前状态
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
#         self.status_display.setReadOnly(True)

#         status_layout.addWidget(self.status_display)
#         layout.addWidget(status_group)
        # 状态信息（新：用户态卡片）
        status_group = QGroupBox("系统状态")
        status_layout = QVBoxLayout(status_group)

        # 创建用户态状态卡片
        self.status_card = UserStatusCard(self)

        # 把卡片里的进度条作为全局 progress_bar 使用（兼容原逻辑）
        self.progress_bar = self.status_card.progress_bar

        status_layout.addWidget(self.status_card)
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

    # ============
    # 禁用逻辑
    # ===========
    def lock_adjustment_controls(self):
        """
        禁用右侧调节面板 + 键盘选择，防止用户在分析期间操作导致模型紊乱
        """
        if hasattr(self, "right_panel"):
            self.right_panel.setEnabled(False)

        if hasattr(self, "piano_widget"):
            self.piano_widget.setEnabled(False)

        if hasattr(self, "key_select_widget"):  # 如果你是单独的键选择控件
            self.key_select_widget.setEnabled(False)
        # 🚫 禁用文件列表
        if hasattr(self, "file_list_widget"):
            self.file_list_widget.setEnabled(False)
        # 目标音高下拉菜单
        if hasattr(self, "note_selector"):
            self.note_selector.setEnabled(False)


    def unlock_adjustment_controls(self):
        """
        在分析完成后启用所有调节控件
        """
        if hasattr(self, "right_panel"):
            self.right_panel.setEnabled(True)

        if hasattr(self, "piano_widget"):
            self.piano_widget.setEnabled(True)

        if hasattr(self, "key_select_widget"):
            self.key_select_widget.setEnabled(True)
        # 🔓 恢复文件列表
        if hasattr(self, "file_list_widget"):
            self.file_list_widget.setEnabled(True)
        # 目标音高下拉菜单
        if hasattr(self, "note_selector"):
            self.note_selector.setEnabled(True)



    # RightMechanicsPanel
    # ===================================================
    #   MainWindow -> Panel (数据发送函数)
    # ===================================================
    def inform_right_target_key(self,new_key: PianoKey):
        """设置调律的目标频率，并通知 RightMechanicsPanel。"""
        if hasattr(self, 'right_panel'):
            self.right_panel.set_target_key(self.db_manager,new_key)
            # 示例：更新主窗口状态
            # self.update_status(f"目标频率已设置为: {target_freq:.2f} Hz")
    def inform_right_current(self, current_freq: float):
        """设置调律的目标频率，并通知 RightMechanicsPanel。"""
        if hasattr(self, 'right_panel'):
            self.right_panel.set_current_frequency(current_freq)
            # 示例：更新主窗口状态
            # self.update_status(f"目标频率已设置为: {target_freq:.2f} Hz")
    def inform_right_params(self, new_params: Dict[str, Any]):
        if hasattr(self, 'right_panel'):
            self.right_panel.set_params(new_params)


    def setup_menu_bar(self):
        """设置菜单栏"""
        menubar = self.menuBar()

        # # 视图菜单

        # === 视图菜单 ===
        view_menu = menubar.addMenu("视图(&V)")

        # 显示调试状态窗口（旧版系统状态）
        self.action_show_debug_status = QAction("显示调试状态窗口", self)
        self.action_show_debug_status.setCheckable(True)
        self.action_show_debug_status.setChecked(False)
        self.action_show_debug_status.triggered.connect(self._toggle_debug_status_window)

        # 随机调音子窗口
        self.actionRandomTuning = QAction("随机调音子窗口",self)
        self.actionRandomTuning.triggered.connect(self.open_random_tuning)

        view_menu.addAction(self.action_show_debug_status)
        view_menu.addAction(self.actionRandomTuning)


        # --- 参数菜单 ---
        params_menu = menubar.addMenu("参数(&P)")

        # 1. 钢琴参数配置
        self.action_piano_config = QAction("钢琴物理参数配置", self)
        self.action_piano_config.triggered.connect(self._open_piano_config_dialog)
        params_menu.addAction(self.action_piano_config)

        # 2. 摩擦模型配置
        self.action_friction_config = QAction("摩擦模型配置", self)
        self.action_friction_config.triggered.connect(self._open_friction_config_dialog)
        params_menu.addAction(self.action_friction_config)

        # 3. 施力敏感度 (K_D)  暂时不在这里提供这个的修改了
        self.action_kd_config = QAction("施力敏感度 (K_D) 设置", self)
        self.action_kd_config.triggered.connect(self._open_kd_config_dialog)
        # params_menu.addAction(self.action_kd_config)
        # ------------------------
        # 导出菜单
        export_menu = menubar.addMenu("导出(&E)")

        action_export_repair = QAction("导出修复时间", self)
        action_export_repair.triggered.connect(self._open_export_repair_dialog)
        export_menu.addAction(action_export_repair)

        # --------------------------
        # 设置菜单
        settings_menu = menubar.addMenu("设置(&S)")

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

        # --- 音色设置子菜单 ---
        tone_menu = settings_menu.addMenu("音色设置")

        # 打开音色管理窗口
        self.action_open_tone_manager = QAction("选择音色库", self)
        self.action_open_tone_manager.triggered.connect(self._open_tone_manager)
        tone_menu.addAction(self.action_open_tone_manager)

        # 使用 sin 波
        self.action_use_sine = QAction("使用默认合成器", self, checkable=True)
        self.action_use_sine.setChecked(True)
        self.action_use_sine.triggered.connect(self._switch_to_sine)
        tone_menu.addAction(self.action_use_sine)


        # --- 音高检测算法选择 ---
        algo_menu = settings_menu.addMenu("音高检测算法选择")

        self.algo_action_group = QActionGroup(self)
        self.algo_action_group.setExclusive(True)

        for algo in PitchDetectionAlgorithm:
            action = QAction(algo.value, self, checkable=True)
            action.setData(algo)

            if algo == self.settings_pitch_algorithm:
                action.setChecked(True)

            self.algo_action_group.addAction(action)
            algo_menu.addAction(action)

        self.algo_action_group.triggered.connect(self._set_pitch_algorithm)

        # --- 基准音 A4 频率设置 ---
        basefreq_menu = settings_menu.addMenu("标准音 A4 频率")

        self.basefreq_action_group = QActionGroup(self)
        self.basefreq_action_group.setExclusive(True)

        basefreq_options = [432, 436, 438, 440, 442, 444]
        for freq in basefreq_options:
            action = QAction(f"{freq} Hz", self, checkable=True)
            action.setData(freq)

            if freq == self.settings_standard_a4:
                action.setChecked(True)

            self.basefreq_action_group.addAction(action)
            basefreq_menu.addAction(action)

        self.basefreq_action_group.triggered.connect(self._set_standard_a4)

        # 添加分隔线，区分不同类别的设置.其上为选择项，其下为直接设置项
        settings_menu.addSeparator()

        # 音频输入设备选择
        self.action_audio_device = QAction("音频输入设备", self)
        self.action_audio_device.triggered.connect(self._open_audio_device_dialog)
        settings_menu.addAction(self.action_audio_device)

        # 采样率
        action_set_samplerate = QAction("设置采样率", self)
        action_set_samplerate.triggered.connect(self._open_samplerate_dialog)
        settings_menu.addAction(action_set_samplerate)

        # 鼠标控制平滑设置
        self.action_mouse_smooth = QAction("鼠标控制平滑设置", self)
        self.action_mouse_smooth.triggered.connect(self._open_mouse_smooth_dialog)
        settings_menu.addAction(self.action_mouse_smooth)

        # 调律完成阈值
        self.action_tune_threshold = QAction("调律完成判定阈值", self)
        self.action_tune_threshold.triggered.connect(self._open_tune_threshold_dialog)
        settings_menu.addAction(self.action_tune_threshold)

        self.action_tune_dial_range = QAction("音分表盘范围", self)
        self.action_tune_dial_range.triggered.connect(self._open_tune_dial_range_dialog)
        settings_menu.addAction(self.action_tune_dial_range)




        # 添加分隔线，区分不同类别的设置.其上为选择项，其下为直接设置项
        settings_menu.addSeparator()

        # 加入设置
        settings_menu.addAction(self.action_toggle_save_recording)
        settings_menu.addAction(self.action_toggle_save_prompt)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")

        act_manual = QAction("软件使用说明", self)
        act_manual.triggered.connect(lambda: self.open_help_doc("软件使用说明"))
        help_menu.addAction(act_manual)

        act_mech = QAction("力学系统说明", self)
        act_mech.triggered.connect(lambda: self.open_help_doc("力学系统说明"))
        help_menu.addAction(act_mech)

        act_pitch = QAction("音高检测算法说明", self)
        act_pitch.triggered.connect(lambda: self.open_help_doc("音高检测算法说明"))
        help_menu.addAction(act_pitch)


        act_report = QAction("项目开发报告", self)
        act_report.triggered.connect(lambda: self.open_help_doc("项目开发报告"))
        help_menu.addAction(act_report)

        help_menu.addSeparator()

        act_start_report = QAction("开题报告", self)
        act_start_report.triggered.connect(lambda: self.open_help_doc("923113370211-罗健玮-开题报告"))
        help_menu.addAction(act_start_report)

        act_keshe_report = QAction("课程设计报告", self)
        act_keshe_report.triggered.connect(lambda: self.open_help_doc("923113370211-罗健玮-课程设计报告"))
        help_menu.addAction(act_keshe_report)

        act_start_ppt = QAction("开题PPT", self)
        act_start_ppt.triggered.connect(lambda: self.open_help_doc("923113370211-罗健玮-开题PPT"))
        help_menu.addAction(act_start_ppt)

        help_menu.addSeparator()

        act_video = QAction("视频教程", self)
        act_video.triggered.connect(lambda: self.open_help_doc("视频教程"))
        help_menu.addAction(act_video)

    def _open_export_repair_dialog(self):
        """打开修复时间批量导出窗口"""
        #dlg = ExportRepairTimeDialog(mechanics=self.right_panel.mechanics, parent=self)
        dlg = ExportRepairTimeDialog(
        main_right_panel=self.right_panel,
        piano_generator=self.piano_generator,
        current_key_id = self.target_key.key_id,
        db_manager=self.db_manager,
        parent=self
        )
        dlg.exec()


    def _open_audio_device_dialog(self):
        """打开音频输入设备选择对话框"""
        if not AUDIO_DEVICE_DIALOG_AVAILABLE:
            QMessageBox.critical(self, "错误", "音频设备选择模块未找到。")
            return

        # 获取当前设备索引
        current_device = self.config_data.get('audio_input_device')
        if current_device is None:
            try:
                current_device = sd.default.device[0]
            except:
                current_device = 0

        dialog = AudioDeviceDialog(current_device, self)
        if dialog.exec() == QDialog.Accepted:
            new_device_index = dialog.get_selected_device_index()

            # 更新配置
            self.config_data['audio_input_device'] = new_device_index
            self.config_manager.save_config(self.config_data)

            # 重新初始化音频系统
            if self.audio_detector:
                # 如果正在录音，先停止
                if self.audio_detector.is_recording:
                    self.on_stop_recording()

                # 重新初始化音频检测器
                self.init_audio_system()

            device_name = self._get_current_device_name(new_device_index)
            self.update_status(f"音频输入设备已切换到: {device_name}")

            # 更新状态卡片显示
            if self.status_card:
                self.status_card.set_input_device(device_name)

    def open_random_tuning(self):
        from RandomTuningDialog import RandomTuningDialog
        dlg = RandomTuningDialog(self.piano_generator, self.audio_engine, self)
        dlg.setModal(False)          # 非模态，方便一边练一边看主界面
        dlg.show()


    def _open_tune_dial_range_dialog(self):
        choices = ["±100 cents", "±50 cents", "±20 cents", "±10 cents"]
        values = [100, 50, 20, 10]

        # item, ok = QInputDialog.getItem(self, "表盘范围", "选择范围：", choices, 0, False)
        item, ok = QInputDialog.getItem(self, "表盘范围", "选择范围：", choices, values.index(self.tuning_dial_range_cents), False)
        if not ok:
            return

        sel_val = values[choices.index(item)]
        self.config_data["tuning_dial_range_cents"] = sel_val
        self.tuning_dial_range_cents = sel_val
        # self.save_config()
        self.config_manager.save_config(self.config_data)

        # 更新右侧面板
        if hasattr(self, "right_panel"):
            self.right_panel.dial.set_range(sel_val)

        QMessageBox.information(self, "设置成功", f"音分表盘范围已经修改为 ±{sel_val} cents")

    def _open_tune_threshold_dialog(self):
        dialog = QInputDialog(self)
        dialog.setWindowTitle("调律完成判定阈值")
        dialog.setLabelText("请输入调律完成阈值（音分）：")
        dialog.setInputMode(QInputDialog.DoubleInput)
        dialog.setDoubleValue(self.config_data.get("tuning_done_threshold_cents", 0.5))
        dialog.setDoubleRange(0.1, 20.0)
        dialog.setDoubleDecimals(2)

        if dialog.exec() == QDialog.Accepted:
            value = dialog.doubleValue()
            self.config_data["tuning_done_threshold_cents"] = value
            self.tuning_done_threshold_cents=value
            # self.save_config()
            self.config_manager.save_config(self.config_data)
            QMessageBox.information(self, "设置成功", f"调律完成阈值已设置为 {value} cents")
            self.inform_right_params(self.config_data)

    def _open_mouse_smooth_dialog(self):
        dlg = MouseSmoothConfigDialog(self.config_data, self)
        if dlg.exec() == QDialog.Accepted:
            # 保存设置
            self.config_data["mouse_deadzone"] = dlg.in_deadzone.value()
            self.config_data["mouse_alpha"] = dlg.in_alpha.value()
            self.config_data["mouse_scale"] = dlg.in_scale.value()
            self.config_data["mouse_decay_tau"] = dlg.in_decay_tau.value()

            # 写回配置文件
            self.config_manager.save_config(self.config_data)

            # 通知右侧面板
            self.inform_right_params(self.config_data)

            self.update_status("鼠标控制平滑设置已更新")


    def _toggle_debug_status_window(self, checked: bool):
        """视图菜单：显示/隐藏旧版调试状态窗口"""
        if self.debug_status_window is None:
            self.debug_status_window = DebugStatusWindow(self)
            # 把之前缓存的状态也同步进去
            for msg in getattr(self, "_status_message_cache", []):
                self.debug_status_window.apply_status_update_logic(msg)

        if checked:
            self.debug_status_window.show()
            self.debug_status_window.raise_()
            self.debug_status_window.activateWindow()
        else:
            self.debug_status_window.hide()


    def _set_standard_a4(self, action: QAction):
        """切换 A4 基准频率（例如 440 / 442 / 432 Hz）"""
        new_freq = action.data()

        if new_freq != self.settings_standard_a4:

            # 1. 更新配置
            self.settings_standard_a4 = new_freq

            # 2. 更新钢琴系统频率（无需 rebuild，只用已有的 set_base_frequency）
            if self.piano_generator:
                try:
                    self.piano_generator.set_base_frequency(float(new_freq))
                except Exception as e:
                    print("PianoGenerator 更新基准频率失败：", e)

            # 3. 刷新 UI
            if self.piano_generator:

                # --- A. 更新 note_selector ---
                if hasattr(self, "note_selector"):
                    self.note_selector.blockSignals(True)
                    self.note_selector.clear()

                    # 重新填充 88 键的音名
                    note_names = sorted(
                        self.piano_generator.export_key_frequencies().keys(),
                        key=lambda n: self.piano_generator.get_key_by_note_name(n).midi_number
                    )
                    self.note_selector.addItems(note_names)

                    # 保持当前选择（比如 A4）
                    if self.target_key:
                        self.note_selector.setCurrentText(self.target_key.note_name)
                        self.set_target_note(self.target_key.note_name)

                    self.note_selector.blockSignals(False)

                # --- B. 刷新钢琴键盘绘图 ---
                if hasattr(self, "piano_widget"):
                    self.piano_widget.update()

            # 4. 保存设置
            # self._save_settings()

            # 5. 状态栏提示
            self.update_status(f"标准音已切换为 A4 = {new_freq} Hz")


    def _set_pitch_algorithm(self, action: QAction):
        algo = action.data()  # PitchDetectionAlgorithm
        self.settings_pitch_algorithm = algo

        if self.audio_detector:
            self.audio_detector.set_pitch_algorithm(algo)

        self.update_status(f"音高检测算法已切换为：{algo.value}")

        if self.status_card:
            self.status_card.set_algorithm(algo.value)



        # 保存配置
        # self._save_settings()

    def _open_samplerate_dialog(self):
        current = getattr(self.audio_engine, "sr", 44100)
        dlg = SampleRateDialog(current_rate=current, parent=self)

        if dlg.exec() != QDialog.Accepted:
            return

        new_sr = dlg.get_samplerate()
        try:
            if hasattr(self.audio_engine, "set_samplerate"):
                self.audio_engine.set_samplerate(new_sr)
            else:
                self.audio_engine.sr = new_sr

            self.update_status(f"采样率已切换到 {new_sr} Hz")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法切换采样率：{e}")


    def _open_tone_manager(self):
        if self.audio_engine is None:
            QMessageBox.warning(self, "音频未初始化", "音频引擎尚未初始化。")
            return

        dlg = ToneLibraryDialog(self,self.audio_engine.sr)
        if dlg.exec() != QDialog.Accepted:
            return

        mode = dlg.get_selected_mode()
        samplerate = dlg.get_samplerate()

        try:
            # 统一先切换采样率
            self.audio_engine.set_samplerate(samplerate)

            if mode == "sample":
                folder = dlg.get_sample_folder()
                self.audio_engine.set_sample_folder(folder)
                self.audio_engine.set_mode("sample")
                self.update_status(f"已启用采样音色包：{os.path.basename(folder)}，采样率 {samplerate} Hz")

            elif mode == "sf2":
                sf2_file = dlg.get_sf2_file()
                self.audio_engine.load_sf2(sf2_file)
                self.audio_engine.set_mode("sf2")
                self.update_status(f"已启用 SF2 音色：{os.path.basename(sf2_file)}，采样率 {samplerate} Hz")
            self.action_use_sine.setChecked(False)

        except Exception as e:
            QMessageBox.critical(self, "应用音色失败", f"应用音色失败：{e}")
            self.action_use_sine.setChecked(True)


    def _switch_to_sine(self):
        """切换到内置合成器音色"""
        if self.audio_engine:
            self.audio_engine.set_mode("sine")
            self.update_status("已切换到默认合成器音色")

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
            'mech_Sigma_valid': self.mech_Sigma_valid
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
            self.mech_Sigma_valid = new_params.get('mech_Sigma_valid',self.mech_Sigma_valid)
            print(f"Main-_update_global_physics_params更新变量\n{new_params}")
            self.mech_Kd = new_params.get('mech_Kd', self.mech_Kd)
            # 摩擦参数
            self.mech_fric_limit_0 = new_params.get('mech_fric_limit_0', self.mech_fric_limit_0)
            self.mech_alpha = new_params.get('mech_alpha', self.mech_alpha)
            self.mech_kinetic = new_params.get('mech_kinetic', self.mech_kinetic)
            self.mech_sigma = new_params.get('mech_sigma', self.mech_sigma)
            self.mech_gamma = new_params.get('mech_gamma',self.mech_gamma)
            self.friction_model = new_params.get('friction_model',self.friction_model)
            self.custom_fric_csv_path = new_params.get('custom_fric_csv_path',self.custom_fric_csv_path)
            self.custom_interp_method = new_params.get('custom_interp_method',self.custom_interp_method)


            # right
            self.repair_simulation_dt=new_params.get('repair_simulation_dt',self.repair_simulation_dt)
            self.max_repair_time=new_params.get('max_repair_time',self.max_repair_time)



            # 更新 StringCSVManager 的文件路径
            new_db_path = new_params.get('db_file_path')
            if new_db_path and self.db_manager:
                self.db_manager.file_path = new_db_path
                self.db_manager._initialize_file() # 确保新路径下的文件被初始化/校验
            # --------------------------------------------------

            # 2. 更新集中配置数据 (MainWindow 持有最终状态)
            self.config_data.update(new_params)
            print(f"config_data\n{self.config_data}")
            # 3. 执行持久化
            self.config_manager.save_config(self.config_data)

            self.update_status("物理参数已更新并保存。")

            self.inform_right_params(new_params)


        except Exception as e:
            self.update_status(f"更新参数失败: {e}")
            QMessageBox.critical(self, "更新错误", f"更新钢琴参数失败:\n{e}")
            import traceback
            traceback.print_exc()
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
            'mech_gamma': self.mech_gamma,
            'friction_model':self.friction_model,
            'custom_fric_csv_path':self.custom_fric_csv_path,
            'custom_interp_method':self.custom_interp_method
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
            self.inform_right_params({
                "mech_Kd" :new_Kd
            })



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

        if self.right_panel:
            self.right_panel.inform_mainwindow_params.connect(self._update_global_physics_params)
        # if hasattr(self, "piano_widget"):
        #     # 点击钢琴键时播放声音
        #     # self.piano_widget.key_clicked.connect(
        #     #     lambda note_name: self._play_piano_note(note_name)
        #     # )
        #     self.piano_widget.key_clicked.connect(self._play_piano_note)
    def _play_piano_note(self, note_name: str):
        """点击钢琴键时播放声音"""
        if not self.audio_engine:
            self.update_status("音频引擎未初始化，无法播放")
            print("音频引擎未初始化，无法播放")
            return
        try:
            self.audio_engine.play_note(note_name, velocity=1.0, duration=1.0)
        except Exception as e:
            self.update_status(f"播放音色失败: {e}")
            print(f"播放音色失败: {e}")

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

        if self.status_card:
            self.status_card.set_progress_active(True)

        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True) # 显示进度条
        self.audio_detector.set_progress_callback(self.progress_update_callback) # 设置进度回调
        # 禁用调节模块 + 按键选择
        self.lock_adjustment_controls()
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

                # 2. 更新右侧调节面板
                cents_values = [
                   r.cents_deviation for r in analysis_result.pitch_results
                   if r.cents_deviation is not None
                ]
                if  cents_values:
                    mean_cents = np.mean(cents_values)
                    self.inform_right_current(analysis_result.dominant_frequency)
                else:
                    mean_cents = 0.0

                if  self.status_card:

                    cents = 0.0
                    if analysis_result.dominant_frequency > 0:
                        cents = 1200 * math.log2(analysis_result.dominant_frequency / self.target_freq)
                    # 平均置信度
                    conf_values = [p.confidence for p in analysis_result.pitch_results]
                    mean_conf = float(np.mean(conf_values)) if conf_values else 0.0

                    self.status_card.update_realtime(
                       freq=analysis_result.dominant_frequency,
                       target_freq=current_target_freq,
                       # cents=mean_cents,
                       cents=cents,
                       confidence=mean_conf
                    )
                    self.status_card.set_status_message("文件分析完成")





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

            if self.status_card:
                self.status_card.set_progress_active(False)

            self.start_analysis_btn.setEnabled(True) # 恢复开始按钮
            self.select_folder_btn.setEnabled(True) # 恢复更改目录
            self.mode_realtime.setEnabled(True) # <--- 恢复实时模式按钮
            # 🔓 恢复右侧调节模块 + 钢琴键盘
            self.unlock_adjustment_controls()

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
            if self.status_card:
                self.status_card.set_mode("实时分析")
            # 清除频谱显示
            if hasattr(self, 'spectrum_widget'):
                self.spectrum_widget.update_frame(np.array([]))
        else:
            self.record_group.setVisible(False)
            self.file_group.setVisible(True)
            self.update_status("切换到文件分析模式")
            if self.status_card:
                self.status_card.set_mode("文件分析")

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
            # 🔒 禁用右侧调节面板和键盘选择
            self.lock_adjustment_controls()
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

        if self.status_card:
            self.status_card.set_progress_active(True)

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
                if hasattr(self, "status_card") and self.status_card:
                    # 当前频率
                    current_freq = analysis_result.dominant_frequency

                    # 平均音分
                    cents_vals = [p.cents_deviation for p in analysis_result.pitch_results if p.cents_deviation is not None]
                    mean_cents = np.mean(cents_vals) if cents_vals else 0.0

                    # 平均置信度
                    conf_vals = [p.confidence for p in analysis_result.pitch_results]
                    mean_conf = float(np.mean(conf_vals)) if conf_vals else 0.0

                    # 更新卡片
                    self.status_card.update_realtime(
                        freq=current_freq,
                        target_freq=self.target_key.frequency if self.target_key else None,
                        cents=mean_cents,
                        confidence=mean_conf
                    )

                # 2. 通知调整面板（使用平均偏差）
                cents_values = [r.cents_deviation for r in analysis_result.pitch_results if r.cents_deviation is not None]
                mean_cents = float(np.mean(cents_values)) if cents_values else 0.0
                if cents_values:
                    mean_cents = np.mean(cents_values)
                    self.inform_right_current(analysis_result.dominant_frequency)

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

            if self.status_card:
                self.status_card.set_progress_active(False)


            # 确保主按钮恢复（已在 on_stop_recording 中处理，但这里再次确认）
            self.start_btn.setEnabled(True)
            # 🔓 分析完成后恢复调节模块
            self.unlock_adjustment_controls()
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
        # 同步到用户态卡片
        if self.status_card:
            self.status_card.update_realtime(
               freq=result.frequency,
               target_freq=result.target_frequency,
               cents=cents,
               confidence=result.confidence
            )



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



    def update_status(self, message: str):
        """更新状态信息：
        - 用户态卡片：显示一行简短状态
        - 调试窗口：沿用原来的复杂文本逻辑
        """

        # 如果 UI 还没建好，先缓存
        if not hasattr(self, 'status_card') or self.status_card is None:
            self._status_message_cache.append(message)
            return

        # 先把缓存里的老消息依次应用
        if self._status_message_cache:
            for cached_msg in self._status_message_cache:
                self._apply_status_update_logic(cached_msg)
            self._status_message_cache.clear()

        # 再应用当前消息
        self._apply_status_update_logic(message)

    def _apply_status_update_logic(self, message: str):
        """实际更新调试窗口 + 用户态卡片"""
        # 1. 调试窗口（原版 QTextEdit 行为）
        if self.debug_status_window is not None:
            self.debug_status_window.apply_status_update_logic(message)

        # 2. 用户态系统状态卡片（简洁一行）
        if self.status_card is not None:
            self.status_card.set_status_message(message)

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
            self.inform_right_target_key(new_key)
        else:
            self.update_status(f"错误: 未找到音名 {note_name}")


    def on_note_selector_changed(self, note_name: str):
        """
        处理 QComboBox 或 PianoWidget 点击导致的音名变化。
        注意：QComboBox 发送的是 str，PianoWidget.key_clicked 也发送 str。
        """
        # 确保 QComboBox 和 PianoWidget 的显示一致
        if self.note_selector.currentText() != note_name:   # 这个!=有点意思哈，qt真有你的
            self.note_selector.setCurrentText(note_name) # 确保下拉菜单选中

        self.set_target_note(note_name)
        self._play_piano_note(note_name)

        # 如果正在录音，需要重新启动实时分析以应用新的 target_frequency
        if self.audio_detector and self.audio_detector.is_recording:
            self.update_status("正在切换调律目标，准备重启分析...")
            self.on_stop_recording()
            self.on_start_recording()
        if self.status_card and self.target_key:
            self.status_card.set_target(self.target_key.note_name, self.target_key.frequency)


    def highlight_target_key(self):
        """更新 PianoWidget 突出显示目标键"""
        if hasattr(self, 'piano_widget') and self.piano_widget is not None:
            if self.target_key:
                # 更新自定义 Widget 的目标键
                self.piano_widget.set_target_note(self.target_key.note_name)
                # 更新 Label 模拟显示 (不再需要这个 Label 了，但为保持结构，更新它)
                message = f"Keyscape样式钢琴键盘\n(当前调律目标: {self.target_key.note_name} - {self.target_key.frequency:.1f}Hz 已高亮)"
                # self.piano_display.setText(message) # 不要了旧的 Label 更新



    def closeEvent(self, event):
        """
        重写窗口关闭事件。
        退出前自动收集所有设置并写入 config.json。
        """
        try:
            # 收集所有当前设置
            new_config = self._collect_all_settings()

            # 强制更新 db_file_path（保险）
            if self.db_manager:
                new_config['db_file_path'] = self.db_manager.get_connected_path()

            # 保存到 config.json
            success = self.config_manager.save_config(new_config)

            if success:
                print("程序退出时，所有设置已成功保存到 config.json。")
            else:
                print("程序退出时，配置保存失败（save_config 返回 False）")

            event.accept()

        except Exception as e:
            print(f"退出时保存配置发生错误: {e}")
            event.accept()



    def _collect_all_settings(self) -> Dict[str, Any]:
        if self.config_data:
            config=self.config_data
        else:
            config = {}

        # -----------------------------
        # 力学参数
        # -----------------------------
        config['mech_I'] = self.mech_I
        config['mech_r'] = self.mech_r
        config['mech_k'] = self.mech_k
        config['mech_Sigma_valid'] = self.mech_Sigma_valid
        config['mech_Kd'] = self.mech_Kd

        config['mech_friction_model'] = self.mech_friction_model
        config['mech_fric_limit_0'] = self.mech_fric_limit_0
        config['mech_alpha'] = self.mech_alpha
        config['mech_kinetic'] = self.mech_kinetic
        config['mech_sigma'] = self.mech_sigma
        config['mech_gamma'] = self.mech_gamma
        config['max_repair_time']=self.max_repair_time
        config['repair_simulation_dt']=self.repair_simulation_dt
        config['friction_model'] = self.friction_model
        config['custom_interp_method'] = self.custom_interp_method
        config['custom_fric_csv_path'] = self.custom_fric_csv_path
        # -----------------------------
        # CSV 文件路径
        # -----------------------------
        if self.db_manager:
            config['db_file_path'] = self.db_manager.get_connected_path()
        else:
            config['db_file_path'] = None

        # -----------------------------
        # 设置菜单中的选项
        # -----------------------------
        config['settings_auto_prompt_save'] = self.settings_auto_prompt_save
        config['settings_save_recording_file'] = self.settings_save_recording_file
        config['settings_max_recording_time'] = self.settings_max_recording_time
        config['tuning_done_threshold_cents'] = self.tuning_done_threshold_cents
        config['tuning_dial_range_cents'] = self.tuning_dial_range_cents

        # ---- Enum 需要序列化为字符串 ----
        config['settings_accidental_type'] = self.settings_accidental_type.name
        config['settings_pitch_algorithm'] = self.settings_pitch_algorithm.name
        config['settings_standard_a4'] = self.settings_standard_a4

        # -----------------------------
        # 音频引擎设置
        # -----------------------------
        if self.audio_engine:
            config['audio_sample_rate'] = self.audio_engine.sr
            config['audio_mode'] = self.audio_engine.mode
            config['audio_tone_path'] = getattr(self.audio_engine, "loaded_path", None)

        return config


    def _save_settings(self):
        """
        将所有当前设置写入 config.json
        """
        try:
            config_dict = self._collect_all_settings()
            ok = self.config_manager.save_config(config_dict)
            if ok:
                self.update_status("设置已保存到 config.json")
            else:
                self.update_status("⚠ 设置保存失败，请检查权限")
        except Exception as e:
            self.update_status(f"⚠ 保存设置时发生错误：{e}")

    def open_help_doc(self, base_name: str):
        """
        打开帮助文档：
          - 优先打开同名 .md
          - 如果没有 .md 则打开 .pdf
          - 如果两者都没有则弹警告
        """
        # 1. 构造路径
        md_path = os.path.join(HELP_FOLDER, f"{base_name}.md")
        pdf_path = os.path.join(HELP_FOLDER, f"{base_name}.pdf")
        doc_path = os.path.join(HELP_FOLDER, f"{base_name}.docx")
        ppt_path = os.path.join(HELP_FOLDER, f"{base_name}.pptx")
        video_path = os.path.join(HELP_FOLDER, f"{base_name}.mov")
        video_url="https://www.bilibili.com/video/BV17Z27B8EjL/"

        # 如果是视频教程，先查找本地视频
        if base_name == "视频教程":
            if os.path.exists(video_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(video_path))
                return
            # 本地没有,打开链接
            QDesktopServices.openUrl(QUrl(video_url))
            return

        # 2. 依次尝试

        if os.path.exists(pdf_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(pdf_path))
            return
        if os.path.exists(md_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(md_path))
            return

        if os.path.exists(doc_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(doc_path))
            return

        if os.path.exists(ppt_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(ppt_path))
            return

        # 3. 全都没有
        QMessageBox.warning(self, "文档缺失", f"无法找到帮助文档：{base_name}")

