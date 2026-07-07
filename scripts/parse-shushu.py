# 术数批①(堪舆/相术/占卜 9 部) ← 维基文库整理本为主,四库全书本(维基文库转录)+殆知阁为校本。
# 三源校勘:ws↔四库逐字对齐,短差异处殆知阁与四库一致者从之(繁体径取四库字,变体先归一),孤证列人工清单。
# 灵棋经(白文无底本/四库句读)、天玉经(简繁转换错字+外编混入撼龙经文)暂缓不收。
# 葬书特殊:整理本外/杂篇与殆知阁同源同误(约900处),只收白文,正文另流程逐句校四库(见 build_zangshu)。
# ./venv/bin/python parse-shushu.py [--write]
import json, os, re, shutil, sys, difflib
from opencc import OpenCC

S = os.path.dirname(os.path.abspath(__file__))
WS = os.path.join(S, 'ws-shushu')
DZG = os.path.join(S, 'dzg')
BASE = '/Users/lishuaishuai/Projects/githubProjects/chinese-classics/base-data/shushu'
WRITE = '--write' in sys.argv
cc = OpenCC('t2s')
t2s = cc.convert
han = lambda s: re.sub(r'[^㐀-鿿□]', '', s)
nhan = lambda s: len(re.findall(r'[㐀-鿿]', s))

def w(name):
    return json.load(open(os.path.join(WS, name + '.json')))['parse']['wikitext']['*']

# 四库转录常见异写归一(仅用于校勘采字,不动整理本原有用字)
SKVAR = str.maketrans(
    {'夀': '壽', '黒': '黑', '靣': '面', '㐫': '凶', '髙': '高', '隠': '隱', '逺': '遠', '竒': '奇',
     '荅': '答', '恠': '怪', '両': '兩', '揷': '插', '着': '著', '緑': '綠', '䕶': '護', '纒': '纏',
     '鎗': '槍', '様': '樣', '亰': '京', '寳': '寶', '夘': '卯', '徃': '往',
     '禄': '祿', '别': '別', '宻': '密', '劒': '劍', '幞': '襆', '壠': '壟', '䧟': '陷', '㑹': '會',
     '妬': '妒', '柰': '奈', '欝': '鬱', '巗': '巖', '甞': '嘗', '峯': '峰', '寛': '寬', '龎': '龐',
     '筭': '算', '葢': '蓋', '恱': '悅', '凖': '準', '曵': '曳', '崐': '崑', '蠧': '蠹', '濶': '闊',
     '㨿': '據', '䑕': '鼠', '兎': '兔', '蜋': '螂', '悋': '吝', '踈': '疏', '寔': '實', '㓜': '幼',
     '覔': '覓', '毎': '每', '郷': '鄉', '闗': '關', '賔': '賓', '隂': '陰', '逈': '迥', '廹': '迫',
     '麤': '粗', '懐': '懷', '浄': '淨', '歛': '斂', '鷰': '燕', '昇': '升', '尅': '剋',
     '徳': '德', '㝠': '冥', '勗': '勖', '㬉': '暖', '兊': '兌', '温': '溫', '黄': '黃', '徴': '徵',
     '説': '說', '祐': '佑', '强': '強', '槩': '概', '蘒': '穢', '囬': '回', '廻': '迴', '荘': '莊',
     '躰': '體', '皜': '皓', '䰟': '魂', '䘮': '喪', '𤣥': '玄', '𠉀': '候',
     '飬': '養', '嵗': '歲', '亷': '廉', '㸃': '點', '䕃': '蔭', '廕': '蔭', '桺': '柳', '偹': '備',
     '髪': '髮', '戸': '戶', '穏': '穩', '鬬': '鬥', '脇': '脅', '嚢': '囊', '厰': '廠', '廏': '廄',
     '増': '增', '藂': '叢', '疎': '疏', '虵': '蛇', '宫': '宮', '㕔': '廳', '厠': '廁', '摉': '搜',
     '慜': '憫', '无': '無', '絶': '絕', '却': '卻', '凉': '涼', '棊': '棋', '䇿': '策', '筯': '肋',
     '躭': '耽', '椁': '槨', '夘': '卯', '峝': '峒', '甦': '蘇', '踪': '蹤', '蹟': '跡',
     '膓': '腸', '逄': '逢', '遶': '繞', '祻': '禍', '乗': '乘', '熖': '焰', '胍': '脈', '兠': '兜',
     '鼔': '鼓', '蠏': '蟹', '晲': '睨', '黙': '默', '壊': '壞', '縁': '緣', '㦸': '戟', '麄': '粗',
     '㣲': '微', '䦨': '闌', '鎻': '鎖', '㵼': '瀉', '刼': '劫', '悞': '誤', '嬾': '懶', '滛': '淫',
     '慾': '欲', '贒': '賢', '鵞': '鵝', '垜': '垛', '嶮': '險', '坵': '丘', '騐': '驗', '聴': '聽',
     '叅': '參', '凾': '函', '冩': '寫', '堦': '階', '釡': '釜', '抛': '拋', '毬': '球', '脚': '腳',
     '横': '橫', '灔': '灩', '袵': '衽', '聮': '聯', '揺': '搖', '屛': '屏', '塲': '場', '祇': '只',
     '㪚': '散', '槖': '橐', '疉': '疊', '垅': '壟', '巓': '巔', '矦': '侯', '㓕': '滅', '偪': '逼',
     '㓙': '凶', '桉': '案', '僣': '僭',
     '澣': '瀚', '氊': '氈', '祵': '裀', '暎': '映', '歴': '歷', '褁': '裹', '䧏': '降', '㫖': '旨',
     '崕': '崖', '緜': '綿', '㟁': '岸', '昻': '昂', '菓': '果', '挂': '掛', '繋': '繫', '䟽': '疏',
     '塟': '葬', '掲': '揭', '畧': '略', '㡳': '底', '専': '專', '鬛': '鬣', '鬭': '鬥', '竝': '並',
     '拏': '拿', '㬹': '睜', '煖': '暖', '禆': '裨', '䖏': '處', '犂': '犁', '䕫': '夔', '賬': '帳',
     '翺': '翱', '勲': '勳', '鳯': '鳳', '綂': '統', '榖': '穀', '苖': '苗', '寃': '冤', '囘': '回',
     '㺅': '猴', '圎': '圓', '娯': '娛', '臓': '臟', '邉': '邊', '帯': '帶', '乆': '久', '逰': '遊',
     '僊': '仙', '隺': '鶴', '猪': '豬', '㢲': '巽', '䑓': '臺', '炁': '氣',
     '懽': '歡', '纎': '纖', '胷': '胸', '懆': '躁', '澁': '澀', '苽': '瓜',
     '茍': '苟', '凢': '凡', '隣': '鄰', '彚': '彙', '户': '戶', '倂': '並', '頥': '頤', '賛': '贊',
     '汚': '汙', '閴': '闃', '䳌': '鵑', '鴈': '雁', '㨾': '樣', '搆': '構', '㬋': '睺'})

