# -*- coding: utf-8 -*-
"""科技門類·解析。清洗後文本 → [(篇題, markdown)]。

**體例**（與《文選》正文/李善註、《樂府》詩/解題同構）：
- `==標題==` 切篇；三級以下標題併入篇題，以 `·` 連。
- `{{*|…}}` 古註（哨兵 \\x01…\\x02）：獨佔一段時作引用塊，夾在句中時作圓括號夾註。
- `:` 縮進行是原書之註（《四民月令》崔寔自註），作引用塊。

⚠ **註必須在全文上切，不能逐行判斷**：《齊民要術》每篇開頭那條引書註動輒
橫跨七八個自然段（`{{*|《周書》曰…\\n\\n《世本》曰…\\n\\n…}}`）。逐行看，
起哨兵落在第一行、止哨兵落在末行，兩邊都配不上對，結果是首行吐出一個孤零的
「（」、末行吐出一個「）」，中間幾段裸奔——正文沒丟，但讀起來是壞的。
"""
import re

NOTE_S, NOTE_E = '\x01', '\x02'
HEAD = re.compile(r'^(=+)\s*(.*?)\s*=+\s*$')
NOTE = re.compile(NOTE_S + '(.*?)' + NOTE_E, re.S)
PB = '\x05'          # 註內段界的臨時替身：躲開 render 的空行切段


def _line(s):
    s = re.sub(r'^\s*[:*#;]+', '', s.strip()).strip()
    s = re.sub(r'^[△○●▲]\s*', '', s)
    return s.replace('　　', '').strip()


def _quote(text):
    """多段內容 → 引用塊（段間留空引用行，渲染時仍是一塊）。"""
    ps = [_line(x) for x in re.split(r'\n\s*\n|' + PB, text) if _line(x)]
    return '\n> \n'.join('> ' + p.replace('\n', ' ') for p in ps)


def render(text):
    out = []
    for para in re.split(r'\n\s*\n', text):
        if not para.strip():
            continue
        m = re.fullmatch(r'\s*' + NOTE_S + r'(.*)' + NOTE_E + r'\s*', para, re.S)
        if m:                                   # 整段是註 → 引用塊
            inner = m.group(1).replace(NOTE_S, '（').replace(NOTE_E, '）')
            out.append(_quote(inner))
            continue
        quote = bool(re.match(r'^\s*[:：]', para))
        s = _line(para).replace(NOTE_S, '（').replace(NOTE_E, '）')
        s = re.sub(r'\n\s*|' + PB, '', s)
        if not s:
            continue
        out.append(_quote(s) if quote else s)

    merged = []
    for b in out:
        if b.startswith('> ') and merged and merged[-1].startswith('> '):
            merged[-1] += '\n> \n' + b
        else:
            merged.append(b)
    return '\n\n'.join(merged).strip() + '\n'


def _split_notes(text):
    """把跨段的註縮成單段：段界在註內時，該註整條自成一段。"""
    out, last = [], 0
    for m in NOTE.finditer(text):
        if '\n' not in m.group(1):
            continue
        out.append(text[last:m.start()])
        # 註內的空行換成替身，否則 render 先按空行切段，這條註又被撕開
        out.append('\n\n' + NOTE_S + re.sub(r'\n\s*\n', PB, m.group(1)) +
                   NOTE_E + '\n\n')
        last = m.end()
    out.append(text[last:])
    return ''.join(out)


def parse(text, fallback):
    """→ [(篇題, markdown)]。無標題則整頁作一篇，題用 fallback。"""
    # ⚠ cur 初值取 fallback：整理本常把附註節擺在頁尾，若 cur 從 None 起，
    # 首個標題之前的正文（往往是全篇）會被整段丟掉（《人物志》曾中招）
    stack, buf, cur, out = [], [], fallback, []

    def flush():
        body = render(_split_notes('\n'.join(buf)))
        if body.strip():
            out.append((cur, body))

    for ln in text.split('\n'):
        m = HEAD.match(ln)
        if m:
            lvl, title = len(m.group(1)), m.group(2).strip()
            title = NOTE.sub(lambda x: '（%s）' % x.group(1), title).strip()
            title = re.sub(r"'''|''", '', title).strip()
            if not title:
                continue
            flush(); buf = []
            while stack and stack[-1][0] >= lvl:
                stack.pop()
            stack.append((lvl, title))
            cur = '·'.join(t for _, t in stack)
        else:
            buf.append(ln)
    flush()
    return out
