# -*- coding: utf-8 -*-
"""子部諸子八部·清洗 + 解析 + 落盤。

八部同批走一套管線，各書差異全收在 BOOKS 表裡（頁面集、篇題來源、weight、書目說明）。

原則同 scripts/wenxuan/wx_clean.py（見 memory verification-blindspots #1）：
**絕不設「未知模板整塊刪」的兜底**，未登記的模板留內容並記名，收工斷言為零。

踩過的坑（文選那輪）已內建防護：
 - `<ref[^>]*>` 會連 `<references/>` 一起當開標籤 → 標籤寫精確；
 - 不清「獨佔一行的 `}}`」；
 - 占位符不得含漢字（零改字校驗的子序列判定會失敗）。
"""
import json, os, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'wenxuan'))
from wx_clean import scan_braces, replace_braces, split_top

CACHE = os.environ.get('ZZ_CACHE', 'zzcache.json')
DEST = 'base-data/masters'
NOTE_S, NOTE_E = '\x01', '\x02'
UNKNOWN = {}
PUA = []      # {{PUA|}} 挂賬：私用區缺字，參數為空，無字形信息

CN = '一二三四五六七八九十'


def cn(n):
    if n <= 10: return CN[n - 1]
    if n < 20: return '十' + CN[n - 11]
    a, b = divmod(n, 10)
    return CN[a - 1] + '十' + (CN[b - 1] if b else '')


