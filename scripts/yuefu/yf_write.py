# -*- coding: utf-8 -*-
"""樂府詩集·落盤。→ base-data/literature/yue-fu-shi-ji/{NNN}/{MM}.md

卷題取本卷 1 級標題（=卷二十六·相和歌辭一=，97/100 卷有），缺者取目錄頁的
「*[[/0NN卷|卷二十六]]　相和歌辭一」條目。
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yf_clean as C
import yf_parse as P

CACHE = os.environ.get('YF_CACHE', 'yfmerged.json')
DEST = 'base-data/literature/yue-fu-shi-ji'


def fm(**kw):
    out = ['---']
    for k, v in kw.items():
        out.append(f'{k}: "{v}"' if isinstance(v, str) else f'{k}: {v}')
    out.append('---')
    return '\n'.join(out) + '\n'


def index_titles(idx_raw):
    """目錄頁 → {卷號: 「卷二十六　相和歌辭一」}"""
    out = {}
    for m in re.finditer(r'\*\[\[/(\d+)卷\|([^\]]+)\]\]\s*(.*)', idx_raw):
        n = int(m.group(1))
        名 = m.group(2).strip()
        类 = re.sub(r'\[\[|\]\]', '', m.group(3)).strip()
        out[n] = 名 + ('　' + 类 if 类 else '')
    return out


def main():
    pages = json.load(open(CACHE, encoding='utf-8'))
    idx = index_titles(pages['樂府詩集'])
    os.makedirs(DEST, exist_ok=True)
    total, report = 0, []

    for n in range(1, 101):
        raw = pages['樂府詩集/%03d卷' % n]
        cleaned = C.clean(raw, '卷%d' % n)
        pieces = P.parse_page(cleaned)
        if not pieces:
            report.append((n, 0, '無正文')); continue

        # 卷題：本卷 1 級標題優先，其次目錄頁
        vol = ''
        for ln in cleaned.split('\n'):
            hm = P.HEAD.match(ln)
            # ⚠ 必須按層級取：`^=…=$` 這種寫法會把 ==漢郊祀歌== 也匹配上，
            # 捕獲成 `=漢郊祀歌=`（實測卷1、卷57 中招）
            if hm and len(hm.group(1)) == 1:
                vol = hm.group(2).replace('·', '　').replace('•', '　')
                vol = re.sub(r'[\s　]+', '　', vol).strip('　 ')
                break
        if not vol:
            vol = idx.get(n, '卷%d' % n)

        vdir = os.path.join(DEST, '%03d' % n)
        os.makedirs(vdir, exist_ok=True)
        open(os.path.join(vdir, '_index.md'), 'w', encoding='utf-8').write(
            fm(title=vol, weight=n))

        for j, (pt, body) in enumerate(pieces, 1):
            # 卷首總解題的篇題與卷題同名，改記「題解」
            if pt.replace('·', '　').replace('•', '　').strip() == vol:
                pt = '題解'
            open(os.path.join(vdir, '%03d.md' % j), 'w', encoding='utf-8').write(
                fm(title=pt, weight=j) + '\n' + body)
        total += len(pieces)
        report.append((n, len(pieces), vol))
    return total, report


if __name__ == '__main__':
    n, rep = main()
    print('落盤 %d 卷 · %d 篇' % (len(rep), n))
    for a,b,c in rep[:3]: print('   卷%d → %s（%d 篇）' % (a,c,b))
    empty = [r for r in rep if r[1] == 0]
    if empty: print('   ⚠ 無正文卷:', empty)