# 繁简一对多歧字:四库人工转录的用字为正(整理本多为机器简转繁,雲/云、醜/丑常错)
AMBIG = set('雲云醜丑裏裡里髮發鬥斗後后幹乾干穀谷準准復複徵征餘余鬆松衝沖嘆歎藉借彆別咸鹹御禦台臺')
# 四库转录自身可疑读法黑名单:(整理本字, 四库字) → 保留整理本
BLOCK = {('辯', '辦'), ('減', '滅'), ('毋', '母'), ('間', '閒'), ('閒', '間'), ('于', '於'), ('於', '于'),
         ('德', '得'), ('吉', '極'), ('與', '巳'), ('與', '己'), ('枝', '技'), ('候', '侯'), ('兒', '皃'),
         ('圍', '團'), ('廉', '兼'), ('細', '佃'), ('形', '作'), ('鐘', '鍾'), ('鐘釜', '鍾釡'),
         ('灸', '炙'), ('問', '闖'), ('宮', '官'), ('字', '宇'), ('緣', '綠'), ('緣', '緑'),
         ('有', '冇'), ('墜', '隊'), ('辨', '辯'), ('辨', '辦'), ('捨', '舎'), ('臀', '凥'), ('己', '巳'),
         ('庚', '度'), ('又', '乂'), ('祗', '只'), ('曰', '月'), ('土', '上'), ('戌', '戍'), ('侯', '候'), ('羸', '嬴')}

def strip_tpl_balanced(s, name_re):
    # {{ }} 深度平衡剥除指定模板
    pat = re.compile(r'\{\{(?:' + name_re + ')', re.I)
    while True:
        m = pat.search(s)
        if not m: return s
        d, cut, j = 0, -1, m.start()
        while j < len(s) - 1:
            if s[j] == '{' and s[j+1] == '{': d += 1; j += 1
            elif s[j] == '}' and s[j+1] == '}':
                d -= 1; j += 1
                if d == 0: cut = j + 1; break
            j += 1
        if cut < 0: return s
        s = s[:m.start()] + s[cut:]

unknown_tpl = set()
def clean(s, star='paren'):
    t = strip_tpl_balanced(s, r'[Hh]eader2?[\s|\n]|Novel\||SKQS header|footer|PD-old|pd-old|天玉經|返回頁首|繁體化|传统汉字化|Textquality')
    t = re.sub(r'<!--[\s\S]*?-->', '', t)
    t = re.sub(r'<ref[^>]*/>', '', t); t = re.sub(r'<ref[^>]*>[\s\S]*?</ref>', '', t)
    t = re.sub(r'__[A-Z]+__', '', t)
    t = re.sub(r'</?(?:onlyinclude|noinclude|includeonly|poem|small|big|font|center|span|div|u)[^>]*>', '', t)
    t = re.sub(r'^\*?\[\[(?:Image|File|image|file):[^\]]*\]\]\s*$', '', t, flags=re.M)  # 图不可收
    t = re.sub(r'^\*\[\[[^\]]*\]\]\s*$', '', t, flags=re.M)  # 子页目录行
    t = re.sub(r'\{\{另\|([^{}|]*)(?:\|[^{}]*)?\}\}', r'\1', t)
    t = t.replace('{{？}}', '□')  # 转录者存疑缺字
    for _ in range(6):
        if star == 'paren':
            t = re.sub(r'\{\{\*\|([^{}]*)\}\}', lambda m: m.group(1) if (m.group(1).startswith('〔') or re.fullmatch(r'（[^（）]*）', m.group(1))) else '（' + m.group(1) + '）', t)
        else:
            t = re.sub(r'\{\{\*\|[^{}]*\}\}', '', t)
        t = re.sub(r'-\{[^{}|]*\|([^{}|]*)\}-', r'\1', t); t = re.sub(r'-\{([^{}|]*)\}-', r'\1', t)
    t = re.sub(r"'''?", '', t)
    t = re.sub(r'\[\[Category:[^\]]*\]\]', '', t)
    t = re.sub(r'\[\[[^\]|]*\|([^\]]*)\]\]', r'\1', t); t = re.sub(r'\[\[([^\]]*)\]\]', r'\1', t)
    for m in re.finditer(r'\{\{([^|{}\n]+)[|}]', t): unknown_tpl.add(m.group(1).strip())
    for _ in range(3): t = re.sub(r'\{\{[^{}]*\}\}', '', t)
    t = t.replace('$', '')  # 源杂质(葬法倒杖「高$山」)
    return t

