# -*- coding: utf-8 -*-
"""科技門類·落盤。base-data/keji/{組}/{書}/…

站內原有十四門類無一容得下算經、農書、工藝與譜錄，故新立「科技」一門，
下分算學／農政／工藝／譜錄四組（組目錄同《佛學》之例：目錄有 _index.md
而無 kind: book，故識為 collection 而非書）。

**卷次序**：allpages 給的是字典序（卷十一排在卷二前），一律按此處寫死的
順序落盤；`vols()` 生成的中文數字序列即卷次序。

**《武經總要》本批未收**：其前集卷一（6,971 字）是簡體錄文（簡繁比 98:2），
按鐵律簡→繁屬改字、不可為；且該書四庫分類屬子部兵家，不在本門。另議。
"""
import json, os, re, sys, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kj_clean as C
import kj_parse as P

S = os.environ.get('KJ_CACHE_DIR', os.path.dirname(os.path.abspath(__file__)))
DEST = 'base-data/keji'
CN = '一二三四五六七八九十'


def cn(n):
    if n <= 10:
        return CN[n - 1]
    if n < 20:
        return '十' + CN[n - 11]
    if n % 10 == 0:
        return CN[n // 10 - 1] + '十'
    return CN[n // 10 - 1] + '十' + CN[n % 10 - 1]


def vols(book, fmt, a, b):
    return ['%s/%s' % (book, fmt % cn(i)) for i in range(a, b + 1)]


def nums(book, fmt, a, b):
    return ['%s/%s' % (book, fmt % i) for i in range(a, b + 1)]


GROUPS = [
    ('suanxue',   '算学', 1),
    ('nongzheng', '农政', 2),
    ('gongyi',    '工艺', 3),
    ('pulu',      '谱录', 4),
]

BOOKS = [
 # ── 算學 ───────────────────────────────────────────────────────────
 dict(g='suanxue', slug='jiu-zhang-suan-shu', title='九章算术', author='佚名（刘徽注）',
      dynasty='汉', w=101, pages=['九章算術'],
      summary='中国现存最早的数学专著之一，算经十书之首，凡九章二百四十六问，附三国刘徽注。'),
 dict(g='suanxue', slug='zhou-bi-suan-jing', title='周髀算经', author='佚名（赵爽注）',
      dynasty='汉', w=102, pages=['周髀算經'],
      summary='算经十书之一，言盖天说与四分历法，载勾股定理之最早表述，附赵爽注。'),
 dict(g='suanxue', slug='shu-shu-ji-yi', title='数术记遗', author='徐岳', dynasty='东汉',
      w=103, pages=['數術記遺'],
      summary='旧题东汉徐岳撰、北周甄鸾注，记大数命名与十四种算具，珠算之名首见于此。'),
 dict(g='suanxue', slug='hai-dao-suan-jing', title='海岛算经', author='刘徽', dynasty='三国',
      w=104, pages=['海島算經'],
      summary='三国刘徽撰，以重差术测望海岛山城之高远，凡九问，中国测量学之祖。'),
 dict(g='suanxue', slug='sun-zi-suan-jing', title='孙子算经', author='佚名',
      dynasty='南北朝', w=105, pages=['孫子算經'],
      summary='算经十书之一，凡三卷，「物不知数」题即后世大衍求一术、韩信点兵之源。'),
 dict(g='suanxue', slug='wu-cao-suan-jing', title='五曹算经', author='甄鸾', dynasty='北周',
      w=106, pages=['五曹算經/田曹', '五曹算經/兵曹', '五曹算經/集曹',
                    '五曹算經/倉曹', '五曹算經/金曹'],
      summary='北周甄鸾撰，为田、兵、集、仓、金五曹官吏所设算题，凡五卷。'),
 dict(g='suanxue', slug='wu-jing-suan-shu', title='五经算术', author='甄鸾', dynasty='北周',
      w=107, pages=['五經算術'],
      summary='北周甄鸾撰，专释五经及《论语》《左传》中的算数名物与数字，凡二卷。'),
 dict(g='suanxue', slug='ji-gu-suan-jing', title='缉古算经', author='王孝通', dynasty='唐',
      w=108, pages=['緝古算經'],
      summary='唐王孝通撰，算经十书之殿，凡二十问，首以三次方程解土功、勾股问题。'),

 # ── 農政 ───────────────────────────────────────────────────────────
 dict(g='nongzheng', slug='fan-sheng-zhi-shu', title='氾胜之书', author='氾胜之',
      dynasty='西汉', w=201, pages=['氾勝之書'],
      summary='西汉氾胜之撰，中国最早的农学专著，原书佚，此为后人辑本，述区田法与溲种法。'),
 dict(g='nongzheng', slug='si-min-yue-ling', title='四民月令', author='崔寔', dynasty='东汉',
      w=202, pages=['四民月令'], drop_sec=['記'],
      summary='东汉崔寔撰，按月记士农工商四民之事，汉代田庄经济的实录。原书佚，此为辑本。'),
 dict(g='nongzheng', slug='qi-min-yao-shu', title='齐民要术', author='贾思勰',
      dynasty='北魏', w=203,
      pages=['齊民要術/序', '齊民要術/自序', '齊民要術/雜說'] +
            vols('齊民要術', '卷第%s', 1, 10) + ['齊民要術/後序'],
      summary='北魏贾思勰撰，中国现存最完整最早的综合性农书，凡十卷九十二篇，述耕种、树艺、畜牧、酿造之法。'),
 dict(g='nongzheng', slug='chen-fu-nong-shu', title='农书', author='陈旉', dynasty='南宋',
      w=204, pages=['農書/序', '農書/卷上', '農書/卷中', '農書/卷下',
                    '農書/後序 (陳旉)', '農書/後序 (洪興祖)', '農書/跋', '農書/跋 (江綱)'],
      summary='南宋陈旉撰，中国第一部论述南方水田农事的农书，凡三卷，倡地力常新壮之说。'),
 dict(g='nongzheng', slug='can-shu', title='蚕书', author='秦观', dynasty='北宋',
      w=205, pages=['農書/蠶書'],
      summary='北宋秦观撰，中国现存最早的蚕桑专著，述种变、时食、缫车诸法，凡一卷。'),
 dict(g='nongzheng', slug='nong-sang-ji-yao', title='农桑辑要', author='大司农司',
      dynasty='元', w=206,
      pages=['農桑輯要/序', '農桑輯要/中書省致江浙行省印造《農桑輯要》咨文'] +
            vols('農桑輯要', '卷之%s', 1, 2) +
            ['農桑輯要/論九穀風土時月及苧麻木綿'] + vols('農桑輯要', '卷之%s', 3, 7),
      summary='元大司农司官修，采摭前代农书刊定，凡七卷，元代颁行天下的劝农之书。'),
 dict(g='nongzheng', slug='wang-zhen-nong-shu', title='王祯农书', author='王祯', dynasty='元',
      w=207, pages=vols('王禎農書', '卷%s', 1, 22),
      summary='元王祯撰，兼论南北农事，《农桑通诀》《百谷谱》《农器图谱》三部分俱备，农器图谱尤为前所未有。'),
 dict(g='nongzheng', slug='nong-zheng-quan-shu', title='农政全书', author='徐光启',
      dynasty='明', w=208, pages=nums('農政全書', '卷%02d', 1, 60),
      summary='明徐光启撰、陈子龙等增订，凡六十卷，集古代农学之大成，兼收泰西水法与救荒本草。'),

 # ── 工藝 ───────────────────────────────────────────────────────────
 dict(g='gongyi', slug='ying-zao-fa-shi', title='营造法式', author='李诫', dynasty='北宋',
      w=301, pages=['營造法式/劄子', '營造法式/序', '營造法式/看詳'] +
                   vols('營造法式', '第%s卷', 1, 28),
      summary='北宋李诫奉敕编修，中国现存最完整的古代建筑技术专书，凡三十四卷，立材分制度为营造之准。'),
 dict(g='gongyi', slug='tian-gong-kai-wu', title='天工开物', author='宋应星', dynasty='明',
      w=302, index_page='天工開物',
      summary='明宋应星撰，中国古代最全面的工艺百科，凡十八卷，上自谷物纺织，下迄五金火器，皆图说其法。'),

 # ── 譜錄 ───────────────────────────────────────────────────────────
 dict(g='pulu', slug='qin-jing', title='禽经', author='旧题师旷', dynasty='先秦',
      w=401, pages=['禽經'],
      summary='旧题春秋师旷撰、晋张华注，中国最早的鸟类专著，记禽鸟形性名类。'),
 dict(g='pulu', slug='cha-jing', title='茶经', author='陆羽', dynasty='唐', w=402,
      pages=['茶經/一之源', '茶經/二之具', '茶經/三之造', '茶經/四之器', '茶經/五之煮',
             '茶經/六之飲', '茶經/七之事', '茶經/八之出', '茶經/九之略', '茶經/十之圖'],
      summary='唐陆羽撰，世界第一部茶书，凡三卷十篇，源、具、造、器、煮、饮、事、出、略、图俱全。'),
 dict(g='pulu', slug='cha-lu', title='茶录', author='蔡襄', dynasty='北宋', w=403,
      pages=['茶錄'],
      summary='北宋蔡襄撰，上篇论茶，下篇论茶器，宋代点茶法之要籍。'),
 dict(g='pulu', slug='li-zhi-pu', title='荔枝谱', author='蔡襄', dynasty='北宋', w=404,
      pages=['荔枝譜'],
      summary='北宋蔡襄撰，中国现存最早的荔枝专著，凡七篇，记闽中荔枝品第与栽制之法。'),
 dict(g='pulu', slug='luo-yang-mu-dan-ji', title='洛阳牡丹记', author='欧阳修',
      dynasty='北宋', w=405, pages=['洛陽牡丹記 (歐陽修)'],
      summary='北宋欧阳修撰，花释名、花品序、风俗记三篇，中国最早的牡丹专著。'),
 dict(g='pulu', slug='da-guan-cha-lun', title='大观茶论', author='赵佶', dynasty='北宋',
      w=406, pages=['大觀茶論'],
      summary='宋徽宗赵佶撰，凡二十篇，自产制至点验，论宋代团茶最为详备。'),
 dict(g='pulu', slug='tang-shuang-pu', title='糖霜谱', author='王灼', dynasty='南宋',
      w=407, pages=['糖霜譜'],
      summary='南宋王灼撰，中国第一部制糖专著，凡七篇，记遂宁伞山蔗糖之种、造、用。'),
 dict(g='pulu', slug='ju-lu', title='橘录', author='韩彦直', dynasty='南宋', w=408,
      pages=['橘錄'],
      summary='南宋韩彦直撰，中国现存最早的柑橘专著，凡三卷，别二十七种、详种治之法。'),
 dict(g='pulu', slug='jun-pu', title='菌谱', author='陈仁玉', dynasty='南宋', w=409,
      pages=['菌譜'],
      summary='南宋陈仁玉撰，中国最早的食用菌专著，记台州十一种菌之形味与产候。'),
 dict(g='pulu', slug='bei-yuan-gong-cha-lu', title='宣和北苑贡茶录', author='熊蕃',
      dynasty='南宋', w=410, pages=['宣和北苑貢茶錄', '宣和北苑貢茶錄/北苑別錄'],
      summary='南宋熊蕃撰、熊克增补，记建安北苑贡茶之沿革品目；附赵汝砺《北苑别录》，详其采制纲次。'),
]

ODD = re.compile(r'[�□■]')
HANRE = re.compile(r'[一-鿿]')
SIMP = '来为国无与从东车马门时会说汉铁风鸟鱼龙岁书对长义爱经实举砖'


def fm(**kw):
    out = ['---']
    for k, v in kw.items():
        out.append('%s: "%s"' % (k, v) if isinstance(v, str) else '%s: %s' % (k, v))
    return '\n'.join(out + ['---']) + '\n'


def index_layout(pages, book):
    """《天工開物》的目錄頁是兩級列表：`*[[/乃粒第一]]` 是卷，`**[[/稻]]` 是篇。"""
    vols, cur = [], None
    for ln in pages[book].split('\n'):
        m = re.match(r'^(\*+)\s*\[\[/([^\]|]+)', ln)
        if not m:
            continue
        name = m.group(2).strip()
        if len(m.group(1)) == 1:
            cur = (name, [])
            vols.append(cur)
        elif cur:
            cur[1].append(name)
    # 卷頁本身載宋應星的卷首序（「宋子曰……」，十九卷各百餘字），是正文不是導航，
    # 故置於本卷之首；自序等一級條目下無篇，則自成一卷一篇
    return [(v, [v] + ps) for v, ps in vols]


def write_book(b, pages, root):
    d = os.path.join(root, b['slug'])
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, '_index.md'), 'w', encoding='utf-8').write(
        fm(title=b['title'], weight=b['w'], kind='book',
           author=b['author'], dynasty=b['dynasty'], summary=b['summary']))

    if b.get('index_page'):
        plan = [(v, ['%s/%s' % (b['index_page'], p) for p in ps])
                for v, ps in index_layout(pages, b['index_page'])]
    else:
        plan = [(p.split('/')[-1], [p]) for p in b['pages']]

    nvol = npiece = nchar = nodd = nsimp = 0
    for vi, (vtitle, ps) in enumerate(plan, 1):
        pieces = []
        for p in ps:
            raw = pages.get(p, '')
            if re.match(r'\s*#\s*(重定向|REDIRECT)', raw, re.I):
                continue          # 《天工開物》「曲蘖第十七」是到「麴蘖第十七」的重定向
            txt = C.clean(C.inline(raw, pages), p)
            got = P.parse(txt, p.split('/')[-1])
            for sec in b.get('drop_sec', []):        # 剝離今人所加的節（如 1921 年校記）
                got = [x for x in got if x[0].split('·')[0] != sec]
            pieces += got
        if not pieces:
            print('  ⚠ %s / %s 無正文' % (b['title'], vtitle))
            continue
        nvol += 1
        vdir = os.path.join(d, '%03d' % vi)
        os.makedirs(vdir, exist_ok=True)
        open(os.path.join(vdir, '_index.md'), 'w', encoding='utf-8').write(
            fm(title=vtitle, weight=vi))
        for j, (pt, body) in enumerate(pieces, 1):
            open(os.path.join(vdir, '%03d.md' % j), 'w', encoding='utf-8').write(
                fm(title=pt.replace('"', '”'), weight=j) + '\n' + body)
            npiece += 1
            nchar += len(HANRE.findall(body))
            nodd += len(ODD.findall(body))
            nsimp += sum(body.count(c) for c in SIMP)
    return nvol, npiece, nchar, nodd, nsimp


