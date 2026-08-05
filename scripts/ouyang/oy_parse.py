# -*- coding: utf-8 -*-
"""欧阳修集·结构解析。

底本层级：
  =體裁組=            「古詩三十八首」「賦五首」式，共 106 种，剥去不入篇名
  ==【篇題】== / ===【篇題】===   篇（3222 处以【】标出）
  ====△一====        書簡「第 N 通」，属其上「與某某 N 通」组，作「组·△一」
  其他无【】标题       层级深于当前篇者为篇内小节(##)，否则为篇

判据一律结构性，同王临川集：有正文即篇；无正文而下辖同级者为组。
组的作用域延至下一个同级或更浅的标题，故同组诸篇一律带组名前缀。
"""
import collections, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oy_clean import clean, norm_lines
from oy_fix import TITLE_FIX, JUNK_FIX, MODERN, BRACKET_FIX

# header2 元数据块（title/section/author/previous/next），非正文。
# 有标题的页里它落在首段被丢弃，但无标题页（附錄一等）整页收，须显式剥。
RE_HDR = re.compile(r'\{\{\s*header2?\b.*?^\}\}\s*$', re.S | re.I | re.M)

CACHE = os.environ.get('OY_CACHE', 'oycache.json')
BOOK = '歐陽修集'
# 卷首裸行重复 header 的卷题（「卷七十五·居士外集卷二十五」），剥去
RE_VOLECHO = re.compile(r'^卷[一二三四五六七八九十百]+·')
# 体裁组：「古詩三十八首」「賦五首」「記十首（附一首）」「譜」式
RE_GENRE = re.compile(r'^[^\s]{1,14}?[一二三四五六七八九十百]+首|^譜$')
HANZI = re.compile(r'[一-鿿]')
JUNKCH = re.compile('[぀-ヿ─-╿０-９Ａ-Ｚａ-ｚ＂-＇＊＋－．／＜-＞＠［-｀｛-～'
                    '\ufffd\ue000-\uf8ff\u2e80-\u2fdfA-Za-z]')


# ── 底本标题标记畸形处，逐条修补（只挪 = 与换行，不动一字） ──
# 须在 parse 与 verify 的 src_stream 共用的 load() 里做，两侧同源方能对账。
MALFORMED = {
    # 标题粘在上一篇正文末尾，未另起一行 → 该篇被吞进前篇
    '。===【和梅公儀嘗花{{*|嘉祐二年}}】===':
        '。\n\n===【和梅公儀嘗花{{*|嘉祐二年}}】===',
    '。==【賜相州觀察使劉從廣進奉乾元節馬詔】==':
        '。\n\n==【賜相州觀察使劉從廣進奉乾元節馬詔】==',
    # 闭合标记点错位置，把篇题后半截「命第一表不允批答口宣」甩进正文；
    # 同卷下一篇「…讓恩命第二表不允斷來章批答口宣」可证正确断法
    '==【賜新除建雄軍節度使殿前都指揮使許懷德讓恩】==命第一表不允批答口宣':
        '==【賜新除建雄軍節度使殿前都指揮使許懷德讓恩命第一表不允批答口宣】==',
}


def load():
    pages = json.load(open(CACHE))
    hit = collections.Counter()
    for k, v in pages.items():
        for bad, good in MALFORMED.items():
            if bad in v:
                hit[bad] += v.count(bad)
                v = v.replace(bad, good)
        pages[k] = v
    for bad in MALFORMED:
        if not hit[bad]:
            raise SystemExit('MALFORMED 未命中: %r' % bad)
    return pages


# ── 篇题标点归一（只动标点不动字，故不入字流账） ──
# 【】是底本的篇题界标，剥净；卷130「==【晦明說﹞===」以﹞误作】，一并剥。
# 〈…〉是底本另一种夹注写法（同 {{*|…}}），站内体例一律作（…）；
# 底本此类多失闭合（〕/无闭合各数处），于篇题末补齐。
# ‧(U+2027)、•(U+2022) 是卷题分隔符的异写，底本 89 处作·、36 处作‧、1 处作•，从多数。
def _close(t):
    """补未闭合的（；末尾恰是一层（…）时并入，不作（…（…））——同 _tmpl 夹注例。"""
    if t.count('（') <= t.count('）'):
        return t
    if t.endswith('）'):
        i = t.rfind('（')
        t = t[:i] + t[i + 1:-1]
    return t + '）'


def norm_title(t):
    t = t.replace('【', '').replace('】', '').replace('﹞', '')
    t = t.replace('‧', '·').replace('•', '·')
    if '〈' in t:
        t = _close(t.replace('〈', '（').replace('〉', '）').replace('〕', '）'))
    # 書簡「△七」是底本的「第七通」标记，站内体例作「其七」（同唐诗三百首·其N）；
    # 「△第二道」自带序次，只剥标记不加「其」
    t = re.sub(r'^△(?=[一二三四五六七八九十])', '其', t)
    return t.lstrip('△').strip()


