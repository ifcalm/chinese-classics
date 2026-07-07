# ================= 批② 京氏易传/正易心法/五行大义/乙巳占/灵城精义 =================
# (由 parse-shushu.py 通过 exec 注入执行,与批①共用 clean/collate/write_book 等设施)

def collate_report(body, ref_h, label):
    # 仅报告不改字(用于与殆知阁同源或无权威witness的比对)
    a = han(body)
    aa, bb = t2s(a), t2s(ref_h)
    sm = difflib.SequenceMatcher(None, aa, bb, autojunk=False)
    ops = [o for o in sm.get_opcodes() if o[0] != 'equal']
    big = [o for o in ops if max(o[2]-o[1], o[4]-o[3]) > 4]
    print(f'  [{label}] 汉字{len(a)} 对照差异块 {len(ops)}(大块 {len(big)})')
    for tag, a1, a2, b1, b2 in big[:20]:
        print('     ?', tag, repr(aa[max(0,a1-8):a2+8][:60]), '||', repr(bb[max(0,b1-8):b2+8][:60]))
    return len(ops)

def build_jingshi():
    t = w('京氏易傳')
    # 整理者校语 2 条,剥离(其余 {{*|}} 为陆绩注)
    t = t.replace('{{*|誤作「三百六十四爻」。}}', '').replace('{{*|此數為《系辭上》揲蓍之數。}}', '')
    # 卷末宋人后语(商瞿传承源流至「積算雜占條例法具如別錄」)被整理者误套注模板,解开作正文
    j = t.find('{{*|前是')
    assert j > 0
    k = t.find('\n}}', j)
    t = t[:j] + t[j+4:k] + t[k+3:]
    i = t.find('{|')
    if i > 0: t = t[:i]  # 尾部八宫卦序表为整理者所加图示,删(收录日志披露)
    t = clean(t, 'paren')
    t = re.sub(r'^[:：]+', '', t, flags=re.M)  # wiki 缩进
    parts = re.split(r'^==(京氏易傳卷[上中下])==\s*$', t, flags=re.M)
    chs = []
    for k in range(1, len(parts), 2):
        ttl = parts[k].replace('京氏易傳', '')
        chs.append((ttl, len(chs) + 1, to_paras(parts[k+1])))
    assert len(chs) == 3, len(chs)
    body = '\n'.join('\n'.join(p) for _, _, p in chs)
    skref = ''.join(sk_hanref(w('京氏易傳(四庫全書本)__卷' + j), keep_notes=True) for j in '上中下')
    dz = open(os.path.join(DZG, '京氏易传.txt'), encoding='utf-8').read()
    fixed = collate(body, skref, dz, '京氏易传')
    parts2 = fixed.split('\n'); k = 0; out = []
    for ttl, wt, paras in chs:
        out.append((ttl, wt, parts2[k:k+len(paras)])); k += len(paras)
    write_book('jing-shi-yi-zhuan', 'zhanbu', {
        'title': '京氏易传', 'weight': 5, 'kind': 'book',
        'summary': '汉京房撰，吴陆绩注，三卷。今存京氏易学之硕果，八宫卦、纳甲、飞伏、世应之说悉本此书，后世纳甲筮法之远祖。据维基文库整理本收录（陆绩注转括注），校以四库全书本转录。'
    }, out)

