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


# 底本錄文的花括號筆誤：整批只此一處，逐字列明，不做通用「修花括號」的兜底——
# 兜底會把別處真正的結構問題悄悄抹平。補的是一個 `}`（標記），漢字一個未動。
# 《孔子家語·卷九》「大夫之妻，為命婦」那條夾註只用單 `}` 收尾，深度掃描遂越過它
# 一直吃到下一條夾註的 `}}`，把中間正文吞掉、並讓後兩條夾註成為孤立殘留。
FIXUP = {
    '孔子家語/卷九': [('{{*|大夫之妻，為命婦}。}', '{{*|大夫之妻，為命婦}}。')],
}


def fixup(page, raw):
    for a, b in FIXUP.get(page, ()):
        if a not in raw:
            raise AssertionError('%s 的底本筆誤补丁失效（上游已改？）：%s' % (page, a))
        raw = raw.replace(a, b)
    return raw


LINK = re.compile(r"\[\[\s*(?:\.\./)?/?([^\[\]|#]+?)\s*(?:\|[^\]]*)?\]\]")


def order_by_links(mainraw, subs):
    """按主页 TOC 链接的出现次序排子页；主页没提到的按原序缀在后面。

    `order()` 靠抽末尾数字排序，遇到题名无数字的书就废了——《昌言》的
    卷上/卷中/卷下会被按字母排成 卷上/卷下/卷中，《明儒学案》七十八个学案名
    更是全乱。这类书的正确次序只有主页目录知道，故据其链接次序排。
    """
    want, seen = [], set()
    for m in LINK.finditer(mainraw):
        tail = m.group(1).split('/')[-1].strip()
        if tail in subs and tail not in seen:
            want.append(tail); seen.add(tail)
    return want + [s for s in subs if s not in seen]


