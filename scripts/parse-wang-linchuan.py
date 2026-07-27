#!/usr/bin/env python3
"""王臨川集（北宋·王安石）解析器：补齐唐宋八大家最后一家。

底本：维基文库《王臨川集》整理本一百卷（繁体）。**不是**2026-07-03 撤收的
四部丛刊明嘉靖本，也不是四库系——避讳字频法实测 玄=8、弘=2（旧《临川文集》
玄=0、弘=0 是四库避讳改字的实证），且全书零「钦定四库全书/臣等谨案/考證」
馆臣痕迹，正是 docs/source-risk-audit.md 要求的「可追溯专书本」。

**取渲染 HTML 而非 wikitext**：卷页大量用 `{{:篇名}}`(702 处) 与
`{{#lst:}}`(72 处) transclusion，正文散在两千多个独立篇页里；渲染由服务端
解析 transclusion，一百次请求即得全书。

结构：一卷一子目录、一篇一文件。**不按卷建单文件**——`.reader__text` 无
`white-space:pre-wrap`，单换行会塌缩，且 `isVerse()` 遇标题即不做诗句居中，
按卷建文件会让一千多首诗失去分行与居中（见 src/pages/Reader.tsx renderText）。
每卷内 h2=体裁组、h3=篇题；卷一至卷十二无体裁组，h2 即篇题。

用法:
    python3 scripts/parse-wang-linchuan.py --check   # 只质检不落盘
    python3 scripts/parse-wang-linchuan.py           # 写 base-data
"""
import html
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'base-data/literature/wang-lin-chuan-ji')
CACHE = os.environ.get('WS_CACHE') or os.path.join(ROOT, '.ws-cache')
UA = ('chinese-classics-collector/1.0 '
      '(https://github.com/ifcalm/chinese-classics; ifcalm.ok@gmail.com)')
HZ = re.compile(r'[一-鿿㐀-䶿\U00020000-\U0003FFFF]')
_last = [0.0]

# 无码缺字：模板 title 的「字符描述」→ 存形。模板自身已给出真字者取真字
# （同三命通会 SKchar 取真字例）；余者一律 IDS 存形，不做编辑性断言。
# 「上艹下尔」卷060 给出真字 𦬼，据同书内证归一其余 5 处。
GLYPH = {
    '左亻右瓜': '𠇗', '（左目右市）': '𥄔', '上非下土': '𡌦', '左女右戍': '𡜐',
    '上艹下尔': '𦬼', '上艸下榮': '𦾵',
    '上雨下池': '⿱雨池', '左糸右丏': '⿰糸丏', '外囗內曷': '⿴囗曷',
    '左扌右弃': '⿰扌弃', '上竹下廢': '⿱竹廢', '上執下目': '⿱執目',
    '上艹下不': '⿱艹不', '上矛下心': '⿱矛心', '左禾右夅': '⿰禾夅',
    '左兀右干': '⿰兀干', '左冫右青': '⿰冫青', '淵-氵+言': '⿰言𠕒',
}


# ── 抓源 ────────────────────────────────────────────────
def _api(params, key):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, key + '.json')
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    gap = time.time() - _last[0]
    if gap < 1.5:
        time.sleep(1.5 - gap)
    base = 'https://zh.wikisource.org/w/api.php'
    # 带 text 的转换请求负载很长，GET 会超 URL 长度上限，一律走 POST
    if 'text' in params:
        cmd = ['curl', '-4', '-s', '-H', 'User-Agent: ' + UA]
        for k, v in params.items():
            cmd += ['--data-urlencode', '%s=%s' % (k, v)]
        cmd.append(base)
    else:
        cmd = ['curl', '-4', '-s', '-H', 'User-Agent: ' + UA,
               base + '?' + urllib.parse.urlencode(params)]
    for attempt in range(5):
        # node fetch 走 IPv6 不通；裸 curl 无 UA 会被限流 429
        out = subprocess.run(cmd, capture_output=True, text=True)
        _last[0] = time.time()
        try:
            d = json.loads(out.stdout)
            break
        except ValueError:
            sys.stderr.write('retry %d %s\n' % (attempt, key))
            time.sleep(5 * (attempt + 1))
    else:
        raise SystemExit('抓取失败: ' + key)
    if 'error' in d:
        raise SystemExit('%s: %s' % (key, d['error'].get('code')))
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False)
    return d


