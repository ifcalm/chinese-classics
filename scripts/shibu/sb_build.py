# -*- coding: utf-8 -*-
"""史部三通與史論·落盤。清洗解析復用 `scripts/keji/kj_clean.py`、`kj_parse.py`。

落點三處：史部（政書、史論、雜史）、子部（語錄、政論、兵書）、筆記。
按四庫分類歸門，不因抓取批次而混放。

**體量**：本批是全站單批最大的一次——《通典》161.9 萬字、《文獻通考》160.5 萬、
《朱子語類》156.9 萬、《唐會要》80.9 萬。

**掛帳的簡體卷**：《通典》卷三十六、卷三十七與《日知錄》卷二十三、二十四、
二十六、二十八、二十九是簡體錄文。按鐵律簡→繁屬改字、不可為；剝掉則書有洞。
照《天工開物·磚》之例照收並掛帳——字形不作底本憑據。
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), 'keji'))
import kj_clean as C
import kj_parse as P
from kj_build import cn, vols, nums, fm

S = os.environ.get('SB_CACHE_DIR', os.path.dirname(os.path.abspath(__file__)))

CNUM = {c: i for i, c in enumerate('〇一二三四五六七八九')}


def cn2int(t):
    """中文數字 → int，支持到「三百四十八」。認不出返回 None。"""
    if not t or any(c not in '〇一二三四五六七八九十百' for c in t):
        return None
    n = cur = 0
    for c in t:
        if c == '百':
            n += (cur or 1) * 100; cur = 0
        elif c == '十':
            n += (cur or 1) * 10; cur = 0
        else:
            cur = CNUM[c]
    return n + cur


LEAD = ('序', '自序', '總序', '总序', '原序', '抄白', '提要', '目錄', '目录')


def order(book, index, skip=()):
    """按卷次排出一部書的頁序。

    ⚠ 不能用 allpages 給的字典序——那會把「卷十一」排到「卷二」前面、
    把「卷100」排到「卷2」前面。各書卷名格式又互不相同（通典作 /卷001、
    文獻通考作 /卷一百七十七、唐才子傳作 /卷10、朱子語類作 /140），
    故一律抽出數字再排；序、自序、提要之類無數字者置於卷首。
    """
    subs = [p for p in index[book][1:] if p.split('/')[-1] not in skip]
    head, body = [], []
    for p in subs:
        tail = p.split('/')[-1]
        m = re.search(r'(\d+)$', tail)
        n = int(m.group(1)) if m else cn2int(re.sub(r'^卷第?', '', tail))
        (body if n is not None else head).append((n, p))
    head.sort(key=lambda x: (x[1].split('/')[-1] not in LEAD, x[1]))
    body.sort(key=lambda x: (x[1].count('/'), x[0]))
    # 前集在後集之前：卷路徑深的按「前/後」再排一次
    body.sort(key=lambda x: (0 if '前集' in x[1] else 1 if '後集' in x[1] else 0,))
    return [p for _, p in head] + [p for _, p in body]


BOOKS = [
 # ── 史部 ───────────────────────────────────────────────────────────
 dict(root='base-data/history', slug='dong-guan-han-ji', title='东观汉记',
      author='刘珍等', dynasty='东汉', w=285, src='東觀漢記', skip=('提要',),
      summary='东汉官修当代史，与《史记》《汉书》并称「三史」，唐后散佚。（维基文库只录得明、章、和、殇四帝纪，非全书）'),
 dict(root='base-data/history', slug='da-tang-xin-yu', title='大唐新语',
      author='刘肃', dynasty='唐', w=302, src='大唐新語',
      summary='唐刘肃撰，仿《世说新语》体例记唐初至大历间朝野遗事，分匡赞、规谏等三十门。'),
 dict(root='base-data/history', slug='tang-cai-zi-zhuan', title='唐才子传',
      author='辛文房', dynasty='元', w=304, src='唐才子傳',
      summary='元辛文房撰，为唐五代诗人二百七十八人立传，附见一百二十人，唐诗研究之要籍。'),
 dict(root='base-data/history', slug='tong-dian', title='通典', author='杜佑',
      dynasty='唐', w=320, src='通典',
      summary='唐杜佑撰，凡二百卷，中国第一部典章制度通史，分食货、选举、职官、礼、乐、兵、刑、州郡、边防九门。'),
 dict(root='base-data/history', slug='tong-zhi', title='通志', author='郑樵',
      dynasty='南宋', w=330, src='通志',
      summary='南宋郑樵撰纪传体通史，二十略最为精粹，与《通典》《文献通考》并称「三通」。（维基文库只录得总序与十一卷，非全书）'),
 dict(root='base-data/history', slug='wen-xian-tong-kao', title='文献通考',
      author='马端临', dynasty='元', w=340, src='文獻通考',
      summary='元马端临撰，续杜佑《通典》而广其门类为二十四考，制度史之集大成。（维基文库录得一百六十二卷，全书三百四十八卷）'),
 dict(root='base-data/history', slug='tang-hui-yao', title='唐会要', author='王溥',
      dynasty='北宋', w=350, src='唐會要',
      summary='北宋王溥撰，凡一百卷，分门辑录唐代典章沿革，会要体之祖，多存两《唐书》所无之史料。'),
 dict(root='base-data/history', slug='ri-zhi-lu', title='日知录', author='顾炎武',
      dynasty='清', w=360, src='日知錄', refs='note',
      summary='清顾炎武撰，凡三十二卷，经义、治道、博闻三部，考据与经世之学并重，清代朴学开山。'),
 dict(root='base-data/history', slug='nian-er-shi-zha-ji', title='廿二史札记',
      author='赵翼', dynasty='清', w=370, pages=['廿二史劄記'],
      summary='清赵翼撰，以史事归纳比较见长，与钱大昕《廿二史考异》、王鸣盛《十七史商榷》并称清代三大史考。'),
 dict(root='base-data/history', slug='wen-shi-tong-yi', title='文史通义',
      author='章学诚', dynasty='清', w=380, src='文史通義',
      summary='清章学诚撰，内篇外篇论史学义例与文史流别，「六经皆史」之说出焉。'),

 # ── 子部 ───────────────────────────────────────────────────────────
 dict(root='base-data/masters', slug='wu-jing-zong-yao', title='武经总要',
      author='曾公亮、丁度', dynasty='北宋', w=12.1, src='武經總要',
      summary='北宋曾公亮等奉敕编，中国第一部官修综合性兵书，前集详制度器械，火药配方之最早记载在焉。'),
 dict(root='base-data/masters', slug='zhu-zi-yu-lei', title='朱子语类',
      author='黎靖德编', dynasty='南宋', w=24.1, src='朱子語類', stray='note',
      summary='南宋黎靖德编，凡一百四十卷，辑朱熹与门人问答语录，理学文献之渊薮，条末小字为记录者名。'),
 dict(root='base-data/masters', slug='ming-yi-dai-fang-lu', title='明夷待访录',
      author='黄宗羲', dynasty='清', w=25.1, pages=['明夷待訪錄'],
      summary='清黄宗羲撰，凡二十一篇，斥「为天下之大害者，君而已矣」，中国古代政治批判之绝响。'),

 # ── 筆記 ───────────────────────────────────────────────────────────
 dict(root='base-data/biji', slug='chao-ye-qian-zai', title='朝野佥载',
      author='张鷟', dynasty='唐', w=12, src='朝野僉載',
      summary='唐张鷟撰，记初唐至开元间朝野轶闻、酷吏与谐谑之事，多为两《唐书》采录。'),
]

ODD = re.compile(r'[�□■]')
HANRE = re.compile(r'[一-鿿]')
SIMP = '来为国无与从东车马门时会说汉铁风鸟鱼龙岁书对长义爱经实举学权'


def write_book(b, pages, index):
    if 'pages' not in b:
        b['pages'] = order(b['src'], index, b.get('skip', ()))
    d = os.path.join(b['root'], b['slug'])
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, '_index.md'), 'w', encoding='utf-8').write(
        fm(title=b['title'], weight=b['w'], kind='book',
           author=b['author'], dynasty=b['dynasty'], summary=b['summary']))
    nvol = npiece = nchar = nodd = nsimp = 0
    for vi, p in enumerate(b['pages'], 1):
        raw = pages.get(p, '')
        if not raw or re.match(r'\s*#\s*(重定向|REDIRECT)', raw, re.I):
            print('  ⚠ %s / %s 缺页或重定向' % (b['title'], p))
            continue
        txt = C.clean(C.inline(raw, pages), p, b.get('refs') == 'note',
                      b.get('stray', 'drop'))
        pieces = P.parse(txt, p.split('/')[-1])
        if not pieces:
            print('  ⚠ %s / %s 無正文' % (b['title'], p))
            continue
        nvol += 1
        vdir = os.path.join(d, '%03d' % vi)
        os.makedirs(vdir, exist_ok=True)
        open(os.path.join(vdir, '_index.md'), 'w', encoding='utf-8').write(
            fm(title=p.split('/')[-1], weight=vi))
        for j, (pt, body) in enumerate(pieces, 1):
            open(os.path.join(vdir, '%04d.md' % j), 'w', encoding='utf-8').write(
                fm(title=pt.replace('"', '”'), weight=j) + '\n' + body)
            npiece += 1
            nchar += len(HANRE.findall(body))
            nodd += len(ODD.findall(body))
            nsimp += sum(body.count(c) for c in SIMP)
    return nvol, npiece, nchar, nodd, nsimp


def main():
    pages = json.load(open(os.path.join(S, 'sbcache.json'), encoding='utf-8'))
    index = json.load(open(os.path.join(S, 'sbindex.json'), encoding='utf-8'))
    rows = []
    for b in BOOKS:
        rows.append((b['title'],) + write_book(b, pages, index))
    print('%-14s %5s %7s %10s %6s %6s' % ('书', '卷', '篇', '汉字', '缺字', '简体'))
    for t, v, p, c, o, s in rows:
        print('%-14s %5d %7d %10d %6d %6d' % (t, v, p, c, o, s))
    print('合计 %d 部 · %d 卷 · %d 篇 · %d 汉字；缺字 %d、简体 %d'
          % (len(rows), sum(r[1] for r in rows), sum(r[2] for r in rows),
             sum(r[3] for r in rows), sum(r[4] for r in rows), sum(r[5] for r in rows)))


if __name__ == '__main__':
    main()
