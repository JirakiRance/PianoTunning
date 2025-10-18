
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['PianoTunerDLL.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('AudioDetector.py', '.'),
        ('PitchDetector.py', '.')
    ],
    hiddenimports=[
        'numpy', 'librosa', 'sounddevice', 'wave', 'queue', 
        'datetime', 'threading', 'enum', 'dataclasses',
        'numpy.core._multiarray_umath'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='PianoTunerDLL',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    aslibrary=True,  # 编译为DLL
)