def main():
    pages = json.load(open(os.path.join(S, 'kjcache.json'), encoding='utf-8'))
    os.makedirs(DEST, exist_ok=True)
    open(os.path.join(DEST, '_index.md'), 'w', encoding='utf-8').write(
        fm(title='科技', subtitle='算学 · 农政 · 工艺 · 谱录', weight=10,
           summary='历代算经、农书、工艺与谱录之书。'))
    for g, name, w in GROUPS:
        gd = os.path.join(DEST, g)
        os.makedirs(gd, exist_ok=True)
        open(os.path.join(gd, '_index.md'), 'w', encoding='utf-8').write(
            fm(title=name, weight=w))

    rows = []
    for b in BOOKS:
        rows.append((b['title'],) + write_book(b, pages, os.path.join(DEST, b['g'])))
    print('%-14s %5s %6s %9s %5s %5s' % ('书', '卷', '篇', '汉字', '缺字', '简体'))
    for t, v, p, c, o, s in rows:
        print('%-14s %5d %6d %9d %5d %5d' % (t, v, p, c, o, s))
    print('合计 %d 部 · %d 卷 · %d 篇 · %d 汉字；缺字 %d、简体 %d'
          % (len(rows), sum(r[1] for r in rows), sum(r[2] for r in rows),
             sum(r[3] for r in rows), sum(r[4] for r in rows), sum(r[5] for r in rows)))


if __name__ == '__main__':
    main()
