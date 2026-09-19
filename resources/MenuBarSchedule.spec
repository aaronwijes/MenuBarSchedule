# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['resources/MenuBarSchedule.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name='MenuBarSchedule',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['Resources/AppIcon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MenuBarSchedule',
)
app = BUNDLE(
    coll,
    name='MenuBarSchedule.app',
    icon='Resources/AppIcon.icns',
    bundle_identifier=None,
    info_plist={
        'CFBundleDisplayName': 'MenuBarSchedule',
        'CFBundleName': 'MenuBarSchedule',
        'CFBundleShortVersionString': '0.0.0',
        'CFBundleVersion': '0.0.0',
        'LSUIElement': True,
        'NSHighResolutionCapable': True,
    },
)