def build_zhengyixinfa():
    t = open(os.path.join(DZG, '正易心法.txt'), encoding='utf-8').read()
    lines = [l.strip() for l in t.split('\n') if l.strip()]
    # 行0=题署,行1=陈希夷传(编者所加传记,剥);正文至李潜书后前
    i_sh = next(i for i, l in enumerate(lines) if '顷得之庐山' in l)
    i_ba = next(i for i, l in enumerate(lines) if l == '跋' or l.startswith('跋 ') or l.rstrip() == '跋')
    def fix(l):
        l = l.replace('重为64', '重为六十四').replace('64卦', '六十四卦')
        l = l.replace('三月九曰', '三月九日').replace('初七曰', '初七日')
        return l
    body_lines = [fix(l) for l in lines[2:min(i_sh, i_ba)]]
    shuhou = [fix(l) for l in lines[i_sh:i_ba] if l != '书后']
    ba = [fix(l) for l in lines[i_ba:] if l.strip() != '跋']
    wsb = w('正易心法')
    zhang = [l for l in body_lines if re.search(r'[一二三四五六七八九十]+章$', l)]
    miss = sum(1 for z in zhang if z[:4] not in wsb)
    print(f'  [正易心法] 章数 {len(zhang)}(应42) 章首四字不见于维基白文: {miss}(异文仅报告)')
    chs = [('正文四十二章', 1, body_lines), ('书后', 2, shuhou), ('跋', 3, ba)]
    write_book('zheng-yi-xin-fa', 'zhanbu', {
        'title': '正易心法', 'weight': 15, 'kind': 'book',
        'summary': '旧题麻衣道者撰、陈抟注（消息），四十二章章四句，朱熹考为南宋人依托（或即跋者戴师愈）。主张学易者当于羲皇心地中驰骋、勿于周孔脚迹下盘旋，宋代易学史名篇。附宋李潜书后（崇宁三年）、戴师愈跋（乾道元年）。据殆知阁本收录（简体），章句与维基文库录文互校。'
    }, chs)

def build_wuxingdayi():
    main = clean(w('五行大義'))
    mparas = to_paras(main)
    i_ba = next(i for i, p in enumerate(mparas) if '天瀑' in p)
    # 序 = 跋以前、去掉「==五行大義序==」标题与撰署行
    xu = [p for p in mparas[:i_ba] if not p.startswith('## ')]
    ba_paras = mparas[i_ba:]
    # 跋起点回溯:天瀑跋可能不止一段,向前找到跋首段(非序文)
    chs = [('序', 1, xu)]
    hanzi_num = '一二三四五'
    for k in range(1, 6):
        t = clean(w('五行大義__' + str(k)))
        t = re.sub(r'^[:：]+', '', t, flags=re.M)
        chs.append(('卷' + hanzi_num[k-1], k + 1, to_paras(t)))
    chs.append(('跋', 7, ba_paras))
    body = '\n'.join('\n'.join(p) for _, _, p in chs)
    dz = open(os.path.join(DZG, '五行大义.txt'), encoding='utf-8').read()
    collate_report(body, han(dz), '五行大义')
    write_book('wu-xing-da-yi', 'wuxing', {
        'title': '五行大义', 'weight': 10, 'kind': 'book',
        'summary': '隋萧吉撰，五卷二十四段。集汉魏以来阴阳五行说之大成，文章醇古，援证多存佚亡之书，中土久佚，赖日本传本以存，清季自东瀛复归（佚存丛书本，附日本刊行者跋）。据维基文库转录收录（原书句读体，与殆知阁本互校）。'
    }, chs)

# 卷十「君臣品位立成」表:维基整理本按官位逐列平铺、无句读,读者不可通读。
# 据殆知阁本(十万卷楼丛书系统)行序,重排为春/夏/秋/冬四季顺读并补句读,
# 顺带正孤立 AMBIG 讹字「醜」→「丑」。四季二十官已与殆知阁逐格核对无误。
_YSZ_PINWEI_ROWS = [
    '春三月：寅為皇后，甲為天子，卯為太子，乙為太子妻，辰為太子吏，巳為司空，丙為司徒，午為太尉，丁為太傅（又云國師），未為九卿，申為司隸，庚為詔獄，酉為庶民，辛為卒徒，戌為夷狄，亥為宗廟，壬為內相，子為宮府，癸為內藏，丑為大將軍。',
    '夏三月：巳為皇后，丙為天子，午為太子，丁為太子妻，未為太子吏，申為司空，庚為司徒，酉為太尉，辛為太傅（又云上），戌為九卿，亥為司隸，壬為詔獄，子為庶民，癸為卒徒，丑為夷狄，寅為宗廟，甲為內相，卯為宮府，乙為內藏，辰為大將軍。',
    '秋三月：申為皇后，庚為天子，酉為太子，辛為太子妻，戌為太子吏，亥為司空，壬為司徒，子為太尉，癸為太傅（又云上），丑為九卿，寅為司隸，甲為詔獄，卯為庶民，乙為卒徒，辰為夷狄，巳為宗廟，丙為內相，午為宮府，丁為內藏，未為大將軍。',
    '冬三月：亥為皇后，壬為天子，子為太子，癸為太子妻，丑為太子吏，寅為司空，甲為司徒，卯為太尉，乙為太傅（又云上），辰為九卿，巳為司隸，丙為詔獄，午為庶民，丁為卒徒，未為夷狄，申為宗廟，庚為內相，酉為宮府，辛為內藏，戌為大將軍。',
]

