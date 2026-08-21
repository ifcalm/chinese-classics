# -*- coding: utf-8 -*-
"""樂府詩集·清洗。剝維基標記，保留正文與郭茂倩解題小註。

原則同 scripts/wenxuan/wx_clean.py（見 memory verification-blindspots #1）：
**絕不設「未知模板整塊刪」的兜底**，未登記的模板一律留內容並記名，收工斷言為零。

本書比《文選》乾淨：22 種模板、括號全配平、`<ref>` 僅 1 處。要當心的是缺字：
`{{PUA|}}` **參數為空**，不含任何字形信息，只能作 □ 挂賬。
"""
import re
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'wenxuan'))
from wx_clean import scan_braces, replace_braces, split_top   # 掃描工具共用

PUA = []      # {{PUA|}} 挂賬：私用區缺字，參數為空，無字形信息
QMARK = []    # {{？|字形描述}} 挂賬：以文字描述字形，存形

NOTE_S, NOTE_E = '\x01', '\x02'

DROP_WHOLE = ('Textquality', 'PD-old', '檢索', 'footer', 'Footer',
              'Col-begin', 'Col-break', 'Col-end', '正体化', '正體化',
              '唐朝作品', '南北朝作品', '北宋作品', '西晉作品', '漢朝作品')
UNKNOWN = {}


#
# 源本手誤修復：卷五十七有 `《史記}}{{ProperNoun|樂書》`——
# `{{ProperNoun|史記}}` 的開括號丟失、`樂書` 的又未閉合，令該頁結尾深度為 1。
# 括號一錯位，其後所有 scan_braces 深度計數全亂（實測該卷 68 處 ProperNoun 漏掉 58 處）。
# 只去標記、不增刪漢字。
SRC_FIX = [('《史記}}{{ProperNoun|樂書》', '《史記樂書》')]


def clean(t, page=''):
    for a, b in SRC_FIX:
        t = t.replace(a, b)
    assert len(re.findall(r'\{\{', t)) == len(re.findall(r'\}\}', t)), \
        '%s 大括號不配平，先修源本手誤再清洗' % page

    # 保護解題小註（{{*|古坤字。}}、{{*|一解}} 之類），免得被末尾兜底拆開
    t = replace_braces(t, r'\{\{\*\|', lambda s: NOTE_S + s + NOTE_E)

    # header / header2 / Collection header 整塊剝
    t = replace_braces(t, r'\{\{\s*[Cc]ollection\s+header\s*(?=[|}])', lambda s: '')
    t = replace_braces(t, r'\{\{\s*[Hh]eader2?\s*(?=[|}])', lambda s: '')

    # 缺字
    def pua(s):
        PUA.append(page); return '□'          # ⚠ 占位符不得含漢字（見 wx_clean 坑 3）
    t = replace_braces(t, r'\{\{PUA\s*(?=[|}])', pua)

    def qm(s):
        QMARK.append((page, s.strip())); return '〔' + s.strip() + '〕'
    t = replace_braces(t, r'\{\{？\|', qm)

    # 異文 {{另|挂|對}}：取正文所用的首參，異文棄（站內不做異文層）
    t = replace_braces(t, r'\{\{另\|', lambda s: split_top(s)[0])

    # 取內容型
    t = replace_braces(t, r'\{\{YL\|', lambda s: s)
    t = replace_braces(t, r'\{\{ProperNoun\|', lambda s: s)

    for name in DROP_WHOLE:
        t = replace_braces(t, r'\{\{\s*' + re.escape(name) + r'\s*(?=[|}])',
                           lambda s: '')

    # 字詞轉換
    t = re.sub(r'-\{A\|zh-hans:[^;]*;zh-hant:([^}]*)\}-', r'\1', t)
    t = re.sub(r'-\{([^}]*)\}-', r'\1', t)

    # 連結
    t = re.sub(r'\[\[[Cc]ategory:[^\]]*\]\]', '', t)
    t = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', t)

    # HTML
    t = re.sub(r'</?onlyinclude>', '', t)
    t = re.sub(r'</?poem>', '', t)
    t = re.sub(r'<br\s*/?>', '\n', t)
    t = re.sub(r'<ref[^>]*>.*?</ref>', '', t, flags=re.S)
    t = re.sub(r'__[A-Z]+__', '', t)          # __TOC__ 等魔術字

    # 未登記模板：留內容並記名，絕不整塊刪
    for s, e, inner in reversed(scan_braces(t, r'\{\{')):
        name = split_top(inner)[0].strip()
        UNKNOWN[name] = UNKNOWN.get(name, 0) + 1
        t = t[:s] + inner + t[e:]
    return t
