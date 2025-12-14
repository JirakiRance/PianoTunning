# # This Python file uses the following encoding: utf-8

# # if __name__ == "__main__":
# #     pass
# # main.py
# import sys
# import os



# # ----------------------------
# # 资源定位函数（PyInstaller 必须）
# # ----------------------------
# def resource_path(relative_path: str):
#     """
#     在开发环境与 PyInstaller 打包后返回正确的资源路径
#     """
#     if hasattr(sys, "_MEIPASS"):
#         base_path = sys._MEIPASS
#     else:
#         base_path = os.path.dirname(os.path.abspath(__file__))
#     return os.path.join(base_path, relative_path)

# # ----------------------------------------------------
# # 1. 自动查找 fluidsynth/bin 目录（无论开发环境 or EXE）
# # ----------------------------------------------------
# def locate_fluidsynth_bin():
#     """
#     查找 fluidsynth DLL 所在目录：
#     - 打包后：_MEIPASS/tools/fluidsynth/bin
#     - 开发环境：项目根目录/tools/fluidsynth/bin
#     """
#     # 先查 _MEIPASS
#     if hasattr(sys, "_MEIPASS"):
#         path = os.path.join(sys._MEIPASS, "tools", "fluidsynth", "bin")
#         if os.path.isdir(path):
#             return path

#     # 开发环境路径
#     base = os.path.dirname(os.path.abspath(__file__))
#     path = os.path.join(base, "tools", "fluidsynth", "bin")

#     if os.path.isdir(path):
#         return path

#     return None
# # ----------------------------------------------------
# # 2. 将 fluidsynth/bin 添加到 DLL 搜索路径（核心）
# # ----------------------------------------------------
# def setup_fluidsynth_dll_path():
#     dll_dir = locate_fluidsynth_bin()
#     if dll_dir and os.path.isdir(dll_dir):
#         try:
#             os.add_dll_directory(dll_dir)
#             os.environ["PATH"] = dll_dir + os.pathsep + os.environ.get("PATH", "")
#             print("已加入 fluidsynth DLL 搜索路径:", dll_dir)
#         except Exception as e:
#             print("无法加入 DLL 搜索路径:", e)
#     else:
#         print("未找到 fluidsynth/bin 目录，请检查路径")

# setup_fluidsynth_dll_path()



# if getattr(sys, 'frozen', False):
#     exe_dir = sys._MEIPASS
#     os.add_dll_directory(exe_dir)
#     os.environ["PATH"] = exe_dir + os.pathsep + os.environ.get("PATH", "")




# current_dir = os.path.dirname(os.path.abspath(__file__))
# ui_path = resource_path("UI")
# src_path = resource_path("src")

# # 确保所有路径被正确添加
# paths_to_add = [current_dir, ui_path, src_path]
# for path in paths_to_add:
#     if path not in sys.path and os.path.exists(path):
#         sys.path.insert(0, path)

# print(f"当前目录: {current_dir}")
# print(f"UI路径: {ui_path}")
# print(f"SRC路径: {src_path}")
# print(f"Python路径: {sys.path}")

# # 检查关键目录是否存在
# for path_name, path in [("UI", ui_path), ("SRC", src_path)]:
#     if not os.path.exists(path):
#         print(f"警告: {path_name}路径不存在: {path}")

# # 检查 mainwindow.py 是否存在
# mainwindow_path = os.path.join(ui_path, "mainwindow.py")
# if not os.path.exists(mainwindow_path):
#     print(f"错误: mainwindow.py 不存在于: {mainwindow_path}")
#     sys.exit(1)

# # 导入编译后的资源文件
# try:
#     #import res_rc  # 这会注册qrc中的资源
#     import rc_res
#     print("成功导入资源文件")
# except ImportError as e:
#     print(f"资源文件导入失败: {e}")


# from PySide6.QtWidgets import QApplication,QSplashScreen
# from PySide6.QtGui import QIcon,QPixmap
# from PySide6.QtCore import Qt,QTimer



# # 尝试多种方式导入 MainWindow
# MainWindow = None
# try:
#     # 方式1: 直接导入
#     from UI.mainwindow import MainWindow
#     print(" 成功从 UI.mainwindow 导入 MainWindow")
# except ImportError as e:
#     print(f"从 UI.mainwindow 导入失败: {e}")
#     try:
#         # 方式2: 直接导入 mainwindow
#         import mainwindow
#         MainWindow = mainwindow.MainWindow
#         print("✓ 成功直接导入 mainwindow")
#     except ImportError as e:
#         print(f"直接导入 mainwindow 失败: {e}")
#         try:
#             # 方式3: 使用 importlib 动态导入
#             import importlib.util
#             spec = importlib.util.spec_from_file_location("mainwindow", mainwindow_path)
#             mainwindow_module = importlib.util.module_from_spec(spec)
#             spec.loader.exec_module(mainwindow_module)
#             MainWindow = mainwindow_module.MainWindow
#             print("✓ 成功使用 importlib 导入 MainWindow")
#         except Exception as e:
#             print(f"使用 importlib 导入失败: {e}")
#             sys.exit(1)

# if MainWindow is None:
#     print("错误: 无法导入 MainWindow 类")
#     sys.exit(1)