def order(book, index, skip=(), mainraw=None):
    """按卷次排出一部書的頁序。

    ⚠ 不能用 allpages 給的字典序——那會把「卷十一」排到「卷二」前面、
    把「卷100」排到「卷2」前面。各書卷名格式又互不相同（通典作 /卷001、
    文獻通考作 /卷一百七十七、唐才子傳作 /卷10、朱子語類作 /140），
    故一律抽出數字再排；序、自序、提要之類無數字者置於卷首。
    """
    subs = [p for p in index[book][1:] if p.split('/')[-1] not in skip]
    if mainraw is not None:                       # toc 模式：以主页目录次序为准
        tails = [p.split('/')[-1] for p in subs]
        byname = {p.split('/')[-1]: p for p in subs}
        return [byname[t] for t in order_by_links(mainraw, tails)]
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
 # ── 紀事本末（四庫史部此類站內此前為零；插在編年 250/260 與別史 270 之間）──
 # 底本是四庫全書本，乾隆館臣刪改痕跡明確（「敵」320 處、「鄰境」2 處，而「建州」
 # 「女真」「滿洲」全書 0 次）。殆知閣本指紋逐項相同（敵 320、鄰境 2、女直 2），
 # 是同一遞修本，別無更早之電子本可取。已挂 known-issues 与 #34 四库底本审计。
 # 卷首傅以渐序系他人所撰，按铁律弃；谷应泰自序存。
 dict(root='base-data/history', slug='ming-shi-ji-shi-ben-mo', title='明史纪事本末',
      author='谷应泰', dynasty='清', w=265, src='明史紀事本末',
      drop=('明史紀事本末序',), usesection=1,
      summary='清谷应泰撰，凡八十卷，仿袁枢《通鉴纪事本末》体例纪明代事迹，每卷一事，'
              '篇末各系论断。成书于顺治十五年（1658），早《明史》八十年，取材《明实录》'
              '及谈迁、张岱诸家野史，为明代史事之独立史源。据维基文库四库全书本收录；'
              '卷首傅以渐序系他人所撰不收，谷应泰自序存。'),

 # ── 目錄（四庫史部「目錄類」，站內此前為零；插在政書 350 與史評 360 之間）──
 # 「解題」是目錄提要而非注疏，不在「注疏不收」之列（用户 2026-08-22 已界定）。
 dict(root='base-data/history', slug='jun-zhai-du-shu-zhi', title='郡斋读书志',
      author='晁公武', dynasty='南宋', w=355, src='郡齋讀書志', maxlvl=2,
      summary='南宋晁公武撰，中国现存最早的私家藏书目提要，每书具解题，述作者行事与全书要旨，多录今已亡佚之书。'),
 dict(root='base-data/history', slug='zhi-zhai-shu-lu-jie-ti', title='直斋书录解题',
      author='陈振孙', dynasty='南宋', w=356, src='直齋書錄解題', maxlvl=2,
      summary='南宋陈振孙撰，著录家藏五万馀卷，解题详辨卷帙源流与作者行事，与晁公武《郡斋读书志》并称宋代私家目录双璧。'),
 dict(root='base-data/history', slug='ri-zhi-lu', title='日知录', author='顾炎武',
      dynasty='清', w=360, src='日知錄', refs='note',
      summary='清顾炎武撰，凡三十二卷，经义、治道、博闻三部，考据与经世之学并重，清代朴学开山。'),
 # ⚠《廿二史札记》已移出本表，改由 scripts/parse-zhaji.py 据殆知阁本收全本
 #   （维基条目只有 10,938 汉字＝全书 2%，且页首今人导读、页尾外链节）。
 #   **切勿加回来**——本表一跑就会拿维基残页把 39 万字的全本盖掉。
 #   `drop=` / `retitle=` 两个选项是那次修复留下的，仍可给别的书用。
 dict(root='base-data/history', slug='wen-shi-tong-yi', title='文史通义',
      author='章学诚', dynasty='清', w=380, src='文史通義',
      summary='清章学诚撰，内篇外篇论史学义例与文史流别，「六经皆史」之说出焉。'),

 # ── 子部 ───────────────────────────────────────────────────────────
 # ══ 子部三批（2026-08-27）══════════════════════════════════════════
 # A 理學立本：站內原有近思錄/朱子語類/傳習錄，卻無周張二程原文——有轉述而無源頭。
 #   weight 23.2-23.5，排在近思錄 24 之前，本在末先。
 dict(root='base-data/masters', slug='tai-ji-tu-shuo', title='太极图说',
      author='周敦颐', dynasty='北宋', w=23.2, pages=['太極圖說'],
      summary='北宋周敦颐撰，正文二百四十九字，自无极太极推及阴阳五行、人极中正，宋明理学之开山纲领。'),
 dict(root='base-data/masters', slug='tong-shu', title='通书',
      author='周敦颐', dynasty='北宋', w=23.3, pages=['通書'],
      summary='北宋周敦颐撰，四十章，即《易通》，以诚为枢纽贯通天道人道，与《太极图说》并为濂溪之学所寄。'),
 dict(root='base-data/masters', slug='zheng-meng', title='正蒙',
      author='张载', dynasty='北宋', w=23.4, src='正蒙',
      summary='北宋张载撰，十七篇，立太虚即气、一物两体之说，「民胞物与」《西铭》即在其《乾称篇》，关学之本。'),
 dict(root='base-data/masters', slug='er-cheng-yi-shu', title='二程遗书',
      author='程颢、程颐', dynasty='北宋', w=23.5, src='二程遺書',
      summary='即《河南程氏遗书》二十五卷，朱熹编次二程门人所记语录，洛学文献之主体，《近思录》多取材于此。'),

 # B 先秦小家·孔門文獻·漢魏子書：諸子九流補其缺，漢代子書補其半壁。
 dict(root='base-data/masters', slug='kong-zi-jia-yu', title='孔子家语',
      author='王肃注', dynasty='三国魏', w=0.5, src='孔子家語', toc=1,
      summary='记孔子及门弟子言行，十卷四十四篇，旧题孔安国序、王肃注，宋以来多疑为王肃缀辑，然所存孔门遗说多与《论语》《礼记》相发。'),
 dict(root='base-data/masters', slug='kong-cong-zi', title='孔丛子',
      author='孔鲋', dynasty='秦汉间', w=0.6, src='孔叢子',
      summary='旧题秦末孔鲋撰，记孔子及子思、子高、子顺、孔臧诸孔氏子孙言行，附《连丛子》，孔门家学之传述。'),
 dict(root='base-data/masters', slug='yin-wen-zi', title='尹文子',
      author='尹文', dynasty='战国', w=15.1, src='尹文子', toc=1,
      summary='战国尹文撰，大道上下二篇，以形名相符论名实治道，名家兼综黄老刑名之作。'),
 dict(root='base-data/masters', slug='shen-zi', title='慎子',
      author='慎到', dynasty='战国', w=15.2, pages=['慎子'],
      summary='战国慎到撰，今存七篇及佚文，主势治、尚法而弃智去己，法家「势」派之宗。'),
 dict(root='base-data/masters', slug='deng-xi-zi', title='邓析子',
      author='邓析', dynasty='春秋', w=15.3, src='鄧析子',
      summary='旧题春秋郑邓析撰，无厚、转辞二篇，操两可之说、设无穷之辞，先秦名辩之滥觞。'),
 dict(root='base-data/masters', slug='shi-zi', title='尸子',
      author='尸佼', dynasty='战国', w=15.4, src='尸子', toc=1,
      summary='战国尸佼撰，原书二十篇久佚，清人辑为卷上下并存疑一卷，杂糅儒墨名法，为杂家之先。'),
 dict(root='base-data/masters', slug='wen-zi', title='文子',
      author='辛钘', dynasty='战国', w=15.5, src='文子',
      summary='旧题老子弟子文子撰，十二篇，即《通玄真经》，述道德之义而多与《淮南子》互见，定州汉简出土证其战国已有其书。'),
 dict(root='base-data/masters', slug='xin-yu', title='新语',
      author='陆贾', dynasty='西汉', w=19.5, src='新語',
      # 卷上/卷下 是把 01-12 各篇 {{:轉錄}} 起来的汇总页，与各篇本身重复。
      # 不跳过则每篇收两遍（实测 □ 由 102 变 204），而两侧同源故校验查不出。
      skip=('卷上', '卷下'),
      summary='西汉陆贾撰，十二篇，为高祖论「马上得之，宁可以马上治之」而作，汉初崇儒尚仁义之首倡。'),
 dict(root='base-data/masters', slug='xin-shu', title='新书',
      author='贾谊', dynasty='西汉', w=19.6, src='新書', toc=1,
      summary='西汉贾谊撰，十卷五十八篇，《过秦论》《陈政事疏》皆在其中，论秦亡汉兴之故与众建诸侯之策。'),
 dict(root='base-data/masters', slug='fa-yan', title='法言',
      author='扬雄', dynasty='西汉', w=21.6, src='法言',
      summary='西汉扬雄撰，十三卷，拟《论语》为问答体，尊孔孟而斥诸子，汉代儒学之重镇。'),
 dict(root='base-data/masters', slug='tai-xuan-jing', title='太玄经',
      author='扬雄', dynasty='西汉', w=21.7, pages=['太玄經'],
      summary='西汉扬雄撰，拟《易》而作，立八十一首、七百二十九赞，以方州部家配三方九州，汉代象数之学名著。'),
 dict(root='base-data/masters', slug='feng-su-tong-yi', title='风俗通义',
      author='应劭', dynasty='东汉', w=22.3, src='風俗通義',
      summary='东汉应劭撰，今存十卷，辨风正俗、纠谬正名，兼存汉代礼俗、传说与佚闻，考据家所重。'),
 dict(root='base-data/masters', slug='du-duan', title='独断',
      author='蔡邕', dynasty='东汉', w=22.4, pages=['獨斷'],
      summary='东汉蔡邕撰，二卷，记汉代典章名物、宗庙谥法与帝系沿革，汉制之实录。'),
 dict(root='base-data/masters', slug='chang-yan', title='昌言',
      author='仲长统', dynasty='东汉', w=22.5, src='昌言', toc=1,
      summary='东汉仲长统撰，原书三十四篇久佚，今存卷上中下及附录，斥豪强兼并、论治乱循环，汉末政论之峻切者。'),

 # C 明清思想：接理學之後（傳習錄 25 / 明夷待訪錄 25.1）。
 dict(root='base-data/masters', slug='kun-zhi-ji', title='困知记',
      author='罗钦顺', dynasty='明', w=25.2, pages=['困知記'],
      summary='明罗钦顺撰，正续四卷，主理在气中、辨心性之别，与王阳明往复论学，明代气学之要籍。'),
 dict(root='base-data/masters', slug='shen-yin-yu', title='呻吟语',
      author='吕坤', dynasty='明', w=25.3,
      pages=['呻吟語/序', '呻吟語/性命', '呻吟語/存心', '呻吟語/倫理', '呻吟語/談道',
             '呻吟語/修身', '呻吟語/問學', '呻吟語/應務', '呻吟語/養生', '呻吟語/天地',
             '呻吟語/世運', '呻吟語/聖賢', '呻吟語/品藻', '呻吟語/治道', '呻吟語/人情',
             '呻吟語/物理', '呻吟語/廣喻', '呻吟語/詞章'],
      summary='明吕坤撰，内外六卷十七篇，三十年间随得随录之语，切近日用而气象沉毅，明代语录体名著。'),
 dict(root='base-data/masters', slug='fen-shu', title='焚书',
      author='李贽', dynasty='明', w=25.4, src='焚書', toc=1,
      summary='明李贽撰，六卷附增补，书答、杂述、读史、诗汇为一编，倡童心之说、非圣无法，明末思想解放之标帜。'),
 dict(root='base-data/masters', slug='ming-ru-xue-an', title='明儒学案',
      author='黄宗羲', dynasty='清', w=25.5, src='明儒學案', toc=1,
      skip=('于准序', '仇兆鼇序', '莫晉序', '賈念祖跋', '賈樸跋', '賈潤序',
            '鄭性序', '黃千秋跋', '馮全垓跋'),
      summary='清黄宗羲撰，六十二卷，分十九学案叙明代二百余家学术源流，各系小传、语录与文录，中国第一部完整的学术史。'
              '卷首师说、发凡与黄氏自序存，于准、仇兆鳌、莫晋、贾氏父子、郑性、冯全垓诸序跋系他人所撰不收。'),
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

