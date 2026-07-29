#!/usr/bin/env python3
"""道家 C 批八部：抓页 + 结构勘察。"""
import json, re, ws
BOOKS = {
    '性命圭旨': None, '太上感應篇集註': None, '淨明忠孝全書': None,
    '太上洞玄靈寶赤書玉訣妙經': None, '玉清金笥青華秘文金寶內鍊丹訣': None,
    '一切道經音義妙門由起': None, '谷神篇': None, '疑仙傳': None,
}


def kids(t):
    out, cont = [], None
    while True:
        p = {'action': 'query', 'list': 'allpages', 'apprefix': t + '/', 'aplimit': '500',
             'apnamespace': '0', 'format': 'json', 'formatversion': '2'}
        if cont:
            p['apcontinue'] = cont
        r = ws.api(p, 'ck-%d-%s' % (abs(hash(t)) % 99999, cont or '0'))
        out += [x['title'] for x in r['query']['allpages']]
        cont = r.get('continue', {}).get('apcontinue')
        if not cont:
            return out


store = {}
for b in BOOKS:
    ks = [k for k in kids(b) if '全覽' not in k and '四庫全書本' not in k]
    pages = ks or [b]
    tx = {}
    for i in range(0, len(pages), 50):
        r = ws.post({'action': 'query', 'titles': '|'.join(pages[i:i + 50]), 'prop': 'revisions',
                     'rvprop': 'content', 'rvslots': 'main', 'redirects': 1,
                     'format': 'json', 'formatversion': '2'}, 'cg-%d-%d' % (abs(hash(b)) % 99999, i))
        for p in r['query']['pages']:
            if 'missing' not in p:
                tx[p['title']] = p['revisions'][0]['slots']['main']['content']
    store[b] = tx
    print('%-24s %2d 页  %s' % (b, len(tx), list(tx)[:3]))
json.dump(store, open('c-raw.json', 'w', encoding='utf-8'), ensure_ascii=False)
