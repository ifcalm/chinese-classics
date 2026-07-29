#!/usr/bin/env python3
"""道家 C 批落盘：base-data/taoism/<组>/<slug>/。篇名一律简体（站内铁律）。"""
import html, json, os, re, shutil, subprocess
BASE = '/Users/lishuaishuai/Projects/githubProjects/chinese-classics/base-data/taoism'
UA = 'chinese-classics-collector/1.0 (ifcalm.ok@gmail.com)'
HZ = re.compile(r'[一-鿿㐀-䶿\U00020000-\U0003FFFF]')

CONF = {
 '性命圭旨': ('alchemy', 'xingming-guizhi', 45, '性命圭旨',
   '明·佚名（旧题尹真人高弟）。性命双修内丹要籍，元亨利贞四集三十三说，'
   '为明清内丹学最流行的读本。据维基文库《正统道藏》整理本收录（繁体）。'
   '原书图五十三幅，本站只收文字，图题以〔图：…〕存目。'),
 '玉清金笥青華秘文金寶內鍊丹訣': ('alchemy', 'qinghua-miwen', 35.1, '青华秘文',
   '北宋·张伯端。简称《金华秘文》，与《悟真篇》同出紫阳真人，'
   '以心为君、神为主、气为用立论，详下手功夫。据维基文库整理本收录（繁体）。'),
 '谷神篇': ('alchemy', 'gushen-pian', 39, '谷神篇',
   '元·林辕（玄巢子）。分上下两卷，以诗歌口诀论内丹，力辨神仙与道家之别。'
   '据维基文库《正统道藏》整理本收录（繁体）。原书有图数幅，底本已缺，存目不存图。'),
 '太上感應篇集註': ('ethics', 'ganying-pian-jizhu', 11, '太上感应篇集注',
   '清·佚名辑，康熙四十五年陈廷敬序。《太上感应篇》历代注本中流传最广者，'
   '先发明义理、后证以事实。经文作引用块、注文作正文，同《老子河上公章句》体例。'
   '据维基文库整理本收录（繁体）。'),
 '淨明忠孝全書': ('ethics', 'jingming-zhongxiao-quanshu', 35, '净明忠孝全书',
   '元·黄元吉编集，徐慧校正。净明道根本典籍，六卷附序，'
   '收许逊等祖师传记、坛记道说与玉真先生语录内外别集，主「欲修仙道先修人道」。'
   '据维基文库《正统道藏》整理本收录（繁体）。'),
 '太上洞玄靈寶赤書玉訣妙經': ('ritual', 'chishu-yujue', 39, '赤书玉诀',
   '约东晋出，古《灵宝经》之一，二卷。与《度人经》同系，述五帝真文之奉持科仪。'
   '据维基文库《正统道藏》洞玄部本文类整理本收录（繁体）。符文缺字以□存阙。'),
 '一切道經音義妙門由起': ('classics', 'miaomen-youqi', 50, '一切道经音义妙门由起',
   '唐·史崇玄等奉敕撰，唐玄宗御制序。原书一百十三卷，今仅存序文与《妙门由起》一卷，'
   '为唐代官修道经音义之遗。据维基文库《正统道藏》太平部整理本收录（繁体）。'),
 '疑仙傳': ('immortals', 'yixian-zhuan', 35, '疑仙传',
   '旧题宋·隐夫玉简。三卷，录唐宋间疑似仙迹之人二十余则，'
   '作者自谓「不敢便以神仙为名」，故曰「疑仙」。据维基文库《正统道藏》整理本收录（繁体）。'),
}


def to_simp(lines, key):
    p = 'ws-cache/%s.json' % key
    if os.path.exists(p):
        return json.load(open(p, encoding='utf-8'))['t']
    cmd = ['curl', '-4', '-s', '-H', 'User-Agent: ' + UA]
    for a, b in [('action', 'parse'), ('text', '\n'.join(lines)), ('contentmodel', 'wikitext'),
                 ('variant', 'zh-hans'), ('prop', 'text'), ('format', 'json'),
                 ('formatversion', '2'), ('wrapoutputclass', '')]:
        cmd += ['--data-urlencode', '%s=%s' % (a, b)]
    cmd.append('https://zh.wikisource.org/w/api.php')
    d = json.loads(subprocess.run(cmd, capture_output=True, text=True).stdout)
    t = html.unescape(re.sub(r'<[^>]+>', '', d['parse']['text']))
    # 渲染出的节编辑链接文本会混进标题
    out = [re.sub(r'\s*\[(?:编辑|編輯|edit)\]\s*$', '', x).strip()
           for x in t.split('\n') if x.strip()]
    json.dump({'t': out}, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
    return out


P = json.load(open('c-parsed.json', encoding='utf-8'))
tot_p = tot_c = 0
for book, d in P.items():
    grp, slug, w, zh, summ = CONF[book]
    titles = [re.sub(r'^\[\[|\]\]$', '', x['title']).strip() for x in d['items']]
    simp = to_simp(titles, 'ctitle-' + slug)
    if len(simp) != len(titles):
        raise SystemExit('!! %s 转简 %d≠%d' % (book, len(simp), len(titles)))
    out = os.path.join(BASE, grp, slug)
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)
    ws = ('%g' % w)
    open(os.path.join(out, '_index.md'), 'w', encoding='utf-8').write(
        '---\ntitle: "%s"\nweight: %s\nkind: "book"\nsummary: "%s"\n---\n\n' % (zh, ws, summ))
    n = 0
    for i, (x, s) in enumerate(zip(d['items'], simp), 1):
        body = '\n\n'.join(x['blocks'])
        open(os.path.join(out, '%02d.md' % i), 'w', encoding='utf-8').write(
            '---\ntitle: "%s"\nweight: %d\n---\n\n%s\n' % (s.replace('"', '”'), i, body))
        n += len(HZ.findall(body))
    tot_p += len(d['items']); tot_c += n
    print('%-26s → taoism/%s/%s  w%-5s %2d 篇 %6d 字' % (zh, grp, slug, ws, len(d['items']), n))
print('\n合计 8 部 %d 篇 %d 汉字 (%.2f 万)' % (tot_p, tot_c, tot_c / 10000))
