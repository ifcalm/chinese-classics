# -*- coding: utf-8 -*-
"""昭明文選·零改字校驗。

**兩側必須不同源**（見 memory verification-blindspots #1）：
底本側直接從原始 wikitext 抽漢字流，**不走 clean()**；落盤側從 base-data 抽。
若兩側都走同一個清洗器，清洗器吞掉的內容會在兩側同時消失，校驗必然通過——
那是自證，不是校驗。

判據：落盤漢字流須是底本漢字流的**子序列**（只許刪、不許改、不許增），
且刪去的字要能被「考異 + 卷題/模板名等元數據」解釋。
"""
import json, os, re, sys

HAN = re.compile(r'[一-鿿㐀-䶿]')
CACHE = os.environ.get('WX_CACHE', 'wxcache.json')
DEST = 'base-data/literature/wen-xuan'


def stream(s):
    return ''.join(HAN.findall(s))


def disk_stream():
    out = []
    for d in sorted(os.listdir(DEST)):
        p = os.path.join(DEST, d)
        if not os.path.isdir(p):
            continue
        files = sorted(f for f in os.listdir(p) if f != '_index.md')
        for f in files:
            body = open(os.path.join(p, f), encoding='utf-8').read().split('---', 2)[2]
            out.append(stream(body))
    return ''.join(out)


def src_stream(pages):
    order = ['昭明文選/序'] + ['昭明文選/卷%d' % i for i in range(1, 61)]
    return ''.join(stream(pages[t]) for t in order)


def is_subseq(small, big):
    """小是否為大的子序列；返回 (bool, 首次失配位置)"""
    i = 0
    for ch in big:
        if i < len(small) and small[i] == ch:
            i += 1
    return i == len(small), i


def main():
    pages = json.load(open(CACHE, encoding='utf-8'))
    src, dsk = src_stream(pages), disk_stream()
    print('底本漢字流 %d · 落盤漢字流 %d · 差 %d' % (len(src), len(dsk), len(src) - len(dsk)))

    ok, pos = is_subseq(dsk, src)
    if not ok:
        ctx = dsk[max(0, pos - 40):pos + 40]
        print('✗ 落盤非底本子序列：第 %d 字起對不上' % pos)
        print('  落盤上下文：…%s…' % ctx)
        return 1
    print('✓ 落盤漢字流是底本漢字流的子序列——只刪未改、未增')

    from collections import Counter
    ds, dd = Counter(src), Counter(dsk)
    removed = ds - dd
    print('刪去 %d 字，%d 種字' % (sum(removed.values()), len(removed)))
    print('  刪得最多：%s' % ', '.join('%s×%d' % kv for kv in removed.most_common(12)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
