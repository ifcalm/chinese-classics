#!/usr/bin/env python3
"""道家经典批解析器：抱朴子外篇 / 鹖冠子 / 无能子 / 道教义枢。

底本一律维基文库整理本（繁体）。抱朴子外篇与站内既有《抱朴子内篇》同出
`抱朴子/` 页树，逐字同源；鹖冠子、抱朴子外篇另以四库全书本作第二证人做过
汉字守恒交叉校勘（详 docs/collation-log.md 2026-07-26 节）。

正文一字不改：四库本异体字形（絕/絶、眾/衆）与底本原讹（道教义枢卷二
「青漢道士」当作「青溪」、卷五「二觀義十七」脱「第」）一律存照。剥离项只
有版式与现代整理者校记：{{header}}、分类标签、卷题/卷终行、卷末 #N 校记块。

标题一律简体（站点铁律），正文保持底本繁体。简体标题由维基
LanguageConverter variant=zh-hans 转换后固化在本文件 TITLES 表中——
zh-cn 会静默不转换，勿改。

用法:
    python3 scripts/parse-taoism-classics.py            # 抓源(带缓存)并写 base-data
    python3 scripts/parse-taoism-classics.py --check    # 只跑质检，不落盘
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, 'base-data/taoism')
CACHE = os.environ.get('WS_CACHE') or os.path.join(ROOT, '.ws-cache')
DATE = '2026-07-26'
UA = ('chinese-classics-collector/1.0 '
      '(https://github.com/ifcalm/chinese-classics; ifcalm.ok@gmail.com)')

HZ = re.compile(r'[一-鿿㐀-䶿\U00020000-\U0003FFFF]')
_last = [0.0]

# ── 简体标题表（LanguageConverter variant=zh-hans 转换结果，已固化）──────
BPZ_WAI = """嘉遁 逸民 勖学 崇教 君道 臣节 良规 时难 官理 务正 贵贤 任能 钦士 用刑
审举 交际 备阙 擢才 任命 名实 清鉴 行品 弭讼 酒诫 疾谬 讥惑 刺骄 百里 接疏 钧世
省烦 尚博 汉过 吴失 守塉 安贫 仁明 博喻 广譬 辞义 循本 应嘲 喻蔽 百家 文行 正郭
弹祢 诘鲍 知止 穷达 重言 自叙""".split()

HKZ = """博选 著希 夜行 天则 环流 道端 近叠 度万 王𫓧 泰鸿 泰录 世兵 备知 兵政
学问 世贤 天权 能天 武灵王""".split()

# 无能子：(繁体页名, 简体篇题, 卷)，卷次与阙篇依维基文库目录页
WNZ = [
    ('聖過', '圣过第一', '上'), ('明本', '明本第二', '上'), ('析惑', '析惑第三', '上'),
    ('無憂', '无忧第四', '上'), ('質妄', '质妄第五', '上'), ('真修', '真修第七', '上'),
    ('文王說', '文王说第一', '中'), ('首陽子說', '首阳子说第二', '中'),
    ('老君說', '老君说第三', '中'), ('孔子說', '孔子说第四', '中'),
    ('范蠡說', '范蠡说第六', '中'), ('宋玉說', '宋玉说第七', '中'),
    ('商隱說', '商隐说第八', '中'), ('嚴陵說', '严陵说第九', '中'),
    ('孫登說', '孙登说第十', '中'),
    ('答通問', '答通问第一', '下'), ('答華陽子問', '答华阳子问第二', '下'),
    ('答愚中子問', '答愚中子问第三', '下'), ('魚說', '鱼说第四', '下'),
    ('鴆說', '鸩说第五', '下'), ('答魯問', '答鲁问第六', '下'),
    ('紀見', '纪见第八', '下'), ('固本', '固本第十一', '下'),
]
JUAN_CN = {'上': '卷上', '中': '卷中', '下': '卷下'}

DJYS_VOLS = [1, 2, 3, 4, 5, 7, 8, 9, 10]
DJYS_NUM = {1: '一', 2: '二', 3: '三', 4: '四', 5: '五',
            7: '七', 8: '八', 9: '九', 10: '十'}
# 每卷义目（简体），用作 summary；与底本目录行一一对应
DJYS_YIMU = {
    1: '道德义第一·法身义第二·三宝义第三·位业义第四',
    2: '三洞义第五·七部义第六·十二部义第七',
    3: '两半义第八·道意义第九·十善义第十·因果义第十一',
    4: '五廕义第十二·六情义第十三·三业义第十四·十恶义第十五',
    5: '三一义第十六·二观义第十七·三乘义第十八（原缺）',
    7: '三界义第二十三·五道义第二十四·混元义第二十五',
    8: '理教义第二十六·境智义第二十七·自然义第二十八·道性义第二十九',
    9: '福田义第三十·净土义第三十一·三世义第三十二·五浊义第三十三',
    10: '动寂义第三十四·感应义第三十五·有无义第三十六·假实义第三十七',
}


# ── 抓源 ────────────────────────────────────────────────
def wikitext(page):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, 'wt-' + page.replace('/', '__') + '.json')
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            return json.load(f)['parse']['wikitext']
    gap = time.time() - _last[0]
    if gap < 1.5:
        time.sleep(1.5 - gap)
    url = 'https://zh.wikisource.org/w/api.php?' + urllib.parse.urlencode({
        'action': 'parse', 'page': page, 'prop': 'wikitext',
        'format': 'json', 'formatversion': '2'})
    for attempt in range(5):
        # node fetch 走 IPv6 不通，一律 curl -4
        out = subprocess.run(['curl', '-4', '-s', '-H', 'User-Agent: ' + UA, url],
                             capture_output=True, text=True)
        _last[0] = time.time()
        try:
            d = json.loads(out.stdout)
            break
        except ValueError:
            sys.stderr.write('retry %d %s\n' % (attempt, page))
            time.sleep(5 * (attempt + 1))
    else:
        raise SystemExit('抓取失败: ' + page)
    if 'error' in d:
        raise SystemExit('页面不存在: %s (%s)' % (page, d['error'].get('code')))
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False)
    return d['parse']['wikitext']


# ── 清洗 ────────────────────────────────────────────────
def drop_templates(t):
    """由内向外剥模板，避免非贪婪正则吞掉中段（parse-shibu 旧坑）。

    {{!|真字|构件}} 生僻字模板取真字；{{*|…}} 一类本批未出现，遇到即硬失败。
    """
    t = re.sub(r'\{\{\s*!\s*\|\s*([^|}]+?)\s*\|[^}]*\}\}', r'\1', t)
    while True:
        n = re.sub(r'\{\{[^{}]*\}\}', '', t)
        if n == t:
            return t
        t = n


def clean(t):
    t = drop_templates(t)
    t = re.sub(r'-\{(.*?)\}-', r'\1', t)                    # 繁简转换标记留内容
    t = re.sub(r'\[\[[^\]|]*\|([^\]]*)\]\]', r'\1', t)
    t = re.sub(r'\[\[([^\]]*)\]\]', r'\1', t)
    t = t.replace('__NOEDITSECTION__', '').replace('__NOTOC__', '')
    t = re.sub(r"'''?", '', t)
    return t


BANNED = [(r'\{\{|\}\}', '残留模板'), (r'\[\[|\]\]', '残留链接'),
          (r'Category:|分類:|分类:', '残留分类标签'), (r'__[A-Z]+__', '残留魔术字'),
          (r'<ref|<small|<poem|<u>', '残留 HTML 标签'), (r"'''", '残留粗体')]


def assert_clean(text, where):
    for pat, label in BANNED:
        m = re.search(pat, text)
        if m:
            raise SystemExit('!! %s: %s @%d  …%s…'
                             % (where, label, m.start(), text[max(0, m.start() - 40):m.start() + 40]))


def paras(lines):
    out = [l.strip() for l in lines]
    return [l for l in out if l]


# ── 各书解析 ────────────────────────────────────────────
def parse_baopuzi_waipian():
    """外篇每段以 `#` 列表项承载，剥 # 即得段落。"""
    chapters = []
    for k in range(1, 53):
        t = clean(wikitext('抱朴子/外篇/卷%02d' % k))
        body = re.sub(r'^=+.*?=+\s*$', '', t, flags=re.M)
        lines = []
        for line in body.split('\n'):
            s = line.strip()
            if not s:
                continue
            if s.startswith('#'):
                s = s.lstrip('#').strip()
            elif s.startswith('*') or s.startswith(':'):
                raise SystemExit('!! 抱朴子外篇卷%d 未预期的列表标记: %s' % (k, s[:40]))
            lines.append(s)
        text = '\n\n'.join(paras(lines))
        assert_clean(text, '抱朴子外篇卷%d' % k)
        chapters.append(('%02d' % k, '抱朴子外篇 卷%s %s' % (cn_num(k), BPZ_WAI[k - 1]),
                         '抱朴子外篇' + BPZ_WAI[k - 1], text, k))
    return chapters


