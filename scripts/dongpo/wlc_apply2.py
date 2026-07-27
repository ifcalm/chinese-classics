#!/usr/bin/env python3
"""第二轮：跨标点的乱码块与非汉字杂讯字符，逐处按四庫本回改。"""
import glob, json, os, re
BASE = '/Users/lishuaishuai/Projects/githubProjects/chinese-classics/base-data/literature/wang-lin-chuan-ji'
FM = re.compile(r'\A---\n.*?\n---\n', re.S)

# (文件, 讹, 正, 依据) —— 讹串按文件实际写法（含标点）给出
PASS2 = [
    ('043/02.md', '臣男⑽雱', '臣男雱', '⑽ 系编码损坏衍出，四庫本作「臣男雱」'),
    ('047/03.md', '衡ヨ紱糸延', '衡紞紘綖', '四庫本「衡紞紘綖」，冕之組帶'),
    ('047/08.md', '三靈之獺＃ㄖ瀉兀┕惟皇帝', '三靈之祐。中賀。恭惟皇帝', '四庫本「三靈之祐中賀㳟惟皇帝」'),
    ('047/11.md', '敕張ぃ航記鶇笫攏群闢具來', '敕張昪：郊丘大事，群闢具來', '四庫本「勑張昪郊丘大事群辟具来」'),
    ('048/23.md', '阜成邦採，ゼ文告慶', '阜成邦采，摛文告慶', '四庫本「阜成邦采摛文告慶」'),
    ('049/01.md', '疇其展き之勞', '疇其展宷之勞', '四庫本「疇其展宷之勞」'),
    ('081/10.md', '帝暉溫ㄧ', '帝暉溫睟', '四庫本「帝暉温睟」'),
    ('081/11.md', '何嘗候問。ダ朅來冗局', '何嘗候問。朅來冗局', 'ダ 系衍，四庫本无'),
    ('081/38.md', '風華懋美，┤舳南之筠', '風華懋美，嶢若東南之筠', '四庫本「風華懋美嶢若東南之筠」'),
    ('081/43.md', '堵食Ｏ埽取所承學', '惇率常憲，取所承學', '四庫本「惇率常憲取所承學」'),
    ('097/04.md', '方ㄧ而夭', '方晬而夭', '四庫本「方晬而夭」，晬＝周歲'),
    ('036/27.md', '銛�塋鸊鵜', '銛鋒瑩鸊鵜', '四庫本「銛鋒瑩鸊鵜」'),
    ('038/07.md', '夫孰驅兮亡�', '夫孰驅兮亡', '四庫本无此字，� 系损坏残留'),
    ('038/09.md', '於皇來', '於皇來塈', '四庫本「於皇來塈」'),
    ('057/09.md', '忽此兼叨，�無前比', '忽此兼叨，夐無前比', '四庫本「忽此兼叨夐無前比」'),
    ('072/01.md', '《鴟鴞以遺王⺶非疾成王', '《鴟鴞》以遺王，亦非疾成王', '四庫本「鴟鴞以遺王亦非疾成王」'),
    ('099/02.md', '溫⿰冫青之愛', '溫凊之愛', '四庫本「温凊」，《禮記》冬溫夏凊；原为缺字存形，今得真字'),
]
TITLE = [('047/11.md', '赐允太子太师致仕张昪桓澳辖寂阄悔',
          '赐允太子太师致仕张昪不赴南郊陪位诏', '四庫本篇题「賜允太子太師致仕張昪不赴南郊陪位詔」')]

log, miss = [], []
for rel, bad, good, why in PASS2:
    p = os.path.join(BASE, rel)
    t = open(p, encoding='utf-8').read()
    if bad not in t:
        miss.append((rel, bad))
        continue
    open(p, 'w', encoding='utf-8').write(t.replace(bad, good))
    log.append({'file': rel, 'bad': bad, 'good': good, 'why': why, 'kind': '正文'})
for rel, bad, good, why in TITLE:
    p = os.path.join(BASE, rel)
    t = open(p, encoding='utf-8').read()
    if bad not in t:
        miss.append((rel, bad))
        continue
    open(p, 'w', encoding='utf-8').write(t.replace(bad, good))
    log.append({'file': rel, 'bad': bad, 'good': good, 'why': why, 'kind': '篇题'})
print('第二轮回改 %d 处' % len(log))
if miss:
    print('!! 未命中:', miss)
json.dump(log, open('wlc-applied2.json', 'w', encoding='utf-8'), ensure_ascii=False)
