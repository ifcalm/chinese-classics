# -*- coding: utf-8 -*-
"""宋詞諸家·零改字校驗。兩側不同源：底本側取源 JSON 的 paragraphs 拼漢字流
（**不走任何清洗**），落盤側從 base-data 抽。判據：落盤漢字流須是底本漢字流的
子序列（只許刪、不許改、不許增）。

題名不入校驗——`词牌·首句前七字` 是本站按體例合成的，非底本原文；
但其漢字全部來自 rhythmic 與首句，故合成不引入新字。
"""
import json, glob, os, re, sys, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sc_build import BOOKS, DEST, SLUG, files

HAN = re.compile(r'[一-鿿㐀-䶿]')
stream = lambda s: ''.join(HAN.findall(s))


def disk_stream(slug):
    out = []
    for f in sorted(glob.glob(os.path.join(DEST, slug, '*.md'))):
        if f.endswith('_index.md'):
            continue
        out.append(stream(open(f, encoding='utf-8').read().split('---', 2)[2]))
    return ''.join(out)


def is_subseq(small, big):
    i = 0
    for ch in big:
        if i < len(small) and small[i] == ch:
            i += 1
    return i == len(small), i


def main():
    src = collections.defaultdict(str)
    want = {a for a, _, _ in BOOKS}
    for f in files():
        for p in json.load(open(f, encoding='utf-8')):
            a = (p.get('author') or '').strip()
            if a in want:
                src[a] += stream(''.join(p.get('paragraphs', [])))
    bad = 0
    print('%-16s %8s %8s %7s' % ('书', '底本', '落盘', '留存'))
    for au, title, _ in BOOKS:
        s, d = src[au], disk_stream(SLUG[au])
        ok, pos = is_subseq(d, s)
        print('%-16s %8d %8d %6.1f%%  %s' % (
            title, len(s), len(d), len(d) / len(s) * 100 if s else 0,
            '✓' if ok else '✗ 第%d字起失配' % pos))
        if not ok:
            bad += 1
            print('    落盘：…%s…' % d[max(0, pos - 30):pos + 30])
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
