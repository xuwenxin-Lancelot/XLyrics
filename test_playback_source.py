# -*- coding: utf-8 -*-
"""验证改造后的 PlaybackSource 是否通过 CDP 读到酷狗进度。"""
import os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from playback_source import PlaybackSource

src = PlaybackSource()
print('已创建 PlaybackSource, 当前选择:', src.selected)
print('access reader:', src.accessible.binary if src.accessible else None)

samples = []
for i in range(30):
    val, stamp = src.snapshot()
    if val and val.get('ok'):
        samples.append(val['position_ms'])
        if i % 5 == 0:
            print('采样%02d: %s | %s | %dms | src=%s' % (
                i, val.get('identity', '')[:24], val.get('state'),
                val.get('position_ms', 0), val.get('source')))
    else:
        if i % 5 == 0:
            print('采样%02d: 未就绪 %s' % (i, (val or {}).get('error', '')))
    time.sleep(0.25)

print('\n=== 结果 ===')
if len(samples) >= 2:
    print('有效样本:', len(samples), '首:', samples[0], '末:', samples[-1])
    print('推进:', samples[-1] - samples[0], 'ms')
    print('CDP 模式确认: 读取器 =', src.accessible.binary)
    print('VERIFY_OK' if samples[-1] > samples[0] else 'VERIFY_PARTIAL')
else:
    print('VERIFY_FAIL')
src.close()