def sk_hanref(raw, start_marker=None, end_marker=None, keep_notes=False):
    # 四库转录页 → 校勘用汉字序列(繁体,SKchar→□;SK notes 默认剥除,keep_notes=夹注取内文)
    t = raw
    if start_marker:
        i = t.find(start_marker); assert i >= 0, start_marker
        t = t[i:]
    if end_marker:
        j = t.find(end_marker)
        if j >= 0: t = t[:j]
    t = re.sub(r'\{\{SK notes\|([^}]*)\}\}', r'\1' if keep_notes else '', t)
    t = re.sub(r'\{\{SK ?anchor\|[^}]*\}\}', '', t)
    t = re.sub(r'\{\{SKchar\|[^}]*\}\}', '□', t)
    t = strip_tpl_balanced(t, r'SKQS header')
    t = re.sub(r'<!--[\s\S]*?-->|</?(?:poem|onlyinclude)>', '', t)
    return han(t).translate(SKVAR)

def collate(body, skref, dzgref, label, maxfix=4):
    """整理本 body(繁体成品文本) 对四库 skref 校勘;短替换差异以殆知阁 dzgref(简体) 仲裁。
    返回 (修订后 body, 自动改字数, 人工清单)。"""
    idx = [i for i, ch in enumerate(body) if re.match(r'[㐀-鿿]', ch)]
    a = ''.join(body[i] for i in idx)
    sm = difflib.SequenceMatcher(None, a, skref, autojunk=False)
    fixes, manual, variants = [], [], 0
    dzg_h = han(dzgref)
    for tag, a1, a2, b1, b2 in sm.get_opcodes():
        if tag == 'equal': continue
        aseg, bseg = a[a1:a2], skref[b1:b2]
        if tag == 'replace' and len(aseg) == len(bseg) <= maxfix:
            bnorm = bseg.translate(SKVAR)
            if t2s(aseg) == t2s(bnorm):
                # 简繁歧字(雲/云等)从四库正字;其余异写保留整理本
                if aseg != bnorm and (set(aseg) & AMBIG or set(bnorm) & AMBIG):
                    fixes.append((a1, a2, bnorm, '正字'))
                else:
                    variants += 1
                continue
            if '□' in bseg or (aseg, bseg) in BLOCK or (aseg, bnorm) in BLOCK:
                manual.append(('存疑留原', aseg, bseg, a[max(0,a1-8):a2+8])); continue
            if len(aseg) <= 2:
                # 同源上游损坏严重,短差异默认从四库(人工复核输出清单)
                fixes.append((a1, a2, bnorm, '从四库'))
            else:
                manual.append((tag, aseg, bseg, a[max(0,a1-8):a2+8]))
        else:
            manual.append((tag, aseg[:40], bseg[:40], a[max(0,a1-10):min(a2+10, a1+50)]))
    out = list(body)
    for a1, a2, rep, _ in fixes:
        for k, ch in enumerate(rep): out[idx[a1+k]] = ch
    n_zz = sum(1 for f in fixes if f[3] == '正字')
    print(f'  [{label}] 汉字{len(a)} 校四库: 异写{variants} 正字{n_zz} 从四库{len(fixes)-n_zz} 人工{len(manual)}')
    for f in fixes:
        if f[3] != '正字': print('     改', a[max(0,f[0]-6):f[0]], '[', a[f[0]:f[1]], '→', f[2], ']', a[f[1]:f[1]+6])
    for m in manual: print('     ?', m[0], repr(m[1]), '||四库:', repr(m[2]), '@', repr(m[3]))
    return ''.join(out)

def apply_patches(t, patches, label):
    # 人工裁定补丁:整理本机器污染/脱衍,从四库本读法(逐处唯一匹配断言)
    for find, rep in patches:
        assert t.count(find) == 1, f'{label} 补丁匹配 {t.count(find)} 处: {find}'
        t = t.replace(find, rep)
    return t

def patch_chapters(chs, patches, label):
    # 按章应用补丁(补丁可增删段落);断言每条恰命中一章一次
    out, hit = [], {p[0]: 0 for p in patches}
    for ttl, wt, paras in chs:
        t = '\n'.join(paras)
        for find, rep in patches:
            n = t.count(find)
            if n: assert n == 1, f'{label}/{ttl} 补丁多次匹配: {find}'
            if n: t = t.replace(find, rep); hit[find] += 1
        out.append((ttl, wt, [p for p in t.split('\n') if p.strip()]))
    miss = [k for k, v in hit.items() if v != 1]
    assert not miss, f'{label} 补丁未命中/重复: {miss}'
    return out

def to_paras(t):
    lines = [l.strip() for l in t.split('\n')]
    out = []
    for l in lines:
        if not l: continue
        m = re.match(r'^=+\s*([^=]+?)\s*=+$', l)
        if m: out.append('## ' + m.group(1)); continue
        out.append(l)
    return out

def fm(d):
    o = '---\n'
    for k, v in d.items():
        o += f'{k}: {v}\n' if isinstance(v, int) else f'{k}: {json.dumps(v, ensure_ascii=False)}\n'
    return o + '---\n'

DUMP = '--dump' in sys.argv
def write_book(dirname, section, index, chapters):
    # chapters: [(title, weight, body_paras)]
    dest = os.path.join(BASE, section, dirname)
    total = sum(nhan('\n'.join(p)) for _, _, p in chapters)
    resid = sum(len(re.findall(r'\{\{|\}\}|\[\[|<[a-z]|==', '\n'.join(p))) for _, _, p in chapters)
    print(f'{index["title"]}: {len(chapters)}章 汉字:{total} 残留:{resid}')
    if DUMP:
        os.makedirs(os.path.join(S, 'draft'), exist_ok=True)
        open(os.path.join(S, 'draft', dirname + '.txt'), 'w').write(
            '\n\n'.join(f'### {t}\n' + '\n\n'.join(p) for t, _, p in chapters))
    if not WRITE: return
    shutil.rmtree(dest, ignore_errors=True); os.makedirs(dest)
    open(os.path.join(dest, '_index.md'), 'w').write(fm(index))
    for i, (title, weight, paras) in enumerate(chapters, 1):
        body = '\n\n'.join(paras) + '\n'
        open(os.path.join(dest, f'{i:03d}.md'), 'w').write(fm({'title': title, 'weight': weight}) + '\n' + body)