def render(page):
    key = 'rd-' + page.replace('/', '__')
    return _api({'action': 'parse', 'page': page, 'prop': 'text', 'format': 'json',
                 'formatversion': '2', 'disableeditsection': '1'}, key)['parse']['text']


def to_simplified(strings):
    """维基 LanguageConverter 批转简体。变体名必须 zh-hans——zh-cn 静默不转换。"""
    out = []
    SEP = '\n＠＠\n'
    for i in range(0, len(strings), 150):
        chunk = strings[i:i + 150]
        d = _api({'action': 'parse', 'text': SEP.join(chunk), 'contentmodel': 'wikitext',
                  'variant': 'zh-hans', 'prop': 'text', 'format': 'json',
                  'formatversion': '2', 'wrapoutputclass': ''}, 'conv-wlc-%d' % i)
        t = html.unescape(re.sub(r'<[^>]+>', '', d['parse']['text']))
        parts = [x.strip() for x in t.split('＠＠')]
        parts = [x for x in parts if x != '']
        if len(parts) != len(chunk):
            raise SystemExit('!! 简体转换分段数不符 %d vs %d @%d'
                             % (len(parts), len(chunk), i))
        out.extend(parts)
    return out


# ── 清洗 ────────────────────────────────────────────────
def strip_head(t):
    """剥卷首导航块（header2/footer 表、Textquality 标、姊妹计划、TOC 锚）。"""
    t = re.sub(r'<style.*?</style>', '', t, flags=re.S)
    t = re.sub(r'<script.*?</script>', '', t, flags=re.S)
    m = re.search(r'<meta property="mw:PageProp/toc"\s*/?>', t)
    if m:
        return t[m.end():]
    m = re.search(r'<div class="mw-heading', t)
    if not m:
        raise SystemExit('!! 卷首既无 TOC 锚也无标题，版式未预期')
    return t[m.start():]


def detag(t):
    """标签转文本。校语 tooltip 必须先整块删——否则「一作X」会漏进正文。"""
    # {{另}}/{{另2}} 的异文校语渲染成 variant-tooltip 子 span，只留主字
    t = re.sub(r'<span class="variant-tooltip">.*?</span>', '', t, flags=re.S)
    # <ref> 脚注上标：卷84 引清·过珙《古文評註》评语，非王安石正文，连标记一并剥
    t = re.sub(r'<sup[^>]*class="[^"]*reference[^"]*"[^>]*>.*?</sup>', '', t, flags=re.S)
    # 无码缺字：渲染成显示 ?/？ 的 span，按字符描述存形
    def glyph(m):
        desc = html.unescape(m.group(1)).split()[0].strip()
        if desc not in GLYPH:
            raise SystemExit('!! 未登记的字符描述: %r' % desc)
        return GLYPH[desc]
    t = re.sub(r'<span[^>]*title="字符描述：([^"]+)"[^>]*>[^<]*</span>', glyph, t)
    t = re.sub(r'<br\s*/?>', '\n', t)
    t = re.sub(r'<[^>]+>', '', t)
    t = html.unescape(t)
    t = t.replace('​', '').replace('\xa0', ' ')
    return t


BANNED = [('姊妹计划', '姊妹计划残渣'), ('数据项', '数据项残渣'),
          ('Category:', '分类标签残渣'), ('一作「', '异文校语漏入正文'),
          ('《四庫全書》本無', '校语漏入正文'),
          # 缺字残留只认这一条：?／？ 在本书是正常标点（「汝今何㳟昔何慢？」），不可当判据
          ('字符描述', '缺字模板残渣'),
          ('mw-', 'HTML 类名残渣'), ('@media', 'CSS 残渣'),
          ('《古文評註》', '他人评注漏入正文')]

