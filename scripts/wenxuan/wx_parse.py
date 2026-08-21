# -*- coding: utf-8 -*-
"""昭明文選·解析。清洗後的文本 → 卷/篇結構 + 經註分層。

**層級**：源本各卷用 1–4 級標題不等（實測 33 頁用 1-2 級、16 頁 1-3 級、
8 頁 1-4 級、4 頁只有 2 級）。故不寫死層級，按標題樹處理：
**最深的、自身帶正文的節點即為「篇」**，祖先標題併入篇題（如
「古詩一十九首·行行重行行」）。

**經註分層**：正文作普通段落，李善註作引用塊。
⚠ 與河上公章句相反（那裡經文入引用塊、註作正文）——因為那本書的本體是註，
被註的經是引文；而《文選》的本體是正文，李善註是附加的註疏。讀者要讀的是賦與詩。
"""
import re
from wx_clean import NOTE_S, NOTE_E, BLK_S, BLK_E

HEAD = re.compile(r'^(=+)\s*(.*?)\s*=+\s*$')


def split_notes(seg):
    """把一段文字切成 [(kind, text)]，kind ∈ {'body','note'}。"""
    out, i, cur = [], 0, ''
    while i < len(seg):
        ch = seg[i]
        if ch in (NOTE_S, BLK_S):
            end = NOTE_E if ch == NOTE_S else BLK_E
            j = seg.find(end, i + 1)
            j = len(seg) if j < 0 else j
            if cur.strip():
                out.append(('body', cur))
            cur = ''
            note = seg[i + 1:j].strip()
            if note:
                out.append(('note', note))
            i = j + 1
        else:
            cur += ch; i += 1
    if cur.strip():
        out.append(('body', cur))
    return out


def render(lines):
    """篇正文行 → markdown。正文作段落，註作引用塊。"""
    blocks = []
    for raw in lines:
        s = raw.strip()
        if not s:
            continue
        s = re.sub(r'^[:*#;]+', '', s)          # wiki 縮排/列表標記
        s = s.replace('　　', '').strip()   # 全角首行縮進（站內慣例不留）
        if not s:
            continue
        for kind, text in split_notes(s):
            text = text.strip()
            if not text:
                continue
            if kind == 'body':
                blocks.append(text)
            else:
                blocks.append('> ' + text.replace('\n', ' '))
    # 合併相鄰引用塊為一塊，讀起來不至於碎
    merged = []
    for b in blocks:
        if b.startswith('> ') and merged and merged[-1].startswith('> '):
            merged[-1] += '\n> ' + b[2:]
        else:
            merged.append(b)
    return '\n\n'.join(merged).strip() + '\n'


def parse_page(text):
    """→ [(篇題, markdown)]，篇題為祖先標題以 · 連綴。"""
    lines = text.split('\n')
    stack = []            # [(level, title)]，篇題只取 3 級及以下
    buf, cur_path = [], None
    out = []

    def flush():
        if cur_path is None:
            return
        body = render(buf)
        if body.strip():
            out.append((cur_path, body))

    for ln in lines:
        m = HEAD.match(ln)
        if m:
            lvl, title = len(m.group(1)), m.group(2).strip()
            title = re.sub(r'[' + NOTE_S + NOTE_E + BLK_S + BLK_E + r']', '', title)
            title = re.sub(r"'''|''", '', title).strip()   # 粗體標記不入篇題
            if not title:
                continue
            flush(); buf = []
            while stack and stack[-1][0] >= lvl:
                stack.pop()
            stack.append((lvl, title))
            # 1、2 級是卷級類目（賦甲/京都上/詩庚），不入篇題；
            # 若本頁最深只到 2 級，則該級即篇題，保留最深一層。
            deep = [t for lv, t in stack if lv >= 3]
            cur_path = '·'.join(deep) if deep else stack[-1][1]
        else:
            buf.append(ln)
    flush()

    # 祖先若已被更深的篇覆蓋，且自身正文很短（多為題解註），併入首個子篇
    return out