# slug, 書名, 作者, 朝代, weight, 頁面集, summary
BOOKS = [
    dict(slug='chunqiu-fanlu', title='春秋繁露', author='董仲舒', dynasty='西汉', weight=21.1,
         pages=['春秋繁露/卷%02d' % i for i in range(1, 18)],
         vol=lambda t: '卷' + cn(int(t.rsplit('卷', 1)[1])),
         summary='西汉·董仲舒撰，十七卷八十二篇（今存七十九篇），以阴阳五行说解《春秋》公羊义，'
                 '天人感应、大一统之说所本，汉代经学与政治思想的枢纽之作。'
                 '据维基文库《春秋繁露》整理本收录（繁体，有标点）；玄 10 不避讳、无馆臣痕迹，非四库系。'),
    dict(slug='bai-hu-tong', title='白虎通', author='班固 等', dynasty='东汉', weight=21.3,
         pages=['白虎通/卷%02d' % i for i in range(1, 11)],
         vol=lambda t: '卷' + cn(int(t.rsplit('卷', 1)[1])),
         summary='东汉建初四年白虎观经学会议的结论汇编，章帝亲裁、班固奉诏撰集，十卷四十三篇，'
                 '逐条论爵、号、谥、社稷、礼乐、封禅诸典，是今文经学的官方定论。'
                 '据维基文库《白虎通》整理本收录（繁体，有标点）；玄 17 不避讳、无馆臣痕迹，非四库系。'),
    dict(slug='xin-xu', title='新序', author='刘向', dynasty='西汉', weight=21.2,
         pages=['新序/雜事/卷' + c for c in ['一', '二', '三', '亖', '五']] +
               ['新序/刺奢', '新序/節士', '新序/義勇', '新序/善謀/卷上', '新序/善謀/卷下'],
         vol=None,
         # 源本各頁 header 的 section/title 欄不統一（有的填「雜事」有的填「新序卷第一」），
         # 十卷篇題按通行本結構寫死
         titles=['雜事第一', '雜事第二', '雜事第三', '雜事第四', '雜事第五',
                 '刺奢第六', '節士第七', '義勇第八', '善謀第九', '善謀第十'],
         summary='西汉·刘向采辑先秦至汉初史事传说编成，十卷，分杂事、刺奢、节士、义勇、善谋五类，'
                 '与《说苑》同为刘向编纂的故事体说理集。'
                 '据维基文库《新序》整理本收录（繁体，有标点）；无馆臣痕迹，非四库系。'),
    dict(slug='qian-fu-lun', title='潜夫论', author='王符', dynasty='东汉', weight=21.4,
         pages=['潛夫論/卷' + c for c in ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']],
         vol=lambda t: '卷' + t.rsplit('卷', 1)[1],
         summary='东汉·王符撰，十卷三十六篇，隐居著书不欲彰名，故曰潜夫。'
                 '论衰世之弊、务本抑末、考绩明选，与《论衡》《昌言》并称东汉三大批判之作。'
                 '据维基文库《潜夫论》整理本收录（繁体，有标点）；玄弘胤不避讳、无馆臣痕迹，非四库系。'
                 '整理本另有附录四篇（后汉书本传、历代序跋、书目著录、佚文），系整理者辑录非王符原书，未收。'),
    dict(slug='shen-jian', title='申鉴', author='荀悦', dynasty='东汉', weight=21.5,
         pages=['申鑒/%d' % i for i in range(1, 6)] +
               ['申鑒/注申鑒序', '申鑒/何孟春序', '申鑒/王鏊序', '申鑒/跋申鑒注後'],
         vol=None,
         # 四篇序跋的 header section 欄有兩篇同填「申鑒注序」，故篇題寫死
         titles=['政體第一', '時事第二', '俗嫌第三', '雜言上第四', '雜言下第五',
                 '注申鑒序', '何孟春序', '王鏊序', '跋申鑒注後'],
         summary='东汉·荀悦撰，五篇，献帝时作，申重前鉴以匡时政，论政体、时事、俗嫌、杂言。'
                 '据维基文库《申鉴》整理本收录（繁体，有标点），含明黄省曾注与明人序跋四篇；'
                 '玄弘不避讳、无馆臣痕迹，非四库系。黄省曾注作引用块与正文分层。'),
    dict(slug='ren-wu-zhi', title='人物志', author='刘劭', dynasty='三国', weight=22.1,
         pages=['人物志/自序'] + ['人物志/' + c for c in
                ['九徵', '體別', '流業', '材理', '材能', '利害', '接識', '英雄',
                 '八觀', '七繆', '效難', '釋爭']],
         vol=None,
         summary='三国魏·刘劭撰，三卷十二篇，据形质情性辨识人材，中国唯一一部系统的人才学专著，'
                 '西凉刘昞为之作注。据维基文库《人物志》整理本收录（繁体，有标点）；'
                 '玄弘不避讳、无馆臣痕迹，非四库系。刘昞注作引用块与正文分层；'
                 '整理本另有今人所加白话注释十三条，按只收古代典籍之例剥离未收。'),
    dict(slug='liu-zi', title='刘子', author='刘昼', dynasty='北齐', weight=22.2,
         pages=['劉子/%02d' % i for i in range(1, 31)],
         vol=None,
         summary='北齐·刘昼撰，杂糅儒道、兼取名法，论修身治国凡五十五篇（今本存目不一），'
                 '旧亦题刘勰撰，四库已辨其非。据维基文库《刘子》整理本收录（繁体，有标点）；'
                 '无馆臣痕迹，非四库系。'),
    dict(slug='chang-duan-jing', title='长短经', author='赵蕤', dynasty='唐', weight=23.1,
         pages=['長短經/卷' + c for c in ['一', '二', '三', '四', '五', '六', '七', '八', '九']],
         vol=lambda t: '卷' + t.rsplit('卷', 1)[1],
         summary='唐·赵蕤撰，九卷六十四篇，纵横捭阖之术与王霸经权之道，历叙君臣、政体、'
                 '将略、地形、霸纪，世称《反经》。据维基文库《长短经》整理本收录（繁体，有标点）；'
                 '玄 74、弘 40 不避讳、无馆臣痕迹，非四库系。'),
]

DROP_WHOLE = ('Textquality', 'PD-old', '檢索', 'footer', 'Footer', 'Novel', 'novel',
              'Novel-f', 'SKQS header', '四部叢刊頁眉', '漢朝作品', '唐朝作品',
              '南北朝作品', '三國作品')


def clean(t, page=''):
    # 保護古註 {{*|...}}（申鑒的黃省曾註、人物志的劉昞註）
    t = replace_braces(t, r'\{\{\*\|', lambda s: NOTE_S + s + NOTE_E)
    # header 系整塊剝（篇題另從 section 欄取）
    t = replace_braces(t, r'\{\{\s*[Hh]eader2?\s*(?=[|}])', lambda s: '')
    for name in DROP_WHOLE:
        t = replace_braces(t, r'\{\{\s*' + re.escape(name) + r'\s*(?=[|}])', lambda s: '')
    # 缺字：{{PUA|}} 參數為空無字形（同樂府詩集），{{!|字形|IDS}} 取首參，{{?|IDS}} 存形
    def pua(s):
        PUA.append(page); return '□'          # ⚠ 占位符不得含漢字
    t = replace_braces(t, r'\{\{PUA\s*(?=[|}])', pua)
    t = replace_braces(t, r'\{\{!\|', lambda s: split_top(s)[0].strip() or '|')
    t = re.sub(r'\{\{!\}\}', '|', t)
    t = replace_braces(t, r'\{\{\?\|', lambda s: '〔' + s.strip() + '〕')
    # 異文/參校：取正文所用的首參
    t = replace_braces(t, r'\{\{另\|', lambda s: split_top(s)[0])
    t = replace_braces(t, r'\{\{參\|', lambda s: split_top(s)[0])
    t = replace_braces(t, r'\{\{\s*reflist\s*(?=[|}])', lambda s: '')

    # 字詞轉換
    t = re.sub(r'-\{A\|zh-hans:[^;]*;zh-hant:([^}]*)\}-', r'\1', t)
    t = re.sub(r'-\{A\|([^}]*)\}-', r'\1', t)
    t = re.sub(r'-\{([^}]*)\}-', r'\1', t)
    # 連結
    t = re.sub(r'\[\[[Cc]ategory:[^\]]*\]\]', '', t)
    t = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', t)
    # HTML：<ref> 是今人白話注釋（人物志 13 條），按只收古代典籍之例剝離
    t = re.sub(r'<references\s*/?>', '', t)
    t = re.sub(r'<ref\s[^>]*/>', '', t)
    t = re.sub(r'<ref(?:\s[^>]*)?>.*?</ref>', '', t, flags=re.S)
    t = re.sub(r'<ref(?:\s[^>]*)?>.*', '', t)      # 源本未閉合者截至行尾
    t = re.sub(r'</?onlyinclude>|</?poem>|</?div[^>]*>|</?includeonly>', '', t)
    t = re.sub(r'<br\s*/?>', '\n', t)
    t = re.sub(r'__[A-Z]+__', '', t)
    # 註中註：扁平化併入母註（只丟標記不丟字，同 wenxuan）
    t = replace_braces(t, r'\{\{\*\|', lambda s: s)
    # 未登記模板：留內容並記名
    for s, e, inner in reversed(scan_braces(t, r'\{\{')):
        name = split_top(inner)[0].strip()
        UNKNOWN[name] = UNKNOWN.get(name, 0) + 1
        t = t[:s] + inner + t[e:]
    return t


def header_section(raw):
    """從 header 的 section / title 欄取篇題（無 == 標題的書靠它）。"""
    # ⚠ 用括號掃描而非 `\n\}\}` 正則：申鑒的 header 整個寫在一行上，
    # 要求換行收尾會匹配失敗、篇題退化成頁名尾段（實測落成「1」「2」）
    sp = scan_braces(raw, r'\{\{\s*[Hh]eader2?\s*(?=[|}])')
    if not sp:
        return ''
    inner = sp[0][2]
    for f in ('section', 'title'):
        mm = re.search(r'\|?\s*' + f + r'\s*=\s*([^|\n]*)', inner)
        if mm:
            v = mm.group(1).strip()
            v = re.sub(r'\{\{[^{}]*\}\}', '', v)
            v = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', v)
            v = re.sub(r"'''|''|-\{|\}-|\[\[\.\./\]\]", '', v).strip()
            if v and v not in ('../', ''):
                return v
    return ''


HEAD = re.compile(r'^(=+)\s*(.*?)\s*=+\s*$')
# 今人所加的節：註釋、校勘記、參考文獻之類，非古籍正文
MODERN = re.compile(r'^(註釋|注釋|注释|校勘記|校勘记|參考|参考|附註|附注|說明|说明)$')


def render(lines):
    blocks = []
    for raw in lines:
        s = raw.strip()
        if not s:
            continue
        s = re.sub(r'^[:*#;]+', '', s).replace('　　', '').strip()
        if not s:
            continue
        # 古註就地切出：註前正文成段，註作引用塊
        parts, cur = [], ''
        i = 0
        while i < len(s):
            if s[i] == NOTE_S:
                j = s.find(NOTE_E, i + 1)
                j = len(s) if j < 0 else j
                if cur.strip(): parts.append(('b', cur))
                note = s[i + 1:j].strip()
                if note: parts.append(('n', note))
                cur = ''; i = j + 1
            else:
                cur += s[i]; i += 1
        if cur.strip(): parts.append(('b', cur))
        # 古註常嵌在句讀之前（人物志劉昞註尤甚），直接切開會把「。」「？」
        # 孤零零留在下一段開頭。把註後緊跟的句讀回貼到註前正文末尾。
        for i in range(len(parts) - 1):
            if parts[i][0] == 'n' and parts[i + 1][0] == 'b':
                m = re.match(r'^([。，、；：？！」』）]+)(.*)$', parts[i + 1][1])
                if m:
                    for j in range(i - 1, -1, -1):
                        if parts[j][0] == 'b':
                            parts[j] = ('b', parts[j][1] + m.group(1)); break
                    parts[i + 1] = ('b', m.group(2))
        for k, v in parts:
            if not v.strip(): continue
            blocks.append(v if k == 'b' else '> ' + v.replace('\n', ' '))
    merged = []
    for b in blocks:
        if b.startswith('> ') and merged and merged[-1].startswith('> '):
            merged[-1] += '\n> ' + b[2:]
        else:
            merged.append(b)
    return '\n\n'.join(merged).strip() + '\n'


def parse_page(text, fallback_title):
    """有 == 標題則按標題切篇；否則整頁一篇，篇題用 header 的 section。"""
    lines = text.split('\n')
    if not any(HEAD.match(l) for l in lines):
        body = render(lines)
        return [(fallback_title, body)] if body.strip() else []
    out, buf, cur = [], [], fallback_title
    for ln in lines:
        m = HEAD.match(ln)
        if m:
            # ⚠ cur 初值取 fallback_title：整理本常把 ===註釋=== 之類擺在頁尾，
            # 若 cur 從 None 起，首個標題之前的正文（往往是全篇）會被整段丟掉
            # （實測人物志/自序、九徵、新序/雜事/卷亖 三頁產出 0 篇）。
            b = render(buf)
            if b.strip(): out.append((cur, b))
            title = re.sub(r"'''|''", '', m.group(2)).strip()
            title = title.replace(NOTE_S, '（').replace(NOTE_E, '）')
            cur, buf = title, []
        else:
            buf.append(ln)
    b = render(buf)
    if b.strip(): out.append((cur, b))
    # 今人所加的注釋/校勘節，按只收古代典籍之例剝離
    return [(t, b) for t, b in out if not MODERN.match(t)]


def fm(**kw):
    out = ['---']
    for k, v in kw.items():
        out.append(f'{k}: "{v}"' if isinstance(v, str) else f'{k}: {v}')
    out.append('---')
    return '\n'.join(out) + '\n'


def main():
    pages = json.load(open(CACHE, encoding='utf-8'))
    report = []
    for bk in BOOKS:
        bdir = os.path.join(DEST, bk['slug'])
        os.makedirs(bdir, exist_ok=True)
        open(os.path.join(bdir, '_index.md'), 'w', encoding='utf-8').write(
            fm(title=bk['title'], kind='book', date='2026-08-21', weight=bk['weight'],
               tags='["子部"]'.replace('"', '"'), draft='true',
               author=bk['author'], dynasty=bk['dynasty'], summary=bk['summary'],
               showToc='false', tocOpen='false', ShowShareButtons='false'))
        n_piece = 0
        if bk['vol']:                      # 分卷書：卷 → 目錄，篇 → 檔
            for vi, pt in enumerate(bk['pages'], 1):
                raw = pages[pt]
                pieces = parse_page(clean(raw, pt), header_section(raw) or pt.split('/')[-1])
                if not pieces: continue
                vdir = os.path.join(bdir, '%02d' % vi)
                os.makedirs(vdir, exist_ok=True)
                open(os.path.join(vdir, '_index.md'), 'w', encoding='utf-8').write(
                    fm(title=bk['vol'](pt), weight=vi))
                for j, (t, b) in enumerate(pieces, 1):
                    open(os.path.join(vdir, '%02d.md' % j), 'w', encoding='utf-8').write(
                        fm(title=t, weight=j) + '\n' + b)
                n_piece += len(pieces)
        else:                              # 不分卷：篇直接落在書目錄下
            k = 0
            fixed = bk.get('titles')
            for pi, pt in enumerate(bk['pages']):
                raw = pages[pt]
                fb = fixed[pi] if fixed else (header_section(raw) or pt.split('/')[-1])
                pieces = parse_page(clean(raw, pt), fb)
                if fixed: pieces = [(fb, b) for _, b in pieces]
                for t, b in pieces:
                    k += 1
                    open(os.path.join(bdir, '%02d.md' % k), 'w', encoding='utf-8').write(
                        fm(title=t, weight=k) + '\n' + b)
            n_piece = k
        report.append((bk['title'], n_piece))
    return report


if __name__ == '__main__':
    rep = main()
    for t, n in rep: print('   %-8s %3d 篇' % (t, n))
    print('八部合計 %d 篇' % sum(n for _, n in rep))
    print('未登記模板:', UNKNOWN if UNKNOWN else '無 ✓')
