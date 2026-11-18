# -*- coding: utf-8 -*-
# CDP playback reader for KuGou, integrated into Better Lyrics (浮词).
# Author of Better Lyrics: Kerwin. CDP reader added 2026-11-17.
#
# Replaces PlaybackReader.exe's MSAA path for KuGou. Emits one JSON line per
# sample in the EXACT schema PlaybackReader.Read() produced, so the rest of
# Better Lyrics (PlaybackSource/PlaybackClock/lyric matching) needs no changes:
#   {"ok":true,"identity":"artist - title","position_ms":..,"duration_ms":..,
#    "state":"playing"|"paused","precision":"millisecond","source":"CDP",
#    "sampled_unix_ms":..}
#
# Requires KuGou launched with --remote_debug_port=9225 and 推荐 page open.
# Better Lyrics' auto-launch hook will handle that.

import base64
import json
import os
import socket
import struct
import sys
import time
import urllib.request
import urllib.parse

PORT = int(os.environ.get('KUGOU_CDP_PORT', 9225))


def _http(path, method='GET', timeout=2):
    req = urllib.request.Request('http://127.0.0.1:%d%s' % (PORT, path), method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read(4 * 1024 * 1024).decode('utf-8', 'replace'))


class WS:
    def __init__(self, url, timeout=5):
        rest = url.split('://', 1)[1]
        hostport, path = rest.split('/', 1)
        path = '/' + path
        host, port = hostport.split(':')
        self.sock = socket.create_connection((host, int(port)), timeout=timeout)
        self.sock.settimeout(timeout)
        key = base64.b64encode(os.urandom(16)).decode('ascii')
        req = ('GET %s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\n'
               'Connection: Upgrade\r\nSec-WebSocket-Key: %s\r\n'
               'Sec-WebSocket-Version: 13\r\n\r\n') % (path, hostport, key)
        self.sock.sendall(req.encode('ascii'))
        resp = b''
        while b'\r\n\r\n' not in resp:
            c = self.sock.recv(4096)
            if not c:
                raise RuntimeError('CDP handshake closed')
            resp += c
        if b'101' not in resp.split(b'\r\n', 1)[0]:
            raise RuntimeError('CDP handshake failed')
        self.buf = resp.split(b'\r\n\r\n', 1)[1]
        self.closed = False

    def _exact(self, n):
        while len(self.buf) < n:
            c = self.sock.recv(65536)
            if not c:
                self.closed = True
                raise RuntimeError('CDP closed')
            self.buf += c
        d, self.buf = self.buf[:n], self.buf[n:]
        return d

    def send(self, text):
        p = text.encode('utf-8')
        mask = os.urandom(4)
        n = len(p)
        h = bytearray([0x81])
        if n < 126:
            h.append(0x80 | n)
        elif n < 65536:
            h.append(0x80 | 126); h += struct.pack('!H', n)
        else:
            h.append(0x80 | 127); h += struct.pack('!Q', n)
        h += mask
        self.sock.sendall(bytes(h) + bytes(b ^ mask[i % 4] for i, b in enumerate(p)))

    def recv(self):
        while True:
            b0, b1 = self._exact(2)
            op = b0 & 0x0f
            n = b1 & 0x7f
            if n == 126:
                n = struct.unpack('!H', self._exact(2))[0]
            elif n == 127:
                n = struct.unpack('!Q', self._exact(8))[0]
            if b1 & 0x80:
                mask = self._exact(4)
                d = bytes(b ^ mask[i % 4] for i, b in enumerate(self._exact(n)))
            else:
                d = self._exact(n)
            if op == 0x8:
                self.closed = True
                raise RuntimeError('CDP closed by peer')
            if op in (0x1, 0x2):
                return d.decode('utf-8', 'replace')

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


BRIDGE = r'''(() => {
  if (window.__kgReader) return true;
  window.__kgReader = { status(cb) {
    const t = setTimeout(()=>window.__kgResult(JSON.stringify({error:'timeout'})),8000);
    window[cb] = v => { clearTimeout(t); try {
      const s = typeof v === 'string' ? JSON.parse(v) : v;
      window.__kgResult(JSON.stringify({ok:true, raw:s}));
    } catch(e){ window.__kgResult(JSON.stringify({error:String(e)})); } };
    try { external.SuperCall(864, JSON.stringify({callback:cb})); }
    catch(e){ clearTimeout(t); window.__kgResult(JSON.stringify({error:String(e)})); }
  }}; return true;
})()'''


