# -*- coding: utf-8 -*-
"""科技門類·零改字校驗。

**兩側不同源**：底本側直接從原始 wikitext 抽漢字流（只展開 `{{:轉錄}}`，
**不走 clean**），落盤側從 base-data 抽。同源則清洗器吞掉的內容兩側一起
消失，校驗必過——那是自證。

判據：落盤漢字流須是底本漢字流的**子序列**（只許刪、不許改、不許增）。
"""
import html as _html
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kj_build import BOOKS, DEST, S, index_layout
import kj_clean as C

HAN = re.compile(r'[一-鿿㐀-䶿]')
stream = lambda s: ''.join(HAN.findall(s))
# 源側須先解 HTML 實體：wikitext 把生僻字寫成 `&#38828;`（＝鞬），不解則底本流
# 裏根本沒這個字，落盤流反倒「多」出一個，子序列判據會誤報。這是傳輸層解碼，
# 不是清洗——兩側仍不同源。
src_stream = lambda s: stream(_html.unescape(s))


def disk_stream(b):
    root = os.path.join(DEST, b['g'], b['slug'])
    out = []
    for dp, dirs, fs in sorted(os.walk(root)):
        dirs.sort()
        for f in sorted(fs):
            if f == '_index.md':
                continue
            out.append(stream(open(os.path.join(dp, f), encoding='utf-8')
                              .read().split('---', 2)[2]))
    return ''.join(out)


def src_pages(b, pages):
    if b.get('index_page'):
        return ['%s/%s' % (b['index_page'], p)
                for _, ps in index_layout(pages, b['index_page']) for p in ps]
    return b['pages']


def is_subseq(small, big):
    i = 0
    for ch in big:
        if i < len(small) and small[i] == ch:
            i += 1
    return i == len(small), i


def main():
    pages = json.load(open(os.path.join(S, 'kjcache.json'), encoding='utf-8'))
    bad = 0
    print('%-14s %9s %9s %7s' % ('书', '底本', '落盘', '留存'))
    for b in BOOKS:
        src = ''.join(src_stream(C.inline(pages[p], pages)) for p in src_pages(b, pages))
        dsk = disk_stream(b)
        ok, pos = is_subseq(dsk, src)
        print('%-14s %9d %9d %6.1f%%  %s' % (
            b['title'], len(src), len(dsk), len(dsk) / len(src) * 100,
            '✓' if ok else '✗ 第%d字起失配' % pos))
        if not ok:
            bad += 1
            print('    落盘：…%s…' % dsk[max(0, pos - 30):pos + 30])
            print('    底本：…%s…' % src[max(0, pos - 30):pos + 30])
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
