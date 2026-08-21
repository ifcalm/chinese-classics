# -*- coding: utf-8 -*-
"""唐人別集·零改字校驗。

**兩側不同源**：底本側直接取源 JSON 的 title+paragraphs 拼漢字流，**不走 tj_clean**；
落盤側從 base-data 抽。同源則清洗器吞掉的內容兩側一起消失，校驗必過——那是自證。

判據：落盤漢字流須是底本漢字流的**子序列**（只許刪、不許改、不許增）。
"""
import json, glob, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tj_build import BOOKS, DEST, files

HAN = re.compile(r'[一-鿿㐀-䶿]')
stream = lambda s: ''.join(HAN.findall(s))


def disk_stream(slug):
    out = []
    for f in sorted(glob.glob(os.path.join(DEST, slug, '*.md'))):
        if f.endswith('_index.md'):
            continue
        raw = open(f, encoding='utf-8').read()
        head, body = raw.split('---', 2)[1], raw.split('---', 2)[2]
        out.append(stream(re.search(r'title: "(.*)"', head).group(1)))
        out.append(stream(body))
    return ''.join(out)


def is_subseq(small, big):
    i = 0
    for ch in big:
        if i < len(small) and small[i] == ch:
            i += 1
    return i == len(small), i


def main():
    src = {b['poet']: [] for b in BOOKS}
    for f in files():
        for p in json.load(open(f, encoding='utf-8')):
            a = (p.get('author') or '').strip()
            if a in src:
                src[a].append(stream(p.get('title') or '') +
                              stream(''.join(p.get('paragraphs', []))))
    bad = 0
    print('%-12s %9s %9s %7s' % ('书', '底本', '落盘', '留存'))
    for b in BOOKS:
        s = ''.join(src[b['poet']])
        d = disk_stream(b['slug'])
        ok, pos = is_subseq(d, s)
        print('%-12s %9d %9d %6.1f%%  %s' % (
            b['title'], len(s), len(d), len(d) / len(s) * 100,
            '✓' if ok else '✗ 第%d字起失配' % pos))
        if not ok:
            bad += 1
            print('    落盘上下文：…%s…' % d[max(0, pos - 40):pos + 40])
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
