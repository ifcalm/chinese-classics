# -*- coding: utf-8 -*-
"""全真批·十二部逐书配置与结构装配。

体例分三型（差异只在「篇题从哪来」，装配逻辑共用）：
  heading  维基编者已用 ==/=== 标出篇题(重陽全真集/磻溪集/甘水仙源錄…)
  bare     篇题是无任何标记的裸行(洞玄金玉集/雲光集)
  single   整页无题的语录体(丹陽真人語錄/盤山語錄)

篇的判据同王临川集：有正文即篇；无正文而下辖同级者为组。组分两类——体裁组
(七言律詩/詞/碑文…)剥去不入篇名；其余组(词牌、组诗题)以「组·篇题」并入，
同站内《东坡词》「词牌·首句」例，否则词牌与组诗归属全丢。
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qz_clean import clean, norm_lines, strip_editor
from qz_parse import sections, load, GENRE, BARE_TITLE_WHITELIST, TERM, CONT

# ── 卷首撰人行（穷举，不用正则兜底以免误伤篇题），同道教义枢「剥卷题」例剥去 ──
BYLINES = {
    '終南山重陽子王嚞譔', '終南山重陽子王喆撰', '終南山重陽子王喆譔',
    '崑崙無為清淨丹陽馬真人述', '棲霞長春子邱處機撰', '棲霞長春子丘處機撰',
    '廣寧子郝大通撰', '聖水玉陽王處一撰', '靈隱子王頤中集',
    '林間羽客樗櫟道人編', '林間羽客樗礫道人編', '夷門天樂道人李道謙集',
    '夷山天樂道人李道謙編', '夷門天樂道人李道謙編',
}
RE_VOLTITLE = re.compile(r"卷之[一二三四五六七八九十]+|卷[上中下]$")
RE_VOLEND = re.compile(r"(卷之[一二三四五六七八九十]+|語録|語錄|集|記|錄|傳)竟$|^竟$")
DROP_LEAD_BLOCK = {'雲光集', '終南山祖庭仙真內傳'}      # 卷首目錄非正文

BOOKS = {
    'chongyang-quanzhen-ji': dict(
        cn='重阳全真集', src='重陽全真集', kind='heading', w=10,
        author='金·王重阳', desc='全真祖师王重阳诗词总集，十三卷。'),
    'chongyang-jiaohua-ji': dict(
        cn='重阳教化集', src='重陽教化集', kind='heading', w=12,
        author='金·王重阳', desc='王重阳与马丹阳师徒唱和集，三卷，前后序随书收录。'),
    'chongyang-fenli-shihua-ji': dict(
        cn='重阳分梨十化集', src='重陽分梨十化集', kind='heading', w=14,
        author='金·王重阳', desc='王重阳分梨十化度马丹阳事迹诗词集。'),
    'dongxuan-jinyu-ji': dict(
        cn='洞玄金玉集', src='洞玄金玉集', kind='bare', w=20,
        author='金·马钰', desc='全真第二代宗师马丹阳诗词集，十卷。'),
    'danyang-zhenren-yulu': dict(
        cn='丹阳真人语录', src='丹陽真人語錄', kind='single', w=22,
        author='金·马钰述，王颐中集', desc='马丹阳语录，门人灵隐子王颐中集录。'),
    'panxi-ji': dict(
        cn='磻溪集', src='磻溪集', kind='heading', w=30,
        author='金·丘处机', desc='长春真人丘处机诗词集，六卷。'),
    'yunguang-ji': dict(
        cn='云光集', src='雲光集', kind='bare', w=40,
        author='金·王处一', desc='玉阳真人王处一诗词集，四卷。'),
    'taigu-ji': dict(
        cn='太古集', src='太古集', kind='taigu', w=50,
        author='金·郝大通', desc='广宁真人郝大通易学丹道著作，四卷；卷二卷三诸图底本为图，存图题与解说。'),
    'panshan-yulu': dict(
        cn='盘山栖云王真人语录', src='盤山棲雲王眞人語録', kind='single', w=60,
        author='元·王志谨述，论志焕编', desc='栖云真人王志谨语录，门人论志焕编，序随书收录。'),
    'jinlian-zhengzong-ji': dict(
        cn='金莲正宗记', src='金蓮正宗記', kind='heading', w=70,
        author='元·秦志安', desc='全真五祖七真传记，五卷，序随书收录。'),
    'zhongnanshan-zuting-xianzhen-neizhuan': dict(
        cn='终南山祖庭仙真内传', src='終南山祖庭仙真內傳', kind='heading', w=75,
        author='元·李道谦', desc='终南山祖庭全真道士传记，上中下三卷，序随书收录。'),
    'ganshui-xianyuan-lu': dict(
        cn='甘水仙源录', src='甘水仙源錄', kind='heading', w=80,
        author='元·李道谦', desc='全真碑铭传记总集，十卷，收祖师碑传、宫观记与诗序。'),
}


def _lines(raw, src=None):
    """清洗成行，并把卷题/卷终/撰人行/体裁名分流到剥离账。"""
    keep, lead, dropped = [], [], []
    ls, dr = strip_editor(norm_lines(clean(raw)))
    dropped += dr
    for ln in ls:
        # 体裁名可能带零散空白（'''七言詩'''（ 藏頭）），比对前先归一
        flat = re.sub(r'\s+', '', ln)
        if (flat in BYLINES or flat in GENRE or (src and flat == src)
                or (RE_VOLTITLE.search(flat) or RE_VOLEND.search(flat)) and len(flat) <= 16):
            lead.append(ln)
        else:
            keep.append(ln)
    return keep, lead, dropped


def _vol_sort(k):
    CN = '一二三四五六七八九十'
    m = re.search(r'(\d+)$', k)
    if m:
        return (1, int(m.group(1)), '')
    if k.endswith('序') and '後' not in k:
        return (0, 0, '')
    if '後序' in k:
        return (9, 0, '')
    m = re.search(r'卷([一二三四五六七八九十]+)$', k)
    if m:
        g = m.group(1)
        n = CN.index(g) + 1 if len(g) == 1 else (10 + CN.index(g[1]) + 1 if g[0] == '十' else 10)
        return (1, n, '')
    for i, c in enumerate('上中下'):
        if k.endswith('卷' + c):
            return (1, i + 1, '')
    return (5, 0, k)


def tokenize(src, kind, key):
    """页 → [('H', 级, 题)|('B', 行)]，两型的差别只在这一步。"""
    page = load(src)[key]
    toks, first, lead_extra = [], True, []
    for lv, title, raw in sections(page):
        if title is not None:
            ct = re.sub(r'\s+', '', clean(title))
            if ct in BYLINES or RE_VOLEND.search(ct):
                lead_extra.append(ct)
            else:
                toks.append(('H', lv, ct))
        body, lead, dropped = _lines(raw, src)
        if first and src in DROP_LEAD_BLOCK:
            whole, _ = strip_editor(norm_lines(clean(raw)))
            TOC.append(''.join(whole)); body, lead, first = [], [], False
        first = False
        if kind == 'bare':
            for ln in body:
                bare = (ln[-1] not in TERM and ln[-1] not in CONT and
                        (not any(c in ln for c in '，、') or ln in BARE_TITLE_WHITELIST))
                toks.append(('H', 9, ln) if bare else ('B', ln))
        else:
            toks += [('B', ln) for ln in body]
        toks.append(('N', lead + lead_extra, dropped))
        lead_extra = []
    return toks


GROUPS = set()
TOC = []          # 卷首目錄，非正文，剥去后登记备查


def assemble(src, kind):
    """token 流 → 卷/篇。卷界=卷题式标题；组=无正文之题，作用域延至下一同级组。"""
    vols, notes, lead_all = [], [], []
    for key in sorted(load(src), key=_vol_sort):
        toks = tokenize(src, kind, key)
        has_vol = any(t[0] == 'H' and RE_VOLTITLE.search(t[2]) for t in toks)
        cur = None if has_vol else {'name': key.split('/')[-1], 'pieces': []}
        vols += [cur] if cur else []
        pend = None
        for t in toks:
            if t[0] == 'N':
                lead_all += t[1]; notes += t[2]; continue
            if t[0] == 'H' and RE_VOLTITLE.search(t[2]):
                cur = {'name': t[2], 'pieces': []}
                vols.append(cur); pend = None; continue
            if cur is None:
                cur = {'name': key.split('/')[-1], 'pieces': []}
                vols.append(cur)
            if t[0] == 'H':
                cur['pieces'].append({'raw': t[2], 'title': t[2], 'lines': [], 'grp': pend})
            else:
                if not cur['pieces']:
                    cur['pieces'].append({'raw': '', 'title': None,
                                          'lines': [], 'grp': None})
                cur['pieces'][-1]['lines'].append(t[1])
        # 无正文之题即组：登记为 pend，其后诸篇冠以「组·」直至下一组
        for v in vols:
            out, grp = [], None
            for p in v['pieces']:
                if not p['lines']:
                    GROUPS.add(p['title'])
                    grp = None if p['title'] in GENRE else p['title']
                    continue
                if p['raw'] in GENRE:
                    # 体裁标题下直接接正文：该篇本无题（洞玄金玉集卷一首篇即如此），
                    # 体裁名剥去，题留待由首句派生，同站内《东坡词》「词牌·首句」例
                    GROUPS.add(p['raw']); grp = None
                    out.append({'raw': '', 'title': None, 'lines': p['lines'], 'grp': None})
                    continue
                out.append({'raw': p['raw'],
                            'title': '%s·%s' % (grp, p['title']) if grp else p['title'],
                            'lines': p['lines'], 'grp': grp})
            v['pieces'] = out
    return [v for v in vols if v['pieces']], notes, lead_all


def _layer_jingzhu(lines):
    """四言经文作引用块、（…）夹注还原为注文段，同河上公章句/太上感应篇集注体例。"""
    out = []
    for ln in lines:
        if re.fullmatch(r'（.*）', ln):
            out.append(ln[1:-1])
        elif len(ln) <= 8 and '，' not in ln and '。' not in ln:
            out.append('> ' + ln)
        else:
            out.append(ln)
    return out


RE_CUT = re.compile(r'[。，、；：！？]')


def derive_title(lines):
    """无题之篇取首句为题，同站内《东坡词》「词牌·首句」例。"""
    for ln in lines:
        t = RE_CUT.split(ln.lstrip('> ').strip())[0].strip()
        if t:
            return t[:16]
    return '無題'


def build(slug):
    cfg = BOOKS[slug]
    kind = 'heading' if cfg['kind'] in ('taigu', 'single') else cfg['kind']
    vols, notes, lead = assemble(cfg['src'], kind)
    if cfg['kind'] == 'taigu':
        for p in vols[0]['pieces']:                # 卷一《参同契》简要释义
            p['lines'] = _layer_jingzhu(p['lines'])
    if cfg['kind'] == 'single':                       # 语录体：源以「正文」行分序与语录
        for v in vols:
            ls = [l for p in v['pieces'] for l in p['lines']]
            cut = next((i for i, l in enumerate(ls) if l == '正文'), None)
            v['pieces'] = ([{'raw': '', 'title': '序', 'lines': ls[:cut], 'grp': None},
                            {'raw': '正文', 'title': '語錄', 'lines': ls[cut + 1:], 'grp': None}]
                           if cut else [{'raw': '', 'title': cfg['src'],
                                         'lines': ls, 'grp': None}])
    for v in vols:
        for p in v['pieces']:
            if not p.get('title'):
                first = p['lines'][0].lstrip('> ').strip() if p['lines'] else ''
                if first and len(first) <= 24 and not RE_CUT.search(first):
                    p['title'], p['raw'], p['lines'] = first, first, p['lines'][1:]
                else:
                    p['title'] = derive_title(p['lines'])
    return vols, notes, lead, cfg
