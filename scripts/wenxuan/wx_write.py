# -*- coding: utf-8 -*-
"""昭明文選·落盤。→ base-data/literature/wen-xuan/{NNN}/{MM}.md

卷題取自源本 header2 的 section + notes（如「卷第二十九 詩己」+「雜詩上」）。
篇題剝去與卷級類目重複的祖先層（詩己、雜詩上），只留「古詩一十九首·行行重行行」。
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wx_clean as W
import wx_parse as P

CACHE = os.environ.get('WX_CACHE', 'wxcache.json')
DEST = 'base-data/literature/wen-xuan'
CN = '一二三四五六七八九十'


def cn_num(n):
    if n <= 10: return CN[n - 1]
    if n < 20: return '十' + CN[n - 11]
    if n < 100:
        a, b = divmod(n, 10)
        return CN[a - 1] + '十' + (CN[b - 1] if b else '')
    return str(n)


def header_meta(raw):
    """從 {{header2|...}} 取 section / notes，去粗體與轉換標記。"""
    m = re.search(r'\{\{\s*[Hh]eader2?\s*\|(.*?)\n\}\}', raw, re.S)
    if not m:
        return '', ''
    def field(name):
        mm = re.search(r'\|\s*' + name + r'\s*=\s*(.*)', m.group(1))
        if not mm: return ''
        v = mm.group(1).strip()
        v = re.sub(r'\{\{[^{}]*\}\}', '', v)      # Textquality 等模板混在同一行
        v = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', v)
        v = re.sub(r"'''|''", '', v)
        v = re.sub(r'-\{A\|zh-hans:[^;]*;zh-hant:([^}]*)\}-', r'\1', v)
        v = re.sub(r'-\{([^}]*)\}-', r'\1', v)
        return re.sub(r'\s+', '', v).strip()
    return field('section'), field('notes')


def fm(**kw):
    out = ['---']
    for k, v in kw.items():
        out.append(f'{k}: "{v}"' if isinstance(v, str) else f'{k}: {v}')
    out.append('---')
    return '\n'.join(out) + '\n'


def trim_title(path, tokens):
    parts = [p for p in path.split('·') if re.sub(r'\s+', '', p) not in tokens]
    return '·'.join(parts) if parts else path.split('·')[-1]


def index_classes(idx_raw):
    """從目錄頁取 卷號 → 大類(·小類)。目錄有缺（書、序兩節未列卷），
    故用「後出的卷承前一節大類」補全。"""
    big = sub = ''
    out, seen = {}, []
    for ln in idx_raw.split('\n'):
        m = re.match(r'^(=+)\s*(.*?)\s*=+\s*$', ln)
        if m:
            txt = re.sub(r"'''|''", '', m.group(2)).strip()
            if len(m.group(1)) == 2: big, sub = txt, ''
            elif len(m.group(1)) == 3: sub = txt
            continue
        mm = re.match(r'^\*\[\[/卷(\d+)', ln)
        if mm:
            n = int(mm.group(1))
            out.setdefault(n, '·'.join(x for x in (big, sub) if x))
            seen.append((n, big))
    # 目錄未列的卷：取編號小於它的最近一卷的大類
    for n in range(1, 61):
        if n not in out:
            prev = [b for k, b in seen if k < n]
            out[n] = prev[-1] if prev else ''
    return out


def main():
    pages = json.load(open(CACHE, encoding='utf-8'))
    idx_cls = index_classes(pages['昭明文選'])
    os.makedirs(DEST, exist_ok=True)
    order = ['昭明文選/序'] + ['昭明文選/卷%d' % i for i in range(1, 61)]
    total_pieces = 0
    report = []

    for idx, title in enumerate(order):
        raw = pages[title]
        section, notes = header_meta(raw)
        cleaned, _ = W.clean(raw, title)
        # 用 {{novel}} 的 9 卷沒有 header2，其類目寫在首個標題之前的
        # 「文選卷第六十 / 賦庚 / 書上」等行裡，取來補足
        if not section and not notes:
            pre = []
            for ln in cleaned.split('\n'):
                if P.HEAD.match(ln): break
                s = re.sub(r'^[;:*#\s]+', '', ln).strip()
                if s and not re.match(r'^文選卷第', s): pre.append(s)
            notes = '·'.join(pre[:2])
        # 導航殘留（「↑返回《昭明文選》」之類）不入卷題
        notes = re.sub(r'[↑←→].*$', '', notes).strip('·　 ')
        section = re.sub(r'[↑←→].*$', '', section).strip('·　 ')
        pieces = P.parse_page(cleaned)
        if not pieces:
            report.append((title, 0, '無正文')); continue

        # 卷級類目詞：用於從篇題剝去重複祖先
        tokens = set()
        for src in (section, notes):
            for tok in re.split(r'[，、\s]+', src):
                tok = re.sub(r'^卷第?[一二三四五六七八九十百]+', '', tok).strip()
                if tok: tokens.add(tok)

        if title.endswith('/序'):
            dname, vol_title = '000', '序'
        else:
            n = int(title.rsplit('卷', 1)[1])
            dname = '%03d' % n
            cls = '·'.join(x for x in (
                re.sub(r'^卷第?[一二三四五六七八九十百]+', '', section).strip(), notes) if x)
            if not cls:
                cls = idx_cls.get(n, '')          # 本卷 header 無類目時取目錄頁
            vol_title = '卷' + cn_num(n) + ('　' + cls if cls else '')

        vdir = os.path.join(DEST, dname)
        os.makedirs(vdir, exist_ok=True)
        open(os.path.join(vdir, '_index.md'), 'w', encoding='utf-8').write(
            fm(title=vol_title, weight=idx))

        for j, (path, body) in enumerate(pieces, 1):
            pt = trim_title(path, tokens)   # 兜底：層級判定後仍殘留的類目詞
            open(os.path.join(vdir, '%02d.md' % j), 'w', encoding='utf-8').write(
                fm(title=pt, weight=j) + '\n' + body)
        total_pieces += len(pieces)
        report.append((title, len(pieces), vol_title))

    return total_pieces, report


if __name__ == '__main__':
    n, rep = main()
    print('落盤 %d 卷 · %d 篇' % (len(rep), n))
    for t, c, v in rep[:4]: print('   %s → %s（%d 篇）' % (t, v, c))
    empty = [r for r in rep if r[1] == 0]
    if empty: print('   ⚠ 無正文卷:', empty)
