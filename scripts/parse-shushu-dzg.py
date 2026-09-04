# -*- coding: utf-8 -*-
"""术数五部 ← 殆知阁本（简体）。堪舆：《地理人子须知》《山洋指迷》；
相术：《神相全编》《柳庄相法》《神相铁关刀》。

**为什么走殆知阁而不走维基**：这两部维基文库都有条目，但都不能用——
《人子须知》维基本只有 11,820 汉字（凡例＋序＋书目＋琐言，约全书 4%），
殆知阁本 306,159 字是全帙；《山洋指迷》维基无此页。

**为什么同批另三部不在这里**：《青乌经》《天元五歌》《阳宅指南》维基本繁体清爽，
走 `scripts/shibu/` 那条管线，见其 BOOKS。

**同批查过而不收的三部，理由列此，免得日后重查**：
- 《天玉经》——殆知阁本是注本，经文与注文同为顶格段落，**纯文本里不可分离**；
  维基页只有 32 字节。按「注疏不收」，无白文可得。
- 《地理辨正》——蒋大鸿注青囊经、青囊序、青囊奥语等五经，经注混排；且其
  「青囊奥语」一章与站内既有的《青囊奥语》白文重复。
- 《入地眼全书》——殆知阁本只有卷一、二、四、六、九、十，**十卷缺其四**；
  维基本（57,935 字节）是机器繁化且连词带字一起换过的坏本：「周兆熊」作「週兆熊」、
  「余乞假」作「餘乞假」、「辜託长老」作「辜負長老」、「所能逮」作「所能逮捕」。
  两个源都不可用。

**取舍**：他人序跋不收，自序、凡例、自撰琐言存（同《明儒学案》之例）。
《人子须知》弃李维祯序、曾璠序、徐阶序、祝眉寿序四篇；存凡例、自序、郢中重刻自序、
引用诸名家堪舆书目、琐言凡十条、附杂说二欵，皆徐氏兄弟自撰。
《山洋指迷》弃序一序二序三与增注者凡例，及「周景一先生著」等四行题署。

**《山洋指迷》剥增注**：此本是「严陵张九仪先生增注」本，其凡例自言
「另增注解加圈别之」，排印圈号在纯文本里已失，注文落成全角括号，全书 500 处
9,119 汉字。按「注疏不收」剥去，剥是删、不违只删不改不增，剥后即周景一白文。
**⚠ 此法只对注源单一的书用**：括号里全是张九仪与抄本诠注，无一句周景一本文；
若像《金楼子》那样自注与他人案语混装在同一种标记里，一刀切会删掉作者正文。

**相术三部（2026-09-02 同日续收）**：
- 《神相全编》——**底本非全帙**。通行本十二卷，殆知阁本只 30,647 字、无卷次，
  内容止于总论、十三部位、十二宫、学堂、五行形相与诸格例，约当卷一至卷四之数，
  不含麻衣石室神异赋、女相、气色详论。照《东观汉记》之例**照收并在提要里写明非全书**。
- 《柳庄相法》——篇题作「一、未出腹预知贵贱」，带顿号，通用篇题判据认不出，
  故用 `titlere` 单给一条规则。全书 150 题，上下册各自另起编号。
- 《神相铁关刀》——卷一至卷四齐全；卷端题名忽作「卷一」忽作「（卷二）」，
  volre 兼收两式。「铁关刀原序」是破纳云谷山人自序，存。

**已知讹字**（见 docs/known-issues.md）：殆知阁本有 IT 词表串入之讹，
《人子须知》两处「李维祯」作「利瓦伊祯／利瓦伊桢」（LeVi→利瓦伊），一处在弃收的
郢中序、一处在卷七上之二正文内。《柳庄相法》另有成片的「日」讹作「曰」
（「三曰知一生」「夏曰火旺」）。**一律照收不改**——只删不改不增是铁律。

用法: python3 scripts/parse-shushu-dzg.py [--write]
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'scripts', 'dzg')
WRITE = '--write' in sys.argv
HAN = re.compile(r'[一-鿿㐀-䶿]')
han = lambda s: len(HAN.findall(s))

# 篇题判据：无标点、够短，且其后正文成段。图说残题（「图」「说」「卦」「河」）
# 与正文里的问答短句（「或曰：肌理刷开，未尝闻之。」）都得挡在外面——
# 前者靠「其后正文须成段」挡，后者靠「不含标点」挡。
# 顿号不在其中：《神相铁关刀》有「涎、精、汗、泪、溺各有所属」这样的篇题，
# 《柳庄相法》有「斑有黑、黄、大、小」，把顿号算进标点会把它们判成正文。
PUNCT = '。，；：？！“”‘’「」《》〈〉（）()·…—:;,.?!"\''
BODYMIN = 60          # 标题之后须有这么多汉字，才算标题而非图说残题；逐书可覆写
TITLEMAX = 15         # 再长的无标点短行是落款（「嘉靖甲子孟春德兴山人徐善继书于双芝堂」）


def strip_paren(s):
    """剥全角括号夹注，做到不动点（有嵌套）。"""
    for _ in range(6):
        t = re.sub(r'（[^（）]*）', '', s)
        if t == s:
            return t
        s = t
    return s


BOOKS = [
    dict(src='人子须知', slug='ren-zi-xu-zhi', title='地理人子须知',
         author='徐善继、徐善述', dynasty='明', w=80,
         root='base-data/shushu/kanyu',
         skip_head=1,                       # 首行「重刊人子须知…徐善继述 同着」是题署
         cut=True,                          # 卷一之上末四十五行今人文字，见 CUT_FROM
         volre=r'^重刊人子须知资孝地理心学统宗(卷.+)$',
         head='卷首',
         drop=('郢中重刻人子须知序', '重刊人子须知序', '旧序'),
         summary='明徐善继、徐善述兄弟撰，凡八卷分上下，为龙、穴、砂、水、明堂、阳宅诸法'
                 '各立专篇，附图数百，博采前代堪舆百馀家而断以己意，明代形法之集大成者。'
                 '据殆知阁本收录（简体）；李维祯、曾璠、徐阶、祝眉寿四序系他人所撰不收，'
                 '凡例、自序、郢中重刻自序、引用书目、琐言、杂说皆徐氏自撰，存。'),
    dict(src='山洋指迷原本', slug='shan-yang-zhi-mi', title='山洋指迷',
         author='周景一', dynasty='明', w=85,
         root='base-data/shushu/kanyu',
         volre=r'^(卷[一二三四五六七八九十]+)$',
         head=None,                         # 前四行题署与三序全弃，无卷首
         paren=True,
         drop=('序一', '序二', '序三', '凡例', '周景一先生著', '严陵张九仪先生增注',
               '山阴吴卿瞻、姚两方校阅', '山阴吴太古、姑苏俞法陶同校'),
         summary='明周景一撰，凡四卷，前三卷论山龙之开面地步、龙穴砂水真伪，第四卷专论平洋，'
                 '为峦头一派辨形析理最细密之作。据殆知阁本收录（简体），'
                 '清张九仪增注 500 处按「注疏不收」剥去，存周景一白文。'),
    # ── 相术（2026-09-02）──────────────────────────────────────────────
    dict(src='神相全编', slug='shen-xiang-quan-bian', title='神相全编',
         author='旧题陈抟秘传、袁忠彻订正', dynasty='明', w=30,
         root='base-data/shushu/xiangshu',
         skip_head=2,                       # 空行＋「《神相全编》」题名行
         volre=r'^(?!)$',                   # 底本无卷次，全书作一卷
         head='全编', drop=(), bodymin=12, leaddash=True,   # 本书各条极短，「一取威仪」正文才三十馀字
         summary='旧题宋陈抟秘传、明袁忠彻订正，相法总论之集大成者，十观、五法、'
                 '十三部位、十二宫、四学堂八学堂、五岳四渎、五星六耀以至诸格例，'
                 '相书言部位、宫位者多本于此。'
                 '据殆知阁本收录（简体）。此本非全帙：通行本十二卷，而此本三万馀字、无卷次，'
                 '约当前四卷之数，不含麻衣石室神异赋、女相与气色详论。'),
    dict(src='柳庄相法', slug='liu-zhuang-xiang-fa', title='柳庄相法',
         author='袁珙', dynasty='明', w=40,
         root='base-data/shushu/xiangshu',
         volre=r'^(上册|下册)$',
         titlere=r'^[一二三四五六七八九十百零]+、',
         head=None, drop=(), bodymin=0,     # 篇题规则严，不必再用正文长度兜底
         qsplit=True,                       # 永乐问答一行问答连排，题只取问句
         summary='明袁珙撰，珙号柳庄居士，以相术名于洪武、永乐间。上册自「未出腹预知贵贱」'
                 '至「论行说」凡九十馀题，兼载永乐帝问答；下册专论气色，分四时、十二月而断。'
                 '据殆知阁本收录（简体），底本有成片的「日」讹作「曰」，照收不改。'),
    dict(src='神相铁关刀', slug='shen-xiang-tie-guan-dao', title='神相铁关刀',
         author='云谷山人', dynasty='清', w=50,
         root='base-data/shushu/xiangshu',
         skip_head=1,                       # 首行题名
         volre=r'^神相铁关刀[（(]?(卷[一二三四五六七八九十]+)[）)]?$',
         head='卷首', drop=(), bodymin=12,
         summary='旧题破纳云谷山人得之异人、自谓希夷先生秘本，凡四卷，'
                 '自须眉发毛所属、面部刻误秘旨，至相气、相神与各官各部秘诀，'
                 '论断细密而多口诀，清以来相家习用之书。据殆知阁本收录（简体）。'),
]


# 卷端题署（版心题名下的著者行），非正文，逐行剔除。不能当「篇」丢——
# 当篇丢会连它后面那段正文一起没了；它们又必须剔除，否则会被当成篇题，
# 三十八个卷各顶一个「江右山人徐善继述同着」。
BYLINE = re.compile(r'^(?:重刊人子须知资孝地理心学统宗\s*)?'
                    r'[江右德兴]{2}山人徐善继述\s*同着$')

# 殆知阁《人子须知》卷一之上末尾窜入四十五行今人文字：一条「望阳按」引今人卫星图
# 论全球龙脉，续以孟广顺《龙兴中国——踏寻龙的足迹》（摘自 2004 年《报告文学》
# 第 58 期）。**近现代作品不收是铁律，且该文尚在著作权期内**，整块剔除。
# 起点锚在按语首句，终点是下一个卷题（卷一之下）。全书今人窜入只此一处——
# 「卫星」「俄罗斯」「美国」「欧洲」「摘自」诸词的出现位置全落在这四十五行内。
CUT_FROM = '望阳按：由于时代之局限'


# 殆知阁《神相全编》给每段正文加了行首破折号（「——如虎下山，百兽自惊」），
# 是数字化者的排版记号、非底本文字，剥掉。破折号不是汉字，剥它不动汉字流。
LEADDASH = re.compile(r'^[—－–-]{1,3}\s*')


def norm(s):
    return re.sub(r'\s+', '', s)


def is_title(s, tre=None):
    if tre is not None:                     # 书自带篇题规则时，一律以它为准
        return bool(tre.match(s))
    return 0 < len(s) <= TITLEMAX and not any(c in PUNCT for c in s) and HAN.search(s)


QSPLIT = re.compile(r'^(.{4,30}?[？?])(.+)$', re.S)


def qsplit(s):
    """问答体的一行里问与答连排时，题只取问句，答退回正文。

    《柳庄相法》上册后半是永乐帝问答，一问一答挤在同一行：
    「三、朕昨见一尚书天庭低，何故又得为官？对曰：天庭虽低，曰月角开辅……」
    整行作篇题则目录里全是长段。切在第一个问号处，**问句与答语各出现一次、
    次序不变**，故仍是底本的子序列——若把问句既留在题里又留在正文里，
    落盘流就会多出一份，校验立刻报错。
    """
    m = QSPLIT.match(s)
    return (m.group(1), m.group(2).strip()) if m else (s, None)


def parse(b):
    raw = open(os.path.join(SRC, b['src'] + '.txt'), encoding='utf-8').read()
    lines = raw.split('\n')[b.get('skip_head', 0):]
    if b.get('paren'):
        lines = [strip_paren(x) for x in lines]
    if b.get('leaddash'):
        lines = [LEADDASH.sub('', x.strip()) for x in lines]
    tre = re.compile(b['titlere']) if b.get('titlere') else None
    bodymin = b.get('bodymin', BODYMIN)
    lines = [norm(x) if is_title(norm(x), tre) else x.strip() for x in lines]

    vre = re.compile(b['volre'])
    if b.get('cut'):
        i = next((k for k, x in enumerate(lines) if x.startswith(CUT_FROM)), None)
        assert i is not None, '%s：今人窜入段的锚句没找到（上游改了？）' % b['title']
        j = next(k for k in range(i + 1, len(lines)) if vre.match(lines[k]))
        print('  剔除今人窜入 %d 行（%d–%d）' % (j - i, i, j - 1))
        lines = lines[:i] + lines[j:]
    vols, cur = [], None
    if b.get('head'):
        cur = {'title': b['head'], 'pieces': []}
        vols.append(cur)
    for ln in lines:
        if not ln or BYLINE.match(ln):
            continue
        m = vre.match(ln)
        if m:
            cur = {'title': m.group(1), 'pieces': []}
            vols.append(cur)
            continue
        if cur is None:
            continue                       # 卷一之前的题署行（山洋指迷）
        cur['pieces'].append(ln)

    # 段落序列 → 篇。标题行开新篇，但其后正文不足 BODYMIN 者退回正文（图说残题）。
    out = []
    for v in vols:
        ps, i = [], 0
        L = v['pieces']
        while i < len(L):
            s = L[i]
            if is_title(s, tre):
                j, acc = i + 1, 0
                while j < len(L) and not is_title(L[j], tre):
                    acc += han(L[j]); j += 1
                if acc >= bodymin:
                    t, rest = qsplit(s) if b.get('qsplit') else (s, None)
                    ps.append({'title': t,
                               'body': ([rest] if rest else []) + L[i + 1:j]})
                    i = j
                    continue
            if not ps:                      # 卷首无篇题的散文
                ps.append({'title': v['title'], 'body': []})
            ps[-1]['body'].append(s)
            i += 1
        ps = [p for p in ps if norm(p['title']) not in b['drop']]
        if ps:
            out.append({'title': v['title'], 'pieces': ps})
    return out


def fm(**kw):
    o = ['---']
    for k, x in kw.items():
        o.append('%s: %s' % (k, x if isinstance(x, (int, float)) else '"%s"' % x))
    return '\n'.join(o) + '\n---\n'


def write(b, vols):
    d = os.path.join(ROOT, b['root'], b['slug'])
    for dp, dns, fns in os.walk(d, topdown=False):       # 全量重写
        for f in fns:
            if f.endswith('.md'):
                os.remove(os.path.join(dp, f))
        if dp != d:
            os.rmdir(dp)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, '_index.md'), 'w', encoding='utf-8').write(
        fm(title=b['title'], weight=b['w'], kind='book',
           author=b['author'], dynasty=b['dynasty'], summary=b['summary']))
    for vi, v in enumerate(vols, 1):
        vd = os.path.join(d, '%03d' % vi)
        os.makedirs(vd, exist_ok=True)
        open(os.path.join(vd, '_index.md'), 'w', encoding='utf-8').write(
            fm(title=v['title'], weight=vi))
        for j, p in enumerate(v['pieces'], 1):
            open(os.path.join(vd, '%04d.md' % j), 'w', encoding='utf-8').write(
                fm(title=p['title'].replace('"', '”'), weight=j)
                + '\n' + '\n\n'.join(p['body']) + '\n')


def main():
    for b in BOOKS:
        vols = parse(b)
        np = sum(len(v['pieces']) for v in vols)
        nc = sum(han(p['title']) + han(''.join(p['body']))
                 for v in vols for p in v['pieces'])
        print('%-12s 卷 %3d · 篇 %4d · 汉字 %7d' % (b['title'], len(vols), np, nc))
        if '-v' in sys.argv:
            for v in vols:
                print('   [%s] %s' % (v['title'],
                                      ' / '.join(p['title'] for p in v['pieces'])))
        if WRITE:
            write(b, vols)
    print('已写入' if WRITE else '(dry-run，加 --write 落盘)')


if __name__ == '__main__':
    main()