class Cdp:
    def __init__(self):
        self.ws = None
        self.serial = 0

    def connect(self):
        targets = _http('/json/list')
        page = None
        for t in targets:
            if t.get('type') != 'page':
                continue
            try:
                u = urllib.parse.urlparse(t.get('url', ''))
            except Exception:
                continue
            if u.hostname == 'pc.service.kugou.com' and (
                    u.path.startswith('/yueku/') or u.path.startswith('/search/2024/')):
                page = t
                break
        if not page:
            raise RuntimeError('未找到酷狗推荐页；请打开推荐页')
        self.ws = WS(page['webSocketDebuggerUrl'])
        self._rpc('Runtime.addBinding', {'name': '__kgResult'})
        self._eval(BRIDGE)
        ready = self._eval("typeof external !== 'undefined' && typeof external.SuperCall === 'function'")
        if ready is not True:
            raise RuntimeError('酷狗页面未就绪')

    def _rpc(self, method, params=None):
        self.serial += 1
        i = self.serial
        self.ws.send(json.dumps({'id': i, 'method': method, 'params': params or {}}))
        end = time.monotonic() + 6
        while time.monotonic() < end:
            m = json.loads(self.ws.recv())
            if m.get('id') == i:
                if 'error' in m:
                    raise RuntimeError(str(m['error']))
                return m.get('result', {})
        raise RuntimeError('CDP rpc 超时')

    def _eval(self, expr):
        r = self._rpc('Runtime.evaluate', {'expression': expr, 'returnByValue': True})
        if r.get('exceptionDetails'):
            raise RuntimeError('CDP evaluate 异常')
        return r.get('result', {}).get('value')

    def snapshot(self):
        cb = 'kg_' + str(int(time.time() * 1000))
        self._eval('window.__kgReader.status(%s)' % json.dumps(cb))
        end = time.monotonic() + 8
        while time.monotonic() < end:
            m = json.loads(self.ws.recv())
            if m.get('method') != 'Runtime.bindingCalled':
                continue
            p = m.get('params', {})
            if p.get('name') != '__kgResult':
                continue
            payload = json.loads(p.get('payload', '{}'))
            if payload.get('error'):
                raise RuntimeError(payload['error'])
            return payload['raw']
        raise RuntimeError('等待酷狗进度回调超时')

    def close(self):
        if self.ws:
            self.ws.close()
            self.ws = None


def to_row(raw, now_ms):
    if str(raw.get('status', '0')) != '1':
        return {'ok': False, 'error': '酷狗尚未播放', 'sampled_unix_ms': now_ms}
    name = (raw.get('filename', '') or '')
    # Only strip a real media extension. The old code did name.rsplit('.', 1)[0],
    # which ate everything after the last dot — so an artist like "G.E.M.邓紫棋"
    # lost the artist AND the song ("G.E.M.邓紫棋 - 光年之外" -> "G.E.M").
    lowered = name.lower()
    for ext in ('.mp3', '.flac', '.m4a', '.wav', '.ape', '.ogg', '.aac', '.wma'):
        if lowered.endswith(ext):
            name = name[:-len(ext)]
            break
    identity = name
    if identity.endswith(' - 酷狗音乐'):
        identity = identity[:-len(' - 酷狗音乐')]
    play = str(raw.get('play_status', ''))
    try:
        pos = int(round(int(raw.get('progress', 0)) / 10000))
    except (TypeError, ValueError):
        pos = 0
    try:
        dur = int(raw.get('duration', 0) or 0)
    except (TypeError, ValueError):
        dur = 0
    pos = max(0, pos)
    if dur > 0:
        pos = min(pos, dur)
    state = 'playing' if play == 'playing' else 'paused' if play in ('paused', 'pasued') else 'unknown'
    return {
        'ok': True,
        'identity': identity.strip(),
        'position_ms': pos,
        'duration_ms': dur,
        'state': state,
        'precision': 'millisecond',
        'source': 'CDP',
        'sampled_unix_ms': now_ms,
    }


def main():
    # Force UTF-8 output so the parent reader can decode non-ASCII error text.
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    cdp = Cdp()
    interval = 0.1
    while True:
        try:
            if cdp.ws is None or getattr(cdp.ws, 'closed', False):
                cdp.connect()
            raw = cdp.snapshot()
            row = to_row(raw, int(time.time() * 1000))
        except Exception as exc:
            row = {'ok': False, 'error': str(exc), 'sampled_unix_ms': int(time.time() * 1000)}
            cdp.close()
            time.sleep(0.5)
        print(json.dumps(row, ensure_ascii=False), flush=True)
        time.sleep(interval)


if __name__ == '__main__':
    main()