def _ysz_fix_pinwei(t):
    a = t.find('君臣品位立成。')
    end_mark = '醜為大將軍辰為大將軍未為大將軍戌為大將軍'
    b = t.find(end_mark)
    assert a >= 0 and b > a, ('乙巳占品位立成段未定位', a, b)
    b += len(end_mark)
    rep = '君臣品位立成。\n\n' + '\n\n'.join(_YSZ_PINWEI_ROWS)
    return t[:a] + rep + t[b:]

# 卷十「三辰八角風」表同为无句读平铺:三辰(四三合局)×八卦对照。维基本此段
# 首行衍四「〓」残符、「己酉醜」讹(应作「巳酉丑」),据殆知阁本补正为四行顺读。
_YSZ_SANCHEN_ROWS = [
    '申子辰之日：艮震巽離坤兌乾坎。',
    '巳酉丑之日：巽離坤兌乾坎艮震。',
    '亥卯未之日：乾坎艮震巽離坤兌。',
    '寅午戌之日：坤兌乾坎艮震巽離。',
]

def _ysz_fix_sanchen(t):
    a = t.find('三辰八角風。')
    b = t.find('風從辱上來')  # 表后接正文散句,以此为界
    assert a >= 0 and b > a, ('乙巳占三辰八角段未定位', a, b)
    rep = '三辰八角風。辱殺反吉抵誣誕忿爭\n\n' + '\n\n'.join(_YSZ_SANCHEN_ROWS) + '\n\n'
    return t[:a] + rep + t[b:]

# 卷十地支「巳」讹作天干「己」的校正:仅改逐处经殆知阁本核实为「巳」者(三合金局
# 巳酉丑之「巳酉」、六情占「時加巳酉」、「巳亥」等),干支/天干/纳甲/纪日之「己」一概不动。
# (n=预期替换次数,防误伤;须在替「醜」前,但本组键不含「醜」,先后皆可。)
_YSZ_JISI = [
    ('己酉為寬大之日', '巳酉為寬大之日', 1),
    ('假令己酉注寬大之日', '假令巳酉注寬大之日', 1),
    ('時加己酉，鳥', '時加巳酉，鳥', 5),   # 六情占系列(鳥鳴其上×3、鳥來鳴×2);「為貴客」「止王相」之己酉不改
    ('更轉己酉上來', '更轉巳酉上來', 1),
    ('時加己亥為重角', '時加巳亥為重角', 1),
    ('令長有憂喪。己亥之日', '令長有憂喪。巳亥之日', 1),
]

def _ysz_fix_jisi(t):
    for old, new, n in _YSZ_JISI:
        assert t.count(old) == n, ('乙巳占己巳校正计数异常', old, t.count(old), n)
        t = t.replace(old, new)
    return t

