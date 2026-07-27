#!/usr/bin/env python3
"""取四庫本《東坡全集》115 卷作第二证人（仅用于核验，绝不回写正文）。"""
import json, re, sys, ws
HZ = re.compile(r'[一-鿿㐀-䶿\U00020000-\U0003FFFF]')
titles = ['東坡全集 (四庫全書本)/卷%03d' % k for k in range(1, 116)]
store = {}
for i in range(0, len(titles), 25):
    r = ws.post({'action': 'query', 'titles': '|'.join(titles[i:i + 25]), 'prop': 'revisions',
                 'rvprop': 'content', 'rvslots': 'main', 'redirects': 1,
                 'format': 'json', 'formatversion': '2'}, 'siku-%03d' % i)
    for p in r['query']['pages']:
        if 'missing' in p:
            continue
        m = re.match(r'.*?/卷(\d+)', p['title'])
        store[int(m.group(1))] = ''.join(
            HZ.findall(p['revisions'][0]['slots']['main']['content']))
    sys.stderr.write('\r%d' % len(store))
sys.stderr.write('\n')
n = sum(len(v) for v in store.values())
print('四庫本取回 %d 卷 / %d 汉字 (%.2f 万)' % (len(store), n, n / 10000))
print('缺卷:', [k for k in range(1, 116) if k not in store])
json.dump(store, open('siku.json', 'w', encoding='utf-8'), ensure_ascii=False)
