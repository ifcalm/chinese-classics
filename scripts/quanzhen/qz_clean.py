# -*- coding: utf-8 -*-
"""全真批·底本清洗。

底本性质(2026-07-31 判定)：维基文库这批《正统道藏》「繁体整理本」实为殆知阁系
简体文本经 MediaWiki zh-hant/zh-tw 词表转换而成——殆知阁同处作「内存胜心」「网络贯
天珠」「循环受苦」「卜算子」，维基对应作「記憶體」「網路」「迴圈」「蔔運算元」，
且两边连游离拉丁字「灭心忘尽o」都一致。故殆知阁即转换前上游，可作词表讹字的证人；
但它是简体，无法为「余/餘」一类繁体字形作证，那类一律存照不改。
"""
import re

# ── 词表级繁化讹字回改（殆知阁逐处核出转换前读法，见 docs/collation-log.md） ──
WORDFIX = [
    ('蔔運算元', '卜算子'),   # 词牌「卜算子」被当成 CS 术语 operator
    ('運算元', '算子'),
    ('迴圈', '循環'),         # loop
    ('記憶體', '內存'),       # memory
    ('網路', '網絡'),         # network
    ('蔔', '卜'),             # 「卜筭」「拆起卜字」；全批无「蘿蔔」义
    # U+FFFD 是解码失败标记，绝不会是底本内容。重陽全真集/教化集的藏頭、拆字、攢字诗
    # 以此标缺字；殆知阁同处作 □，且两边占位符「连续游程」序列匹配 93.3%、
    # 总数 1178 vs 1172，故回改为 □ 存阙（同东坡全集 {{PUA}}→□ 例）。
    ('\ufffd', '□'),
]

DROP_TMPL = ('Header', 'Novel', 'footer', 'PD-old', 'Textquality', 'album header',
             '檢索', 'Col-begin', 'Col-break', 'Col-end', 'Otheruses', 'edition',
             '元朝作品', '金朝作品', '莊子注', '悟真篇注')


def _tmpl(t):
    """模板处理：留年号、夹注转括注、缺图存目，其余整块删。"""
    t = re.sub(r'\{\{\s*YL\s*\|([^|}]*)\}\}', r'\1', t)                 # 年号留字面
    t = re.sub(r'\{\{\s*missing image\s*\}\}', '〔原書有圖，底本闕〕', t, flags=re.I)
    t = re.sub(r'\{\{\s*\?\s*\}\}', '□', t)                              # 源自标缺字
    t = re.sub(r'\{\{\s*\*\s*\|([^{}]*)\}\}', r'（\1）', t)              # 夹注
    for _ in range(4):                                                   # 模板可嵌套，由内向外剥
        t = re.sub(r'\{\{\s*(?:%s)\b[^{}]*\}\}' % '|'.join(DROP_TMPL), '', t, flags=re.I)
        t = re.sub(r'\{\{[^{}]*\}\}', '', t)
    return t


def clean(t, wordfix=True):
    t = re.sub(r'\[\[\s*(Category|分類|分类)\s*:[^\]]*\]\]', '', t, flags=re.I)
    t = re.sub(r'^\s*(Category|分類|分类)\s*:.*$', '', t, flags=re.I | re.M)
    t = re.sub(r'<ref[^>]*>.*?</ref>', '', t, flags=re.S)
    t = re.sub(r'<ref[^>]*/>', '', t)
    t = _tmpl(t)
    t = re.sub(r'</?(onlyinclude|includeonly|noinclude|poem|div|span|center|br\s*/?)[^>]*>', '', t)
    t = re.sub(r'<[^>]+>', '', t)
    t = re.sub(r"'''+", '', t)
    t = re.sub(r'\[\[[^\]|]*\|([^\]]*)\]\]', r'\1', t)
    t = re.sub(r'\[\[([^\]]*)\]\]', r'\1', t)
    t = re.sub(r'-\{([^{}]*)\}-', r'\1', t)                              # 字词转换标记留内容
    if wordfix:
        for a, b in WORDFIX:
            t = t.replace(a, b)
    return t


# ── 整理者校注：#N 锚 + 卷末 #N 说明行 + 「注：(…)」行，同云笈七签/道教义枢例剥去 ──
RE_ANCHOR = re.compile(r'#\d+')
RE_NOTELN = re.compile(r'^\s*#\d+\s*\S')
RE_EDNOTE = re.compile(r'^\s*注[：:]\s*[（(]')
# 整理者自述式校语：（錄入者據律後添詞牌－南鄉子）、*（…錄入者…）
RE_TYPIST = re.compile(r'[*＊]?[（(][^）)]*(錄入者|录入者|整理者|原缺|原脫|據律|据律)[^）)]*[）)]')


def strip_editor(lines):
    out, dropped = [], []
    for ln in lines:
        s = ln.strip().replace('　', '')
        if RE_NOTELN.match(s) or RE_EDNOTE.match(s):
            dropped.append(s)
            continue
        s2 = RE_TYPIST.sub('', ln)
        if s2 != ln:
            dropped.append(ln)
        out.append(RE_ANCHOR.sub('', s2))
    return out, dropped


def norm_lines(t):
    """整块文本 → 去空白的行序列（保留行内全角空格作诗行分栏）。"""
    out = []
    for ln in t.split('\n'):
        s = ln.strip().strip('　').strip()
        if s:
            out.append(s)
    return out