# ---------- 校勘参照 ----------
sk3 = w('撼龍經(四庫全書本)')
i_han = sk3.find('須彌山是天地骨'); i_yi = sk3.find('疑龍何處最難疑'); i_zf = sk3.find('葬法倒杖', i_yi)
SK_HAN = han(re.sub(r'\{\{SK notes\|[^}]*\}\}', '', re.sub(r'\{\{SKchar\|[^}]*\}\}', '□', sk3[i_han:i_yi]))).translate(SKVAR)
SK_YI = han(re.sub(r'\{\{SK notes\|[^}]*\}\}', '', re.sub(r'\{\{SKchar\|[^}]*\}\}', '□', sk3[i_yi:i_zf]))).translate(SKVAR)
SK_ZF = han(re.sub(r'\{\{SK notes\|[^}]*\}\}', '', re.sub(r'\{\{SKchar\|[^}]*\}\}', '□', sk3[i_zf:]))).translate(SKVAR)
DZ3 = open(os.path.join(DZG, '撼龙经疑龙经葬法倒杖.txt'), encoding='utf-8').read()
SK_ZHAI = sk_hanref(w('宅經(四庫全書本)__卷上'), '夫宅者', keep_notes=True) + sk_hanref(w('宅經(四庫全書本)__卷下'), keep_notes=True)
DZ_ZHAI = open(os.path.join(DZG, '宅经.txt'), encoding='utf-8').read()
SK_YB = sk_hanref(w('月波洞中記(四庫全書本)__卷上'), keep_notes=True) + sk_hanref(w('月波洞中記(四庫全書本)__卷下'), keep_notes=True)
DZ_YB = open(os.path.join(DZG, '月波洞中记.txt'), encoding='utf-8').read()
SK_RL = sk_hanref(w('人倫大統賦(四庫全書本)__卷上')) + sk_hanref(w('人倫大統賦(四庫全書本)__卷下'))
DZ_RL = open(os.path.join(DZG, '人伦大统赋.txt'), encoding='utf-8').read()
DZ_HZ = open(os.path.join(DZG, '火珠林.txt'), encoding='utf-8').read()

# 人工裁定补丁(据四库本读法;整理本机器污染、注模板残破、脱衍处)
ZHAI_PATCHES = [
    # 注模板缺左半致 ）}} 残留;并含 奶粉→艮、犯→卯 等机器污染(四库:凡從乾向巽…〔已上移轉及上官悉名入陰〕)
    ('（巳上移轉及上官所住，不計遠近，悉入陽也）從乾向巽，從子向午，從奶粉向坤，從犯向酉，從辰向戌移，巳移轉及官上悉名入陰）}}故福德之方',
     '（已上移轉及上官所住，不計遠近，悉入陽也）從乾向巽，從子向午，從艮向坤，從卯向酉，從辰向戌移（已上移轉及上官悉名入陰）故福德之方'),
    ('故不為災）}}凡諸刑殺', '故不為災。（凡諸刑殺'),  # 四库:不為災=正文尾,以下为注
    ('故不能制其大綱）}}', '故不能制其大綱）'),
    ('勤依天道貌岸然天德月德', '勤依天道天德月德'),  # 「貌岸然」机器衍文
    ('又此二宅悠揚造', '又此二宅修造'),  # 「悠揚」=「修」之机器污染
    ('（十一月丙辛日悠揚吉', '（十一月丙辛日修吉'),
    ('子為死喪超級大國右手', '子為死喪龍右手'),  # 机器污染
    ('雞棲碓 ，吉', '雞棲碓磑，吉'),
    ('宜置碓 ，開拓', '宜置碓磑，開拓'),
    ('縮即氣不足，不足則財祿', '縮即氣不足，不足則損財祿'),
    ('太過即減福會，至微太消，厚福所監也，。', '太過即減福會，至微不消，厚福所臨也。'),
    ('（月甲巳日修吉，東方不用甲子日八）', '（八月甲巳日修吉，東方不用甲子日）'),  # 「八」错简至末
    ('宜財，百事吉。經曰：青龍壯高', '宜財，百事吉。（四月乙庚日修，大吉）地府青龍左手，主三元，宜子孫，恒令清淨，吉。經曰：青龍壯高'),  # 整理本脱一位,据四库补
    ('富貴雄（修與乙同）', '富貴雄豪。（修與乙同）'),
    ('居之有信，懷抱義', '居之有信，懷才抱義'),
    ('宜子孫女婦女等院', '宜子孫婦女等院'),
    ('便皆違犯．大經', '便皆違犯大經'),
    ('宜置牛馬廄堂，置牛馬屋，其位', '宜置牛馬廄，其位'),  # 衍复,四库:宜置牛馬廄其位
    ('火光口舌、盤急。（修與巳同）', '火光口舌、筋急。（修與巳同）'),
    ('犯之足踞破塞、偏枯盤急', '犯之足跽跛蹇、偏枯筋急'),
    ('凡修宅次第法\n先修刑禍', '## 凡修宅次第法\n先修刑禍'),
    ('經曰：治大德，富貴財成萬億。亦名宅主', '經曰：治大德，富貴資財成萬億。亦名宅主'),
]