# 脚注上标残渣 [1] [12]
REF_RESIDUE = re.compile(r'\[\d+\]')


def assert_clean(text, where):
    m = REF_RESIDUE.search(text)
    if m:
        i = m.start()
        raise SystemExit('!! %s: 脚注上标残渣 %s …%s…'
                         % (where, m.group(), text[max(0, i - 50):i + 50]))
    for pat, label in BANNED:
        if pat in text:
            i = text.index(pat)
            raise SystemExit('!! %s: %s …%s…'
                             % (where, label, text[max(0, i - 50):i + 50]))


def blocks_of(chunk):
    """篇内 HTML → 段落列表。诗行(br)各成一段，否则 .reader__text 单换行会塌缩。"""
    out = []
    for m in re.finditer(r'<div class="poem">(.*?)</div>|<p\b[^>]*>(.*?)</p>',
                         chunk, re.S):
        is_poem = m.group(1) is not None
        body = detag(m.group(1) if is_poem else m.group(2))
        for line in body.split('\n'):
            s = line.strip()
            if s:
                out.append(s)
    return out


HEAD_RE = re.compile(
    r'<div class="mw-heading mw-heading([23])"><h[23][^>]*>(.*?)</h[23]></div>', re.S)


# 脚注区标题：底本用「註」系字，简体「注」系一并列入以防漏
FOOT_NAMES = ('註', '注', '註釋', '注釋', '註解', '參考', '参考')


def strip_tail(t):
    """剥卷末 ws-footer 导航表与 NewPP 解析注释。"""
    for pat in (r'<table class="ws-noexport', r'<!--\s*\nNewPP'):
        m = re.search(pat, t)
        if m:
            t = t[:m.start()]
    return t


def genre_tokens(juan_title):
    """卷题里的体裁标签，如「內制一（冊文　表本　青詞）」→ {內制,冊文,表本,青詞}。"""
    toks = re.split(r'[　\s（）()·]+', juan_title)
    out = set()
    for x in toks:
        x = re.sub(r'[一二三四五六七八九十]+$', '', x).strip()
        if len(x) >= 2:
            out.add(x)
    return out


def parse_juan(k, juan_title):
    """篇的判据是结构性的：有正文者即篇；无正文而下辖更深级标题者为组。

    组分两种——体裁组（名见卷题，如冊文/表本/論議）不并入篇名；组诗题
    （如卷四「酬王浚賢良松泉」下辖「松」「泉」）并入篇名，同李太白集
    「前出塞九首 一」体例，否则两首都只叫「松」「泉」失去归属。
    """
    t = strip_tail(strip_head(render('王臨川集/卷%03d' % k)))
    heads = list(HEAD_RE.finditer(t))
    if not heads:
        raise SystemExit('!! 卷%d 无标题' % k)
    genres = genre_tokens(juan_title)
    items, group = [], None
    for i, m in enumerate(heads):
        title = detag(m.group(2)).strip()
        lvl = m.group(1)
        end = heads[i + 1].start() if i + 1 < len(heads) else len(t)
        body = blocks_of(t[m.end():end])
        deeper = i + 1 < len(heads) and heads[i + 1].group(1) > lvl
        if not body and deeper:
            is_genre = any(g.startswith(title) or title.startswith(g) for g in genres)
            group = None if is_genre else title
            continue
        if not body and title in FOOT_NAMES:
            continue
        items.append((title, group, body))
        if not deeper:
            group = None if lvl == '2' else group
    # 卷末脚注区标题(页脚模板所发,本书 100 卷实测全空)属版式，剥；非空则硬失败
    while items and items[-1][0] in FOOT_NAMES:
        title, _, body = items.pop()
        if body:
            raise SystemExit('!! 卷%d 脚注区「%s」非空，需人工判断: %r'
                             % (k, title, body[:2]))
    for title, _, body in items:
        if not body:
            raise SystemExit('!! 卷%d 篇「%s」正文为空' % (k, title))
    return items