# from LaunchScreen import LaunchScreen

# if __name__ == "__main__":
#     app = QApplication(sys.argv)

#     # 1. 创建启动界面
#     splash = LaunchScreen(":/images/PianoTuningCover.png")
#     splash.show()
#     app.processEvents()

#     # 2. 提供回调给 MainWindow
#     def report(percent, text):
#         splash.update_progress(percent, text)
#         app.processEvents()

#     # 3. 创建主窗口
#     window = MainWindow(report)
#     window.set_launch_progress_callback(report)

#     # 4. 主窗口加载完成 → 延迟 1 秒再关闭 Splash
#     def finish_splash():
#         splash.close()
#         window.show()

#     # 保证 splash 至少停留 1 秒
#     QTimer.singleShot(1000, finish_splash)

#     window.resize(1400, 800)

#     sys.exit(app.exec())


# This Python file uses the following encoding: utf-8

import sys
import os

# ----------------------------
# 资源定位函数（PyInstaller 必须）
# ----------------------------
def resource_path(relative_path: str):
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


# ----------------------------
#  声明全局变量（供 MainWindow 引用）
# ----------------------------
current_dir = None
ui_path = None
src_path = None
mainwindow_path = None


# ----------------------------------------------------
# fluidsynth DLL 路径工具
# ----------------------------------------------------
def locate_fluidsynth_bin():
    if hasattr(sys, "_MEIPASS"):
        p = os.path.join(sys._MEIPASS, "tools", "fluidsynth", "bin")
        if os.path.isdir(p):
            return p

    base = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(base, "tools", "fluidsynth", "bin")
    return p if os.path.isdir(p) else None


def setup_fluidsynth_dll_path():
    dll_dir = locate_fluidsynth_bin()
    if dll_dir and os.path.isdir(dll_dir):
        try:
            os.add_dll_directory(dll_dir)
            os.environ["PATH"] = dll_dir + os.pathsep + os.environ.get("PATH", "")
        except Exception as e:
            print("无法加入 DLL 搜索路径:", e)


# ----------------------------------------------------
# ★★★★★  main.py 初始化逻辑 + 进度汇报 0~60%
# ----------------------------------------------------
def init_environment(report):

    global current_dir, ui_path, src_path, mainwindow_path

    report(2, "正在启动程序…")

    # 1. 设置 DLL 路径
    report(5, "设置 Fluidsynth 环境…")
    setup_fluidsynth_dll_path()

    # 2. 冻结环境 DLL 设置
    report(10, "加载打包环境…")
    if getattr(sys, 'frozen', False):
        exe_dir = sys._MEIPASS
        os.add_dll_directory(exe_dir)
        os.environ["PATH"] = exe_dir + os.pathsep + os.environ.get("PATH", "")

    # 3. 计算路径并赋值给全局变量
    report(20, "准备界面模块路径…")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ui_path = resource_path("UI")
    src_path = resource_path("src")

    # sys.path 注入
    for p in [current_dir, ui_path, src_path]:
        if p and os.path.exists(p) and p not in sys.path:
            sys.path.insert(0, p)

    # 4. 检查目录
    report(30, "检查项目结构…")
    for name, p in [("UI", ui_path), ("SRC", src_path)]:
        if not os.path.exists(p):
            print(f"[警告] {name} 路径不存在：{p}")

    # 5. MainWindow 文件
    mainwindow_path = os.path.join(ui_path, "mainwindow.py")
    if not os.path.exists(mainwindow_path):
        print("错误: mainwindow.py 不存在:", mainwindow_path)
        sys.exit(1)

    # 6. 动态导入 MainWindow
    report(40, "加载主界面模块…")

    MainWindowClass = None
    try:
        from UI.mainwindow import MainWindow as MW
        MainWindowClass = MW
    except:
        try:
            import mainwindow
            MainWindowClass = mainwindow.MainWindow
        except:
            import importlib.util
            spec = importlib.util.spec_from_file_location("mainwindow", mainwindow_path)
            mwmod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mwmod)
            MainWindowClass = mwmod.MainWindow

    if MainWindowClass is None:
        print("错误：无法导入 MainWindow")
        sys.exit(1)

    report(50, "环境初始化完成")
    return MainWindowClass


# ----------------------------------------------------
# 主程序
# ----------------------------------------------------
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
try:
    import rc_res
except Exception as e:
    print("rc_res 导入失败:", e)
from src.LaunchScreen import LaunchScreen


if __name__ == "__main__":

    app = QApplication(sys.argv)
    app.setApplicationName("钢琴调律辅助系统")

    # 1. Splash
    splash = LaunchScreen(":/images/PianoTuningCover.png")
    splash.show()
    app.processEvents()

    def report(p, t):
        splash.update_progress(p, t)
        app.processEvents()

    # 2. MAIN 初始化（0–60）
    MainWindowClass = init_environment(report)

    # 3. 创建主窗口（内部会继续 60–100）
    window = MainWindowClass(report)

    report(100, "启动完成，正在打开应用…")

    # 4. 延迟关闭 Splash
    def finish_splash():
        splash.close()
        window.show()

    QTimer.singleShot(1000, finish_splash)

    window.resize(1400, 800)
    sys.exit(app.exec())
