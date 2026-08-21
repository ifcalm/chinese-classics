# -*- coding: utf-8 -*-
"""科技門類·清洗。維基文庫 wikitext → 純文本（保留 == 標題 == 與註釋哨兵）。

**三個坑**（都會靜默吞正文，見 memory verification-blindspots）：

1. `{{header}}`／`{{Header2}}`／`{{Novel|…}}` 的參數裏有換行、有嵌套模板，
   用 `\\}\\}` 正則收尾會在第一個內層 `}}` 就斷開，剩下的參數殘留成正文。
   一律用括號深度掃描。
2. `<ref>` 裏是今人校記（「四庫本作…」「原作脊字下月以目替」），**連內容一起去**；
   但 `<references/>` 是自閉合標籤，若用 `<ref[^>]*>` 匹配，會從它非貪婪地吃到
   下一個 `</ref>`，把中間整段正文刪掉（《文選》卷一曾中招）。
3. `{{PUA|}}` 參數為空——私用區缺字且無字形信息，落 `□`。全書 968 處，
   《農政全書》佔 563 處；這是源本的洞，不是解析丟的。

**註釋分層**（與《文選》正文/李善註、《樂府》詩/解題同構）：
`{{*|…}}` 是古註與夾註，落引用塊或圓括號夾註；`:` 縮進行是原書之註。
"""
import html as _html
import re

NOTE_S, NOTE_E = '\x01', '\x02'      # 註釋哨兵，parse 階段再決定作塊還是夾註

# 版面／元信息模板：整塊丟棄（含參數）
JUNK = (r'header2?|Header2?|Novel|footer|PD-old|PD-|Textquality|檢索|Clear|clear'
        r'|wikipedia|see also|TOC limit|reflist|傳統漢字化|沒有作者|Authority'
        r'|sub title|另作|CJK-New-Char|Timeline|align|nowrap|Similar|similar|wwc|Novel-f'
        r'|Col-begin|Col-break|Col-end|-|ruby|Ruby|anchor|Anchor'
        r'|未完成|TextQuality|Incomplete'
        r'|十通|会要|會要|Alsosee|alsosee|edition|NoteTA|noteTA'
        r'|GFDL|PD-[A-Za-z0-9-]*|消歧義頁|消歧义页|未校订|未校訂|Disambig'
        r'|[^|}\n]{2,4}作品')


def scan_braces(t, open_re):
    """→ [(起, 訖)]，`open_re` 起始的 {{…}} 全塊，按深度配平，**跨行**。

    ⚠ 只取最外層：`{{*|…{{*|…}}…}}` 這種嵌套（《齊民要術》卷三、四、五、六）
    裏層也會被 finditer 命中，若不濾掉，替換區間互相重疊，結果是把外層的
    後半段當正文吐出來。
    """
    out = []
    for m in re.finditer(open_re, t):
        if out and m.start() < out[-1][1]:
            continue
        i, d = m.start(), 0
        while i < len(t):
            if t.startswith('{{', i):
                d += 1; i += 2
            elif t.startswith('}}', i):
                d -= 1; i += 2
                if d == 0:
                    out.append((m.start(), i)); break
            else:
                i += 1
        else:
            raise AssertionError('模板未配平：%s' % t[m.start():m.start() + 60])
    return out


def replace_braces(t, open_re, fn):
    spans = scan_braces(t, open_re)
    if not spans:
        return t
    out, last = [], 0
    for a, b in spans:
        out.append(t[last:a]); out.append(fn(t[a:b])); last = b
    out.append(t[last:])
    return ''.join(out)


def _args(block):
    """{{名|a|b}} → [a, b]，只切頂層 `|`。"""
    inner = block[2:-2]
    parts, d, cur = [], 0, []
    for ch in inner:
        if ch == '{': d += 1
        elif ch == '}': d -= 1
        if ch == '|' and d == 0:
            parts.append(''.join(cur)); cur = []
        else:
            cur.append(ch)
    parts.append(''.join(cur))
    return [p.strip() for p in parts[1:]]


