# -*- coding: utf-8 -*-
"""子部諸子八部·零改字校驗。

**兩側必須不同源**（見 memory verification-blindspots #1）：底本側直接從原始
wikitext 抽漢字流、**不走 clean()**；落盤側從 base-data 抽。兩側同源則清洗器
吞掉的內容會同時消失，校驗必然通過——那是自證。

判據：落盤漢字流須是底本漢字流的**子序列**（只許刪、不許改、不許增）。
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zz_build import BOOKS, DEST

HAN = re.compile(r'[一-鿿㐀-䶿]')
CACHE = os.environ.get('ZZ_CACHE', 'zzcache.json')
stream = lambda s: ''.join(HAN.findall(s))


def disk_stream(slug):
    root = os.path.join(DEST, slug)
    out = []
    for dp, dirs, fs in sorted(os.walk(root)):
        dirs.sort()
        for f in sorted(fs):
            if f == '_index.md':
                continue
            body = open(os.path.join(dp, f), encoding='utf-8').read().split('---', 2)[2]
            out.append(stream(body))
    return ''.join(out)


def is_subseq(small, big):
    i = 0
    for ch in big:
        if i < len(small) and small[i] == ch:
            i += 1
    return i == len(small), i


def main():
    pages = json.load(open(CACHE, encoding='utf-8'))
    bad = 0
    print('%-10s %9s %9s %7s' % ('书', '底本', '落盘', '留存'))
    for bk in BOOKS:
        src = ''.join(stream(pages[t]) for t in bk['pages'])
        dsk = disk_stream(bk['slug'])
        ok, pos = is_subseq(dsk, src)
        flag = '✓' if ok else '✗ 第%d字起失配' % pos
        print('%-10s %9d %9d %6.1f%%  %s' % (
            bk['title'], len(src), len(dsk), len(dsk) / len(src) * 100, flag))
        if not ok:
            bad += 1
            print('    落盘上下文：…%s…' % dsk[max(0, pos - 40):pos + 40])
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
