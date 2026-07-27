#!/usr/bin/env python3
"""取四庫本《臨川文集》一百卷作证人（仅核验，不回写）。"""
import json, re, sys, ws
HZ = re.compile(r'[一-鿿㐀-䶿\U00020000-\U0003FFFF]')
titles = ['臨川文集 (四庫全書本)/卷%03d' % k for k in range(1, 101)]
store = {}
for i in range(0, len(titles), 25):
    r = ws.post({'action': 'query', 'titles': '|'.join(titles[i:i + 25]), 'prop': 'revisions',
                 'rvprop': 'content', 'rvslots': 'main', 'redirects': 1,
                 'format': 'json', 'formatversion': '2'}, 'wlcsiku-%03d' % i)
    for p in r['query']['pages']:
        if 'missing' in p:
            continue
        k = int(re.search(r'/卷(\d+)', p['title']).group(1))
        store[k] = ''.join(HZ.findall(p['revisions'][0]['slots']['main']['content']))
    sys.stderr.write('\r%d' % len(store))
sys.stderr.write('\n')
n = sum(len(v) for v in store.values())
print('四庫本《臨川文集》取回 %d 卷 / %d 汉字 (%.2f 万)' % (len(store), n, n / 10000))
print('缺卷:', [k for k in range(1, 101) if k not in store])
json.dump(store, open('wlc-siku.json', 'w', encoding='utf-8'), ensure_ascii=False)
