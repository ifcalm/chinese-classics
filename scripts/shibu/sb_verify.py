# -*- coding: utf-8 -*-
"""史部三通與史論·零改字校驗。兩側不同源：底本側從原始 wikitext 抽漢字流（只展開
`{{:轉錄}}`、不走 clean），落盤側從 base-data 抽。判據：落盤漢字流須是底本
漢字流的子序列（只許刪、不許改、不許增）。
"""
import html as _html
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sb_build import BOOKS, S, order
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), 'keji'))
import kj_clean as C

HAN = re.compile(r'[一-鿿㐀-䶿]')
stream = lambda s: ''.join(HAN.findall(s))
# 源側須先解 HTML 實體：wikitext 把生僻字寫成 `&#38828;`（＝鞬），不解則底本流
# 裏根本沒這個字，落盤流反倒「多」出一個，子序列判據會誤報。這是傳輸層解碼，
# 不是清洗——兩側仍不同源。
src_stream = lambda s: stream(_html.unescape(s))


def disk_stream(b):
    out = []
    for dp, dirs, fs in sorted(os.walk(os.path.join(b['root'], b['slug']))):
        dirs.sort()
        for f in sorted(fs):
            if f == '_index.md':
                continue
            out.append(stream(open(os.path.join(dp, f), encoding='utf-8')
                              .read().split('---', 2)[2]))
    return ''.join(out)


def is_subseq(small, big):
    i = 0
    for ch in big:
        if i < len(small) and small[i] == ch:
            i += 1
    return i == len(small), i


def main():
    pages = json.load(open(os.path.join(S, 'sbcache.json'), encoding='utf-8'))
    index = json.load(open(os.path.join(S, 'sbindex.json'), encoding='utf-8'))
    for b in BOOKS:
        if 'pages' not in b:
            b['pages'] = order(b['src'], index, b.get('skip', ()))
    bad = 0
    print('%-14s %9s %9s %7s %8s' % ('书', '底本', '落盘', '留存', '头模板'))
    for b in BOOKS:
        src = hdr = ''
        for p in b['pages']:
            t = C.inline(pages[p], pages)
            src += src_stream(t)
            for a, z in C.scan_braces(t, r'(?i)\{\{\s*(?:header2?|Novel)\s*(?=[|}])'):
                hdr += src_stream(t[a:z])
        dsk = disk_stream(b)
        ok, pos = is_subseq(dsk, src)
        rest = len(src) - len(hdr)
        print('%-14s %9d %9d %6.1f%% %8d  %s' % (
            b['title'], len(src), len(dsk), len(dsk) / rest * 100 if rest else 0,
            len(hdr), '✓' if ok else '✗ 第%d字起失配' % pos))
        if not ok:
            bad += 1
            print('    落盘：…%s…' % dsk[max(0, pos - 30):pos + 30])
            print('    底本：…%s…' % src[max(0, pos - 30):pos + 30])
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
