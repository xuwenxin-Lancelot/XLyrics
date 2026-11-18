# -*- coding: utf-8 -*-
"""CDP playback reader for NetEase Cloud Music (网易云音乐).

Why this exists
---------------
NetEase 3.x renders its window with CEF. It reports title/artist to the Windows
media session (SMTC) but *not* the timeline, so SMTC yields position 0. Its
accessibility tree is not exposed either, so the old MSAA reader finds no
progress slider. What the player page does expose is the progress slider in the
DOM, which we read over the DevTools protocol.

Requires NetEase launched with `--remote-debugging-port=9223`.

Output schema mirrors the MSAA reader so PlaybackSource needs no reinterpretation:
  {"ok":true,"progress_fraction":0.302,"window_title":"歌名 - 歌手",
   "title":..,"artist":..,"identity":..,"position_ms":..,"duration_ms":..,
   "state":"playing"|"paused","source":"CDP","precision":"percent",
   "sampled_unix_ms":..}
"""
import json
import os
import sys
import time
import urllib.request

from cdp_reader import WS

PORT = int(os.environ.get('NETEASE_CDP_PORT', 9223))

# The player page. One synchronous Runtime.evaluate returns everything we need.
SAMPLE = r"""
(function(){
  var out={};
  var s=document.querySelector('[aria-label="播放进度调节"]');
  if(!s){out.error='未找到网易云进度条，请打开播放窗口';return out;}
  var style=s.getAttribute('style')||'';
  var m=style.match(/--track-precent:\s*([0-9.]+)%/);
  out.percent=(m?parseFloat(m[1]):null);
  var t=(s.textContent||'').replace(/\s+/g,' ').trim();
  var mm=t.match(/(\d{1,2}:\d{2})\s*\/\s*(\d{1,2}:\d{2})/);
  out.cur=mm?mm[1]:null;
  out.total=mm?mm[2]:null;

  var titleEl=document.querySelector('[data-testid="tid_minibar_title"] .main-title');
  var title='';
  if(titleEl){
    var spans=titleEl.querySelectorAll('span');
    for(var i=0;i<spans.length;i++){
      if(spans[i].children.length===0){
        var v=(spans[i].textContent||'').trim();
        if(v){title=v;break;}
      }
    }
  }
  out.title=title;
  var a=document.querySelector('[data-testid="tid_minibar_title"] .author');
  out.artist=a?(a.textContent||'').trim():'';

  var btn=document.querySelector('#btn_pc_minibar_play');
  if(btn){
    out.state=btn.querySelector('[class*=cmd-icon-pause]')?'playing'
             :btn.querySelector('[class*=cmd-icon-play]')?'paused':'unknown';
  }else{
    out.state='unknown';
  }
  return out;
})()
"""


# Local CDP requests must never go through a proxy: a stale proxy env var
# (VPN clients rotate ports) would otherwise break the reader outright.
_DIRECT = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _http_json(path, timeout=2):
    url = 'http://127.0.0.1:%d%s' % (PORT, path)
    req = urllib.request.Request(url)
    with _DIRECT.open(req, timeout=timeout) as r:
        return json.loads(r.read(4 * 1024 * 1024).decode('utf-8', 'replace'))


def _secs(text):
    if not text:
        return None
    try:
        parts = [int(p) for p in text.split(':')]
    except (ValueError, AttributeError):
        return None
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return None


class Cdp:
    def __init__(self):
        self.ws = None
        self.serial = 0

    def connect(self):
        targets = _http_json('/json/list')
        page = None
        for t in targets:
            if t.get('type') == 'page' and 'orpheus' in (t.get('url') or ''):
                page = t
                break
        if not page:
            raise RuntimeError('未找到网易云播放页面；请以调试模式启动网易云')
        self.ws = WS(page['webSocketDebuggerUrl'])
        # Fail fast if the page is not the app shell we expect.
        if self._eval('typeof document!=="undefined" && !!document.body') is not True:
            raise RuntimeError('网易云页面未就绪')

    def _eval(self, expr):
        self.serial += 1
        i = self.serial
        self.ws.send(json.dumps({'id': i, 'method': 'Runtime.evaluate',
                                 'params': {'expression': expr, 'returnByValue': True}}))
        end = time.monotonic() + 8
        while time.monotonic() < end:
            m = json.loads(self.ws.recv())
            if m.get('id') != i:
                continue
            if 'error' in m:
                raise RuntimeError(str(m['error']))
            r = m.get('result', {})
            if r.get('exceptionDetails'):
                raise RuntimeError('页面脚本异常')
            return r.get('result', {}).get('value')
        raise RuntimeError('CDP 响应超时')

    def snapshot(self, now_ms):
        raw = self._eval(SAMPLE) or {}
        if raw.get('error'):
            return {'ok': False, 'error': raw['error'], 'state': 'unknown',
                    'source': 'CDP', 'sampled_unix_ms': now_ms}
        total = _secs(raw.get('total'))
        cur = _secs(raw.get('cur'))
        percent = raw.get('percent')
        duration_ms = total * 1000 if total else 0
        position_ms = None
        if percent is not None and duration_ms:
            position_ms = int(round(percent / 100.0 * duration_ms))
        elif cur is not None:
            position_ms = cur * 1000
        if position_ms is None:
            position_ms = 0
        fraction = (percent / 100.0) if percent is not None else (
            (position_ms / duration_ms) if duration_ms else 0.0)
        title = (raw.get('title') or '').strip()
        artist = (raw.get('artist') or '').strip()
        # The app expects `identity` as "artist - title" (same as KuGou's row).
        # `window_title` keeps NetEase's own caption order ("title - artist")
        # so the legacy caption-splitting path stays correct.
        identity = ('%s - %s' % (artist, title)) if title and artist else (title or '')
        window_title = ('%s - %s' % (title, artist)) if title and artist else (title or '')
        return {
            'ok': True,
            'progress_fraction': fraction,
            'window_title': window_title,
            'title': title,
            'artist': artist,
            'identity': identity,
            'position_ms': position_ms,
            'duration_ms': duration_ms,
            'state': raw.get('state') or 'unknown',
            'source': 'CDP',
            'precision': 'percent',
            'sampled_unix_ms': now_ms,
        }

    def close(self):
        if self.ws:
            self.ws.close()
            self.ws = None


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    once = '--once' in sys.argv
    interval = 0.12
    cdp = Cdp()
    while True:
        try:
            if cdp.ws is None:
                cdp.connect()
            row = cdp.snapshot(int(time.time() * 1000))
            sys.stdout.write(json.dumps(row, ensure_ascii=False) + '\n')
            sys.stdout.flush()
            if once:
                return 0
            time.sleep(interval)
        except Exception as e:
            try:
                cdp.close()
            except Exception:
                pass
            row = {'ok': False, 'error': str(e), 'state': 'unknown',
                   'source': 'CDP', 'sampled_unix_ms': int(time.time() * 1000)}
            sys.stdout.write(json.dumps(row, ensure_ascii=False) + '\n')
            sys.stdout.flush()
            if once:
                return 1
            time.sleep(1.5)


if __name__ == '__main__':
    sys.exit(main() or 0)
