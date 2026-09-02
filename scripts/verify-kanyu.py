# -*- coding: utf-8 -*-
"""堪舆二部·零改字校验（对 `scripts/parse-kanyu.py` 的产出）。

**两侧不同源**：底本侧直接从 `scripts/dzg/*.txt` 原文抽汉字流，**不走 parse-kanyu
的任何清洗**——不剥括号、不剔题署、不切今人窜入段。落盘侧从 base-data 抽，
篇题一并计入（篇题在底本里本就是正文中的一行）。

判据：落盘汉字流须是底本汉字流的**子序列**（只许删、不许改、不许增）。
本批的三种处理——剥张九仪增注、剔卷端题署、切孟广顺今人文字——全是删，
故子序列判据仍应成立；判据过不去就说明有一处不是删而是改。

用法: python3 scripts/verify-kanyu.py
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HAN = re.compile(r'[一-鿿㐀-䶿]')
stream = lambda s: ''.join(HAN.findall(s))

# 只取 slug/root/src 三项，刻意不 import parse-kanyu 的解析逻辑
BOOKS = [
    ('人子须知', 'base-data/shushu/kanyu/ren-zi-xu-zhi', '地理人子须知'),
    ('山洋指迷原本', 'base-data/shushu/kanyu/shan-yang-zhi-mi', '山洋指迷'),
]


def disk_stream(d):
    out = []
    for dp, dirs, fs in sorted(os.walk(d)):
        dirs.sort()
        for f in sorted(fs):
            if f == '_index.md':
                continue
            t = open(os.path.join(dp, f), encoding='utf-8').read()
            head, body = t.split('---', 2)[1], t.split('---', 2)[2]
            m = re.search(r'title:\s*"(.*)"', head)
            out.append(stream(m.group(1) if m else '') + stream(body))
    return ''.join(out)


def is_subseq(small, big):
    i = 0
    for ch in big:
        if i < len(small) and small[i] == ch:
            i += 1
    return i == len(small), i


def main():
    bad = 0
    print('%-14s %9s %9s %7s' % ('书', '底本', '落盘', '留存'))
    for src, rel, title in BOOKS:
        s = stream(open(os.path.join(ROOT, 'scripts/dzg', src + '.txt'),
                        encoding='utf-8').read())
        d = disk_stream(os.path.join(ROOT, rel))
        ok, pos = is_subseq(d, s)
        print('%-14s %9d %9d %6.1f%%  %s' % (
            title, len(s), len(d), len(d) / len(s) * 100,
            '✓' if ok else '✗ 第%d字起失配' % pos))
        if not ok:
            bad += 1
            print('    落盘：…%s…' % d[max(0, pos - 30):pos + 30])
            print('    底本：…%s…' % s[max(0, pos - 30):pos + 30])
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
