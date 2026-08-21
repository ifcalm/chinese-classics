# -*- coding: utf-8 -*-
"""小學補全與集部詩文評·落盤。

兩處落點：
- `base-data/xiaoxue/`：門類原僅《說文解字》一部，補訓詁三種與韻書一種。
- `base-data/literature/shihua/`：集部下新設「詩文評」一組（目錄有 _index.md
  而無 kind: book，故識為 collection）。站內原有的《文心雕龍》《人間詞話》
  仍留在集部平鋪處**不動**——挪位置會位移已發布的 URL，得不償失。

清洗與解析復用 `scripts/keji/kj_clean.py`、`kj_parse.py`。

**未收**：
- 《蕙風詞話》況周頤（1859–1926）卒於民國，屬近現代，按鐵律不收。
- 《廣韻》維基本只有「上平聲卷」且標着 {{未完成}}，實存 1,650 字（全書約三十萬），
  是殘頁不是書。《字彙》0 字、《廣雅》371 字、《溫公續詩話》3 字，同理。
- 《康熙字典》五百餘頁皆字書條目，每頁近百字、零標點，不合按 #32 之例。
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), 'keji'))
import kj_clean as C
import kj_parse as P
from kj_build import cn, vols, nums, fm

S = os.environ.get('XX_CACHE_DIR', os.path.dirname(os.path.abspath(__file__)))

BOOKS = [
 # ── 小學（訓詁、韻書）───────────────────────────────────────────────
 dict(root='base-data/xiaoxue', slug='fang-yan', title='方言', author='扬雄',
      dynasty='西汉', w=2,
      pages=['方言/方言序', '方言/刻方言序'] + vols('方言', '卷%s', 1, 13),
      summary='西汉扬雄撰、晋郭璞注，全称《輶轩使者绝代语释别国方言》，中国第一部比较方言词汇专著。'),
 dict(root='base-data/xiaoxue', slug='shi-ming', title='释名', author='刘熙',
      dynasty='东汉', w=3, pages=vols('釋名', '卷%s', 1, 8),
      summary='东汉刘熙撰，以声训释名物典礼一千五百馀条，凡八卷二十七篇，训诂学名著。'),
 dict(root='base-data/xiaoxue', slug='ji-jiu-pian', title='急就篇', author='史游',
      dynasty='西汉', w=4,
      pages=['急就篇/急就篇注敘'] + vols('急就篇', '卷%s', 1, 4),
      summary='西汉史游撰、唐颜师古注，汉代通行的识字课本，以韵语编次姓名、器物、官职诸门。'),
 dict(root='base-data/xiaoxue', slug='zhong-yuan-yin-yun', title='中原音韵',
      author='周德清', dynasty='元', w=5, pages=['中原音韻'],
      summary='元周德清撰，据元曲用韵定十九韵部，废入声、分阴阳，近代汉语语音史第一要籍。'),

 # ── 集部·詩文評 ───────────────────────────────────────────────────
 dict(root='base-data/literature/shihua', slug='shi-pin', title='诗品',
      author='钟嵘', dynasty='南朝梁', w=1,
      pages=['詩品/卷上', '詩品/卷中', '詩品/卷下'],
      summary='南朝梁钟嵘撰，品第汉魏至齐梁五言诗人一百二十二家为上中下三品，中国第一部诗论专著。'),
 dict(root='base-data/literature/shihua', slug='er-shi-si-shi-pin', title='二十四诗品',
      author='旧题司空图', dynasty='唐', w=2, pages=['二十四詩品'],
      summary='旧题唐司空图撰，以四言韵语状写雄浑、冲淡等二十四种诗境，意象批评之典范。'),
 dict(root='base-data/literature/shihua', slug='liu-yi-shi-hua', title='六一诗话',
      author='欧阳修', dynasty='北宋', w=3, pages=['六一詩話'],
      summary='北宋欧阳修撰，「诗话」一体自此得名，以闲谈笔记论诗，开一代风气。'),
 dict(root='base-data/literature/shihua', slug='zhong-shan-shi-hua', title='中山诗话',
      author='刘攽', dynasty='北宋', w=4, pages=['中山詩話'],
      summary='北宋刘攽撰，继欧阳修之后的早期诗话，多记本朝诗人轶事与句法得失。'),
 dict(root='base-data/literature/shihua', slug='bi-ji-man-zhi', title='碧鸡漫志',
      author='王灼', dynasty='南宋', w=5, pages=nums('碧雞漫志', '%d', 0, 5),
      summary='南宋王灼撰，凡五卷，考歌曲源流与唐宋大曲本事，词乐研究之要籍。'),
 dict(root='base-data/literature/shihua', slug='sui-han-tang-shi-hua',
      title='岁寒堂诗话', author='张戒', dynasty='南宋', w=6, pages=['歲寒堂詩話'],
      summary='南宋张戒撰，尊杜抑苏黄，倡「言志为本」，为严羽《沧浪诗话》先声。'),
 dict(root='base-data/literature/shihua', slug='cang-lang-shi-hua', title='沧浪诗话',
      author='严羽', dynasty='南宋', w=7, pages=nums('滄浪詩話', '卷%d', 1, 5),
      summary='南宋严羽撰，分诗辨、诗体、诗法、诗评、考证五门，以禅喻诗、倡「妙悟」「兴趣」，影响最巨的诗话。'),
 dict(root='base-data/literature/shihua', slug='bai-shi-shi-shuo',
      title='白石道人诗说', author='姜夔', dynasty='南宋', w=8, pages=['白石道人詩說'],
      summary='南宋姜夔撰，凡三十则，论诗之高妙、章法与四种高妙，简约而多创见。'),
 dict(root='base-data/literature/shihua', slug='yue-fu-zhi-mi', title='乐府指迷',
      author='沈义父', dynasty='南宋', w=9, pages=['樂府指迷'],
      summary='南宋沈义父撰，论作词之法，标举「协律、雅正、含蓄、柔婉」四则，宋人词论之代表。'),
 dict(root='base-data/literature/shihua', slug='si-ming-shi-hua', title='四溟诗话',
      author='谢榛', dynasty='明', w=10, pages=['四溟詩話'],
      summary='明谢榛撰，凡四卷，后七子中论诗最精者，重悟与法之兼资、情景之妙合。'),
 dict(root='base-data/literature/shihua', slug='jiang-zhai-shi-hua', title='姜斋诗话',
      author='王夫之', dynasty='明', w=11, pages=['薑齋詩話'],
      summary='明末王夫之撰，含《诗译》《夕堂永日绪论》，以「情景相生」「现量」论诗，思辨最深。'),
 dict(root='base-data/literature/shihua', slug='yuan-shi', title='原诗',
      author='叶燮', dynasty='清', w=12, pages=['原詩'],
      summary='清叶燮撰，内外二篇，以理事情与才胆识力立论，中国古代最具体系的诗学专著。'),
 dict(root='base-data/literature/shihua', slug='shuo-shi-sui-yu', title='说诗晬语',
      author='沈德潜', dynasty='清', w=13, pages=['說詩晬語'],
      summary='清沈德潜撰，凡二卷，倡格调说，论历代诗体源流与作法，清代诗教之纲。'),
 dict(root='base-data/literature/shihua', slug='sui-yuan-shi-hua', title='随园诗话',
      author='袁枚', dynasty='清', w=14, pages=nums('隨園詩話', '%02d', 1, 16),
      summary='清袁枚撰，凡十六卷，倡性灵说，谈艺兼采轶闻，清代流传最广的诗话。'),
 dict(root='base-data/literature/shihua', slug='ci-gai', title='词概',
      author='刘熙载', dynasty='清', w=15, pages=['詞概'],
      summary='清刘熙载《艺概》之一，论词之源流、体格与作家，语约而识精。'),
]

GROUP_INDEX = [
    ('base-data/literature/shihua', '诗文评', 55),
]

ODD = re.compile(r'[�□■]')
HANRE = re.compile(r'[一-鿿]')


def write_book(b, pages):
    d = os.path.join(b['root'], b['slug'])
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, '_index.md'), 'w', encoding='utf-8').write(
        fm(title=b['title'], weight=b['w'], kind='book',
           author=b['author'], dynasty=b['dynasty'], summary=b['summary']))
    nvol = npiece = nchar = nodd = 0
    for vi, p in enumerate(b['pages'], 1):
        raw = pages.get(p, '')
        if re.match(r'\s*#\s*(重定向|REDIRECT)', raw, re.I):
            continue
        pieces = P.parse(C.clean(C.inline(raw, pages), p), p.split('/')[-1])
        if not pieces:
            print('  ⚠ %s / %s 無正文' % (b['title'], p))
            continue
        nvol += 1
        vdir = os.path.join(d, '%03d' % vi)
        os.makedirs(vdir, exist_ok=True)
        open(os.path.join(vdir, '_index.md'), 'w', encoding='utf-8').write(
            fm(title=p.split('/')[-1], weight=vi))
        for j, (pt, body) in enumerate(pieces, 1):
            open(os.path.join(vdir, '%03d.md' % j), 'w', encoding='utf-8').write(
                fm(title=pt.replace('"', '”'), weight=j) + '\n' + body)
            npiece += 1
            nchar += len(HANRE.findall(body))
            nodd += len(ODD.findall(body))
    return nvol, npiece, nchar, nodd


def main():
    pages = json.load(open(os.path.join(S, 'xxcache.json'), encoding='utf-8'))
    for path, name, w in GROUP_INDEX:
        os.makedirs(path, exist_ok=True)
        open(os.path.join(path, '_index.md'), 'w', encoding='utf-8').write(
            fm(title=name, weight=w))
    rows = []
    for b in BOOKS:
        rows.append((b['title'],) + write_book(b, pages))
    print('%-14s %5s %6s %9s %5s' % ('书', '卷', '篇', '汉字', '缺字'))
    for t, v, p, c, o in rows:
        print('%-14s %5d %6d %9d %5d' % (t, v, p, c, o))
    print('合计 %d 部 · %d 卷 · %d 篇 · %d 汉字；缺字 %d'
          % (len(rows), sum(r[1] for r in rows), sum(r[2] for r in rows),
             sum(r[3] for r in rows), sum(r[4] for r in rows)))


if __name__ == '__main__':
    main()
