# -*- coding: utf-8 -*-
# Added 2026-11-17 by WorkBuddy for the CDP integration of Better Lyrics.
# Ensures KuGou runs with its CEF debug port open so cdp_reader.py can read
# precise playback progress. Uses only the standard library.
import os
import re
import subprocess
import time
import urllib.parse
import urllib.request

PORT = int(os.environ.get('KUGOU_CDP_PORT', 9225))
RECOMMEND = 'https://pc.service.kugou.com/yueku/2024/find/index.html'


def _http(path, method='GET', timeout=2):
    req = urllib.request.Request('http://127.0.0.1:%d%s' % (PORT, path), method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(4 * 1024 * 1024).decode('utf-8', 'replace')


def _json(path, method='GET', timeout=2):
    import json
    return json.loads(_http(path, method, timeout))


def _recommend_ready():
    try:
        import json
        targets = _json('/json/list', timeout=1.5)
        for t in targets:
            if t.get('type') != 'page':
                continue
            u = urllib.parse.urlparse(t.get('url', ''))
            if u.hostname == 'pc.service.kugou.com' and (
                    u.path.startswith('/yueku/') or u.path.startswith('/search/2024/')):
                return True
    except Exception:
        pass
    return False


def _find_exe():
    candidates = []
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r'kugou\shell\open\command') as k:
            cmd = winreg.QueryValueEx(k, '')[0]
        m = re.search(r'"([^"]+KuGou\.exe)"', cmd, re.I)
        if m:
            candidates.append(m.group(1))
    except Exception:
        pass
    candidates += [
        r'C:\RUANjian\KGMusic\KuGou.exe',
        r'C:\Program Files (x86)\KuGou2012\KuGou.exe',
        r'C:\Program Files\KuGou2012\KuGou.exe',
    ]
    for p in candidates:
        if p and os.path.isfile(p):
            return p
    return None


def ensure_kugou_debug():
    """Return (ok, message). Launches KuGou in CDP debug mode if needed."""
    if _recommend_ready():
        return True, '酷狗 CDP 已就绪'
    exe = _find_exe()
    if not exe:
        return False, '未找到酷狗安装路径'
    try:
        subprocess.run(['taskkill', '/IM', 'KuGou.exe', '/T', '/F'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
    except Exception:
        pass
    time.sleep(1.2)
    try:
        subprocess.Popen([exe, '--remote_debug_port=%d' % PORT,
                          '--remote-debugging-address=127.0.0.1'],
                         cwd=os.path.dirname(exe),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        return False, '启动酷狗失败: %s' % e
    for _ in range(60):
        try:
            _http('/json/version', timeout=0.5)
            break
        except Exception:
            time.sleep(0.5)
    try:
        _http('/json/new?' + urllib.parse.quote(RECOMMEND, safe=''), method='PUT', timeout=2)
    except Exception:
        pass
    for _ in range(60):
        if _recommend_ready():
            return True, '酷狗 CDP 已就绪'
        time.sleep(0.5)
    return False, '酷狗推荐页未加载，请手动打开"推荐"'