def parse_hekuanzi():
    t = clean(wikitext('鶡冠子'))
    parts = re.split(r'^==\s*(.+?)\s*==\s*$', t, flags=re.M)
    if len(parts) != 1 + 2 * len(HKZ):  # 篇前部分 + 19*(标题, 正文)
        raise SystemExit('!! 鹖冠子分篇数异常: %d' % ((len(parts) - 1) // 2))
    chapters = []
    for i in range(1, len(parts), 2):
        n = (i + 1) // 2
        text = '\n\n'.join(paras(parts[i + 1].split('\n')))
        assert_clean(text, '鹖冠子' + HKZ[n - 1])
        chapters.append(('%02d' % n, '鹖冠子 %s' % HKZ[n - 1], excerpt(text), text, n))
    return chapters


def parse_wunengzi():
    chapters = []
    for n, (trad, simp, juan) in enumerate(WNZ, 1):
        text = '\n\n'.join(paras(clean(wikitext('無能子/' + trad)).split('\n')))
        assert_clean(text, '无能子' + simp)
        chapters.append(('%02d' % n, '无能子 %s %s' % (JUAN_CN[juan], simp),
                         excerpt(text), text, n))
    return chapters


YIMU_LINE = re.compile(r'^[^\s　]{1,6}義(第[一二三四五六七八九十]+|[一二三四五六七八九十]+)(原缺)?$')


def parse_daojiao_yishu():
    """道藏电子本：首行卷题、次行撰者、义目目录行、义目标题、卷末 #N 校记块。

    剥离卷题与卷终行（版式，同三命通会卷末题名例）及 #N 校记（现代整理者校语，
    同云笈七签每卷末校记例）；撰者署名与义目目录行系底本原文，保留。
    """
    chapters = []
    for k in DJYS_VOLS:
        raw = clean(wikitext('道教義樞/%d' % k))
        lines = paras(raw.split('\n'))
        if not lines[0].startswith('道教義樞卷之'):
            raise SystemExit('!! 道教义枢卷%d 首行非卷题: %s' % (k, lines[0][:40]))
        lines = lines[1:]
        out, notes = [], 0
        for s in lines:
            if s.startswith('#') or s.startswith('＃'):
                if '當作' not in s and '疑脫' not in s and '疑作' not in s:
                    raise SystemExit('!! 道教义枢卷%d 未预期的 # 行: %s' % (k, s[:40]))
                notes += 1
                continue
            if re.match(r'^道教義樞卷之[一二三四五六七八九十]+竟$', s):
                continue
            out.append('### ' + s if YIMU_LINE.match(s) else s)
        text = '\n\n'.join(out)
        assert_clean(text, '道教义枢卷%d' % k)
        if not text.startswith('　') and '### ' not in text:
            raise SystemExit('!! 道教义枢卷%d 未识别出义目标题' % k)
        chapters.append(('%02d' % k, '道教义枢 卷%s' % DJYS_NUM[k],
                         DJYS_YIMU[k], text, k))
        sys.stderr.write('  卷%d 剥校记 %d 条\n' % (k, notes))
    return chapters


CN = '〇一二三四五六七八九'


def cn_num(k):
    if k < 10:
        return CN[k]
    if k == 10:
        return '十'
    if k < 20:
        return '十' + CN[k % 10]
    tens = CN[k // 10] + '十'
    return tens + (CN[k % 10] if k % 10 else '')


def excerpt(text, cap=32):
    body = re.sub(r'^###.*$', '', text, flags=re.M).strip()
    first = re.split(r'(?<=。)', body.split('\n')[0])[0]
    return first if len(first) <= cap else first[:cap] + '…'


# ── 落盘 ────────────────────────────────────────────────
def fm(title, summary, weight, tags, show_toc=True, kind=None):
    lines = ['---', 'title: "%s"' % title, 'date: %s' % DATE]
    if kind:
        lines.append('kind: "%s"' % kind)
    lines += ['weight: %s' % weight, 'tags: [%s]' % ', '.join('"%s"' % t for t in tags),
              'draft: true', 'summary: "%s"' % summary,
              'showToc: %s' % ('true' if show_toc else 'false'),
              'tocOpen: false', 'ShowShareButtons: false', '---', '', '']
    return '\n'.join(lines)


def write_book(rel, title, summary, weight, tags, body_note, chapters):
    d = os.path.join(BASE, rel)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, '_index.md'), 'w', encoding='utf-8') as f:
        f.write(fm(title, summary, weight, tags, show_toc=False, kind='book')
                + body_note + '\n')
    total = 0
    for name, ctitle, csummary, text, order in chapters:
        with open(os.path.join(d, name + '.md'), 'w', encoding='utf-8') as f:
            f.write(fm(ctitle, csummary, order, tags) + text + '\n')
        total += len(HZ.findall(text))
    print('✓ %-34s %2d 篇  %6d 汉字' % (rel, len(chapters), total))
    return total


BOOKS = [
    ('alchemy/baopuzi-waipian', '抱朴子外篇', 44, ['道家', '抱朴子'],
     '葛洪撰，论时政得失、人事臧否，与《抱朴子内篇》相对的儒家治世之言。'
     '据维基文库整理本收录（繁体，明卢舜治校本系统，五十二篇全）。',
     '《抱朴子外篇》五十二卷，按卷分篇收录。葛洪自序谓「内篇二十卷，外篇五十卷」，'
     '此本篇数与自序相符，末二卷为《重言》《自叙》。\n\n'
     '与四库全书本逐字对校，异文均系四库异体字形（樸/朴、絕/絶、說/説）与版本异文，'
     '整理本无缺文；《广譬》篇另有两条格言为四库本所无，此本存之。',
     parse_baopuzi_waipian),
    ('classics/hekuanzi', '鹖冠子', 47, ['道家'],
     '战国黄老道家要籍，十九篇。旧题楚人鹖冠子撰，言道德而杂刑名兵法。'
     '据维基文库整理本收录（繁体）。',
     '《鹖冠子》十九篇全。《汉书·艺文志》列于道家，《隋志》以下皆作三卷，'
     '宋陆佃为之作注亦十九篇。\n\n'
     '与四库全书本逐字对校，93.29% 全同，差异均为四库异体字形（廝/厮、眾/衆、略/畧），'
     '整理本无缺文。本次只收正文，不收陆佃注。',
     parse_hekuanzi),
    ('classics/wunengzi', '无能子', 48, ['道家'],
     '唐光启年间隐者撰，三卷，明老庄自然之旨而杂以释氏之说。'
     '据维基文库整理本收录（繁体），今存二十三篇。',
     '《无能子》三卷，今存二十三篇：卷上六篇（阙第六）、卷中九篇（阙第五）、'
     '卷下八篇（阙第七、第九、第十）。阙篇系底本原阙，非本站失收。',
     parse_wunengzi),
    ('classics/daojiao-yishu', '道教义枢', 49, ['道家'],
     '唐孟安排集，道教教义类书，以三十七义条贯道门义理。'
     '据维基文库《正统道藏》太平部整理本收录（繁体），十卷存九卷。',
     '《道教义枢》十卷，底本《正统道藏》太平部本原缺第六卷，'
     '卷五《三乘义第十八》亦原缺，今存九卷三十三义。每卷首列义目，'
     '各义分「义曰」「释曰」两层。\n\n'
     '底本原讹一律存照不改：卷二署「青漢道士孟安排集」（他卷均作「青溪」）、'
     '卷五「二觀義十七」与卷七「五道義二十四」脱「第」字。',
     parse_daojiao_yishu),
]


def main():
    check_only = '--check' in sys.argv
    grand = 0
    for rel, title, weight, tags, summary, note, fn in BOOKS:
        chapters = fn()
        if check_only:
            n = sum(len(HZ.findall(c[3])) for c in chapters)
            print('· %-34s %2d 篇  %6d 汉字 (未落盘)' % (rel, len(chapters), n))
            grand += n
            continue
        grand += write_book(rel, title, summary, weight, tags, note, chapters)
    print('合计 %d 汉字' % grand)


if __name__ == '__main__':
    main()
