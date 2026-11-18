# -*- mode: python ; coding: utf-8 -*-
# Modified 2026-11-17: KuGou progress via CDP. Native DLLs that require MSVC
# (PlaybackReader/RoundedBackdrop/QrcDecode) are excluded; the CDP reader exe
# is bundled instead. Missing native backdrop falls back to Qt translucent bg.
from pathlib import Path

base = Path(SPECPATH)
analysis = Analysis([str(base / 'desktop_lyrics.py')], pathex=[str(base)],
    binaries=[(str(base / 'dist_reader' / 'cdp_reader.exe'), '.')],
    datas=[(str(base / 'assets' / 'floating-lyrics.ico'), 'assets'),
           (str(base / 'assets' / 'floating-lyrics.png'), 'assets'),
           (str(base / 'LICENSE'), '.'),
           (str(base / 'THIRD_PARTY_NOTICES.md'), '.'),
           (str(base / 'third_party'), 'third_party')],
    hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=['tkinter'], noarchive=False)
# Qt 6.12 uses Windows' unversioned ICU API; strip Python's versioned ICU copies.
analysis.binaries = [entry for entry in analysis.binaries
    if Path(entry[0]).name.casefold() != 'icuuc.dll'
    and not Path(entry[0]).name.casefold().startswith('icudt')]
pyz = PYZ(analysis.pure)
exe = EXE(pyz, analysis.scripts, [], exclude_binaries=True, name='浮词CDP',
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
    console=False, disable_windowed_traceback=False,
    icon=str(base / 'assets' / 'floating-lyrics.ico'))
collection = COLLECT(exe, analysis.binaries, analysis.datas,
    strip=False, upx=False, name='浮词CDP')
