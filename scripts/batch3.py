# ================= 批③ 命理组 淵海子平/滴天髓闡微/神峰通考/三命通會 =================
# (由 parse-shushu.py 通过 exec 注入执行,与批①②共用 clean/collate/write_book 等设施)
# 命理组维基文库源均为简体录文。字符转繁不用本地 OpenCC(会把「五干」误作「五幹」),
# 改取维基文库「渲染后繁体」(variant=zh-hant,其 LanguageConverter 保护干/云等歧字)。
# 缓存于 ws-render/*.html(由 fetch-render.py 预取)。三命通會另有四库本(繁体)可字校。
import html as _htmllib

WR = os.path.join(S, 'ws-render')

def _tags(s): return re.sub(r'<[^>]+>', '', s).strip()

def wsr(title):
    # 维基渲染繁体 HTML → 带 wiki 标题(==/===)的纯文本
    h = open(os.path.join(WR, title.replace('/', '__') + '.html'), encoding='utf-8').read()
    h = re.sub(r'<(style|script)\b[^>]*>[\s\S]*?</\1>', '', h)                 # 去内联CSS/JS
    h = re.sub(r'<span style="color:transparent[^"]*">[^<]*</span>', '', h)     # 注〈〉透明占位
    h = re.sub(r'<div class="mw-heading[^"]*"><h([23])[^>]*>(.*?)</h\1></div>',
               lambda m: '\n' + '=' * int(m.group(1)) + _tags(m.group(2)) + '=' * int(m.group(1)) + '\n',
               h, flags=re.S)
    h = re.sub(r'</p>|<p[^>]*>|<br[^>]*>|</?li[^>]*>|</?dd[^>]*>|</?dt[^>]*>', '\n', h)
    h = re.sub(r'<[^>]+>', '', h)
    h = _htmllib.unescape(h)
    # 丢弃 CSS 残行与站点提示行
    drop = ('.mw-parser-output', '姊妹計劃', '此文檔未完成', '一般而言，文獻應保留',
            '「來源」指存在', '注意：作品創建者', 'Public domain', 'PD-old',
            '公有領域', '在全世界都屬於', '之前出版')
    out = [l for l in h.split('\n') if not any(d in l for d in drop) and not l.strip().startswith('.')]
    return '\n'.join(out)

def wsr_slice(title, start, end=None):
    t = wsr(title)
    i = t.find(start); assert i >= 0, (title, '起点未找到', start)
    t = t[i:]
    if end:
        j = t.find(end); assert j >= 0, (title, '终点未找到', end); t = t[:j]
    return t

# 维基繁体转换器于生僻干支词仍偶将 干(天干)误作 幹(才幹之幹)。命理文中 幹≈干,
# 仅护 才幹/幹蠱/營幹/枝幹 等真幹词,余 幹→干。(三命通會取四库原繁体,干字不误,不需此修。)
_GAN_PROTECT = ['才幹', '幹蠱', '營幹', '枝幹', '幹濟', '骨幹', '能幹', '幹辦', '精幹', '幹練']
def _fix_gan(t):
    holder = {w: chr(0xE000 + i) for i, w in enumerate(_GAN_PROTECT)}
    for wpro, hc in holder.items():
        t = t.replace(wpro, hc)
    t = t.replace('幹', '干')
    for wpro, hc in holder.items():
        t = t.replace(hc, wpro)
    return t

def write_mingli_index():
    if not WRITE: return
    d = os.path.join(BASE, 'mingli'); os.makedirs(d, exist_ok=True)
    summ = '子平八字命理典籍。'
    open(os.path.join(d, '_index.md'), 'w').write(fm({
        'title': '命理', 'date': '2026-07-07', 'weight': 30, 'tags': ['术数'], 'draft': True,
        'summary': summ, 'showToc': False, 'tocOpen': False, 'ShowShareButtons': False
    }) + '\n' + summ + '\n')

# ---------- 淵海子平 ----------
def build_yuanhai():
    t = wsr_slice('淵海子平', '基礎')
    t = _fix_gan(clean(t))
    paras = to_paras(t)
    # 首「基礎」独占一行(渲染时被切开),与下句合并复原「基礎五干屬陽」
    if len(paras) >= 2 and paras[0] == '基礎':
        paras = [paras[0] + paras[1]] + paras[2:]
    write_book('yuan-hai-zi-ping', 'mingli', {
        'title': '渊海子平', 'weight': 10, 'kind': 'book',
        'summary': '旧题宋徐大升撰，明杨淙增校、李钦重编，宋祖本已佚，今传为明人合《渊海》《渊源》二书增补而成，子平（八字）命学集大成之祖本，日主、格局、六亲、女命诸论皆备。据维基文库整理本收录（简体录文，取维基繁体转换本，无善本可校，异文阙疑）。'
    }, [('渊海子平', 1, paras)])

