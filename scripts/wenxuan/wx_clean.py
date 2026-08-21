# -*- coding: utf-8 -*-
"""昭明文選·清洗。剝維基標記，保留正文與李善注，剔除胡克家考異。

原則(見 memory verification-blindspots #1)：**絕不設「未知模板整塊刪」的兜底**。
未登記的模板一律留內容並記名，收工斷言未登記項為零。

踩過的三個坑，改動前先讀：
 1. `<ref[^>]*>` 會連 `<references/>` 一起當開標籤，從它非貪婪吃到下一個 `</ref>`，
    中間整段正文被當考異刪掉（實測卷1 吞掉《東都賦》開頭）。標籤必須寫精確。
 2. 別清「獨佔一行的 `}}`」：`{{header2}}` 的閉合括號正是獨佔一行，刪掉它會令
    header 未閉合、深度掃描跑到頁尾，整頁被剝光（實測留存率 0%）。
 3. 考異節標題有三種寫法，只認 `{{+|文選考異}}` 會漏掉粗體與標題形態；
    但判定必須「恰好相等」——序頁的《文選考異序》是胡克家序文本身，屬正文。
"""
import re

# ── 成對標記掃描（處理嵌套） ─────────────────────────────
def scan_braces(t, open_re):
    """返回 [(start, end, inner)]，end 為 '}}' 之後。跳過嵌套內層。"""
    out, i = [], 0
    pat = re.compile(open_re)
    while True:
        m = pat.search(t, i)
        if not m:
            break
        depth, j = 1, m.end()
        while j < len(t) and depth:
            if t.startswith('{{', j):
                depth += 1; j += 2
            elif t.startswith('}}', j):
                depth -= 1; j += 2
            else:
                j += 1
        out.append((m.start(), j, t[m.end():j - 2]))
        i = j
    return out


def replace_braces(t, open_re, fn):
    """自後向前替換，避免位移。fn(inner) -> str"""
    for s, e, inner in reversed(scan_braces(t, open_re)):
        t = t[:s] + fn(inner) + t[e:]
    return t


def split_top(inner):
    """按頂層 | 切參數，忽略嵌套模板內的 |"""
    parts, depth, cur, i = [], 0, '', 0
    while i < len(inner):
        if inner.startswith('{{', i):
            depth += 1; cur += '{{'; i += 2
        elif inner.startswith('}}', i):
            depth -= 1; cur += '}}'; i += 2
        elif inner[i] == '|' and depth == 0:
            parts.append(cur); cur = ''; i += 1
        else:
            cur += inner[i]; i += 1
    parts.append(cur)
    return parts


# ── 缺字 ────────────────────────────────────────────────
SK = []   # {{SKchar|N}} 挂賬：缺字庫編號，無碼點無 IDS，無從回推字形


def unihan(inner):
    cp = inner.strip()
    try:
        return chr(int(cp, 16))
    except ValueError:
        return '〔' + cp + '〕'


def bang(inner):
    """{{!|字形|IDS}}：首參為字（可能是 {{Unihan|碼點}}）。無參則為半角豎線。"""
    if not inner.strip():
        return '|'
    first = split_top(inner)[0].strip()
    return replace_braces(first, r'\{\{Unihan\|', unihan)


# ── 考異剔除 ────────────────────────────────────────────
KAOYI = re.compile(r'袁本|茶陵本|各本|案：|陳云|何校|尤本|五臣作|善作|此校|傳寫')


def _bare(line):
    """剝去標記後的行文本，用於判定考異節標題。"""
    x = re.sub(r'\{\{\*\|([^{}]*)\}\}', r'\1', line)
    x = re.sub(r'\{\{\+\|([^{}]*)\}\}', r'\1', x)
    x = re.sub(r'^[;:*#\s]+', '', x)          # 行首 wiki 列表/縮排標記
    return x.replace('=', '').replace("'''", '').strip()


