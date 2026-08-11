# -*- mode: python ; coding: utf-8 -*-
"""Web 版 PyInstaller 打包配置（onedir）"""

from PyInstaller.utils.hooks import collect_all

# uvicorn 运行时动态加载较多模块，全量收集
uvicorn_datas, uvicorn_binaries, uvicorn_hidden = collect_all("uvicorn")

a = Analysis(
    ["launcher.py"],
    pathex=["."],
    binaries=uvicorn_binaries,
    datas=[
        ("web/dist", "web/dist"),           # 前端构建产物
        ("app_icon.png", "."),              # 托盘图标
    ] + uvicorn_datas,
    hiddenimports=[
        "app.main",
        "app.database",
        "app.numbering",
        "core",
        "core.parser",
        "core.generator",
        "core.tree_model",
        "pystray",
        "PIL",
    ] + uvicorn_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Creo编号器Web",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,                          # 无控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="app_icon.ico",
    version="version_info.txt",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Creo编号器Web",
)
