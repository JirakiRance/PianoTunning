# -*- mode: python ; coding: utf-8 -*-

import os
import glob

block_cipher = None

# ===========================================================
# ⭐ 1. 指向真正的 fluidsynth.py（49KB）
# ===========================================================
real_fluidsynth = r"D:\PianoTunning\PT\venv\Lib\site-packages\fluidsynth.py"
if not os.path.isfile(real_fluidsynth):
    raise RuntimeError("找不到真正的 fluidsynth.py，请检查路径: " + real_fluidsynth)

# ===========================================================
# ⭐ 2. 自动打包 C:\tools\fluidsynth\bin 下的所有 DLL
# ===========================================================
fluidsynth_dir = r"C:\tools\fluidsynth\bin"
fluidsynth_bins = []

if os.path.isdir(fluidsynth_dir):
    for dll in glob.glob(os.path.join(fluidsynth_dir, "*.dll")):
        fluidsynth_bins.append((dll, "."))  # 复制到 dist 根目录
else:
    print("⚠ 警告: 未找到 C:\\tools\\fluidsynth\\bin，无法打包 fluidsynth DLL")

# ===========================================================
# 原始 Analysis（极小修改）
# ===========================================================
a = Analysis(
    ['main.py'],
    pathex=['.', './src'],
    binaries=fluidsynth_bins,         # ⭐ 注入 fluidsynth DLL
    datas=[
        ('data', 'data'),
        ('help', 'help'),
        ('recordings', 'recordings'),
        ('UI', 'UI'),
        ('src', 'src'),

        # ⭐ 3. 强制把真正的 fluidsynth.py 放进可执行包
        (real_fluidsynth, '.'),       # 放在运行根目录（与 main.py 同级）
    ],
    hiddenimports=[
        # 核心包
        'numpy', 'librosa', 'sounddevice', 'soundfile', 'scipy',
        'PySide6', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets',
        'numba', 'pooch', 'resampy', 'audioread',
        'res_rc',

        # UI 模块
        'UI.mainwindow',

        # 自定义模块
        'AudioDetector',
        'AudioEngine',
        'ConfigManager',
        'FrictionConfigWidget',
        'MechanicsEngine',
        'MouseSmoothConfigDialog',
        'PianoConfigWidget',
        'PianoGenerator',
        'PianoWidget',
        'PitchDetector',
        'RightMechanicsPanel',
        'SampleRateConfigWidget',
        'SpectrumWidget',
        'StringCSVManager',
        'ToneLibraryDialog',
        'TuningDialWidget',
        'UserStatusCard',

        # ⭐ fluidsynth 顶级模块（使用真正的 fluidsynth.py）
        'fluidsynth',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],

    # ⭐ 4. 禁止 PyInstaller 打包错误的 fluidsynth 文件夹
    excludes=[
        #'fluidsynth.*',       # 彻底排除错误的 fluidsynth 目录
    ],

    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PianoTuning',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='NannoAlice.ico',
)
