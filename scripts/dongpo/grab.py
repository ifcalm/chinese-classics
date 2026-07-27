#!/usr/bin/env python3
"""批量抓取《東坡全集》全部篇页 wikitext（50 篇/请求）。"""
import json, sys, ws

idx = json.load(open('wlc-idx.json', encoding='utf-8'))
tgs = sorted({it['target'] for v in idx for it in v['items']})
print('唯一目标 %d，需 %d 个请求' % (len(tgs), (len(tgs) + 49) // 50))
store, miss, redir = {}, [], {}
for i in range(0, len(tgs), 50):
    ch = tgs[i:i + 50]
    r = ws.post({'action': 'query', 'titles': '|'.join(ch), 'prop': 'revisions',
                'rvprop': 'content', 'rvslots': 'main', 'redirects': 1,
                'format': 'json', 'formatversion': '2'}, 'dp-grab-%05d' % i)
    q = r['query']
    for m in q.get('redirects', []) + q.get('normalized', []):
        redir[m['from']] = m['to']
    for p in q['pages']:
        if 'missing' in p:
            miss.append(p['title'])
        else:
            store[p['title']] = p['revisions'][0]['slots']['main']['content']
    sys.stderr.write('\r%d/%d' % (i + len(ch), len(tgs)))
sys.stderr.write('\n')
print('取回 %d 页，缺 %d 页，重定向 %d 条' % (len(store), len(miss), len(redir)))
if miss:
    print('缺页:', miss[:30])
json.dump({'text': store, 'redirect': redir, 'missing': miss},
          open('dp-raw.json', 'w', encoding='utf-8'), ensure_ascii=False)
