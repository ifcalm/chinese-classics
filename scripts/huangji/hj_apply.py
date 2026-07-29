#!/usr/bin/env python3
"""落实回改与补文到中间件，逐处断言命中。"""
import json, re
from hj_fix import FIX, ADD
HZ = re.compile(r'[一-鿿㐀-䶿\U00020000-\U0003FFFF]')
VOL = {'卷十一': '皇極經世/卷十一', '卷十二': '皇極經世/卷十二',
       '卷十三': '皇極經世/卷十三', '卷十四': '皇極經世/卷十四'}
tx = json.load(open('hj-raw.json', encoding='utf-8'))
log = []
for vol, bad, good, why in FIX:
    k = VOL[vol]
    n = tx[k].count(bad)
    if not n:
        raise SystemExit('!! 未命中 %s %s' % (vol, bad))
    tx[k] = tx[k].replace(bad, good)
    log.append({'kind': '回改', 'vol': vol, 'bad': bad, 'good': good, 'n': n, 'why': why})
    print('回改 %-4s %s→%s ×%d' % (vol, bad, good, n))
for vol, anchor, add, why in ADD:
    k = VOL[vol]
    if tx[k].count(anchor) != 1:
        raise SystemExit('!! 锚点不唯一 %s %r (%d)' % (vol, anchor, tx[k].count(anchor)))
    tx[k] = tx[k].replace(anchor, anchor + add, 1)
    log.append({'kind': '补文', 'vol': vol, 'anchor': anchor, 'add': add,
                'n': len(HZ.findall(add)), 'why': why})
    print('补文 %-4s +%2d 字  %s' % (vol, len(HZ.findall(add)), add[:34]))
json.dump(tx, open('hj-fixed.json', 'w', encoding='utf-8'), ensure_ascii=False)
json.dump(log, open('hj-fixlog.json', 'w', encoding='utf-8'), ensure_ascii=False)
n = sum(len(HZ.findall(v)) for v in tx.values())
print('\n回改后四卷 %d 汉字 (%.2f 万)' % (n, n / 10000))
