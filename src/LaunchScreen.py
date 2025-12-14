# launch_screen.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QSize

class LaunchScreen(QWidget):
    """
    独立启动界面：支持
    - 图片
    - 状态文字
    - 进度条
    提供 update_progress(percent, text) 方法供外部调用
    """

    def __init__(self, pixmap_path: str, parent=None):
        super().__init__(parent)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # --- 布局 ---
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # --- 图片 ---
        self.label_pic = QLabel()
        pix = QPixmap(pixmap_path)

        # 自动缩放
        if pix.width() > 600:
            pix = pix.scaled(pix.width()//4, pix.width()//4, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.label_pic.setPixmap(pix)
        self.label_pic.setAlignment(Qt.AlignCenter)

        # --- 文本 ---
        self.label_text = QLabel("正在加载…")
        self.label_text.setStyleSheet("color: white; font-size: 18px;")
        self.label_text.setAlignment(Qt.AlignCenter)

        # --- 进度条 ---
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255, 255, 255, 40);
                border: 1px solid rgba(255,255,255,80);
                border-radius: 4px;
                height: 8px;   /* 进度条更细 */
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #4cd964;   /* Apple 系绿：专业、清爽 */
                border-radius: 4px;
            }
        """)


        # 加入布局
        layout.addWidget(self.label_pic)
        layout.addWidget(self.label_text)
        layout.addWidget(self.progress)

        self.resize(pix.width() + 60, pix.height() + 120)

    # ------------------------------------------------------
    #   外部调用接口：更新进度 + 文本
    # ------------------------------------------------------
    def update_progress(self, percent: int, text: str = None):
        self.progress.setValue(percent)
        if text:
            self.label_text.setText(text)
        self.repaint()  # 强制刷新
