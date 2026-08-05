# -*- coding: utf-8 -*-
"""全真批·质检。

零改字校验（同道家C批口径）：底本清洗后的汉字流 与 落盘汉字流 逐字比对，
**只允许 delete，不允许 insert/replace**；每一处 delete 都必须能在剥离账上认领
（卷题/卷终/撰人行/体裁组名/整理者校注）。字流只取迻录自底本的篇题(raw)与正文，
组前缀是合成的显示题，不入字流。词表讹字回改在底本侧同步施加，另有独立账目。
"""
import difflib, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qz_clean import clean, norm_lines, strip_editor
import qz_books
from qz_books import BOOKS, build, _vol_sort, BYLINES, GENRE, RE_VOLTITLE, RE_VOLEND

HZ = re.compile(r'[一-鿿]')
CACHE = os.environ.get('QZ_CACHE', 'dzcache')
# 编码损坏铁证：假名/制表/全角拉丁数字/非中文标点的全角符号/替换字符/私用区/康熙部首。
# 全角的！？，、。：；（）「」等是正常中文标点，不计入。
JUNK = re.compile('[\u3040-\u30ff\u2500-\u257f'
                  '\uff10-\uff19\uff21-\uff3a\uff41-\uff5a'
                  '\uff02-\uff07\uff0a\uff0b\uff0d\uff0e\uff0f'
                  '\uff1c-\uff1e\uff20\uff3b-\uff40\uff5b-\uff5e'
                  '\ufffd\ue000-\uf8ff\u2e80-\u2fdf'
                  'A-Za-z]')


def src_stream(src):
    pages = json.load(open(os.path.join(CACHE, src + '.json')))
    out = []
    for k in sorted(pages, key=_vol_sort):
        t = re.sub(r'^(={2,6})\s*(.+?)\s*=*\s*$', r'\2', clean(pages[k]), flags=re.M)
        lines, _ = strip_editor(norm_lines(t))
        out += lines
    return ''.join(HZ.findall(''.join(out)))


def accounted(s, titles=()):
    """被删去的一段是否可在剥离账上认领：反复扣除账上诸项，扣净即认领。

    titles 传入本书篇题——卷首目錄整块被剥后，difflib 会把它对齐成一处删除，
    而目錄内容正是诸篇题的重复，故须一并可认领。
    """
    s = ''.join(HZ.findall(s))
    if not s:
        return True
    # 目錄须最先扣除：其内含「詩」「詞」等体裁字，若让 phase1 先扣会把整块打碎
    for t in qz_books.TOC:
        s = s.replace(''.join(HZ.findall(t)), '')
    if not s:
        return True
    # 长者优先：GENRE 里同时有「詩」与「五言律詩」，短者先删会打碎长者
    # 两轮：先扣结构性剥离项（卷题/卷终/撰人行/体裁组），再扣目錄与篇题。
    # 次序不能反——篇题里有「磻溪」，先扣会把「磻溪集卷之一」打碎。
    phase1 = sorted({''.join(HZ.findall(w)) for w in
                     list(BYLINES) + list(GENRE) + list(qz_books.GROUPS) if w},
                    key=len, reverse=True)
    phase2 = phase1 + sorted({''.join(HZ.findall(w)) for w in
                              list(qz_books.TOC) + list(titles) if w},
                             key=len, reverse=True)
    residue = re.compile(r'卷之|卷[上中下]|竟|目錄|正文|[一二三四五六七八九十百]+|'
                         + '|'.join(re.escape(b['src']) for b in BOOKS.values()))
    for vocab in (phase1, phase2):
        prev = None
        while prev != s and s:
            prev = s
            for w in vocab:
                if w:
                    s = s.replace(w, '')
            s = RE_VOLEND.sub('', s)
            s = RE_VOLTITLE.sub('', s)
            s = residue.sub('', s)
    return not s


def check(slug):
    vols, notes, lead, cfg = build(slug)
    a = src_stream(cfg['src'])
    b = ''.join(HZ.findall(''.join(
        p.get('raw', '') + ''.join(p['lines']) for v in vols for p in v['pieces'])))
    titles = [p.get('raw', '') for v in vols for p in v['pieces']]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    dels, bad = [], []
    for t, i1, i2, j1, j2 in sm.get_opcodes():
        if t == 'equal':
            continue
        seg, ins = a[i1:i2], b[j1:j2]
        if t == 'delete' and accounted(seg, titles):
            dels.append(seg)
        else:
            bad.append((t, seg, ins))
    txt = ''.join(''.join(p['lines']) for v in vols for p in v['pieces'])
    return dict(cn=cfg['cn'], vols=len(vols),
                pieces=sum(len(v['pieces']) for v in vols),
                hz=len(HZ.findall(txt)), dels=dels, bad=bad, notes=notes, lead=lead,
                junk=sorted(set(JUNK.findall(txt))),
                empty=[(v['name'], p['title']) for v in vols for p in v['pieces']
                       if len(HZ.findall(''.join(p['lines']))) == 0])


if __name__ == '__main__':
    tot = 0
    for slug in (sys.argv[1:] or BOOKS):
        r = check(slug)
        tot += len(r['bad'])
        print('%-22s 卷%2d 篇%4d %7d汉字  剥%3d项 校注%2d  空篇%d 杂讯%s %s' %
              (r['cn'], r['vols'], r['pieces'], r['hz'], len(r['dels']), len(r['notes']),
               len(r['empty']), ''.join(r['junk']) or '无',
               '✓' if not r['bad'] else '⚠%d处' % len(r['bad'])))
        for t, s, i in r['bad'][:6]:
            print('      %-7s 底本%r → 落盘%r' % (t, s[:50], i[:50]))
        if r['empty']:
            print('      空篇:', r['empty'][:5])
    print('-' * 74)
    print('零改字校验：%s' % ('全部只删不增不换' if not tot else '%d 处待查' % tot))