def volkey(k):
    m = re.search(r'卷(\d+)$', k)
    if m:
        return (0, int(m.group(1)), '')
    if k.endswith('補遺'):
        return (1, 0, '')
    m = re.search(r'附錄([一二三四五六七八九十]+)$', k)
    if m:
        return (2, '一二三四五六七八九十'.index(m.group(1)) + 1, '')
    return (3, 0, k)


def headings(text):
    """切成 [(级, 题, 正文)]；容错不对称标记（卷150 有 ===…== ）。"""
    parts = re.split(r'^(={1,6})\s*(.+?)\s*=+\s*$', text, flags=re.M)
    out = [(0, None, parts[0])]
    for i in range(1, len(parts), 3):
        out.append((len(parts[i]), parts[i + 1].strip(), parts[i + 2]))
    return out


def volume_title(page, raw):
    """卷题取 header2 的 section=，如「卷七十五·居士外集卷二十五」。"""
    m = re.search(r'^\s*\|?\s*section\s*=\s*(.+?)\s*$', raw, re.M)
    return clean(m.group(1)).strip() if m and m.group(1).strip() else page.split('/')[-1]


FIXTABLE = os.environ.get('OY_FIXTABLE', 'oy-fixtable.json')


def apply_fixes(vols):
    """施加乱码回改表（键＝卷题|篇题|坏串），逐条记账并核验命中。"""
    if not os.path.exists(FIXTABLE):
        return []
    tab = json.load(open(FIXTABLE))
    done, missed = [], []
    for v in vols:
        for p in v['pieces']:
            for k, good in tab.items():
                vol, piece, bad = k.split(' | ')
                if v['key'] != vol or p.get('key') != piece:
                    continue
                hit = False
                for i, ln in enumerate(p['lines']):
                    # 坏串取自纯汉字流，正文行夹标点，故在汉字流上定位再映射回原行；
                    # 坏段内的标点同属损坏产物，一并替换掉。
                    pos = [j for j, c in enumerate(ln) if HANZI.match(c)]
                    flat = ''.join(ln[j] for j in pos)
                    at = flat.find(bad)
                    if at < 0:
                        continue
                    lo, hi = pos[at], pos[at + len(bad) - 1]
                    p['lines'][i] = ln[:lo] + good + ln[hi + 1:]
                    hit = True
                    break
                (done if hit else missed).append((k, good))
    # 第二轮：残留杂讯锚点，键为含杂讯字的原串（全书唯一），在汉字流上定位
    for bad, good in JUNK_FIX.items():
        hits = 0
        for v in vols:
            for p in v['pieces']:
                for i, ln in enumerate(p['lines']):
                    if bad in ln:
                        p['lines'][i] = ln.replace(bad, good)
                        hits += ln.count(bad)
                        continue
                    pos = [j for j, c in enumerate(ln) if HANZI.match(c) or JUNKCH.match(c)]
                    flat = ''.join(ln[j] for j in pos)
                    at = flat.find(bad)
                    if at < 0:
                        continue
                    lo, hi = pos[at], pos[at + len(bad) - 1]
                    p['lines'][i] = ln[:lo] + good + ln[hi + 1:]
                    hits += 1
        if not hits:
            raise SystemExit('JUNK_FIX 未命中: %r' % bad)
        done.append((bad, good, hits))

    for bad, good in BRACKET_FIX.items():            # 〈…〉夹注归一，只动标点
        hits = 0
        for v in vols:
            for p in v['pieces']:
                for i, ln in enumerate(p['lines']):
                    if bad in ln:
                        p['lines'][i] = ln.replace(bad, good)
                        hits += ln.count(bad)
        if not hits:
            raise SystemExit('BRACKET_FIX 未命中: %r' % bad)
        done.append((bad, good, hits))

    for v in vols:                                   # 篇题本身即乱码者
        for p in v['pieces']:
            for bad, good in TITLE_FIX.items():
                if bad in p['title']:
                    p['title'] = p['title'].replace(bad, good)
                    p['raw'] = p['raw'].replace(bad, good)
                    done.append((bad, good))
    if missed:
        raise SystemExit('回改表 %d 条未命中：%s' % (len(missed), missed[:4]))
    return done


RE_TRANS = re.compile(r'\{\{:\s*([^}|]+?)\s*(\|[^}]*)?\}\}')
# 被嵌页自带的 {{Header|…}} 写在一行且内含 {{-|并序}} 一层嵌套。
# 不能交给 RE_HDR（它按行首 }} 收口，会一路吃到后文某个 }} 行，把正文整段吞掉）。
RE_PAGEHDR = re.compile(
    r'\{\{\s*header2?\b(?:[^{}]|\{\{(?:[^{}]|\{\{[^{}]*\}\})*\}\})*\}\}', re.I)


