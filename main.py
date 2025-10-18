# This Python file uses the following encoding: utf-8

# if __name__ == "__main__":
#     pass
# main.py
import sys
import os

# 添加当前目录和ui文件夹到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
ui_path = os.path.join(current_dir, 'ui')
sys.path.insert(0, current_dir)  # 添加当前目录
sys.path.insert(0, ui_path)      # 添加ui文件夹

from PySide6.QtWidgets import QApplication

try:
    # 从ui文件夹导入MainWindow
    from  UI.mainwindow import MainWindow
    print("成功导入MainWindow")
except ImportError as e:
    print(f"导入失败: {e}")
    # 打印路径信息帮助调试
    print(f"当前目录: {current_dir}")
    print(f"UI路径: {ui_path}")
    print(f"Python路径: {sys.path}")
    sys.exit(1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("千椻调音")
    app.setApplicationVersion("1.0.0")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
