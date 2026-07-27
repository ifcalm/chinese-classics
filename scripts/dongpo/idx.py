#!/usr/bin/env python3
"""《東坡全集》索引解析：卷 → (体裁组, 篇名, 链接目标)。"""
import re, json, ws

ENTRY = re.compile(r'#\[\[([^\]]+)\]\]')
VOL = re.compile(r'^\*\[\[/卷(\d+)\|([^\]]+)\]\]', re.M)


def parse():
    t = ws.wikitext('東坡全集')
    vp = [(int(m.group(1)), m.group(2), m.start()) for m in VOL.finditer(t)]
    out = []
    for i, (k, label, s) in enumerate(vol_iter(vp)):
        e = vp[i + 1][2] if i + 1 < len(vp) else len(t)
        seg = t[s:e]
        items, group = [], None
        pos = 0
        for m in ENTRY.finditer(seg):
            # 该条目前的文本里若有「XX：」则更新体裁组
            pre = seg[pos:m.start()]
            g = re.findall(r'([一-鿿]{1,6})[：:]\s*$', pre.replace('　', ''))
            if g:
                group = g[-1]
            pos = m.end()
            link = m.group(1)
            tgt, _, disp = link.partition('|')
            items.append({'target': tgt, 'display': disp or tgt, 'group': group})
        out.append({'vol': k, 'label': label, 'items': items})
    return out


def vol_iter(vp):
    return [(k, label, s) for k, label, s in vp]


if __name__ == '__main__':
    idx = parse()
    tot = sum(len(v['items']) for v in idx)
    uniq = {it['target'] for v in idx for it in v['items']}
    print('卷 %d  条目 %d  唯一目标 %d' % (len(idx), tot, len(uniq)))
    for v in idx:
        if v['vol'] in (1, 101, 105, 114, 115):
            gs = sorted({it['group'] for it in v['items'] if it['group']})
            print(' 卷%-4d %-8s %4d 条  组:%s' % (v['vol'], v['label'], len(v['items']), gs[:12]))
    short = sorted((len(v['items']), v['vol']) for v in idx)[:5]
    print(' 最少条目的卷:', short)
    json.dump(idx, open('wlc-idx.json', 'w', encoding='utf-8'), ensure_ascii=False)