# 篇题里的 〈自注〉：底本夹注，移出标题作正文首段（同栾城集〈…〉体例）
NOTE_RE = re.compile(r'〈(.*?)〉\s*$', re.S)


def split_note(title):
    m = NOTE_RE.search(title)
    if not m:
        return title.strip(), None
    return title[:m.start()].strip(), '〈%s〉' % m.group(1).strip()


CN = '〇一二三四五六七八九'


def cn_num(k):
    if k < 10:
        return CN[k]
    if k < 20:
        return '十' + (CN[k % 10] if k % 10 else '')
    if k == 100:
        return '一百'
    tens = CN[k // 10] + '十'
    return tens + (CN[k % 10] if k % 10 else '')


def juan_titles():
    """卷题体裁取自书目页，如「卷一‧古詩一」。"""
    key = 'wt-王臨川集'
    d = _api({'action': 'parse', 'page': '王臨川集', 'prop': 'wikitext',
              'format': 'json', 'formatversion': '2'}, key)
    wt = d['parse']['wikitext']
    out = {}
    for m in re.finditer(r'\[\[/卷(\d+)\|[^\]]*\]\]‧(.+)', wt):
        s = m.group(2)
        s = re.sub(r'\{\{\*\|([^}]*)\}\}', r'（\1）', s)
        s = re.sub(r'-\{(.*?)\}-', r'\1', s)
        out[int(m.group(1))] = s.strip()
    return out


def fm(title, weight, extra=''):
    return ('---\ntitle: "%s"\nweight: %s\n%s---\n\n' % (title, weight, extra))


def main():
    check = '--check' in sys.argv
    jt = juan_titles()
    book = {}
    for k in range(1, 101):
        book[k] = parse_juan(k, jt.get(k, ''))
        sys.stderr.write('.')
    sys.stderr.write('\n')

    # 标题批量转简体：卷题 + 全部篇题
    jkeys = sorted(book)
    raw = ['卷%s·%s' % (cn_num(k), jt.get(k, '')) for k in jkeys]
    flat = ['%s %s' % (g, t) if g else t for k in jkeys for t, g, _ in book[k]]
    simp = to_simplified(raw + flat)
    jsimp = dict(zip(jkeys, simp[:len(raw)]))
    it = iter(simp[len(raw):])
    total_pian = total_hz = 0
    for k in jkeys:
        pian = []
        for title, group, body in book[k]:
            stitle = next(it)
            clean_title, note = split_note(stitle)
            _, note_trad = split_note(title)
            blocks = ([note_trad] if note_trad else []) + body
            text = '\n\n'.join(blocks)
            assert_clean(text, '卷%d %s' % (k, clean_title))
            assert_clean(clean_title, '卷%d 标题' % k)
            pian.append((clean_title, group, text))
        d = os.path.join(OUT, '%03d' % k)
        if not check:
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, '_index.md'), 'w', encoding='utf-8') as f:
                f.write(fm(jsimp[k], k))
        for n, (title, group, text) in enumerate(pian, 1):
            total_pian += 1
            total_hz += len(HZ.findall(text))
            if not check:
                with open(os.path.join(d, '%02d.md' % n), 'w', encoding='utf-8') as f:
                    f.write(fm(title, n) + text + '\n')
    if not check:
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, '_index.md'), 'w', encoding='utf-8') as f:
            f.write('---\ntitle: "王临川集"\nweight: 1021\nkind: "book"\n'
                    'summary: "北宋·王安石诗文集，唐宋八大家之一，'
                    '文章峭直简劲、议论雄奇。一百卷，据维基文库整理本收录（繁体，非四库系底本）。"\n'
                    '---\n\n收录《王临川集》一百卷，一卷一目录、一篇一文件。\n')
    print('%s 100 卷 · %d 篇 · %d 汉字 (%.2f 万)'
          % ('[check]' if check else '✓', total_pian, total_hz, total_hz / 10000))


if __name__ == '__main__':
    main()