# ---------- 滴天髓闡微 ----------
_GANZHI = set('甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥')
def _is_chart(l):
    return 2 <= len(l) <= 8 and all(c in _GANZHI for c in l)

def build_ditian():
    t = _fix_gan(clean(wsr_slice('滴天髓闡微', '==通神論==')))
    raw = [l.strip() for l in t.split('\n')]
    # 命造排盘(四柱+大运)在源中为逐个干支独占一段,合并为一行(以全角空格分隔)
    def _flush(buf):
        # 源中时柱与运首偶有粘连(如「丙子丙申」),干支皆两字,按两字重新分柱
        s = ''.join(buf)
        return '　'.join(s[i:i+2] for i in range(0, len(s), 2))
    merged, buf = [], []
    for l in raw:
        if not l:
            continue
        if _is_chart(l):
            buf.append(l); continue
        if buf:
            merged.append(_flush(buf)); buf = []
        merged.append(l)
    if buf:
        merged.append(_flush(buf))
    # 原注包作括注;任氏曰疏解独立成段;== 篇分章、=== 章作 ## 小节
    chs, cur = [], None
    for l in merged:
        m2 = re.match(r'^==([^=].*?)==$', l)
        m3 = re.match(r'^===\s*(.+?)\s*===$', l)
        if m2:
            cur = [m2.group(1), len(chs) + 1, []]; chs.append(cur); continue
        if m3:
            if cur: cur[2].append('## ' + m3.group(1))
            continue
        if l.startswith('原註：') or l.startswith('原注：'):
            l = '（' + l + '）'
        if cur:
            cur[2].append(l)
    assert len(chs) == 2, ('滴天髓篇数', [c[0] for c in chs])
    write_book('di-tian-sui', 'mingli', {
        'title': '滴天髓阐微', 'weight': 20, 'kind': 'book',
        'summary': '旧题宋京图撰、明刘基注（原注），清任铁樵疏注（阐微）。滴天髓为子平命理理气派圭臬，以天道、地道、人道统摄，任氏疏证并附大量命造实例，为清代命学名著。据维基文库整理本收录（简体录文，取维基繁体转换本），经文、刘基原注（括注）、任氏疏三层连排；命造排盘（四柱、大运）合为一行。'
    }, [(ttl, wt, paras) for ttl, wt, paras in chs])

# ---------- 神峰通考 ----------
# 维基本无章节标记,但篇目名多独占一行(說/論/賦/篇/訣/歌/類…),据此升为 ## 小节。
# 张楠自序(敘)属明人原序,保留;仅剥维基整理者近现代校注(4 条)。
_SF_TITLE = re.compile(r'^.{2,10}(說|論|賦|篇|訣|歌|經|法|類|論類|說類)$')
_SF_EDNOTE = re.compile(r'（[^（）]*(?:原文為|原文为|應為|应为|本名為|本名为|指一行所|所訂定|著有[^（）]*等書|等书。|即今)[^（）]*）')
def build_shenfeng():
    t = _fix_gan(clean(wsr_slice('神峰通考', '敘')))
    t = _SF_EDNOTE.sub('', t)
    paras = []
    for l in (x.strip() for x in t.split('\n')):
        if not l:
            continue
        if l == '敘' or (_SF_TITLE.match(l) and '，' not in l and '。' not in l and '、' not in l):
            paras.append('## ' + l)
        else:
            paras.append(l)
    write_book('shen-feng-tong-kao', 'mingli', {
        'title': '神峰通考', 'weight': 30, 'kind': 'book',
        'summary': '明张楠撰，命理名著。倡病药、盖头、动静、雕枯诸说，力辨子平旧说之谬，附诸家歌赋断诀，明代子平学要籍。据维基文库整理本收录（简体录文，取维基繁体转换本，无善本可校，异文阙疑；篇目据原目析出，整理者近现代校注已剥除）。'
    }, [('神峰通考', 1, paras)])