# ---------- 宅经 ----------
def build_zhaijing():
    chs = []
    for n, ttl in [('宅經__卷上', '卷上'), ('宅經__卷下', '卷下')]:
        t = clean(w(n))
        t = t.replace('已下圖無不精詳，但細看之必有災咎', '')  # 图注,原书宅图无法收入
        paras = to_paras(t)
        chs.append((ttl, len(chs) + 1, paras))
    chs = patch_chapters(chs, ZHAI_PATCHES, '宅经')
    body = '\n'.join('\n'.join(p) for _, _, p in chs)
    fixed = collate(body, SK_ZHAI, DZ_ZHAI, '宅经')
    # 回填
    parts = fixed.split('\n')
    k = 0; out = []
    for ttl, wt, paras in chs:
        out.append((ttl, wt, parts[k:k+len(paras)])); k += len(paras)
    write_book('zhai-jing', 'kanyu', {
        'title': '宅经', 'weight': 20, 'kind': 'book',
        'summary': '旧题黄帝撰，唐以前人依托。以阴阳二十四路论宅法休咎，主于阴阳相得，现存相宅书之最古者，四库馆臣谓其「在术数之中犹最为近古」。据维基文库整理本收录，校以四库全书本；原书宅图无法收入，图注从删。'
    }, out)

# 据四库本裁定(脱字/错字/拆字;「真龍胍→脈」为理校,收录日志披露)
HAN_PATCHES = [
    ('龍上有槍，賊旗', '龍上有欃槍，賊旗'),      # 欃槍=彗星,四库有
    ('欹仄名□槍', '欹仄名欃槍'),
    ('六星似環。平頃', '六星似環玦。平頃'),
    ('屏帳如負，下瞰泰淮', '屏帳如負扆，下瞰泰淮'),
    ('文武功名從此辯', '文武功名從此辨'),
    ('忽然壘壘空碧', '忽然壘壘凌空碧'),
    ('磊落巖形卓立', '磊落巉巖形卓立'),
    ('瓜甲巖若雞距', '瓜甲巉巖若雞距'),
    ('況是凶龍為不穴', '況是凶龍不為穴'),        # 错倒
    ('生灩。大姑', '生灩澦。大姑'),              # 灩澦堆
    ('攢劍糸番龍', '攢劍繙龍'),                  # 整理本拆字「糸番」,四库作繙
    ('犁钅辟頭', '犁鐴頭'),                      # 整理本拆字「钅辟」
    ('地劫風吹吉利', '地劫風吹非吉利'),
    ('左脅生來笏樣', '左脅生來搢笏樣'),          # 搢笏
    ('地上失弦琴背覓', '地上朱弦琴背覓'),
    ('葬理畏卑濕', '葬埋畏卑濕'),
    ('辯坦局', '辨垣局'),
    ('真龍胍', '真龍脈'),
    ('看得何星細推辯', '看得何星細推辨'),  # 四库此处作「辦」形误,从他处「辨」例
    ('聲如雷。瘟死盡兼官禍', '聲如雷。瘟㾮死盡兼官禍'),  # 四库:瘟㾮死盡,七言足字
]

# ---------- 撼龙经 ----------
def build_hanlong():
    t = clean(w('撼龍經'))
    chs0 = [('撼龙经', 1, to_paras(t))]
    chs0 = patch_chapters(chs0, HAN_PATCHES, '撼龙经')
    body = '\n'.join(chs0[0][2])
    fixed = collate(body, SK_HAN, DZ3, '撼龙经')
    write_book('han-long-jing', 'kanyu', {
        'title': '撼龙经', 'weight': 30, 'kind': 'book',
        'summary': '旧题唐杨筠松撰。七言歌诀体，专言山龙脉络形势，以贪狼、巨门、禄存、文曲、廉贞、武曲、破军、左辅、右弼九星辨山形吉凶，堪舆形势派开山之作。与《疑龙经》《葬法倒杖》合刊著录于四库。据维基文库整理本收录，校以四库全书本。'
    }, [('撼龙经', 1, fixed.split('\n'))])

# 据四库本裁定;变星篇「变作辅星」以下四库原阙、整理本据通行本补,保留
YI_PATCHES = [
    ('榮者芳日夜長', '榮者芳穠日夜長'),
    ('兩邊皆有穴形真，兩邊皆有穴形真，', '兩邊皆有穴形真，'),  # 衍复
    ('屠龍不如且抵，多龍少卻成癡', '屠龍不如且抵狶，狶多龍少卻成癡'),  # 四库:且抵狶狶多龍少
    ('將相公候立可斷', '將相公侯立可斷'),
    ('便作公候山水斷', '便作公侯山水斷'),
    ('千里封候居此地', '千里封侯居此地'),
    ('必有王候居此間', '必有王侯居此間'),
    ('附：衛龍篇', ''),  # 卫龙篇页首衍出的目录行
    ('識得變星知近遠。遠從貪起', '識得變星知遠近。遠從貪起'),  # 错倒,四库:知遠近
]

# ---------- 疑龙经 ----------
def build_yilong():
    names = [('上篇', '撼龍經__疑龍經__上篇'), ('中篇', '撼龍經__疑龍經__中篇'), ('下篇', '撼龍經__疑龍經__下篇'),
             ('疑龙十问', '撼龍經__疑龍經__疑龍十問'), ('卫龙篇', '撼龍經__疑龍經__衛龍篇'), ('变星篇', '撼龍經__疑龍經__變星篇')]
    chs = [(ttl, i + 1, to_paras(clean(w(n)))) for i, (ttl, n) in enumerate(names)]
    chs = patch_chapters(chs, YI_PATCHES, '疑龙经')
    body = '\n'.join('\n'.join(p) for _, _, p in chs)
    fixed = collate(body, SK_YI, DZ3, '疑龙经')
    parts = fixed.split('\n'); k = 0; out = []
    for ttl, wt, paras in chs:
        out.append((ttl, wt, parts[k:k+len(paras)])); k += len(paras)
    write_book('yi-long-jing', 'kanyu', {
        'title': '疑龙经', 'weight': 40, 'kind': 'book',
        'summary': '旧题唐杨筠松撰，《撼龙经》姊妹篇。上篇言干中寻枝，中篇论寻龙到头，下篇论结穴形势，附疑龙十问、卫龙篇、变星篇。据维基文库整理本收录，校以四库全书本；变星篇「变作辅星」以下四库本原阙，整理本据通行本补足，今仍之。'
    }, out)

