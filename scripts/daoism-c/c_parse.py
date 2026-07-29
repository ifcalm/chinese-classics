#!/usr/bin/env python3
"""道家 C 批八部解析。

统一处理：模板白名单（未登记者硬失败）、{{*s}}/{{*e}} 注块、图片剥离留图题、
道藏整理本「經名：…底本出處：…」提要行提为 summary、小型标点归一。
"""
import json, re, collections

HZ = re.compile(r'[一-鿿㐀-䶿\U00020000-\U0003FFFF]')
# 允许出现的模板；未登记者硬失败，绝不静默放行
KNOWN = {'Novel', 'Novel-f', 'footer', 'Header', 'header', 'PD-old', '宋朝作品', '元朝作品',
         '唐朝作品', '金朝作品', '清朝作品', 'YL', '*s', '*e', '*', '太上感應篇注',
         'missing image', 'center', 'box', '~', 'Album header', 'Textquality',
         'textquality', 'PUA'}
# 道藏整理本卷首提要行
ABSTRACT = re.compile(r'^\s*經名[：:].*?$', re.M)
# 小型标点变体（U+FE50 系）与半角/异形标点归一；只动标点，不动汉字
SMALL = str.maketrans({'﹐': '，', '﹑': '、', '﹕': '：', '﹔': '；', '︰': '：',
                       '﹖': '？', '．': '。', '“': '「', '”': '」',
                       '﹟': '·'})
# 半角标点归一必须放在剥标记之后，否则会把 .png / File: 打坏
HALF = {'.': '。', ':': '：', '!': '！', ',': '，'}
# 明确的 OCR 误植（拉丁字母落在标点位），逐处见校勘日志；存疑者不改
OCR = {'乎7': '乎？', '洞庭J': '洞庭，', '五門下j': '五門下。'}


def check_templates(a, book):
    seen = {m.group(1).strip() for m in re.finditer(r'\{\{\s*([^|}\n:#]+)', a)}
    bad = seen - KNOWN
    if bad:
        raise SystemExit('!! %s 出现未登记模板: %s' % (book, sorted(bad)))


