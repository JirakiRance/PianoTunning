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

# ----------------------------------------------------
# 1. 自动查找 fluidsynth/bin 目录（无论开发环境 or EXE）
# ----------------------------------------------------
def locate_fluidsynth_bin():
    """
    查找 fluidsynth DLL 所在目录：
    - 打包后：_MEIPASS/tools/fluidsynth/bin
    - 开发环境：项目根目录/tools/fluidsynth/bin
    """
    # 先查 _MEIPASS
    if hasattr(sys, "_MEIPASS"):
        path = os.path.join(sys._MEIPASS, "tools", "fluidsynth", "bin")
        if os.path.isdir(path):
            return path

    # 开发环境路径
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, "tools", "fluidsynth", "bin")

    if os.path.isdir(path):
        return path

    return None
# ----------------------------------------------------
# 2. 将 fluidsynth/bin 添加到 DLL 搜索路径（核心）
# ----------------------------------------------------
def setup_fluidsynth_dll_path():
    dll_dir = locate_fluidsynth_bin()
    if dll_dir and os.path.isdir(dll_dir):
        try:
            os.add_dll_directory(dll_dir)
            os.environ["PATH"] = dll_dir + os.pathsep + os.environ.get("PATH", "")
            print("已加入 fluidsynth DLL 搜索路径:", dll_dir)
        except Exception as e:
            print("无法加入 DLL 搜索路径:", e)
    else:
        print("未找到 fluidsynth/bin 目录，请检查路径")

setup_fluidsynth_dll_path()



if getattr(sys, 'frozen', False):
    exe_dir = sys._MEIPASS
    os.add_dll_directory(exe_dir)
    os.environ["PATH"] = exe_dir + os.pathsep + os.environ.get("PATH", "")



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
    #import res_rc  # 这会注册qrc中的资源
    import rc_res
    print("成功导入资源文件")
except ImportError as e:
    print(f"资源文件导入失败: {e}")


from PySide6.QtWidgets import QApplication,QSplashScreen
from PySide6.QtGui import QIcon,QPixmap
from PySide6.QtCore import Qt,QTimer


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
    app.setApplicationName("钢琴调律辅助系统")
    icon_path = resource_path(":/images/NannoAlice01.png")
    app.setWindowIcon(QIcon(icon_path))
    app.setApplicationVersion("1.0.0")


    # ======================================================
    # 创建 Splash Screen（启动封面）
    # ======================================================
    pix = QPixmap(":/images/PianoTuningCover.png")

    scaled_pix = pix.scaled(
        pix.width() // 4,
        pix.height() // 4,
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation
    )


    splash = QSplashScreen(scaled_pix, Qt.WindowStaysOnTopHint)
    splash.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
    splash.show()  # 显示封面

    # 强制刷新
    app.processEvents()

    # ======================================================
    # 启动主窗口（延迟 500ms，让封面至少显示一下）
    # ======================================================
    def load_main_window():
        window = MainWindow()
        window.resize(1400, 800)
        window.show()

        splash.finish(window)  # 关闭封面窗口

    # 延迟执行主窗口
    QTimer.singleShot(1000, load_main_window)


    # window = MainWindow()
    # window.resize(1400,800)
    # window.show()



    sys.exit(app.exec())
