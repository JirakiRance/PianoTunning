from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
                               QPushButton, QLabel, QMessageBox, QProgressBar)
from PySide6.QtCore import Qt, QTimer
import numpy as np
import sounddevice as sd

class AudioDeviceDialog(QDialog):
    def __init__(self, current_device_index, parent=None):
        super().__init__(parent)
        self.current_device_index = current_device_index
        self.selected_device_index = current_device_index
        self.test_stream = None
        self.setup_ui()
        self.load_audio_devices()

    def setup_ui(self):
        self.setWindowTitle("选择音频输入设备")
        self.setFixedSize(600, 500)

        layout = QVBoxLayout(self)

        # 说明标签
        info_label = QLabel("请选择要使用的麦克风或音频输入设备:")
        layout.addWidget(info_label)

        # 当前设备显示
        self.current_device_label = QLabel("")
        layout.addWidget(self.current_device_label)

        # 设备列表
        self.device_list = QListWidget()
        self.device_list.itemSelectionChanged.connect(self.on_device_selection_changed)
        self.device_list.itemDoubleClicked.connect(self.on_device_double_clicked)
        layout.addWidget(self.device_list)

        # 设备详情
        self.device_details = QLabel("选择设备查看详情")
        self.device_details.setWordWrap(True)
        layout.addWidget(self.device_details)

        # 测试进度条
        self.test_progress = QProgressBar()
        self.test_progress.setVisible(False)
        layout.addWidget(self.test_progress)

        # 按钮布局
        button_layout = QHBoxLayout()

        self.test_button = QPushButton("测试设备")
        self.test_button.clicked.connect(self.test_selected_device)
        self.test_button.setEnabled(False)
        button_layout.addWidget(self.test_button)

        button_layout.addStretch()

        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setEnabled(False)
        button_layout.addWidget(self.ok_button)

        layout.addLayout(button_layout)

    def load_audio_devices(self):
        """加载音频设备列表"""
        self.device_list.clear()
        try:
            devices = sd.query_devices()
            input_devices = []

            for i, device in enumerate(devices):
                if device.get('max_input_channels', 0) > 0:
                    device_info = {
                        'index': i,
                        'name': device.get('name', f'Device {i}'),
                        'channels': device.get('max_input_channels', 1),
                        'sample_rate': device.get('default_samplerate', 44100),
                        'hostapi': device.get('hostapi', 0)
                    }
                    input_devices.append(device_info)

            if not input_devices:
                self.device_list.addItem("未找到音频输入设备")
                return

            for device in input_devices:
                device_text = f"{device['name']} (通道: {device['channels']})"
                self.device_list.addItem(device_text)

                # 标记当前选中的设备
                if device['index'] == self.current_device_index:
                    self.device_list.setCurrentRow(self.device_list.count() - 1)
                    self.update_device_details(device)
                    self.current_device_label.setText(f"当前设备: {device['name']}")

        except Exception as e:
            self.device_list.addItem(f"获取设备列表失败: {str(e)}")

    def get_audio_devices(self):
        """获取音频设备列表"""
        try:
            devices = sd.query_devices()
            input_devices = []

            for i, device in enumerate(devices):
                if device.get('max_input_channels', 0) > 0:
                    input_devices.append({
                        'index': i,
                        'name': device.get('name', f'Device {i}'),
                        'channels': device.get('max_input_channels', 1),
                        'sample_rate': device.get('default_samplerate', 44100),
                        'hostapi': device.get('hostapi', 0)
                    })
            return input_devices
        except Exception as e:
            print(f"获取音频设备失败: {e}")
            return []

    def on_device_selection_changed(self):
        """设备选择改变时更新详情"""
        current_row = self.device_list.currentRow()
        devices = self.get_audio_devices()

        if 0 <= current_row < len(devices):
            device = devices[current_row]
            self.update_device_details(device)
            self.selected_device_index = device['index']
            self.test_button.setEnabled(True)
            self.ok_button.setEnabled(True)

    def update_device_details(self, device):
        """更新设备详情显示"""
        details = (f"设备名称: {device['name']}\n"
                  f"设备索引: {device['index']}\n"
                  f"输入通道: {device['channels']}\n"
                  f"默认采样率: {device['sample_rate']} Hz\n"
                  f"API: {device['hostapi']}")
        self.device_details.setText(details)

    def on_device_double_clicked(self, item):
        """双击设备项时直接选择并关闭"""
        self.accept()

    def get_selected_device_index(self):
        """获取选中的设备索引"""
        return self.selected_device_index

    def test_selected_device(self):
        """测试选中的音频设备"""
        current_row = self.device_list.currentRow()
        devices = self.get_audio_devices()

        if current_row == -1 or current_row >= len(devices):
            QMessageBox.warning(self, "警告", "请先选择一个音频设备")
            return

        device = devices[current_row]

        try:
            self.test_button.setEnabled(False)
            self.test_progress.setVisible(True)
            self.test_progress.setValue(0)

            # 测试录音功能
            duration = 2  # 测试2秒
            sample_rate = int(device['sample_rate'])

            def test_callback(indata, frames, time, status):
                if status:
                    print(f"测试状态: {status}")

            # 开始测试录音
            self.test_stream = sd.InputStream(
                device=device['index'],
                channels=1,
                samplerate=sample_rate,
                blocksize=1024,
                callback=test_callback
            )

            self.test_stream.start()

            # 模拟测试进度
            for i in range(101):
                self.test_progress.setValue(i)
                QTimer.singleShot(i * 20, lambda: None)  # 简单的进度模拟

            # 停止测试
            self.test_stream.stop()
            self.test_stream.close()
            self.test_stream = None

            self.test_progress.setVisible(False)
            self.test_button.setEnabled(True)

            QMessageBox.information(self, "测试成功",
                                  f"设备测试成功！\n"
                                  f"设备名称: {device['name']}\n"
                                  f"采样率: {sample_rate} Hz\n"
                                  f"测试时长: {duration} 秒")

        except Exception as e:
            self.test_progress.setVisible(False)
            self.test_button.setEnabled(True)
            if self.test_stream:
                self.test_stream.close()
                self.test_stream = None

            QMessageBox.critical(self, "测试失败",
                               f"设备测试失败：{str(e)}\n"
                               f"请选择其他设备或检查设备连接。")

    def closeEvent(self, event):
        """对话框关闭时确保测试流被关闭"""
        if self.test_stream:
            self.test_stream.close()
        event.accept()