# ---------- 三命通會(全用四库全书本 12 卷,渲染繁体) ----------
# 维基整理本严重节录(卷五仅存23%,漏收大量格局),弃之;四库本完整但为白文无标点。
# 取渲染本:SKchar 生僻字已解析为真字(部分为字形图,取 alt 基础字),SKanchor 篇目→## 小节,
# SK notes 双行夹注(<small>)作括注。较维基文本径转能避免嵌套模板致夹注错乱、生僻字沦为□。
_SM_VAR = str.maketrans({'㸔': '看', '㑹': '會', '㧾': '總', '緫': '總', '䰟': '魂', '㫺': '昔'})
def _skimg(alt):
    m = re.match(r'\s*([㐀-鿿𠀀-𯨟])', alt)  # 字形图 alt 首字为基础字
    return m.group(1) if m else '□'
def _sanming_html(k):
    h = open(os.path.join(WR, '三命通會 (四庫全書本)__卷%02d.html' % k), encoding='utf-8').read()
    h = re.sub(r'<(style|script)\b[^>]*>[\s\S]*?</\1>', '', h)
    h = re.sub(r'<img\b[^>]*\balt="([^"]*)"[^>]*>', lambda m: _skimg(m.group(1)), h)  # SKchar字形图
    h = re.sub(r'<span id="([^"]+)"><a href="#[^"]+">.*?</a></span>', r'\n==\1==\n', h, flags=re.S)  # 篇目
    h = re.sub(r'<span style="color:transparent[^"]*">[^<]*</span>', '', h)  # 夹注〈〉占位
    h = re.sub(r'<small[^>]*>(.*?)</small>', r'（\1）', h, flags=re.S)          # 双行夹注→括注
    h = re.sub(r'<br[^>]*>|</p>|<p[^>]*>|</?dd[^>]*>|</?dt[^>]*>', '\n', h)
    h = re.sub(r'<[^>]+>', '', h)
    h = _htmllib.unescape(h)
    drop = ('.mw-parser-output', '姊妹計劃', '此文檔', '一般而言，文獻', '「來源」指', '注意：作品',
            'Public domain', '公有領域', '在全世界', '之前出版', '本作品在', '維基文庫', '<子部')
    # 末尾维基分类标签(&lt;子部…&gt;,解转义后成 <子部…>)与页尾孤立 □ 皆非正文,剥除
    h = '\n'.join(l for l in h.split('\n')
                  if not any(d in l for d in drop)
                  and not l.strip().startswith('.')
                  and l.strip() != '□')
    return h.translate(SKVAR).translate(_SM_VAR)

# 卷一至卷七已机器断句(逐块汉字保真校验),存断句稿 sanming-c<N>-punct.md,构建时径用,
# 白文重排逻辑仅用于卷八至卷十二;如此重跑 parse-shushu 不会以白文覆盖标点。
def build_sanming():
    hanzi = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二']
    chs = []
    for k in range(1, 13):
        if k <= 7:
            paras = to_paras(open(os.path.join(S, 'sanming-c%d-punct.md' % k), encoding='utf-8').read())
            chs.append(('卷' + hanzi[k-1], k, paras)); continue
        t = _sanming_html(k)
        i = t.find('==三命通會卷' + hanzi[k-1] + '==')
        assert i >= 0, ('三命通會卷名锚点未找到', k)
        t = t[i:]
        paras = []
        for l in to_paras(t):
            ls = l.replace(' ', '').replace('　', '')
            if re.fullmatch(r'##\s*三命通會卷' + hanzi[k-1], ls):
                continue
            if ls == '欽定四庫全書':
                continue
            if k > 1 and '萬民英撰' in ls:
                continue
            paras.append(l)
        chs.append(('卷' + hanzi[k-1], k, paras))
    write_book('san-ming-tong-hui', 'mingli', {
        'title': '三命通会', 'weight': 40, 'kind': 'book',
        'summary': '明万民英撰，十二卷。子平命理集大成之总汇，博采唐宋以来星命诸家格局、神煞、诗诀之说，考据宏富，为命学类书之渊薮，四库全书子部术数类著录。据四库全书本转录收录（白文，篇目仍旧，双行夹注作括注；维基整理本节录过甚故不用）。卷一至卷七为便读者，编者试加新式标点（逐字校勘保真，仅补标点未改一字），余卷仍四库白文原貌。'
    }, chs)

write_mingli_index()
build_yuanhai()
build_ditian()
build_shenfeng()
build_sanming()
