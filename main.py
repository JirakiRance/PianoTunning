# This Python file uses the following encoding: utf-8

# if __name__ == "__main__":
#     pass
# main.py
import sys
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
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)



# 添加当前目录和ui文件夹到Python路径
# current_dir = os.path.dirname(os.path.abspath(__file__))
# ui_path = os.path.join(current_dir, 'ui')
# sys.path.insert(0, current_dir)  # 添加当前目录
# sys.path.insert(0, ui_path)      # 添加ui文件夹
# ----------------------------------------------------
# 把 UI 目录加入路径（使用resource_path，避免打包问题）
# ----------------------------------------------------
# current_dir = os.path.dirname(os.path.abspath(__file__))
# ui_path = resource_path("UI")
# sys.path.insert(0, current_dir)
# sys.path.insert(0, ui_path)
# # 确保路径被正确添加
# if ui_path not in sys.path:
#     sys.path.insert(0, ui_path)
# if current_dir not in sys.path:
#     sys.path.insert(0, current_dir)
# print(f"当前目录: {current_dir}")
# print(f"UI路径: {ui_path}")
# print(f"Python路径: {sys.path}")
# # 检查 UI 目录是否存在
# if not os.path.exists(ui_path):
#     print(f"错误: UI路径不存在: {ui_path}")
#     sys.exit(1)
# ----------------------------------------------------
# 路径设置 - 添加所有必要的路径
# ----------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
ui_path = resource_path("UI")
src_path = resource_path("src")

# 确保所有路径被正确添加
paths_to_add = [current_dir, ui_path, src_path]
for path in paths_to_add:
    if path not in sys.path and os.path.exists(path):
        sys.path.insert(0, path)

print(f"当前目录: {current_dir}")
print(f"UI路径: {ui_path}")
print(f"SRC路径: {src_path}")
print(f"Python路径: {sys.path}")

# 检查关键目录是否存在
for path_name, path in [("UI", ui_path), ("SRC", src_path)]:
    if not os.path.exists(path):
        print(f"警告: {path_name}路径不存在: {path}")

# 检查 mainwindow.py 是否存在
mainwindow_path = os.path.join(ui_path, "mainwindow.py")
if not os.path.exists(mainwindow_path):
    print(f"错误: mainwindow.py 不存在于: {mainwindow_path}")
    sys.exit(1)

# 导入编译后的资源文件
try:
    import res_rc  # 这会注册qrc中的资源
    print("成功导入资源文件")
except ImportError as e:
    print(f"资源文件导入失败: {e}")


from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon


# try:
#     # 从ui文件夹导入MainWindow
#     from  UI.mainwindow import MainWindow
#     print("成功导入MainWindow")
# except ImportError as e:
#     print(f"导入失败: {e}")
#     # 打印路径信息帮助调试
#     print(f"当前目录: {current_dir}")
#     print(f"UI路径: {ui_path}")
#     print(f"Python路径: {sys.path}")
#     sys.exit(1)
# 尝试多种方式导入 MainWindow
MainWindow = None
try:
    # 方式1: 直接导入
    from UI.mainwindow import MainWindow
    print(" 成功从 UI.mainwindow 导入 MainWindow")
except ImportError as e:
    print(f"从 UI.mainwindow 导入失败: {e}")
    try:
        # 方式2: 直接导入 mainwindow
        import mainwindow
        MainWindow = mainwindow.MainWindow
        print("✓ 成功直接导入 mainwindow")
    except ImportError as e:
        print(f"直接导入 mainwindow 失败: {e}")
        try:
            # 方式3: 使用 importlib 动态导入
            import importlib.util
            spec = importlib.util.spec_from_file_location("mainwindow", mainwindow_path)
            mainwindow_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mainwindow_module)
            MainWindow = mainwindow_module.MainWindow
            print("✓ 成功使用 importlib 导入 MainWindow")
        except Exception as e:
            print(f"使用 importlib 导入失败: {e}")
            sys.exit(1)

if MainWindow is None:
    print("错误: 无法导入 MainWindow 类")
    sys.exit(1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("千椻调音")
    #app.setWindowIcon(QIcon("E:/Resources/images/acgs/NanoAlice01.png"))
    icon_path = resource_path(":/images/NannoAlice01.png")
    app.setWindowIcon(QIcon(icon_path))
    app.setApplicationVersion("1.0.0")
    window = MainWindow()
    window.resize(1400,700)
    window.show()
    sys.exit(app.exec())
