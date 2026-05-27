# -*- mode: python ; coding: utf-8 -*-
import sys
import os

# SPECPATH 是 PyInstaller 提供的变量，指向 spec 文件所在目录
PROJECT_ROOT = SPECPATH

block_cipher = None

a = Analysis(
    [os.path.join(PROJECT_ROOT, 'main.py')],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=[
        ('config', 'config'),  # 打包整个 config 目录，保留所有 JSON 文件
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.sip',
        'reportlab',
        'reportlab.lib.pagesizes',
        'reportlab.lib.styles',
        'reportlab.lib.units',
        'reportlab.lib.enums',
        'reportlab.lib.colors',
        'reportlab.platypus',
        'reportlab.platypus.tableofcontents',
        'reportlab.pdfbase',
        'reportlab.pdfbase.ttfonts',
        'reportlab.pdfbase.pdfmetrics',
        'reportlab.graphics',
        'reportlab.graphics.shapes',
        'matplotlib',
        'matplotlib.backends.backend_qtagg',
        'matplotlib.backends.backend_agg',
        'matplotlib.figure',
        'matplotlib.font_manager',
        'matplotlib.dates',
        'openpyxl',
        'json',
        'csv',
        'shutil',
        're',
        'os',
        'tempfile',
        'time',
        'glob',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='BigBoom',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # 无命令行窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # 如需图标，替换为图标路径
)