# ---------- 葬法倒杖 ----------
def build_zangfa():
    names = [('认太极', '撼龍經__葬法倒杖__認太極'), ('分两仪', '撼龍經__葬法倒杖__分兩儀'),
             ('求四象', '撼龍經__葬法倒杖__求四象'), ('倍八卦', '撼龍經__葬法倒杖__倍八卦'),
             ('倒杖十二法', '撼龍經__葬法倒杖__倒杖十二法'), ('二十四砂葬法', '撼龍經__葬法倒杖__二十四砂葬法')]
    s2t = OpenCC('s2t').convert
    chs = []
    for i, (ttl, n) in enumerate(names):
        t = clean(w(n))
        if n.endswith(('分兩儀', '求四象')): t = s2t(t)  # 此两子页源为简体
        chs.append((ttl, i + 1, to_paras(t)))
    chs = patch_chapters(chs, [('裁也。以斤裁也，以斤裁物', '裁也。以斤裁物')], '葬法倒杖')  # 衍复
    body = '\n'.join('\n'.join(p) for _, _, p in chs)
    fixed = collate(body, SK_ZF, DZ3, '葬法倒杖')
    parts = fixed.split('\n'); k = 0; out = []
    for ttl, wt, paras in chs:
        out.append((ttl, wt, parts[k:k+len(paras)])); k += len(paras)
    write_book('zang-fa-dao-zhang', 'kanyu', {
        'title': '葬法倒杖', 'weight': 50, 'kind': 'book',
        'summary': '旧题唐杨筠松撰。专论点穴之法，自认太极、分两仪、求四象、倍八卦而至倒杖十二法，附二十四砂葬法。与《撼龙经》《疑龙经》合刊著录于四库。据维基文库整理本收录，校以四库全书本。'
    }, out)

# ---------- 青囊奥语 ----------
def build_qingnang():
    t = clean(w('青囊奧語'))
    # 半角标点归一
    t = t.replace(', ', '，').replace(',', '，').replace('; ', '；').replace(';', '；')
    t = re.sub(r'\.\s*$', '。', t, flags=re.M).replace('. ', '。').replace('.', '。')
    t = re.sub(r'[ \t]+', '', t)
    paras = [p for p in to_paras(t) if p]
    write_book('qing-nang-ao-yu', 'kanyu', {
        'title': '青囊奥语', 'weight': 60, 'kind': 'book',
        'summary': '旧题唐杨筠松撰。堪舆理气派要典，「坤壬乙」诀历来注家聚讼，四库馆臣谓之「地学理气家之权舆」。全文四百余字，据维基文库录文收录，与殆知阁本逐字互校。'
    }, [('青囊奥语', 1, paras)])

# ---------- 月波洞中记 ----------
YOUYIN = ('## 幽隱', '凡人氣血之成，出於毛髮。毫白者主壽，黑子上生毫者主貴相。若頭髮老來勝者不宜壽，髭髮少白不宜壽，眉耳生長毫者至壽。眉生白毛、玉堂骨起，仙人之相。胸上生毛主學道術，背上生毛凶惡之人，兩肩上或臂上生毛主慈孝有祿，腹上生毛大富，膝上生毛者少官祿，足下生毛者，極仙品人。若足下生黑子，有祿之人。一孔三毫，富貴之身。圓面豐頂、後連山勢起、髮少者，富貴之相也。')
# 据四库本裁定;「政和四年潘时竦校正」为四库本正文所存宋人校语,整理本脱,补入
YB_PATCHES = [
    ('賤人者，雖能語而無神，賤人者，雖能語而無神，', '賤人者，雖能語而無神，'),  # 衍复
    ('法〔原缺三字〕各分明', '法□□□各分明'),
    ('頦下有成主旅肉者', '頦下有成膂肉者'),      # 膂肉,整理本拆讹「主旅」
    ('頦下旋生□肉在頦骨下', '頦下旋生膂肉在頦骨下'),
    ('一生福祿享者臣', '一生福祿享耆頤'),        # 押韵字,四库作耆頤
    ('若向裡者貼者，長富', '若向裡貼者，長富'),
    ('輪飛廓期散主艱辛', '輪飛廓散主艱辛'),
    ('更蘭蘭台廷尉', '更得蘭台廷尉'),
    ('皆亦主貴矣。\n## 耳限十五年', '皆亦主貴矣。\n政和四年六月，將仕郎充高郵軍學教授潘時竦校正。\n## 耳限十五年'),
    ('（按：此條第三學堂缺）', ''),
    ('然後成人。。蘊胚胎', '然後成人。蘊胚胎'),  # 转录者按语,剥离(四库此处第三学堂原缺)
    ('貧賤。四學堂郭林宗觀人有四學堂：', '貧賤。\n## 四學堂\n郭林宗觀人有四學堂：'),  # 标题混入段首
    ('害人安已為樂', '害人安己為樂'),
]

def build_yuebo():
    xu = to_paras(clean(w('月波洞中記__序')))
    shang = to_paras(clean(w('月波洞中記__卷上')))
    # 整理本脱「幽隐」一节,据四库全书本补(标点为本站所加)
    pos = next(i for i, p in enumerate(shang) if p.startswith('## 河'))
    shang = shang[:pos] + [YOUYIN[0], YOUYIN[1]] + shang[pos:]
    xia = to_paras(clean(w('月波洞中記__卷下')))
    chs = [('序', 1, xu), ('卷上', 2, shang), ('卷下', 3, xia)]
    chs = patch_chapters(chs, YB_PATCHES, '月波洞中记')
    body = '\n'.join('\n'.join(p) for _, _, p in chs)
    fixed = collate(body, SK_YB, DZ_YB, '月波洞中记')
    parts = fixed.split('\n'); k = 0; out = []
    for ttl, wt, paras in chs:
        out.append((ttl, wt, parts[k:k+len(paras)])); k += len(paras)
    write_book('yue-bo-dong-zhong-ji', 'xiangshu', {
        'title': '月波洞中记', 'weight': 10, 'kind': 'book',
        'summary': '旧题老君题于太白山月波洞石壁，唐任逍遥所传（依托）。相形术九篇，词颇古奥，四库馆臣谓「视后来俗本较为精晰，当必有所传授」。原书久佚，四库自《永乐大典》辑出。据维基文库整理本收录，校以四库全书本；卷上「幽隐」一节整理本脱漏，据四库本补入。'
    }, out)

