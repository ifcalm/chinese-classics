# -*- coding: utf-8 -*-
"""全真批·落盘 base-data/taoism/quanzhen/。

体例同王临川集/东坡全集：一卷一子目录、一篇一文件。诗词集若按卷并成单文件，
Reader 的 isVerse() 遇标题即不居中，且 .reader__text 无 pre-wrap 会把单换行塌缩，
千余首诗会同时失去分行与居中，故必须一篇一文件。
标题一律简体（站点铁律），正文保持底本繁体。
"""
import os, re, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qz_books import BOOKS, build
from qz_simp import to_simp

ROOT = os.environ.get('QZ_ROOT', 'base-data/taoism/quanzhen')

# 齐言联句：底本常把两联挤在一行，站内体例(王临川集/东坡全集)是一联一段。
# 只改换行不动字，汉字流不变；不齐言者(词、散文)一律保持底本行式。
RE_COUPLET = re.compile(r'^(?:[^，。！？；：、]{4,8}，[^，。！？；：、]{4,8}。)+$')
RE_ONE = re.compile(r'[^，。！？；：、]{4,8}，[^，。！？；：、]{4,8}。')


def split_couplets(lines):
    out = []
    for ln in lines:
        m = RE_COUPLET.match(ln)
        out += RE_ONE.findall(ln) if m and len(ln) > 18 else [ln]
    return out
CN = '一二三四五六七八九十'


def cn_num(n):
    if n <= 10:
        return CN[n - 1]
    if n < 20:
        return '十' + CN[n - 11]
    return CN[n // 10 - 1] + '十' + (CN[n % 10 - 1] if n % 10 else '')


def vol_title(name, idx, simp, pieces=()):
    """卷名归一：页序号/卷之N/卷上 一律作「卷X」，序跋照旧。"""
    s = simp.get(name, name)
    if re.fullmatch(r'\d+', s):
        return '卷' + cn_num(int(s))
    m = re.search(r'卷之([一二三四五六七八九十]+)(.*)$', s)
    if m:
        return ('卷' + m.group(1) + m.group(2).replace('‧', '·')).strip()
    if re.search(r'卷[上中下]$', s):
        return '卷' + s[-1]
    if s.endswith('序'):
        return '后序' if '后' in s or '後' in s else '序'
    # 页级「卷」实为书前序（甘水仙源录、终南山祖庭仙真内传），以其唯一之篇定名
    if len(pieces) == 1 and pieces[0]['title'].rstrip('）)').endswith('序'):
        return '序'
    return s


def fm(**kw):
    out = ['---']
    for k, v in kw.items():
        if v is None:
            continue
        out.append('%s: %s' % (k, ('"%s"' % v) if isinstance(v, str) else v))
    out.append('---')
    return '\n'.join(out) + '\n'


def write_book(slug, simp):
    vols, notes, lead, cfg = build(slug)
    bdir = os.path.join(ROOT, slug)
    if os.path.isdir(bdir):
        shutil.rmtree(bdir)
    os.makedirs(bdir)
    n_pieces = sum(len(v['pieces']) for v in vols)
    open(os.path.join(bdir, '_index.md'), 'w').write(fm(
        title=cfg['cn'], kind='book', weight=cfg['w'], date='2026-07-31',
        tags='["道家", "全真"]', draft='true',
        summary='%s%s据维基文库《正统道藏》整理本收录（繁体）。' % (
            cfg['author'] + '。' if cfg['author'] else '', cfg['desc']),
        showToc='false', tocOpen='false', ShowShareButtons='false'))

    flat = len(vols) == 1
    width = max(2, len(str(max(len(v['pieces']) for v in vols))))
    for vi, v in enumerate(vols, 1):
        if flat:
            vdir = bdir
        else:
            vdir = os.path.join(bdir, '%03d' % vi)
            os.makedirs(vdir)
            open(os.path.join(vdir, '_index.md'), 'w').write(
                fm(title=vol_title(v['name'], vi, simp, v['pieces']), weight=vi))
        w = max(2, len(str(len(v['pieces']))))
        for pi, p in enumerate(v['pieces'], 1):
            body = '\n\n'.join(split_couplets(p['lines'])) + '\n'
            open(os.path.join(vdir, '%0*d.md' % (w if not flat else width, pi)), 'w').write(
                fm(title=simp.get(p['title'], p['title']).replace('"', '”'),
                   weight=pi) + '\n' + body)
    return len(vols), n_pieces, notes, lead


if __name__ == '__main__':
    titles = []
    for slug in BOOKS:
        vols, _n, _l, _c = build(slug)
        for v in vols:
            titles.append(v['name'])
            titles += [p['title'] for p in v['pieces']]
    simp = to_simp(titles)

    os.makedirs(ROOT, exist_ok=True)
    open(os.path.join(ROOT, '_index.md'), 'w').write(fm(
        title='全真', date='2026-07-31', tags='["道家"]', draft='true',
        summary='全真道祖师诗词、语录与碑传，金元两代北宗典籍。',
        showToc='false', tocOpen='false', ShowShareButtons='false', weight=35))
    tv = tp = 0
    for slug in BOOKS:
        nv, np_, notes, lead = write_book(slug, simp)
        tv += nv
        tp += np_
        print('%-22s 卷%2d 篇%4d' % (BOOKS[slug]['cn'], nv, np_))
    print('合计 %d 部 · %d 卷 · %d 篇' % (len(BOOKS), tv, tp))
