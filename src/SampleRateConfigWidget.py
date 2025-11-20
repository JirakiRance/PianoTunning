from PySide6.QtWidgets import (QApplication, QMainWindow,QFileDialog,QListWidget,QListWidgetItem,
                                QInputDialog,QMessageBox,QDialog,QVBoxLayout,QComboBox,
                                QLabel,QHBoxLayout,QPushButton)

SAMPLE_RATES=[44100,48000,96000,22050]

class SampleRateDialog(QDialog):
    def __init__(self, current_rate=44100, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置采样率")

        layout = QVBoxLayout(self)
        self.combo = QComboBox()
        for sr in SAMPLE_RATES:
            self.combo.addItem(str(sr))
        self.combo.setCurrentText(str(current_rate))
        layout.addWidget(QLabel("选择新的采样率："))
        layout.addWidget(self.combo)

        row = QHBoxLayout()
        ok = QPushButton("应用")
        cancel = QPushButton("取消")
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        row.addWidget(ok)
        row.addWidget(cancel)

        layout.addLayout(row)

    def get_samplerate(self):
        return int(self.combo.currentText())
