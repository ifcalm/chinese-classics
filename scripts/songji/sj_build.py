# -*- coding: utf-8 -*-
"""宋人別集·據 chinese-poetry `poet.song.*.json`（全宋詩）輯錄。

與唐人十三家（`scripts/tangji/`）同源同體例，清洗器直接復用 `tj_clean`。
實測本批十六家**一條今人按語也沒有**（唐人那批的按語來自《全唐詩補編》，
全宋詩這份數據沒帶），故剝離數為零；清洗器仍照跑，作把關用。

**只收站內沒有詩文集的作者**：歐陽修（歐陽修集）、蘇軾（東坡全集）、蘇轍
（欒城集）、王安石（王臨川集）、曾鞏（元豐類稿）已有維基文庫整理的全集，
再從全宋詩抓一份詩會與之重出。

**字形掛帳**：陸游 9,271 首中有 390 首各夾一個「来」（合計 411 處，另「无」1 處），
是錄入殘留而非底本簡體；按鐵律簡→繁屬改字，一律不動，掛帳於 known-issues。
其餘十五家零簡體。

**書 weight 取作者生年**（站內別集通例）；與既有詞集撞號的用小數插空——
放翁詞 1125 / 劍南詩稿 1125.1，山谷詞 1045 / 山谷詩集 1045.1，餘同。
"""
import json, glob, os, re, sys, collections

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), 'tangji'))
import tj_clean as C

SRC = os.environ.get('CP_DIR', '')
DEST = 'base-data/literature'

BOOKS = [
 dict(poet='林逋',   slug='lin-he-jing-ji',   title='林和靖集',     w=967,
      summary='林逋存世诗作，据《全宋诗》辑录。西湖孤山处士，梅妻鹤子，「疏影横斜水清浅」擅名千古。'),
 dict(poet='梅堯臣', slug='wan-ling-ji',      title='宛陵集',       w=1002,
      summary='梅尧臣存世诗作，据《全宋诗》辑录。与欧阳修同倡诗文革新，宋诗开山，平淡而山高水深。'),
 dict(poet='邵雍',   slug='yi-chuan-ji-rang-ji', title='伊川击壤集', w=1011,
      summary='邵雍存世诗作，据《全宋诗》辑录。理学家以诗说理，安乐窝中自适之趣，别成一体。'),
 dict(poet='黄庭堅', slug='shan-gu-shi-ji',   title='山谷诗集',     w=1045.1,
      summary='黄庭坚存世诗作，据《全宋诗》辑录。江西诗派宗主，点铁成金、夺胎换骨，瘦硬奇崛。'),
 dict(poet='秦觀',   slug='huai-hai-ji',      title='淮海集',       w=1049.1,
      summary='秦观存世诗作，据《全宋诗》辑录。少游诗如「女郎诗」之评虽苛，清丽婉约自成一格。'),
 dict(poet='賀鑄',   slug='qing-hu-yi-lao-shi-ji', title='庆湖遗老诗集', w=1052.1,
      summary='贺铸存世诗作，据《全宋诗》辑录。词名掩其诗，然诗亦沉郁雄放，工于锻炼。'),
 dict(poet='陳師道', slug='hou-shan-ji',      title='后山集',       w=1053,
      summary='陈师道存世诗作，据《全宋诗》辑录。江西诗派三宗之一，闭门觅句、瘦硬苦吟。'),
 dict(poet='張耒',   slug='ke-shan-ji',       title='柯山集',       w=1054,
      summary='张耒存世诗作，据《全宋诗》辑录。苏门四学士之一，诗务平易晓畅，近白居易一路。'),
 dict(poet='陸游',   slug='jian-nan-shi-gao', title='剑南诗稿',     w=1125.1,
      summary='陆游存世诗作，据《全宋诗》辑录，九千二百馀首，古今存诗最富者。爱国之志与闲适之趣兼具。'),
 dict(poet='范成大', slug='shi-hu-ju-shi-shi-ji', title='石湖居士诗集', w=1126,
      summary='范成大存世诗作，据《全宋诗》辑录。南宋四大家之一，《四时田园杂兴》为田园诗之集成。'),
 dict(poet='楊萬里', slug='cheng-zhai-ji',    title='诚斋集',       w=1127,
      summary='杨万里存世诗作，据《全宋诗》辑录。「诚斋体」活法自然、生趣盎然，南宋四大家之一。'),
 dict(poet='朱熹',   slug='hui-an-shi-ji',    title='晦庵诗集',     w=1130,
      summary='朱熹存世诗作，据《全宋诗》辑录。理学宗师之诗，理趣与清景并出，《观书有感》最脍炙人口。'),
 dict(poet='姜夔',   slug='bai-shi-dao-ren-shi-ji', title='白石道人诗集', w=1154.1,
      summary='姜夔存世诗作，据《全宋诗》辑录。词名之外，诗亦清刚峭拔，别有《白石道人诗说》论其法。'),
 dict(poet='戴復古', slug='shi-ping-shi-ji',  title='石屏诗集',     w=1167,
      summary='戴复古存世诗作，据《全宋诗》辑录。江湖诗派领袖，布衣终身，诗多感慨时事、纪行写景。'),
 dict(poet='劉克莊', slug='hou-cun-ji',       title='后村集',       w=1187.1,
      summary='刘克庄存世诗作，据《全宋诗》辑录，四千五百馀首。江湖诗派巨擘，辛派后劲，议论纵横。'),
 dict(poet='文天祥', slug='wen-shan-ji',      title='文山集',       w=1236,
      summary='文天祥存世诗作，据《全宋诗》辑录。《指南录》《正气歌》皆在其中，忠愤之气烛照千古。'),
]