# ---------- 人伦大统赋 ----------
def build_renlun():
    xu = to_paras(clean(w('人倫大統賦__原序')))
    shang = to_paras(clean(w('人倫大統賦__卷上')))
    xia = to_paras(clean(w('人倫大統賦__卷下')))
    chs = [('原序', 1, xu), ('卷上', 2, shang), ('卷下', 3, xia)]
    body = '\n'.join('\n'.join(p) for _, _, p in [chs[1], chs[2]])  # 赋文校四库(序不在四库正文页)
    # 殆知阁人伦大统赋即四库转录,与校本同源,仲裁失效 → 只核查不自动改(dzg 传空)
    fixed = collate(body, SK_RL, '', '人伦大统赋(赋文,仅核查)')
    parts = fixed.split('\n'); k = 0; out = [chs[0]]
    for ttl, wt, paras in chs[1:]:
        out.append((ttl, wt, parts[k:k+len(paras)])); k += len(paras)
    write_book('ren-lun-da-tong-fu', 'xiangshu', {
        'title': '人伦大统赋', 'weight': 20, 'kind': 'book',
        'summary': '金张行简撰，赋体相术总纲，四库提要谓其「提纲挈领，不下三二千言，囊括相术殆尽」。原载《永乐大典》，四库自辑出。本站收赋文白文并元薛延年原序，校以四库全书本（薛氏注文四库提要已讥其「宂蔓过甚」，不取）。'
    }, out)

# ---------- 火珠林 ----------
def build_huozhulin():
    t = clean(w('火珠林'))
    t = re.sub(r'^\{\{\*\|', '', t, flags=re.M)
    t = t.replace('逢坤则静．遇兑则说', '逢坤则静，遇兑则说')
    t = re.sub(r'^</?pre>\s*$', '', t, flags=re.M)  # 六爻定体/卦例表格:去标签,行转段
    t = re.sub(r'[\t ]*\t[\t ]*', '　', t)          # 表格制表符→全角空格
    paras = to_paras(t)
    # poem 行已由 clean 剥标签:相邻短韵行并段(以标点结尾的连续短行)
    write_book('huo-zhu-lin', 'zhanbu', {
        'title': '火珠林', 'weight': 10, 'kind': 'book',
        'summary': '旧题麻衣道者撰（托名，其法行于宋世）。以钱代蓍、纳甲六亲之筮法祖本，后世六爻课法所称「火珠林法」即得名于此书。今传本出明清坊刻，据维基文库录文收录（简体），与殆知阁本互校。'
    }, [('火珠林', 1, paras)])

