# -*- coding: utf-8 -*-
"""樂府詩集·解析。清洗後文本 → 卷/篇結構。

**層級**：1 級是卷題（=卷二十六·相和歌辭一=），2 級是曲調組（==相和六引==），
3 級是篇（===箜篌引（唐·李賀）===，全書 3,702 處），偶有 4 級。
篇題取 **2 級及以下**的路徑——2 級的曲調名是必要語境：全書大量篇題作「同前（沈約）」，
離了曲調名無從分辨。

**體例**：源本以 `:` 縮進標記郭茂倩的解題引書，無前綴行是詩正文。
故解題作引用塊、詩作普通段落——與《文選》正文作段落、李善註作引用塊同構。
"""
import re

HEAD = re.compile(r'^(=+)\s*(.*?)\s*=+\s*$')
NOTE_S, NOTE_E = '\x01', '\x02'


def render(lines):
    blocks = []
    for raw in lines:
        s = raw.rstrip()
        if not s.strip():
            continue
        quote = bool(re.match(r'^\s*:', s))
        s = re.sub(r'^\s*[:*#;]+', '', s).strip()
        s = s.replace('　　', '').strip()
        # 小註 {{*|一解}} 之類，就地還原為圓括號夾註，不另起塊
        s = s.replace(NOTE_S, '（').replace(NOTE_E, '）')
        if not s:
            continue
        blocks.append(('> ' + s) if quote else s)
    merged = []
    for b in blocks:
        if b.startswith('> ') and merged and merged[-1].startswith('> '):
            merged[-1] += '\n> ' + b[2:]
        else:
            merged.append(b)
    return '\n\n'.join(merged).strip() + '\n'


BRACKET = re.compile(r'^【([^】]+)】\s*(.*)$')


def parse_bracket(text):
    """卷五十八獨用另一套標記：無 `=` 標題，篇題作「【思歸引】晉·石崇」。
    全書僅此一卷（43 篇），故單列一條分支，不去污染主路徑。"""
    buf, cur, out = [], None, []

    def flush():
        if cur is None:
            return
        body = render(buf)
        if body.strip():
            out.append((cur, body))

    for ln in text.split('\n'):
        m = BRACKET.match(ln.strip())
        if m:
            flush(); buf = []
            名, 作 = m.group(1).strip(), m.group(2).strip()
            cur = 名 + ('（%s）' % 作 if 作 else '')
        else:
            buf.append(ln)
    flush()
    return out


def parse_page(text):
    """→ [(篇題, markdown)]"""
    if not any(HEAD.match(l) for l in text.split('\n')):
        return parse_bracket(text)
    stack, buf, cur, out = [], [], None, []

    def flush():
        if cur is None:
            return
        body = render(buf)
        if body.strip():
            out.append((cur, body))

    for ln in text.split('\n'):
        m = HEAD.match(ln)
        if m:
            lvl, title = len(m.group(1)), m.group(2).strip()
            title = title.replace(NOTE_S, '（').replace(NOTE_E, '）')
            title = re.sub(r"'''|''", '', title).strip()
            if not title:
                continue
            flush(); buf = []
            while stack and stack[-1][0] >= lvl:
                stack.pop()
            stack.append((lvl, title))
            deep = [t for lv, t in stack if lv >= 2]
            cur = '·'.join(deep) if deep else stack[-1][1]
        else:
            buf.append(ln)
    flush()
    return out
