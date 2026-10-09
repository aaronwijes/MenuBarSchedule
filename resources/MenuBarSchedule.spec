# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['../main.py'],
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
    icon='AppIcon.icns',
    bundle_identifier='com.aaronwijes.MenuBarSchedule',
    info_plist={
        'CFBundleDisplayName': 'MenuBarSchedule',
        'CFBundleName': 'MenuBarSchedule',
        'CFBundleShortVersionString': '2.0.1',
        'CFBundleVersion': '2.0.1',
        'LSUIElement': True,
        'NSHighResolutionCapable': True,
    },
)