def inline(t, pages):
    """展開 `{{:某頁}}` 轉錄。《農政全書》卷四整篇是轉錄的《井田攷》，
    不展開則該卷只剩一個模板殼——《樂府詩集》七卷曾因此看起來短了一半。"""
    for _ in range(40):
        m = re.search(r'\{\{:\s*([^{}|]+?)\s*\}\}', t)
        if not m:
            break
        t = t[:m.start()] + pages.get(m.group(1), '') + t[m.end():]
    return t


def _drop_orphan_close(t):
    """丟掉沒有對應 `{{` 的孤立 `}}`。

    《碧雞漫志》《滄浪詩話》的源本被機器改壞過，成片出現 `獲}}漢}}雅樂`、
    `}}唐}}武后}}時` 這種——原本是 `{{ProperNoun|漢}}`，起始標記整個掉了，
    只剩收尾。全書五十餘處，逐條寫死不現實；孤立的 `}}` 之間夾的是純正文，
    丟掉標記即得原文，屬只刪不改。
    """
    out, i, d = [], 0, 0
    while i < len(t):
        if t.startswith('{{', i):
            d += 1; out.append('{{'); i += 2
        elif t.startswith('}}', i):
            if d:
                d -= 1; out.append('}}')
            i += 2
        else:
            out.append(t[i]); i += 1
    return ''.join(out)


def _close_unclosed(t):
    """給沒有收尾的 `{{` 補上 `}}`，補在它所在自然段的末尾。

    《朱子語類》卷六、卷二十九、卷四十二各有一處 `{{*|…` 忘了收尾。不補的話
    深度掃描會一路吃到頁尾，整卷正文變成一條註。註在這書裏都是句末的記錄者名
    （`{{*|節}}`、`{{*|賀孫}}`），從不跨段，故補在段末是安全的。
    """
    st, i = [], 0
    while i < len(t):
        if t.startswith('{{', i):
            st.append(i); i += 2
        elif t.startswith('}}', i):
            if st:
                st.pop()
            i += 2
        else:
            i += 1
    for a in reversed(st):
        end = t.find('\n\n', a)
        end = len(t) if end < 0 else end
        t = t[:end] + '}}' + t[end:]
    return t