SHELL = re.compile(r'^[卷巻]\s*[一二三四五六七八九十百零〇\d]+|[卷巻]第?[一二三四五六七八九十百]+$')
HAN30 = re.compile(r'[一-鿿㐀-䶿]')


def post(pieces, drop, retitle=None):
    """篇级后处理：弃掉指定篇题，并把「卷题空壳」并入次篇。

    ① drop：整理本页尾常挂「外部鏈接」节（正文是一条裸链），页首常有今人导读
       （《廿二史劄記》那篇用「西元1727～1814」纪年、引《臺灣通志》议筑城），
       两者皆非原书之文，按铁律不收。逐书按篇题指名弃，不做模糊匹配。
    ② 卷题空壳：《文献通考》职官考二十一卷、《通典》卷三一、《日知录》卷二五
       把「卷四十七　職官考一」这样的卷题单切成一篇，点开只有八个字。本书其余
       各卷（如卷六十八「卷六十八　郊社考一」）卷题本就在首篇篇首，故并入次篇，
       与全书体例取齐。**是并不是删**——一个字都不能少。

    ⚠ 返回 (原序号, 篇题, 正文)，落盘文件名用**原序号**而非重新枚举。
    弃篇/并篇会让后续各篇的位序整体前移，若按新位序命名，《文献通考》那 21 卷
    里每一篇的 URL 都要位移（实测 509 个文件）——为 23 个八字空壳搬走五百多条
    链接不划算。留原号即：空壳那格作废（少数死链），其余各篇 URL 纹丝不动。
    """
    out = []
    for i, (pt, body) in enumerate(pieces, 1):
        if pt in drop:
            continue
        out.append([i, (retitle or {}).get(pt, pt), body])
    merged, k = [], 0
    while k < len(out):
        idx, pt, body = out[k]
        if (k + 1 < len(out) and len(HAN30.findall(body)) < 30
                and SHELL.search(body.strip())):
            out[k + 1][2] = body.strip() + '\n\n' + out[k + 1][2]
            k += 1
            continue
        merged.append((idx, pt, body))
        k += 1
    return merged


