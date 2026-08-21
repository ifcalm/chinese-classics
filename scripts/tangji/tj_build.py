# -*- coding: utf-8 -*-
"""唐人別集·據 chinese-poetry `poet.tang.*.json` 輯錄。

**為何用這個源而非維基文庫**：維基文庫沒有唐宋人別集的錄文——山谷集、劍南詩稿、
淮海集、李義山詩集等頁面根本不存在，樊川文集/王子安集/誠齋集只有 `<pages index=…djvu/>`
掃描頁殼（卷首 16–640 字、標點率 0%）。而站內既有的《王右丞集》403 首與
`poet.tang` 王維 403 首逐首吻合，說明現有唐人集本就出自此源，體例現成。

**體例**（與站內既有四家完全一致，不另立）：
  title      ← 源 title 原樣
  正文       ← paragraphs 逐條作段落，段間空行
  weight     ← 該作者詩在源檔中的出現序（1-based）
  書 weight  ← 作者生年（站內別集通例：陶淵明 365、李白 701、蘇軾 1037）

**唯一的刪**：今人按語（見 tj_clean）。不改字、不補字、不去重——源中同題異文
可能是不同版本而非重複錄入，擅刪即改動底本。字形問題一律掛帳。
"""
import json, glob, os, re, sys, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tj_clean as C

SRC = os.environ.get('CP_DIR', '')            # chinese-poetry 檢出目錄
DEST = 'base-data/literature'

# 生年撞車時用小數插空（站內先例 w35.1、子部 21.1）：
#   劉禹錫 772 撞白居易 772、賈島 779 撞元稹 779
BOOKS = [
    dict(poet='孟浩然',   slug='meng-hao-ran-ji',   title='孟浩然集',   w=689,
         summary='孟浩然存世诗作，据《全唐诗》辑录，盛唐山水田园派代表，清淡自然、兴象玲珑。'),
    dict(poet='王昌齡',   slug='wang-chang-ling-ji', title='王昌龄集',  w=698,
         summary='王昌龄存世诗作，据《全唐诗》辑录，「七绝圣手」，边塞与闺怨兼擅。'),
    dict(poet='高適',     slug='gao-chang-shi-ji',  title='高常侍集',   w=704,
         summary='高适存世诗作，据《全唐诗》辑录，边塞诗派健者，气骨琅然、悲壮浑厚。'),
    dict(poet='岑參',     slug='cen-jia-zhou-ji',   title='岑嘉州集',   w=715,
         summary='岑参存世诗作，据《全唐诗》辑录，边塞诗派巨擘，奇峭瑰丽、雄奇壮阔。'),
    dict(poet='韋應物',   slug='wei-su-zhou-ji',    title='韦苏州集',   w=737,
         summary='韦应物存世诗作，据《全唐诗》辑录，山水田园承陶谢之绪，高雅闲淡、澄澹精致。'),
    dict(poet='孟郊',     slug='meng-dong-ye-ji',   title='孟东野诗集', w=751,
         summary='孟郊存世诗作，据《全唐诗》辑录，与贾岛并称「郊寒岛瘦」，苦吟险奥、寒峭刻深。'),
    dict(poet='劉禹錫',   slug='liu-bin-ke-ji',     title='刘宾客集',   w=772.1,
         summary='刘禹锡存世诗作，据《全唐诗》辑录，「诗豪」豪迈爽朗，竹枝词开民歌入诗一路。'),
    dict(poet='元稹',     slug='yuan-shi-chang-qing-ji', title='元氏长庆集', w=779,
         summary='元稹存世诗作，据《全唐诗》辑录，与白居易并称「元白」，新乐府运动主将，艳情与悼亡兼工。'),
    dict(poet='賈島',     slug='chang-jiang-ji',    title='长江集',     w=779.1,
         summary='贾岛存世诗作，据《全唐诗》辑录，苦吟诗人代表，「推敲」典出其手，清奇僻苦。'),
    dict(poet='李賀',     slug='li-chang-ji-ge-shi', title='李长吉歌诗', w=790,
         summary='李贺存世诗作，据《全唐诗》辑录，「诗鬼」想象诡谲、设色秾丽，长吉体独绝。'),
    dict(poet='杜牧',     slug='fan-chuan-ji',      title='樊川集',     w=803,
         summary='杜牧存世诗作，据《全唐诗》辑录，与李商隐并称「小李杜」，俊爽绮丽、咏史绝句冠绝晚唐。'),
    dict(poet='溫庭筠',   slug='wen-fei-qing-ji',   title='温飞卿集',   w=812,
         summary='温庭筠存世诗作，据《全唐诗》辑录，词为花间鼻祖，诗则秾艳精工、律绝并擅。'),
    dict(poet='李商隱',   slug='li-yi-shan-ji',     title='李义山集',   w=813,
         summary='李商隐存世诗作，据《全唐诗》辑录，晚唐诗坛巨擘，无题诗深情绵邈、用典精丽。'),
]


