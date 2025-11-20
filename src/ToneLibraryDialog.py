# ToneLibraryDialog.py
# ----------------------------------------
# 用途：
#   - 选择「采样音色包文件夹」或「SF2 SoundFont 文件」
#   - 选择统一的采样率
#   - 提供下载引导链接（多个免费音源网站）
#
# Dialog 返回：
#   - mode: "sample" 或 "sf2"
#   - sample_folder: 选中的音色包文件夹（仅 sample 模式有效）
#   - sf2_file: 选中的 SF2 文件（仅 sf2 模式有效）
#   - samplerate: 采样率
# ----------------------------------------

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QFileDialog, QMessageBox, QComboBox, QGroupBox
)
from PySide6.QtCore import Qt
import os

AUDIO_EXT = (".wav", ".flac", ".aiff", ".aif", ".ogg", ".mp3")
SAMPLE_RATES = [22050, 32000, 44100, 48000, 96000]


class ToneLibraryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("音色配置（Sample 包 / SF2）")
        self.setMinimumWidth(720)

        # 选择结果
        self._selected_mode: str = ""          # "sample" / "sf2"
        self._selected_sample_folder: str = ""
        self._selected_sf2_file: str = ""
        self._selected_samplerate: int = 44100

        self._build_ui()

    # ================= UI =================
    def _build_ui(self):
        layout = QVBoxLayout(self)

        # -------- 顶部说明和引导 --------
        guide = QLabel(
            "<h3>音色配置</h3>"
            "<p>你可以选择两种方式发声：</p>"
            "<ol>"
            "<li><b>采样音色包</b>：一个文件夹中包含多个 WAV/FLAC 等采样文件。</li>"
            "<li><b>SF2 SoundFont</b>：一个 .sf2 文件，即完整虚拟乐器。</li>"
            "</ol>"
            "<p>如果你当前没有音色库，可以前往以下免费网站下载：</p>"
            "<ul>"
            "<li><a href='https://freepats.zenvoid.org/'>FreePats – 开源乐器采样库</a></li>"
            "<li><a href='https://musical-artifacts.com/'>Musical Artifacts – 大量 SF2 / SFZ / 采样</a></li>"
            "<li><a href='https://polyphone-soundfonts.com/'>Polyphone SoundFonts – SoundFont 资源</a></li>"
            "<li><a href='https://archive.org/details/SalamanderGrandPianoV3'>Salamander Grand Piano – 高质量钢琴采样</a></li>"
            "</ul>"
            "<p>提示：对于 Keyscape 等商业音源，需要你在 DAW 中自主导出 WAV 采样或 SF2 文件，本软件不会也不能直接解析其内部数据库。</p>"
        )
        guide.setWordWrap(True)
        guide.setOpenExternalLinks(True)
        layout.addWidget(guide)

        # -------- 采样率设置 --------
        rate_row = QHBoxLayout()
        rate_row.addWidget(QLabel("采样率："))
        self.sr_combo = QComboBox()
        for sr in SAMPLE_RATES:
            self.sr_combo.addItem(str(sr))
        self.sr_combo.setCurrentText("44100")
        rate_row.addWidget(self.sr_combo)
        rate_row.addStretch(1)
        layout.addLayout(rate_row)

        # =====================================================
        #  区块 1：采样音色包（Sample Pack）
        # =====================================================
        gb_sample = QGroupBox("采样音色包（Sample Pack）")
        sample_layout = QVBoxLayout(gb_sample)

        sample_hint = QLabel(
            "步骤：\n"
            "1. 在系统中准备好一个文件夹，里面放入若干钢琴采样（WAV/FLAC/...）。\n"
            "2. 点击“选择采样音色包文件夹”，“应用采样音色包”即可启用。"
        )
        sample_hint.setWordWrap(True)
        sample_layout.addWidget(sample_hint)

        btn_sample_select = QPushButton("选择采样音色包文件夹…")
        btn_sample_select.clicked.connect(self._choose_sample_folder)
        sample_layout.addWidget(btn_sample_select)

        self.sample_info_label = QLabel("当前未选择采样音色包。")
        self.sample_info_label.setWordWrap(True)
        sample_layout.addWidget(self.sample_info_label)

        self.sample_preview_list = QListWidget()
        sample_layout.addWidget(self.sample_preview_list)

        layout.addWidget(gb_sample)

        # =====================================================
        #  区块 2：SF2 SoundFont
        # =====================================================
        gb_sf2 = QGroupBox("SF2 SoundFont")
        sf2_layout = QVBoxLayout(gb_sf2)

        sf2_hint = QLabel(
            "步骤：\n"
            "1. 从网上下载 .sf2 声音库（例如钢琴音色）。\n"
            "2. 点击“选择 SF2 文件”，再点击“应用 SF2 音色”即可启用。"
        )
        sf2_hint.setWordWrap(True)
        sf2_layout.addWidget(sf2_hint)

        btn_sf2_select = QPushButton("选择 SF2 文件…")
        btn_sf2_select.clicked.connect(self._choose_sf2_file)
        sf2_layout.addWidget(btn_sf2_select)

        self.sf2_info_label = QLabel("当前未选择 SF2 文件。")
        self.sf2_info_label.setWordWrap(True)
        sf2_layout.addWidget(self.sf2_info_label)

        layout.addWidget(gb_sf2)

        # =====================================================
        # 底部按钮：分别应用 sample 或 SF2
        # =====================================================
        btn_row = QHBoxLayout()

        self.btn_apply_sample = QPushButton("应用采样音色包")
        self.btn_apply_sample.clicked.connect(self._apply_sample)
        btn_row.addWidget(self.btn_apply_sample)

        self.btn_apply_sf2 = QPushButton("应用 SF2 音色")
        self.btn_apply_sf2.clicked.connect(self._apply_sf2)
        btn_row.addWidget(self.btn_apply_sf2)

        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        layout.addLayout(btn_row)

    # ================= Sample 区域逻辑 =================
    def _choose_sample_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择采样音色包文件夹")
        if not folder:
            return

        self._selected_sample_folder = folder

        # 扫描文件夹中支持的音频文件（只预览部分）
        self.sample_preview_list.clear()
        count = 0
        try:
            for name in os.listdir(folder):
                fp = os.path.join(folder, name)
                if os.path.isfile(fp) and name.lower().endswith(AUDIO_EXT):
                    self.sample_preview_list.addItem(name)
                    count += 1
        except Exception as e:
            QMessageBox.critical(self, "扫描失败", f"扫描音色包失败：{e}")
            self.sample_info_label.setText("扫描音色包失败。")
            return

        if count == 0:
            self.sample_info_label.setText(f"目录：{folder}\n未发现支持的音频文件。")
        else:
            self.sample_info_label.setText(
                f"目录：{folder}\n共检测到 {count} 个音频文件（列表仅展示部分）。"
            )

    def _apply_sample(self):
        """用户点击“应用采样音色包”"""
        if not self._selected_sample_folder:
            QMessageBox.warning(self, "未选择音色包", "请先选择一个采样音色包文件夹。")
            return

        # 校验是否真的有音频文件
        cnt = 0
        for name in os.listdir(self._selected_sample_folder):
            fp = os.path.join(self._selected_sample_folder, name)
            if os.path.isfile(fp) and name.lower().endswith(AUDIO_EXT):
                cnt += 1
        if cnt == 0:
            QMessageBox.warning(self, "音色包无效", "该文件夹中没有任何支持的音频文件。")
            return

        self._selected_mode = "sample"
        self._selected_samplerate = int(self.sr_combo.currentText())
        self.accept()

    # ================= SF2 区域逻辑 =================
    def _choose_sf2_file(self):
        sf2_file, _ = QFileDialog.getOpenFileName(
            self,
            "选择 SF2 文件",
            filter="SoundFont (*.sf2)"
        )
        if not sf2_file:
            return

        self._selected_sf2_file = sf2_file
        self.sf2_info_label.setText(f"已选择 SF2 文件：{sf2_file}")

    def _apply_sf2(self):
        """用户点击“应用 SF2 音色”"""
        if not self._selected_sf2_file:
            QMessageBox.warning(self, "未选择 SF2", "请先选择一个 SF2 文件。")
            return

        if not os.path.isfile(self._selected_sf2_file):
            QMessageBox.warning(self, "文件不存在", "所选 SF2 文件不存在，请重新选择。")
            return

        self._selected_mode = "sf2"
        self._selected_samplerate = int(self.sr_combo.currentText())
        self.accept()

    # ================= 对外访问接口 =================
    def get_selected_mode(self) -> str:
        """返回 'sample' 或 'sf2'，如果用户取消则为空字符串"""
        return self._selected_mode

    def get_sample_folder(self) -> str:
        """返回用户选择的采样音色包文件夹路径（仅在 mode='sample' 时有效）"""
        return self._selected_sample_folder

    def get_sf2_file(self) -> str:
        """返回用户选择的 SF2 文件路径（仅在 mode='sf2' 时有效）"""
        return self._selected_sf2_file

    def get_samplerate(self) -> int:
        """返回用户选择的采样率"""
        return self._selected_samplerate