def clean(t):
    """通用清洗：模板、图片、链接、格式标记。图片只剥图，图题留作阙图说明。"""
    # CBETA/电子佛典页码标记（如 pb:CK-KZ_JY082_01p044a>）系数字化残留，整体删
    t = re.sub(r'pb:[A-Za-z0-9_\-]+>', '', t)
    # 组字式缺字 [田x夀] → IDS 存形，不猜真字
    t = re.sub(r'\[([一-鿿])x([一-鿿])\]', lambda m: '⿰' + m.group(1) + m.group(2), t)
    # -{X}- 字词转换标记留内容（武经七书例）
    t = re.sub(r'-\{([^{}]*)\}-', r'\1', t)
    for a, b in OCR.items():
        t = t.replace(a, b)
    # 符文缺字占位
    t = t.replace('＠', '□').replace('@', '□')
    # 私用区码位与半角 ? 均系底本缺字，按站内想尔注例存阙，不猜字
    t = re.sub(r'[\uE000-\uF8FF\U000F0000-\U000FFFFD]', '□', t)
    t = re.sub(r'(?<=[一-鿿])\?(?=[一-鿿，。、])', '□', t)
    # 连续半角空格是缺符位（青华秘文丹诀图符）
    t = re.sub(r'(?<=[一-鿿])[ ]{2,}(?=[，。」])', '□', t)
    t = t.translate(SMALL)
    t = re.sub(r'<onlyinclude>|</onlyinclude>', '', t)
    t = re.sub(r'\{\{\s*(?:Novel|Novel-f|footer|Header|header|PD-old|Album header|'
               r'Textquality|textquality|[宋元唐金清]朝作品)\s*(?:\|[^{}]*)?\}\}', '', t)
    t = re.sub(r'\{\{\s*YL\s*\|\s*([^|}]*?)\s*(?:\|[^}]*)?\}\}', r'\1', t)
    t = re.sub(r'\{\{\s*\*\s*\|\s*([^{}]*?)\s*\}\}', r'（\1）', t)
    t = re.sub(r'\{\{\s*(?:center|box|~)\s*\|\s*([^{}]*?)\s*\}\}', r'\1', t)
    t = re.sub(r'\{\{\s*missing image\s*\}\}', '〔原書有圖，底本闕〕', t)
    # PUA 是维基自标「私用区编码无法识别」，按站内想尔注例存阙，不猜字
    t = re.sub(r'\{\{\s*PUA\s*\|?[^{}]*\}\}', '□', t)
    # 图片：剥图留题（同云笈七签符图例）
    def img(m):
        parts = m.group(1).split('|')
        cap = parts[-1].strip() if len(parts) > 1 else ''
        return ('〔圖：%s〕' % cap) if cap and not re.match(r'^\d+px$', cap) else ''
    t = re.sub(r'\[\[(?:File|Image|檔案|文件):([^\]]*)\]\]', img, t)
    t = re.sub(r'\[\[[^\]|]*\|([^\]]*)\]\]', r'\1', t)
    t = re.sub(r'\[\[([^\]]*)\]\]', r'\1', t)
    t = re.sub(r'\[\[(?:Category|分類|分类):[^\]]*\]\]', '', t, flags=re.I)
    t = re.sub(r'</?(?:poem|div|span|small|center|br\s*/?)[^>]*>', '\n', t)
    t = re.sub(r'<ref[^>]*>.*?</ref>|<ref[^>]*/>', '', t, flags=re.S)
    t = re.sub(r"'''|''", '', t)
    t = re.sub(r'^\s*\{\{.*?\}\}\s*$', '', t, flags=re.M)
    # 行内孤立半角空格系源换行残留，去之（不动全角空格）
    t = re.sub(r'(?<=[一-鿿，。、；：？！」』）])[ ]+(?=[一-鿿「『（])', '', t)
    t = re.sub(r'(?<=[一-鿿])[ ]+(?=[，。、；：？！])', '', t)
    for a, b in HALF.items():
        t = re.sub(r'(?<=[一-鿿])' + re.escape(a) + r'(?=[一-鿿])', b, t)
        t = re.sub(r'(?<=[一-鿿])' + re.escape(a) + r'(?=[\n ])', b, t)
    t = re.sub(r'[ \t]+\n', '\n', t)
    return re.sub(r'\n{3,}', '\n\n', t).strip()


def paras(t):
    return [x.strip() for x in re.split(r'\n{2,}', t) if x.strip()]


def jing_zhu(t):
    """{{*s}}注{{*e}} → 经文作引用块、注作正文（同河上公章句体例）。"""
    out, pos = [], 0
    for m in re.finditer(r'\{\{\*s\}\}(.*?)\{\{\*e\}\}', t, re.S):
        for p in paras(clean(t[pos:m.start()])):
            out.append('> ' + p.replace('\n', ' '))
        out += paras(clean(m.group(1)))
        pos = m.end()
    for p in paras(clean(t[pos:])):
        out.append('> ' + p.replace('\n', ' '))
    return [x for x in out if x.strip('> ')]


def split_head(t, level):
    """按 = 级标题切段，返回 [(题, 正文)]，标题前的内容归入首个无题段。"""
    pat = re.compile(r'^%s\s*(.+?)\s*%s\s*$' % ('=' * level, '=' * level), re.M)
    ms = list(pat.finditer(t))
    out = []
    if not ms:
        return [(None, t)]
    if t[:ms[0].start()].strip():
        out.append((None, t[:ms[0].start()]))
    for i, m in enumerate(ms):
        e = ms[i + 1].start() if i + 1 < len(ms) else len(t)
        out.append((m.group(1), t[m.end():e]))
    return out
