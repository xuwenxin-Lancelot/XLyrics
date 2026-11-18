# -*- mode: python ; coding: utf-8 -*-
# Single-file build of the CDP-based KuGou lyrics app.
# Bundles cdp_reader.exe inside the one-file executable. No external folder.
from pathlib import Path

base = Path(SPECPATH)
analysis = Analysis([str(base / 'desktop_lyrics.py')], pathex=[str(base)],
    binaries=[(str(base / 'dist_reader' / 'cdp_reader.exe'), '.'),
              (str(base / 'dist_reader' / 'netease_reader.exe'), '.'),
              (str(base / 'MediaReader.exe'), '.'),
              (str(base / 'luotuo.exe'), '.'),
              (str(base / 'QrcDecode.dll'), '.'),
              (str(base / 'RoundedBackdrop.dll'), '.')],
    datas=[(str(base / 'assets' / 'x-logo.ico'), 'assets'),
           (str(base / 'assets' / 'x-logo-256.png'), 'assets'),
           (str(base / 'assets' / 'x-logo-64.png'), 'assets'),
           (str(base / 'assets' / 'kugou-logo.png'), 'assets'),
           (str(base / 'assets' / 'netease-logo.png'), 'assets')],
    hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=['tkinter'], noarchive=False)
# Qt 6.12 uses Windows' unversioned ICU API; strip Python's versioned ICU copies.
analysis.binaries = [entry for entry in analysis.binaries
    if Path(entry[0]).name.casefold() != 'icuuc.dll'
    and not Path(entry[0]).name.casefold().startswith('icudt')]
pyz = PYZ(analysis.pure)
exe = EXE(pyz, analysis.scripts, analysis.binaries, analysis.datas, [],
    name='X歌词', debug=False, bootloader_ignore_signals=False,
    strip=False, upx=False, console=False, disable_windowed_traceback=False,
    icon=str(base / 'assets' / 'x-logo.ico'), onefile=True)
