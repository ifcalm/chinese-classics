# -*- coding: utf-8 -*-
"""堪舆二部 ← 殆知阁本（简体）：《地理人子须知》《山洋指迷》。

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

**已知讹字**（见 docs/known-issues.md）：殆知阁本有 IT 词表串入之讹，
《人子须知》两处「李维祯」作「利瓦伊祯／利瓦伊桢」（LeVi→利瓦伊），一处在弃收的
郢中序、一处在卷七上之二正文内。**照收不改**——只删不改不增是铁律。

用法: python3 scripts/parse-kanyu.py [--write]
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
PUNCT = '。，、；：？！“”‘’「」《》〈〉（）()·…—:;,.?!"\''
BODYMIN = 60          # 标题之后须有这么多汉字，才算标题而非图说残题
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


def norm(s):
    return re.sub(r'\s+', '', s)


def is_title(s):
    return 0 < len(s) <= TITLEMAX and not any(c in PUNCT for c in s) and HAN.search(s)


def parse(b):
    raw = open(os.path.join(SRC, b['src'] + '.txt'), encoding='utf-8').read()
    lines = raw.split('\n')[b.get('skip_head', 0):]
    if b.get('paren'):
        lines = [strip_paren(x) for x in lines]
    lines = [norm(x) if is_title(norm(x)) else x.strip() for x in lines]

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
            if is_title(s):
                j, acc = i + 1, 0
                while j < len(L) and not is_title(L[j]):
                    acc += han(L[j]); j += 1
                if acc >= BODYMIN:
                    ps.append({'title': s, 'body': L[i + 1:j]})
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