# 這批繁體本裏零星夾入的簡體字形（陸游 411 處「来」為大宗）：只統計、不改
SIMP = '来为国无与从东车马门时会说汉铁风鸟鱼虫龙岁归书画对开关长发'
ODD = re.compile(r'[�□■]')
HAN = re.compile(r'[一-鿿]')


def files():
    fs = glob.glob(os.path.join(SRC, '全唐诗', 'poet.song.*.json'))
    if not fs:
        sys.exit('未找到 poet.song.*.json，请设 CP_DIR')
    return sorted(fs, key=lambda x: int(os.path.basename(x).split('.')[2]))


def fm(title, weight):
    return '---\ntitle: "%s"\nweight: %s\n---\n' % (title, weight)


def main():
    want = {b['poet']: [] for b in BOOKS}
    for f in files():
        for p in json.load(open(f, encoding='utf-8')):
            a = (p.get('author') or '').strip()
            if a in want:
                want[a].append(p)

    rows = []
    for b in BOOKS:
        d = os.path.join(DEST, b['slug'])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, '_index.md'), 'w', encoding='utf-8').write(
            '---\ntitle: "%s"\nweight: %s\nkind: "book"\nauthor: "%s"\ndynasty: "%s"\n'
            'summary: "%s"\n---\n'
            % (b['title'], b['w'], b['poet'],
               '南宋' if b['w'] >= 1125 else '北宋', b['summary']))
        i = simp = odd = chars = cut = skip = 0
        seen = collections.Counter()
        for p in want[b['poet']]:
            t = C.SUP.sub('', C.MARK.sub('', (p.get('title') or ''))).strip()
            paras, dropped = C.clean(p.get('paragraphs', []))
            cut += len(dropped)
            if not t or not paras:
                skip += 1
                continue
            body = '\n\n'.join(paras)
            i += 1
            simp += sum(body.count(c) for c in SIMP)
            odd += len(ODD.findall(body))
            chars += len(HAN.findall(body))
            seen[(t, body)] += 1
            open(os.path.join(d, '%04d.md' % i), 'w', encoding='utf-8').write(
                fm(t.replace('"', '”'), i) + '\n' + body + '\n')
        rows.append((b['title'], b['poet'], i, chars, simp, odd,
                     sum(v - 1 for v in seen.values() if v > 1), cut, skip))

    print('%-14s %-5s %6s %9s %5s %5s %5s %5s %5s'
          % ('书', '作者', '首', '汉字', '简体', '缺字', '重出', '剥离', '不收'))
    for r in rows:
        print('%-14s %-5s %6d %9d %5d %5d %5d %5d %5d' % r)
    print('合计 %d 部 · %d 首 · %d 汉字；简体 %d、剥离 %d、不收 %d'
          % (len(rows), sum(r[2] for r in rows), sum(r[3] for r in rows),
             sum(r[4] for r in rows), sum(r[7] for r in rows), sum(r[8] for r in rows)))


if __name__ == '__main__':
    main()