def build_yisizhan():
    xu = to_paras(clean(w('乙巳占序')))
    hanzi_num = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
    chs = [('序', 1, xu)]
    for k in range(1, 11):
        t = clean(w('乙巳占__' + str(k)))
        t = re.sub(r'^卷[一二三四五六七八九十]+\s*$', '', t, flags=re.M)
        t = t.replace('==○', '==')
        if k == 10:
            t = _ysz_fix_sanchen(t)  # 须在替醜前
            t = _ysz_fix_pinwei(t)   # 须在替醜前:定位标记含「醜」
            t = _ysz_fix_jisi(t)     # 巳讹作己的逐处校正
        # 全书地支「醜」一律正作「丑」:已逐处核验本书 47 例「醜」皆地支丑,
        # 无「美醜/醜陋」义(整本为星占技术文,维基整理本通体误丑作醜)。
        t = t.replace('醜', '丑')
        chs.append(('卷' + hanzi_num[k-1], k + 1, to_paras(t)))
    body = '\n'.join('\n'.join(p) for _, _, p in chs)
    dz = open(os.path.join(DZG, '乙巳占.txt'), encoding='utf-8').read()
    collate_report(body, han(dz), '乙巳占')
    write_book('yi-si-zhan', 'zhanhou', {
        'title': '乙巳占', 'weight': 10, 'kind': 'book',
        'summary': '唐李淳风撰，十卷一百篇（辨惑第二十原阙）。现存最早的系统天文星占著作之一，天象、日月、五星、云气、候风之占悉备，兼存张衡《灵宪》等佚籍遗文，天文学史要籍。据维基文库整理本收录，与殆知阁本（十万卷楼丛书系统）互校；卷十「君臣品位立成」「三辰八角风」二表原为无句读平铺，据殆知阁本行序重排并补句读。'
    }, chs)

def build_lingcheng():
    t = clean(w('靈城精義'), 'paren')
    parts = re.split(r'^==(形氣章|理氣章)==\s*$', t, flags=re.M)
    chs = []
    for k in range(1, len(parts), 2):
        chs.append((parts[k], len(chs) + 1, to_paras(parts[k+1])))
    assert len(chs) == 2
    body = '\n'.join('\n'.join(p) for _, _, p in chs)
    skref = sk_hanref(w('靈城精義(四庫全書本)__卷上'), keep_notes=True) + sk_hanref(w('靈城精義(四庫全書本)__卷下'), keep_notes=True)
    dz = open(os.path.join(DZG, '灵城精义.txt'), encoding='utf-8').read()
    fixed = collate(body, skref, dz, '灵城精义')
    # 后置补丁:据四库补一字脱文/正机器残文(在校勘改字之后应用,故用校后文本)
    fixed = apply_patches(fixed, [
        ('全在氣運上之。', '全在氣運上卜之。'),
        ('地運之轉者如女人何謂天運', '地運之轉者如此。何謂天運'),
        ('弱不習一乘', '弱不可乘'),
        ('一廣分之氣，只取其四', '十分之氣，只取其四'),
        ('則用客堆培成墳', '則用客土堆培成墳'),
        ('即為村墳墓', '即為村市墳墓'),
    ], '灵城后校')
    parts2 = fixed.split('\n'); k = 0; out = []
    for ttl, wt, paras in chs:
        out.append((ttl, wt, parts2[k:k+len(paras)])); k += len(paras)
    write_book('ling-cheng-jing-yi', 'kanyu', {
        'title': '灵城精义', 'weight': 70, 'kind': 'book',
        'summary': '旧题南唐何溥撰，实明人依托，注题刘基亦赝。上卷形气章论山川形势，下卷理气章论天星卦例，倡三元地运之说，四库馆臣谓其言「实能得其精微，非方技之士支离诞谩者比」。经注连排一仍四库之旧。据维基文库整理本收录，校以四库全书本转录。'
    }, out)

def write_indexes2():
    if not WRITE: return
    for slug, title, wt, summ in [
        ('zhanhou', '占候', 40, '天文气象占验典籍。'),
        ('wuxing', '五行', 50, '阴阳五行理论典籍。'),
    ]:
        d = os.path.join(BASE, slug); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, '_index.md'), 'w').write(fm({
            'title': title, 'date': '2026-07-07', 'weight': wt, 'tags': ['术数'], 'draft': True,
            'summary': summ, 'showToc': False, 'tocOpen': False, 'ShowShareButtons': False
        }) + '\n' + summ + '\n')

write_indexes2()
build_jingshi()
build_zhengyixinfa()
build_wuxingdayi()
build_yisizhan()
build_lingcheng()