def clean(t, page='', keep_refs=False, stray='drop'):
    t = _close_unclosed(_drop_orphan_close(t))
    assert t.count('{{') == t.count('}}'), '%s 有未閉合的 {{，先修源本手誤' % page

    # ① <ref>：多數書裏是今人校記（《教坊記》是任半塘 1962 年箋訂、《農政全書》
    #    《齊民要術》是「四庫本作…」），連內容一起去；但《法書要錄》的 363 條
    #    <ref> 是竇蒙原註（「前簡校刑部員外郎竇臮撰、檢校國子司業竇蒙注定」），
    #    是唐人正文的一部分，須 keep_refs=True 轉成夾註，否則卷五卷六各丟一半。
    #    ⚠ `<references/>` 是自閉合標籤：若用 `<ref[^>]*>` 匹配，會從它非貪婪地
    #    吃到下一個 `</ref>`，把中間整段正文刪掉（《文選》卷一曾中招）。故先去它。
    t = re.sub(r'<references\s*/?>', '', t)
    t = re.sub(r'<ref(?:\s[^>]*)?/>', '', t)
    if keep_refs:
        t = re.sub(r'<ref(?:\s[^>]*)?>(.*?)</ref>',
                   lambda m: NOTE_S + m.group(1).strip() + NOTE_E, t, flags=re.S)
    else:
        t = re.sub(r'<ref(?:\s[^>]*)?>.*?</ref>', '', t, flags=re.S)
    # 源本偶有沒有起始標籤的孤立 </ref>（日知錄/卷02），丟掉即可
    t = t.replace('</ref>', '')
    assert '<ref' not in t, '%s 仍有 <ref 殘留' % page

    # ② 版面模板整塊丟
    t = replace_braces(t, r'(?i)\{\{\s*(?:%s)\s*(?=[|}])' % JUNK, lambda b: '')

    # ③ 字形類模板
    t = replace_braces(t, r'\{\{\s*PUA\s*(?=[|}])',
                       lambda b: (_args(b)[0] if _args(b) and _args(b)[0] else '□'))
    t = replace_braces(t, r'\{\{\s*僻字\s*(?=[|}])',
                       lambda b: (_args(b)[0] if _args(b) else ''))
    # {{?|⿰扌迫}} 以字形描述存形，照《劉子》〔外囗內巷〕之例保留
    t = replace_braces(t, r'\{\{\s*[?？]\s*(?=[|}])',
                       lambda b: ('〔%s〕' % _args(b)[0]) if _args(b) and _args(b)[0]
                       else '□')
    # {{另|底本字|通行字}}、{{參|…}}、{{另2|正文|校註}}：一律取首參——
    # 次參是整理者所改／所註，非底本
    # {{!|𦷺|⿱艹紝}}、{{校|良|長}} 同族：首參是底本字，次參是字形描述或校改字
    # {{**|敦|廟諱}}：首參是字，次參是「廟諱」之類的說明
    t = replace_braces(t, r'\{\{\s*(?:另2?|參|参|校|!|\*\*)\s*(?=\|)',
                       lambda b: (_args(b)[0] if _args(b) else ''))
    # {{ProperNoun|孫過庭}}、{{WavyBookMark|書斷}} 只是專名／書名的排版標記
    t = replace_braces(t, r'(?i)\{\{\s*(?:ProperNoun|WavyBookMark|PN|BookMark|ul|du)\s*(?=\|)',
                       lambda b: (_args(b)[0] if _args(b) else ''))
    for _ in range(6):
        prev = t
        t = replace_braces(t, r'\{\{\s*YL\s*(?=[|}])',
                           lambda b: (_args(b)[0] if _args(b) else ''))
        if t == prev:
            break

    t = replace_braces(t, r'(?i)\{\{\s*(?:quote|annotate)\s*(?=[|}])',
                       lambda b: (_args(b)[0] if _args(b) else ''))
    t = re.sub(r'\{\{\s*!\s*\}\}', '｜', t)          # 表格轉義的豎線

    # {{Unihan|2B3AE}} 是用碼位寫的擴展區漢字，還原成字本身
    t = replace_braces(t, r'(?i)\{\{\s*Unihan\s*(?=\|)', lambda b: (
        chr(int(_args(b)[0], 16))
        if _args(b) and re.fullmatch(r'[0-9A-Fa-f]{4,6}', _args(b)[0]) else '□'))

    # ④ 古註 {{*|…}} → 哨兵。**必須反覆做到不動點**：《齊民要術》卷三至卷六
    # 有 {{*|…{{*|…}}…}} 嵌套，掃描只取最外層，內層留在參數文本裏，一輪不盡
    for _ in range(8):
        prev = t
        t = replace_braces(t, r'\{\{\s*(?:\*|注|\^)\s*(?=[|}])',
                           # 註文本身已帶一對圓括號時剝掉，免得渲染成「（（五人））」
                           lambda b: NOTE_S + re.sub(
                               r'^（(.*)）$', r'\1',
                               '｜'.join(_args(b)).strip(), flags=re.S) + NOTE_E)
        if t == prev:
            break

    # 兜底：仍有模板殘留說明漏了一類，寧可報錯也不靜默留在正文裏
    if stray == 'note':
        # 《朱子語類》有百馀處 `{{賀孫}}`、`{{淳錄云：「…}}`——是 `{{*|` 掉了
        # `*|` 的記錄者標註，內容是正文的一部分，按註處理而非丟棄
        for _ in range(6):
            prev = t
            t = replace_braces(t, r'\{\{(?=[^*|}])',
                               lambda b: NOTE_S + b[2:-2].strip() + NOTE_E)
            if t == prev:
                break
    leftover = re.findall(r'\{\{\s*([^|}\n]{1,20})', t)
    assert not leftover, '%s 未處理的模板：%s' % (page, sorted(set(leftover))[:8])

    # ⑤ 標籤與語言轉換標記
    # <sub> 在政書裏是雙行小註（《文獻通考》8,589 處馬端臨自註、《通典》66 處
    # 杜佑自註），是正文的一部分，轉成註哨兵而非丟棄
    t = re.sub(r'<sub>(.*?)</sub>', lambda m: NOTE_S + m.group(1).strip() + NOTE_E,
               t, flags=re.S)
    t = re.sub(r'</?(?:onlyinclude|noinclude|includeonly|small|sup|sub|big|div|span|'
               r'center|poem|blockquote|u|s)[^>]*>', '', t)
    t = re.sub(r'<br\s*/?>', '\n', t)
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    # -{只}- / -{zh-hant:X}- / -{zh-hans:A;zh-hant:B}-：取繁體那支，沒有就取整體
    def _lc(m):
        body = m.group(1)
        for seg in body.split(';'):
            if seg.strip().startswith(('zh-hant', 'zh-tw', 'zh-hk')):
                return seg.split(':', 1)[1].strip()
        return re.sub(r'^[a-z-]+:', '', body).strip()
    for _ in range(4):
        prev = t
        # 起始的連字號源本偶爾誤成全形破折號（日知錄卷二十八 6 處 `—{云}-`）
        t = re.sub(r'[-—–]\{([^{}]*?)\}-', _lc, t)
        if t == prev:
            break
    t = re.sub(r'__[A-Z]+__', '', t)

    # ⑥ 表格：只留單元格文字，格式標記丟掉
    t = re.sub(r'^\{\|.*$|^\|\}.*$|^!.*$|^\|[-+].*$', '', t, flags=re.M)
    t = re.sub(r'^\|\s*(?:valign|align|colspan|rowspan)[^|]*\|?', '', t, flags=re.M)
    t = re.sub(r'^\|\s*', '', t, flags=re.M)

    # ⑦ 連結與強調
    # 分類／檔案／跨語言連結先整條去掉，否則下一條規則會把它們變成
    # 「Category:詞話」這樣的裸文字留在正文裏
    t = re.sub(r'\[\[\s*(?:Category|分類|分类|File|Image|檔案|文件)\s*:[^\[\]]*\]\]',
               '', t, flags=re.I)
    t = re.sub(r'\[\[[^\[\]|]*\|([^\[\]]*)\]\]', r'\1', t)
    t = re.sub(r'\[\[([^\[\]]*)\]\]', r'\1', t)
    t = re.sub(r'\[https?://\S+\s+([^\]]*)\]', r'\1', t)
    t = re.sub(r'\[https?://\S+\]', '', t)
    t = re.sub(r"'''|''", '', t)
    # 源本偶有沒配對的 [[（通志 35 處寫成 `[[說文解字》`），孤立的方括號丟掉
    t = t.replace('[[', '').replace(']]', '')
    t = _html.unescape(t)

    # ⑧ 行首 ■ 是源本的分條符（《原詩》111 條、《詞概》115 條），不是缺字；
    #    前一行若只是個條次序數（「一」「二」），併入該條首
    t = re.sub(r'\n\s*([一二三四五六七八九十百]+)\s*\n\s*■\s*', r'\n\n\1　', t)
    t = re.sub(r'(?m)^\s*■\s*', '', t)

    t = re.sub(r'[ \t]+\n', '\n', t)
    t = re.sub(r'\n{3,}', '\n\n', t)
    return t.strip()
