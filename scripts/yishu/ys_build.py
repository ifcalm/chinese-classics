# -*- coding: utf-8 -*-
"""藝術門類·落盤。base-data/yishu/{組}/{書}/…

新立「藝術」一門，下分畫論／書論／樂論／器物四組。清洗與解析復用
`scripts/keji/kj_clean.py`、`kj_parse.py`——同是維基文庫整理本，模板體例一致。

**兩部候選未收**：
- 《筆法記》（五代荊浩）：全篇簡體錄文（簡繁 57:0），按鐵律簡→繁屬改字，不可為。
- 《琴史》（宋朱長文）：維基本只有卷一與卷四有正文，卷二、卷三僅存標題（共 174 字），
  六卷之書實存不足四分之一，是殘頁不是書。
二者待有繁體／完整錄文再補。
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), 'keji'))
import kj_clean as C
import kj_parse as P
from kj_build import cn, vols, nums, fm, index_layout   # 共用書寫設施

S = os.environ.get('YS_CACHE_DIR', os.path.dirname(os.path.abspath(__file__)))
DEST = 'base-data/yishu'

GROUPS = [
    ('hualun', '画论', 1),
    ('shulun', '书论', 2),
    ('yuelun', '乐论', 3),
    ('qiwu',   '器物', 4),
]

BOOKS = [
 # ── 畫論 ───────────────────────────────────────────────────────────
 dict(g='hualun', slug='xu-hua', title='叙画', author='王微', dynasty='南朝宋',
      w=101, pages=['敘畫'],
      summary='南朝宋王微撰，与宗炳《画山水序》并为中国最早的山水画论，倡「以一管之笔，拟太虚之体」。'),
 dict(g='hualun', slug='gu-hua-pin-lu', title='古画品录', author='谢赫', dynasty='南齐',
      w=102, pages=['古畫品錄'],
      summary='南齐谢赫撰，中国现存最早的绘画品评专著，首立「六法」，为后世画论之纲。'),
 dict(g='hualun', slug='xu-hua-pin', title='续画品', author='姚最', dynasty='陈',
      w=103, pages=['續畫品'],
      summary='陈姚最撰，续谢赫《古画品录》，评梁陈画家二十馀人，倡「心师造化」。'),
 dict(g='hualun', slug='li-dai-ming-hua-ji', title='历代名画记', author='张彦远',
      dynasty='唐', w=104, pages=vols('歷代名畫記', '卷第%s', 1, 10),
      summary='唐张彦远撰，凡十卷，中国第一部绘画通史，兼论画理、鉴藏、装裱与两京寺观壁画。'),
 dict(g='hualun', slug='tang-chao-ming-hua-lu', title='唐朝名画录', author='朱景玄',
      dynasty='唐', w=105, pages=['唐朝名畫錄'],
      summary='唐朱景玄撰，中国第一部断代画史，以神、妙、能、逸四品评唐画家一百二十馀人。'),
 dict(g='hualun', slug='yi-zhou-ming-hua-lu', title='益州名画录', author='黄休复',
      dynasty='北宋', w=106,
      pages=['益州名畫錄/序', '益州名畫錄/卷上', '益州名畫錄/卷中', '益州名畫錄/卷下'],
      summary='北宋黄休复撰，记唐至宋初成都画家五十八人，首以逸格居神、妙、能三格之上。'),
 dict(g='hualun', slug='tu-hua-jian-wen-zhi', title='图画见闻志', author='郭若虚',
      dynasty='北宋', w=107, pages=vols('圖畫見聞誌', '卷%s', 1, 6),
      summary='北宋郭若虚撰，凡六卷，续《历代名画记》记会昌至熙宁间画事，立「气韵非师」之说。'),
 dict(g='hualun', slug='lin-quan-gao-zhi', title='林泉高致集', author='郭熙、郭思',
      dynasty='北宋', w=108, pages=['林泉高致集'],
      summary='北宋郭熙述、郭思编，山水画论之集大成，「三远」法与「四时之景」皆出于此。'),
 dict(g='hualun', slug='shan-shui-chun-quan-ji', title='山水纯全集', author='韩拙',
      dynasty='北宋', w=109, pages=['山水純全集'],
      summary='北宋韩拙撰，分论山、水、林木、石、云霞、人物、笔墨，补郭熙三远为「六远」。'),
 dict(g='hualun', slug='xuan-he-hua-pu', title='宣和画谱', author='佚名', dynasty='北宋',
      w=110, pages=vols('宣和畫譜', '卷%s', 1, 20),
      summary='北宋宣和年间敕撰，著录御府所藏历代名画六千三百九十六轴，分十门，各系画家小传。'),
 dict(g='hualun', slug='hua-ji', title='画继', author='邓椿', dynasty='南宋', w=111,
      pages=vols('畫繼', '卷%s', 1, 10),
      summary='南宋邓椿撰，续郭若虚书，记熙宁至乾道间画家二百馀人，倡「画者文之极也」。'),
 dict(g='hualun', slug='hua-chan-shi-sui-bi', title='画禅室随笔', author='董其昌',
      dynasty='明', w=112, pages=vols('畫禪室隨筆', '卷%s', 1, 4),
      summary='明董其昌撰，论书论画之札记，南北宗说与「读万卷书，行万里路」出焉。'),
 dict(g='hualun', slug='hua-yu-lu', title='苦瓜和尚画语录', author='石涛', dynasty='清',
      w=113, pages=['苦瓜和尚畫語錄', '苦瓜和尚畫語錄/跋'],
      summary='清石涛撰，凡十八章，「一画」之说与「笔墨当随时代」为清代画论第一奇书。'),

 # ── 書論 ───────────────────────────────────────────────────────────
 dict(g='shulun', slug='bi-zhen-tu', title='笔阵图', author='旧题卫铄', dynasty='东晋',
      w=201, pages=['筆陣圖'],
      summary='旧题东晋卫夫人撰，以「七条笔阵出入斩斫图」喻点画之法，书法技法论之滥觞。'),
 dict(g='shulun', slug='shu-pu', title='书谱', author='孙过庭', dynasty='唐', w=202,
      pages=['書譜'],
      summary='唐孙过庭撰，草书墨迹传世，论书之源流、体势、执使转用与学书三时，书学史上第一篇系统论著。'),
 dict(g='shulun', slug='shu-duan', title='书断', author='张怀瓘', dynasty='唐', w=203,
      pages=['書斷序', '書斷/卷上', '書斷/卷中', '書斷/卷下'],
      summary='唐张怀瓘撰，上卷叙十体源流，中下二卷以神、妙、能三品评书家八十六人。'),
 dict(g='shulun', slug='fa-shu-yao-lu', title='法书要录', author='张彦远', dynasty='唐',
      w=204, pages=['法書要錄/序'] + vols('法書要錄', '卷%s', 1, 6),
      # 全書 363 條 <ref> 是竇蒙原註（唐人），非今人校記，須留作夾註；
      # 丟掉的話卷五、卷六各少一半
      refs='note',
      summary='唐张彦远辑，凡十卷，汇录东汉至唐元和间书论三十馀种，书学文献之渊薮。'),
 dict(g='shulun', slug='xuan-he-shu-pu', title='宣和书谱', author='佚名', dynasty='北宋',
      w=205, pages=['宣和書譜'],
      summary='北宋宣和年间敕撰，著录御府所藏历代法书一千三百馀帖，凡二十卷，与《宣和画谱》并行。'),
 dict(g='shulun', slug='yan-ji', title='衍极', author='郑杓', dynasty='元', w=206,
      pages=['衍極'],
      summary='元郑杓撰、刘有定注，凡五篇，溯书法源流本于六书，注文尤称赅博。'),
 dict(g='shulun', slug='shu-fa-ya-yan', title='书法雅言', author='项穆', dynasty='明',
      w=207, pages=['書法雅言'],
      summary='明项穆撰，凡十七篇，以中和为宗论书，倡「心相」之说，明代书论之巨制。'),
 dict(g='shulun', slug='yi-zhou-shuang-ji', title='艺舟双楫', author='包世臣', dynasty='清',
      w=208, pages=nums('藝舟雙楫', '%02d', 1, 6),
      summary='清包世臣撰，论文与论书各半，力倡北碑，为清代碑学转向之关键文本。'),

 # ── 樂論 ───────────────────────────────────────────────────────────
 dict(g='yuelun', slug='yue-fu-gu-ti-yao-jie', title='乐府古题要解', author='吴兢',
      dynasty='唐', w=301, pages=['樂府古題要解'],
      summary='唐吴兢撰，释乐府古题本事一百馀条，郭茂倩《乐府诗集》解题多本于此。'),
 dict(g='yuelun', slug='jiao-fang-ji', title='教坊记', author='崔令钦', dynasty='唐',
      w=302, pages=['教坊記'],
      summary='唐崔令钦撰，记开元教坊制度、艺人轶事与曲名三百二十四，唐代乐舞之实录。'),
 dict(g='yuelun', slug='jie-gu-lu', title='羯鼓录', author='南卓', dynasty='唐', w=303,
      pages=['羯鼓錄'],
      summary='唐南卓撰，专记羯鼓源流、名手与曲名，中国最早的乐器专著之一。'),
 dict(g='yuelun', slug='yue-fu-za-lu', title='乐府杂录', author='段安节', dynasty='唐',
      w=304, pages=['樂府雜錄'],
      summary='唐段安节撰，分乐部、歌舞俳优、乐器等门，记唐代音乐制度与艺人，燕乐研究之要籍。'),

 # ── 器物 ───────────────────────────────────────────────────────────
 dict(g='qiwu', slug='tao-shuo', title='陶说', author='朱琰', dynasty='清', w=401,
      pages=['陶說/原序'] + vols('陶說', '卷%s', 1, 6) + ['陶說/跋'],
      summary='清朱琰撰，凡六卷，说今、说古、说明、说器，中国第一部系统的陶瓷史专著。'),
 dict(g='qiwu', slug='jing-de-zhen-tao-lu', title='景德镇陶录', author='蓝浦', dynasty='清',
      w=402, pages=['景德鎮陶錄'],
      summary='清蓝浦撰、郑廷桂补辑，记景德镇窑务源流、制法工序与历代窑考，陶瓷文献之要典。'),
]

ODD = re.compile(r'[�□■]')
HANRE = re.compile(r'[一-鿿]')


def write_book(b, pages, root):
    d = os.path.join(root, b['slug'])
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, '_index.md'), 'w', encoding='utf-8').write(
        fm(title=b['title'], weight=b['w'], kind='book',
           author=b['author'], dynasty=b['dynasty'], summary=b['summary']))
    nvol = npiece = nchar = nodd = 0
    for vi, p in enumerate(b['pages'], 1):
        raw = pages.get(p, '')
        if re.match(r'\s*#\s*(重定向|REDIRECT)', raw, re.I):
            continue
        pieces = P.parse(C.clean(C.inline(raw, pages), p, b.get('refs') == 'note'),
                         p.split('/')[-1])
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
    pages = json.load(open(os.path.join(S, 'yscache.json'), encoding='utf-8'))
    os.makedirs(DEST, exist_ok=True)
    open(os.path.join(DEST, '_index.md'), 'w', encoding='utf-8').write(
        fm(title='艺术', subtitle='画论 · 书论 · 乐论 · 器物', weight=11,
           summary='历代画论、书论、乐论与器物谱录。'))
    for g, name, w in GROUPS:
        gd = os.path.join(DEST, g)
        os.makedirs(gd, exist_ok=True)
        open(os.path.join(gd, '_index.md'), 'w', encoding='utf-8').write(
            fm(title=name, weight=w))
    rows = []
    for b in BOOKS:
        rows.append((b['title'],) + write_book(b, pages, os.path.join(DEST, b['g'])))
    print('%-14s %5s %6s %9s %5s' % ('书', '卷', '篇', '汉字', '缺字'))
    for t, v, p, c, o in rows:
        print('%-14s %5d %6d %9d %5d' % (t, v, p, c, o))
    print('合计 %d 部 · %d 卷 · %d 篇 · %d 汉字；缺字 %d'
          % (len(rows), sum(r[1] for r in rows), sum(r[2] for r in rows),
             sum(r[3] for r in rows), sum(r[4] for r in rows)))


if __name__ == '__main__':
    main()
