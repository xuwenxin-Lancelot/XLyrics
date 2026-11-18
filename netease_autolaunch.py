# -*- coding: utf-8 -*-
# Added 2026-11-18 for the NetEase CDP integration.
# Ensures NetEase Cloud Music runs with its CEF debug port open so
# netease_reader.py can read the progress slider. Standard library only.
import ctypes
import ctypes.wintypes as wt
import os
import subprocess
import time
import urllib.request

PORT = int(os.environ.get('NETEASE_CDP_PORT', 9223))
PROCESS = 'cloudmusic.exe'


def _http(path, timeout=2):
    url = 'http://127.0.0.1:%d%s' % (PORT, path)
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read(4 * 1024 * 1024).decode('utf-8', 'replace')


def _page_ready():
    """True when the NetEase app shell is reachable over CDP."""
    try:
        import json
        for t in json.loads(_http('/json/list', timeout=1.5)):
            if t.get('type') == 'page' and 'orpheus' in (t.get('url') or ''):
                return True
    except Exception:
        pass
    return False


def _running_exe():
    """Path of the running cloudmusic.exe, discovered via Toolhelp snapshot."""
    TH32CS_SNAPPROCESS = 0x00000002
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [('dwSize', wt.DWORD), ('cntUsage', wt.DWORD),
                    ('th32ProcessID', wt.DWORD), ('th32DefaultHeapID', ctypes.c_void_p),
                    ('th32ModuleID', wt.DWORD), ('cntThreads', wt.DWORD),
                    ('th32ParentProcessID', wt.DWORD), ('pcPriClassBase', ctypes.c_long),
                    ('dwFlags', wt.DWORD), ('szExeFile', ctypes.c_wchar * 260)]

    k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap in (0, -1):
        return None
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        ok = k32.Process32FirstW(snap, ctypes.byref(entry))
        while ok:
            if entry.szExeFile.lower() == PROCESS:
                h = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False,
                                    entry.th32ProcessID)
                if h:
                    try:
                        buf = ctypes.create_unicode_buffer(1024)
                        size = wt.DWORD(1024)
                        if k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
                            return buf.value
                    finally:
                        k32.CloseHandle(h)
            ok = k32.Process32NextW(snap, ctypes.byref(entry))
    finally:
        k32.CloseHandle(snap)
    return None


def _registry_exe():
    try:
        import winreg
        for root_key in (r'orpheus\shell\open\command',
                         r'cloudmusic\shell\open\command'):
            try:
                with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, root_key) as k:
                    cmd = winreg.QueryValueEx(k, '')[0]
            except OSError:
                continue
            cmd = cmd.strip()
            if cmd.startswith('"'):
                path = cmd[1:cmd.index('"', 1)]
            else:
                path = cmd.split(' ')[0]
            if path.lower().endswith('.exe') and os.path.isfile(path):
                return path
    except Exception:
        pass
    return None


def find_exe():
    for fn in (_running_exe, _registry_exe):
        try:
            p = fn()
        except Exception:
            p = None
        if p and os.path.isfile(p):
            return p
    for p in (r'D:\Program Files\CloudMusic\cloudmusic.exe',
              r'C:\Program Files (x86)\Netease\CloudMusic\cloudmusic.exe',
              r'C:\Program Files\Netease\CloudMusic\cloudmusic.exe',
              r'C:\Program Files\CloudMusic\cloudmusic.exe'):
        if os.path.isfile(p):
            return p
    return None


def _process_running():
    try:
        out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq ' + PROCESS, '/NH'],
                             capture_output=True, text=True, timeout=8,
                             creationflags=subprocess.CREATE_NO_WINDOW)
        return PROCESS.lower() in (out.stdout or '').lower()
    except Exception:
        return False


def ensure_netease_debug(wait_seconds=75, only_if_running=True):
    """Return (ok, message). Restarts NetEase in CDP debug mode when needed.

    `only_if_running` keeps the app from launching NetEase on its own: it will
    only convert an already-running instance into debug mode.
    """
    if _page_ready():
        return True, '网易云 CDP 已就绪'
    if only_if_running and not _process_running():
        return False, '网易云未运行'
    exe = find_exe()
    if not exe:
        return False, '未找到网易云安装路径'
    try:
        subprocess.run(['taskkill', '/IM', PROCESS, '/T', '/F'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
    except Exception:
        pass
    time.sleep(1.5)
    try:
        subprocess.Popen([exe, '--remote-debugging-port=%d' % PORT],
                         cwd=os.path.dirname(exe),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        return False, '启动网易云失败: %s' % e
    deadline = time.monotonic() + wait_seconds
    while time.monotonic() < deadline:
        if _page_ready():
            return True, '网易云已切换到调试模式'
        time.sleep(0.6)
    return False, '网易云界面未就绪，请稍后重试或手动播放一首歌'


if __name__ == '__main__':
    print(ensure_netease_debug())