def files():
    fs = glob.glob(os.path.join(SRC, '全唐诗', 'poet.tang.*.json'))
    if not fs:
        sys.exit('未找到 poet.tang.*.json，请设 CP_DIR')
    # 按檔名中的序號排序——落盤次序即源檔次序，站內既有四家同此
    return sorted(fs, key=lambda x: int(os.path.basename(x).split('.')[2]))


def collect():
    want = {b['poet']: [] for b in BOOKS}
    for f in files():
        for p in json.load(open(f, encoding='utf-8')):
            a = (p.get('author') or '').strip()
            if a in want:
                want[a].append(p)
    return want


def fm(title, weight):
    return '---\ntitle: "%s"\nweight: %s\n---\n' % (title, weight)


# 站內既有四家不含這些字，逐字比對源檔用作字形體檢
SIMP = '来为国无与从东车马门闻听读时会说语汉铁银钱风飞鸟鱼虫龙岁归书画个们这么样对开关长发'
ODD = re.compile(r'[�□■]')


def main():
    data = collect()
    rows = []
    for b in BOOKS:
        ps = data[b['poet']]
        d = os.path.join(DEST, b['slug'])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, '_index.md'), 'w', encoding='utf-8').write(
            '---\ntitle: "%s"\nweight: %s\nkind: "book"\nauthor: "%s"\ndynasty: "唐"\nsummary: "%s"\n---\n'
            % (b['title'], b['w'], b['poet'], b['summary']))

        simp = collections.Counter()
        odd = chars = cut = skip = 0
        seen = collections.Counter()
        i = 0
        for p in ps:
            # 標題裏也嵌校記號（高適《遇崔二[一]有別》、王昌齡《城旁□□[一]…》），
            # 同屬今人校勘的腳手架，一併去
            t = C.SUP.sub('', C.MARK.sub('', (p.get('title') or ''))).strip()
            paras, dropped = C.clean(p.get('paragraphs', []))
            cut += len(dropped)
            if not t.strip() or not paras:      # 源中的空行與「存目」條
                skip += 1
                continue
            # 標題本身也可能整條是按語（孟浩然《送張舍人往江東（…詩同，不重錄…）》）
            body = '\n\n'.join(paras)
            i += 1
            for ch in t + body:
                if ch in SIMP:
                    simp[ch] += 1
            odd += len(ODD.findall(t + body))
            chars += len(re.findall(r'[一-鿿]', body))
            seen[(t, body)] += 1
            open(os.path.join(d, '%04d.md' % i), 'w', encoding='utf-8').write(
                fm(t.replace('"', '”'), i) + '\n' + body + '\n')
        dup = sum(v - 1 for v in seen.values() if v > 1)
        rows.append((b['title'], b['poet'], i, chars, sum(simp.values()), odd, dup, cut, skip))

    print('%-12s %-6s %6s %9s %5s %5s %5s %5s %5s'
          % ('书', '作者', '首', '汉字', '简体', '缺字', '重出', '剥离', '不收'))
    for t, a, n, c, sp, o, dp, cut, skip in rows:
        print('%-12s %-6s %6d %9d %5d %5d %5d %5d %5d'
              % (t, a, n, c, sp, o, dp, cut, skip))
    print('合计 %d 首 · %d 汉字；剥离今人按语 %d 块，不收空条 %d'
          % (sum(r[2] for r in rows), sum(r[3] for r in rows),
             sum(r[7] for r in rows), sum(r[8] for r in rows)))


if __name__ == '__main__':
    main()