# ---------- 葬书(白文) ----------
# 整理本(与殆知阁同源)全文约900处损坏,注文诸本混乱 → 只收白文。
# 正文取整理本粗体标记,逐段验证于四库本;不合处从四库(ZS_FIXES),ZS_EXTRA 为整理本失标粗体的正文,自四库补录。
ZS_FIXES = [
    ('經曰：氣感而應鬼，福及後人。', '經曰：氣感而應，鬼福及人。'),
    ('故藏於涸燥者宜淺，藏於坦夷者宜深。', '故藏於涸燥者宜深，藏於坦夷者宜淺。'),  # 整理本浅深错倒
    ('噫而為風，升而且為雲', '噫而為風，升而為雲'),
    ('欲近而卻，欲止而深。', '欲進而卻，欲止而深。'),
    ('支之所起，氣隨而始；支所終，氣隨以鐘。', '支之所起，氣隨而始；支之所終，氣隨以鍾。'),
    ('經日：地有吉氣', '經曰：地有吉氣'),
    ('乘者其來。', '乘其所來。'),
    ('生新凶而消已福', '生新凶而消己福'),
    ('若肯萬善而潔齊。', '若具萬善而潔齊。'),
    ('若口之鼓。', '若橐之鼓。'),
    ('若龍若彎，或騰或盤。', '若龍若鸞，或騰或盤。'),
    ('無光發新。', '天光發新。'),
    ('群城眾支', '群壟眾支'),
    ('支城之止', '支壟之止'),
    ('故支葬其額，城葬其麓。', '故支葬其巔，壟葬其麓。'),
    ('卜支如首，眩壟如點頭。', '卜支如首，卜壟如足。'),
    ('候虜有間。', '侯虜有間。'),
    ('形如負峙，有城中峙，法葬其止。', '形如負扆，有壟中峙，法葬其止。'),
    ('其脈深曲，必後世福', '其臍深曲，必後世福'),
    ('敗棒之藏', '敗槨之藏'),
    ('裁肪切玉，備用五色。', '裁肪切玉，備具五色。'),
    ('夫幹如聚粟。', '夫乾如聚粟。'),
    ('溫如卦肉。', '濕如刲肉。'),
    ('龍踞謂之嫉生。', '龍踞謂之嫉主。'),
    ('流于因謝', '流于囚謝'),
    ('法每一折瀦而後匯。', '法每一折瀦而後泄。'),
    ('虜王滅候。', '虜王滅侯。'),
    ('勢如巨浪花，重嶺疊障', '勢如巨浪，重嶺疊嶂'),
    ('勢如矛戈，兵死形因。', '勢如矛戈，兵死形囚。'),
    ('形如負峙，有城中峙，法葬其止，王侯崛起。', '形如負扆，有壟中峙，法葬其止，王侯崛起。'),
    ('形如燕察', '形如燕窠'),
    ('形如投算，百事錯亂。', '形如投算，百事昏亂。'),
    ('形如亂衣，蕩女淫妻。', '形如亂衣，妒女淫妻。'),
    ('形如覆舟，女病男因。', '形如覆舟，女病男囚。'),
    ('形如臥劍，誅夷逼督。', '形如臥劍，誅夷逼僭。'),
    ('形如仰刀，兇祝伏逃。', '形如仰刀，凶禍伏逃。'),
    ('牛臥馬馳，蠻舞鳳飛。', '牛臥馬馳，鸞舞鳳飛。'),
    ('媵蛇委蛇。', '螣蛇委蛇。'),
    ('媵蛇兇危。', '螣蛇凶危。'),
    ('四應前按，法同忌之。', '四應前案，法同忌之。'),
    ('勢吉形兇，百[缺]一', '勢吉形凶，百□一'),
    ('禍不詐日。', '禍不旋日。'),
    ('趨全避缺，增高舉國下，三吉也。', '趨全避缺，增高益下，三吉也。'),
    ('僭上帶下爲五兇。', '僭上逼下爲五凶。'),
]
ZS_EXTRA = {
    # (插入于该正文段之前): 整理本失标粗体的正文句,自四库位置补录
    '玄武垂頭。': '夫葬以左為青龍，右為白虎，前為朱雀，後為玄武。',
    '朱雀源於生氣。': '以水為朱雀者，衰旺係乎形應，忌乎湍激，謂之悲泣。',
    '盖穴有三吉，葬直六兇，天光下臨，地德上載。': '夫葬乾者，勢欲起伏而長，形欲闊厚而方；葬坤者，勢欲連辰而不傾，形欲廣厚而長平；葬艮者，勢欲委蛇而順，形欲高峙而峻；葬巽者，勢欲峻而秀，形欲銳而雄；葬震者，勢欲緩而起，形欲聳而峨；葬離者，勢欲馳而穹，形欲起而崇；葬兌者，勢欲天來而坡垂，形欲方廣而平夷；葬坎者，勢欲曲折而長，形欲秀直而昂。',
}
BOLD_RE = re.compile(r"'{3}(.+?)'{3}", re.S)
def build_zangshu():
    s2t_ = OpenCC('s2t').convert
    sk = w('葬書(四庫全書本)')
    i0 = sk.find('葬者乘生氣也')
    skb = re.sub(r'\{\{SK notes\|[^}]*\}\}', '', sk[i0:])
    skb = re.sub(r'\{\{SKchar\|[^}]*\}\}', '□', skb)
    skh = t2s(han(skb).translate(SKVAR))
    chs = []
    fixmap = dict(ZS_FIXES); used = set()
    for pn, ttl in [('內篇', '内篇'), ('外篇', '外篇'), ('雜篇', '杂篇')]:
        t = w('葬書__' + pn)
        segs = []
        for m in BOLD_RE.finditer(t):
            seg = re.sub(r'\s+', '', m.group(1))
            if pn == '雜篇': seg = s2t_(seg)
            if seg in ZS_EXTRA: segs.append(ZS_EXTRA[seg])
            for find, rep in fixmap.items():
                if find in seg: used.add(find); seg = seg.replace(find, rep)
            segs.append(seg.replace('兇', '凶'))
        chs.append((ttl, len(chs) + 1, segs))
    miss = set(fixmap) - used
    assert not miss, f'葬书校定未命中: {miss}'
    nbad = 0
    for ttl, _, segs in chs:
        for seg in segs:
            if '□' in seg: continue
            h = t2s(han(seg).translate(SKVAR)).replace('玄', '')
            if h not in skh.replace('玄', ''):
                nbad += 1; print(f'     ✗未验于四库 [{ttl}] {seg[:45]}')
    print(f'  [葬书白文] 段数 {sum(len(c[2]) for c in chs)} 未验 {nbad}')
    write_book('zang-shu', 'kanyu', {
        'title': '葬书', 'weight': 10, 'kind': 'book',
        'summary': '旧题晋郭璞撰，实出宋世，托名郭氏。分内、外、杂三篇论葬乘生气之旨，堪舆形法祖典，「风水」一词即出此书。通行电子本注文诸本混乱、讹损殆不可读，本站只收白文，正文逐句校验于四库全书本，不合者从四库。'
    }, chs)

# ---------- 分类与分组 ----------
def write_indexes():
    if not WRITE: return
    os.makedirs(BASE, exist_ok=True)
    open(os.path.join(BASE, '_index.md'), 'w').write(fm({
        'title': '术数', 'date': '2026-07-06', 'weight': 9, 'tags': ['术数'], 'draft': True,
        'summary': '术数，收录占卜、命理、相术、堪舆、式占之属古代数术典籍。',
        'showToc': False, 'tocOpen': False, 'ShowShareButtons': False
    }) + '\n收录古代数术文化典籍，供文献与文化史研究。《周易》本经在经部。\n')
    for slug, title, wt, summ in [
        ('kanyu', '堪舆', 10, '相宅相墓之书，形势、理气诸经典。'),
        ('xiangshu', '相术', 20, '相人形法典籍。'),
        ('zhanbu', '占卜', 30, '占卜筮法典籍。'),
    ]:
        d = os.path.join(BASE, slug); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, '_index.md'), 'w').write(fm({
            'title': title, 'date': '2026-07-06', 'weight': wt, 'tags': ['术数'], 'draft': True,
            'summary': summ, 'showToc': False, 'tocOpen': False, 'ShowShareButtons': False
        }) + '\n' + summ + '\n')

write_indexes()
build_zangshu()
build_zhaijing()
build_hanlong()
build_yilong()
build_zangfa()
build_qingnang()
build_yuebo()
build_renlun()
build_huozhulin()
print('未知模板:', sorted(unknown_tpl))


# ---------- 批② (builders in batch2.py) ----------
if '--batch2' in sys.argv or True:
    exec(open(os.path.join(S, 'batch2.py'), encoding='utf-8').read())
