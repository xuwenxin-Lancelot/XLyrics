# -*- mode: python ; coding: utf-8 -*-
# Folder (onedir) build — this is the distribution that satisfies LGPLv3:
# Qt DLLs stay as ordinary replaceable files under _internal/.
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
           (str(base / 'assets' / 'netease-logo.png'), 'assets'),
           (str(base / 'LICENSE'), '.'),
           (str(base / 'THIRD_PARTY_NOTICES.md'), '.'),
           (str(base / 'licenses'), 'licenses')],
    hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=['tkinter'], noarchive=False)

# Qt 6.12 uses Windows' unversioned ICU API; strip Python's versioned ICU copies.
analysis.binaries = [entry for entry in analysis.binaries
    if Path(entry[0]).name.casefold() != 'icuuc.dll'
    and not Path(entry[0]).name.casefold().startswith('icudt')]

pyz = PYZ(analysis.pure)
exe = EXE(pyz, analysis.scripts, [], exclude_binaries=True,
    name='X歌词', debug=False, bootloader_ignore_signals=False,
    strip=False, upx=False, console=False, disable_windowed_traceback=False,
    icon=str(base / 'assets' / 'x-logo.ico'))
coll = COLLECT(exe, analysis.binaries, analysis.datas,
    strip=False, upx=False, name='X歌词')
