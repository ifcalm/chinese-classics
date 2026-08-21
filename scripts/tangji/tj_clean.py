# -*- coding: utf-8 -*-
"""唐人別集·剝離今人按語。

源 `poet.tang` 末尾的輯佚詩出自《全唐詩補編》（陳尚君輯校，1992），詩後綴今人
按語——徵引蔣禮鴻、項楚、劉開揚、俞平伯、孫欽善、游國恩、陶敏、顧學頡、龍榆生，
乃至《南京日報》1978 年文章。按收錄鐵律「近現代校注一律剝離」，這些須去。

**劃線處**：剝「判斷性」文字（今人姓名、按語、疑誤當作、依託俟考），留「書目性」
文字（「一作某」異文、「見《某書》卷幾」出處、宋人詩話引文）。理由：異文小注是
《全唐詩》（康熙御定）原書體例，出處標注是輯佚著錄，宋人詩話本就在收錄範圍內；
而「蔣云」「劉疑」「當刪」是二十世紀學人下的判斷。

**站內既有四家不動**：王維/李白/杜甫/白居易同源同病，但其按語塊常把王琦、嚴羽、
蘇軾（清人、宋人，本在收錄範圍）與詹鍈、吳企明（今人）揉在同一對括號裏，正則
切不開；且那四家已發布，重排編號會位移七十餘篇 URL。故只掛帳，另議。

**必須在合併全文上掃描**：源的 `paragraphs` 按句號機械切分，一條按語常被切成
三四段（「（按：…。」「…。」「）空。」），逐段判斷必漏。

**「空」是空詩佔位**：存目條（韋應物《春雪（存目）》等）剝掉按語後無詩，不收。
"""
import re

PARA = '\x01'                                   # 段落哨兵

# 今人——輯校者與其徵引的當代學人。名單取自實際落在這十三家詩後的按語。
MODERN = re.compile(
    r'(蔣[云、皆]|項[云疑皆]|劉[云疑]|劉開揚|依劉校|俞云|依俞校|孫[云疑]|孫欽善'
    r'|游國恩|廖立|李嘉言|卞孝萱|冀勤|傅璇琮|陶敏|吳白匋|王水照|川口久雄|吳企明'
    r'|市河世寧|上毛河世寧|先生|同志|教授|出版社|人民文學|《南京日報》|《文獻》'
    r'|古籍整理|一九[〇一二三四五六七八九]{2}|二〇[〇一二三四五六七八九]{2})')

# 判斷語——輯校者下的斷語，不論署名與否。書目性的「見《某書》卷幾」不在此列。
JUDGE = re.compile(
    r'(按[：:]|今按|按此|按《|疑|誤|當作|當刪|衍文|不誤|重錄|俟考|依[託托]'
    r'|姑存|姑作|姑附|未詳孰是|存目|不可解|不成句|見示|函告|見告'
    r'|原卷|缺字|模糊)')

MARK = re.compile(r'\[[一二三四五六七八九十〇○\d]+\]')   # 校記號
SUP = re.compile(r'〖[^〗]*〗')                            # 夾注
# 整塊是校記／今人注的標誌：以校記號或〖N〗開頭
LEAD = re.compile(r'^[（(]\s*(\[[一二三四五六七八九十〇○\d]+\]|〖\d+〗)')


def _outer(t):
    """→ 最外層成對（）的 [(起, 訖)]，跨段、可嵌套。"""
    out, stack = [], []
    for i, ch in enumerate(t):
        if ch in '（(':
            stack.append(i)
        elif ch in '）)' and stack:
            a = stack.pop()
            if not stack:
                out.append((a, i + 1))
    return out


def clean(paragraphs):
    """→ (正文段落, 剝離塊)。無詩則正文為空。"""
    t = PARA.join(p.strip() for p in paragraphs if p.strip())
    dropped = []
    keep, last = [], 0
    for a, b in _outer(t):
        seg = t[a:b]
        if MODERN.search(seg) or JUDGE.search(seg) or LEAD.match(seg):
            keep.append(t[last:a]); dropped.append(seg); last = b
    keep.append(t[last:])
    t = ''.join(keep)
    for pat in (SUP, MARK):
        for m in pat.finditer(t):
            dropped.append(m.group(0))
        t = pat.sub('', t)

    out = []
    for p in t.split(PARA):
        p = p.strip().lstrip('。，、；：）)').strip()
        if p and re.search(r'[一-鿿]', p):
            out.append(p)
    if not out or ''.join(out).strip('。，、；：') == '空':
        return [], dropped
    return out, dropped