ODD = re.compile(r'[�□■]')
HANRE = re.compile(r'[一-鿿]')
SIMP = '来为国无与从东车马门时会说汉铁风鸟鱼龙岁书对长义爱经实举学权'


SECT = re.compile(r"\|\s*section\s*=\s*(.+?)\s*(?=\n\s*\||\n\s*\}\})", re.S)
QUOT = re.compile(r"'{2,3}")


def section_of(raw):
    """从 {{header2|…|section=…|…}} 取事目；取不到返回空串（parse 会退回页名）。"""
    m = SECT.search(raw)
    if not m:
        return ''
    t = QUOT.sub('', m.group(1))
    t = re.sub(r"\[\[[^\]|]*\|", '', t).replace('[[', '').replace(']]', '')
    return t.strip()


def prune(bookdir, written):
    """剪除本次未产出的陈旧 .md。

    此前 write_book 只写不删：弃篇、并篇、上游卷数变少时，旧文件原地留着，
    构建产物与管线输出讲的不是同一件事，线上还照旧渲染那些废页
    （23 个卷题空壳并入次篇后，0001.md 仍在）。同 dist-content 的 pruneStale
    之教训，见 memory verification-blindspots #5。
    """
    n = 0
    for dp, dns, fns in os.walk(bookdir, topdown=False):
        for f in fns:
            fp = os.path.join(dp, f)
            if f.endswith('.md') and fp != os.path.join(bookdir, '_index.md') \
                    and fp not in written:
                os.remove(fp); n += 1
        if dp != bookdir and not os.listdir(dp):
            os.rmdir(dp)
    if n:
        print('  剪除陈旧文件 %d（%s）' % (n, os.path.basename(bookdir)))
    return n