def expand_trans(raw, pages):
    """{{:頁名}} 是整篇嵌入，正文在别的页面上（同王临川集 transclusion 例）。
    抓来的页存于 'TRANS/頁名'；源本就无此页者（红链）留空并记账。"""
    missing = []

    used = []

    def sub(m):
        key = 'TRANS/' + m.group(1)
        if key not in pages:
            missing.append(m.group(1))
            return ''
        used.append(m.group(1))
        return RE_PAGEHDR.sub('', pages[key])
    return RE_TRANS.sub(sub, raw), missing, used


def parse(fix=True):
    pages = load()
    vols, strip_log, redlinks = [], [], []
    for key in sorted((k for k in pages
                       if k != BOOK and not k.startswith('TRANS/')), key=volkey):
        raw, miss, trans = expand_trans(pages[key], pages)
        redlinks.extend(miss)
        body_raw = RE_HDR.sub('', raw)
        vt = volume_title(key, raw)
        vol = {'page': key, 'key': vt, 'title': norm_title(vt), 'pieces': []}
        grp = None            # (级, 组名)，作用域至下一同级或更浅标题
        cur = None            # (级, 篇)，用于判定篇内小节
        host = None           # (级, 题)，△第N通所属之篇/组，作用域至下一同级标题
        for lv, title, body in headings(body_raw):
            all_lines = norm_lines(clean(body))
            lines = [l for l in all_lines if not RE_VOLECHO.match(l)]
            strip_log += [l for l in all_lines if RE_VOLECHO.match(l)]
            if title is None:
                if not any(h[1] for h in headings(body_raw)):
                    if lines:                        # 整页无标题者（附錄一年譜）作一篇
                        vol['pieces'].append({
                            'raw': '', 'key': vol['key'].split('‧')[-1],
                            'title': vol['title'].split('·')[-1], 'lines': lines})
                else:
                    # 页首残余：__TOC__、卷题回显，以及卷039「= 記十首 ={{*|附一首}}」、
                    # 卷053「= 古詩三十首{{*|…作 =。…}}」两处因行尾是 }} 而未被识作标题的
                    # 体裁组名——皆非正文，入剥离账
                    strip_log += lines
                continue
            t = clean(title).strip()
            bare = t.strip('【】').strip()
            if grp and lv <= grp[0]:                 # 出组
                grp = None
            if cur and lv <= cur[0]:                 # 出篇
                cur = None
            if host and lv <= host[0] and not bare.startswith('△'):
                host = None
            if lv == 1 and not RE_GENRE.match(bare):
                # 附錄四「像贊」「文評·清聖祖康熙」「文評·清高宗」是作者分组而非体裁，
                # 剥掉会丢失评语归属，故作组名前缀
                strip_log += [bare] + lines      # 组名只作前缀，不入字流
                grp, cur, host = (lv, bare), None, None
                continue
            if lv == 1:                              # 体裁组，剥去不入篇名
                # 卷039「= 記十首 ={{*|附一首}}」夹注写在标题外、
                # 卷053「= 古詩三十首{{*|…作 =。…}}」把 = 写进了模板，
                # 两处源标记畸形致注文落到组下正文位，一并入账
                strip_log.append(t)
                strip_log += lines
                continue
            if not lines:                            # 无正文 → 组
                # 组名只作篇题前缀，不入字流，故须记进剥离账供质检认领
                strip_log.append(bare)
                grp, cur, host = (lv, bare), None, None
                continue
            is_letter = bare.startswith('△')
            # 整篇嵌入者是独立作品，必为篇，不可并作前篇的小节
            if any(x in bare for x in trans):
                cur = None
            if cur and not t.startswith('【') and not is_letter:
                cur[1]['lines'] += ['## ' + bare] + lines   # 篇内小节
                continue
            # raw 迻录自底本、入字流校验，故保持原样；title 是显示题，作标点归一。
            # key 是归一前的旧题，只用来对回改表（表按旧题生成，不重跑对齐）。
            pre = grp[1] if grp else (host[1] if is_letter and host else None)
            piece = {'raw': bare, 'lines': lines,
                     'key': '%s·%s' % (pre, bare) if pre else bare,
                     'title': '%s·%s' % (norm_title(pre), norm_title(bare))
                              if pre else norm_title(bare)}
            vol['pieces'].append(piece)
            cur = (lv, piece)
            if not is_letter:
                host = (lv, bare)
        keep = []
        for p in vol['pieces']:
            if any(m in p['title'] for m in MODERN):
                strip_log += [p.get('raw', '')] + p['lines']   # 近人之作，入剥离账
            else:
                keep.append(p)
        vol['pieces'] = keep
        vols.append(vol)
    if fix:
        apply_fixes(vols)
    return vols, strip_log