def strip_kaoyi(t):
    """剔除四種形態的胡克家考異：<ref>、考異節、卷末獨立塊注。"""
    n = [0, 0, 0]
    # 坑 1：標籤寫精確，且先移除 <references/> 免得被當開標籤
    t2 = re.sub(r'<references\s*/?>', '', t)
    t2 = re.sub(r'<ref\s[^>]*/>', '', t2)              # <ref name="x"/> 自閉合
    t2, k = re.subn(r'<ref(?:\s[^>]*)?>.*?</ref>', '', t2, flags=re.S)
    n[0] = k
    assert '</ref>' not in t2, '仍有未配對的 </ref>：源本 <ref> 未閉合，須人工核'

    # 坑 3：考異節按整行判定，切到下一個標題行或頁尾
    lines, keep, i = t2.split('\n'), [], 0
    while i < len(lines):
        if _bare(lines[i]) == '文選考異':
            n[1] += 1
            i += 1
            while i < len(lines) and not lines[i].startswith('='):
                i += 1
        else:
            keep.append(lines[i]); i += 1
    t2 = '\n'.join(keep)

    # 獨立成行的 {{*|...}} 且含考異措辭 → 考異塊；否則是題解注，留
    for s, e, inner in reversed(scan_braces(t2, r'\{\{\*\|')):
        ls = t2.rfind('\n', 0, s) + 1
        if not t2[ls:s].strip() and KAOYI.search(inner):
            t2 = t2[:s] + t2[e:]; n[2] += 1
    return t2, n


# ── 主清洗 ──────────────────────────────────────────────
DROP_WHOLE = ('Textquality', 'PD-old', '檢索', 'footer', 'Main', 'main',
              'Novel', 'Novel-f', 'novel', 'novel-f', '南北朝作品', '唐朝作品')
UNKNOWN = {}

# 注的哨兵：先把要保留的注轉成不含大括號的記號，免得被末尾兜底拆開
NOTE_S, NOTE_E, BLK_S, BLK_E = '\x01', '\x02', '\x03', '\x04'


def clean(t, page=''):
    t, kao = strip_kaoyi(t)

    # 保護李善注
    t = replace_braces(t, r'\{\{\*\|', lambda s: NOTE_S + s + NOTE_E)
    t = re.sub(r'\{\{\*s\}\}', BLK_S, t)
    t = re.sub(r'\{\{\*e\}\}', BLK_E, t)

    # 整塊剝（坑 2：header 的閉合括號獨佔一行，靠深度掃描配平，不可另行清理）
    t = replace_braces(t, r'\{\{\s*[Hh]eader2?\s*(?=[|}])', lambda s: '')
    t = replace_braces(t, r'\{\{\s*[Nn]ovel-?f?\s*(?=[|}])', lambda s: '')

    # 缺字
    t = replace_braces(t, r'\{\{!\|', bang)
    t = re.sub(r'\{\{!\}\}', '|', t)
    t = replace_braces(t, r'\{\{Unihan\|', unihan)
    t = replace_braces(t, r'\{\{\?\|', lambda s: s.strip())        # 只有 IDS，存形

    def skchar(s):
        # ⚠ 占位符不得含漢字，否則等於往正文增字，零改字校驗的子序列判定會失敗
        SK.append((page, s.strip())); return '□'
    t = replace_braces(t, r'\{\{SKchar\|', skchar)

    # 取內容型
    t = replace_braces(t, r'\{\{ProperNoun\|', lambda s: s)
    t = replace_braces(t, r'\{\{YL\|', lambda s: s)
    t = replace_braces(t, r'\{\{參\|', lambda s: split_top(s)[0])
    t = replace_braces(t, r'\{\{校\|', lambda s: split_top(s)[0])
    t = replace_braces(t, r'\{\{-\|', lambda s: s)

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
    t = re.sub(r'</?poem>', '', t)
    t = re.sub(r'<br\s*/?>', '\n', t)
    t = re.sub(r'</?div[^>]*>', '', t)
    t = re.sub(r'</?sub>', '', t)

    # 註中註：扁平化併入母註（只丟標記不丟字）
    t = replace_braces(t, r'\{\{\*\|', lambda s: s)

    # 未登記模板：留內容並記名，絕不整塊刪
    for s, e, inner in reversed(scan_braces(t, r'\{\{')):
        name = split_top(inner)[0].strip()
        UNKNOWN[name] = UNKNOWN.get(name, 0) + 1
        t = t[:s] + inner + t[e:]
    return t, kao