def write_book(b, pages, index):
    if 'pages' not in b:
        b['pages'] = order(b['src'], index, b.get('skip', ()),
                           pages.get(b['src']) if b.get('toc') else None)
    d = os.path.join(b['root'], b['slug'])
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, '_index.md'), 'w', encoding='utf-8').write(
        fm(title=b['title'], weight=b['w'], kind='book',
           author=b['author'], dynasty=b['dynasty'], summary=b['summary']))
    nvol = npiece = nchar = nodd = nsimp = 0
    written = set()          # 本次产出的文件全路径，收尾据以剪除陈旧残留
    for vi, p in enumerate(b['pages'], 1):
        raw = pages.get(p, '')
        if not raw or re.match(r'\s*#\s*(重定向|REDIRECT)', raw, re.I):
            print('  ⚠ %s / %s 缺页或重定向' % (b['title'], p))
            continue
        txt = C.clean(C.inline(fixup(p, raw), pages), p,
                      b.get('refs') == 'note', b.get('stray', 'drop'))
        # usesection：篇题取 header 的 |section=，而非页名。
        # 纪事本末体一卷即一事，事目（「太祖起兵」「甲申殉難」）只在 header 参数里，
        # 页名是「卷01」——不取的话八十卷全叫「卷01」…「卷80」，一部纪事本末就白收了。
        fb = (section_of(raw) if b.get('usesection') else '') or p.split('/')[-1]
        pieces = post(P.parse(txt, fb, b.get('maxlvl')),
                      b.get('drop', ()), b.get('retitle'))
        if not pieces:
            print('  ⚠ %s / %s 無正文' % (b['title'], p))
            continue
        nvol += 1
        vdir = os.path.join(d, '%03d' % vi)
        os.makedirs(vdir, exist_ok=True)
        vix = os.path.join(vdir, '_index.md')
        open(vix, 'w', encoding='utf-8').write(
            fm(title=p.split('/')[-1], weight=vi))
        written.add(vix)
        for j, pt, body in pieces:
            fp = os.path.join(vdir, '%04d.md' % j)
            open(fp, 'w', encoding='utf-8').write(
                fm(title=pt.replace('"', '”'), weight=j) + '\n' + body)
            written.add(fp)
            npiece += 1
            nchar += len(HANRE.findall(body))
            nodd += len(ODD.findall(body))
            nsimp += sum(body.count(c) for c in SIMP)
    prune(d, written)
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
