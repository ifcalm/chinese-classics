#!/usr/bin/env python3
"""把 89 处替换块分三类：①四庫本异体字形(不动) ②拆字存形(可据证人回填真字) ③乱码。"""
import json, re
IDS = re.compile(r'[⿰-⿻⺀-⿟]')
# 四庫本惯用的刻本异体：两侧同长且逐字成对者，属字形差异，整理本用通行正字，不动
VAR = {('床','牀'),('才','纔'),('靜','静'),('橫','横'),('遙','遥'),('煙','烟'),('腳','脚'),
       ('窻','窗'),('涼','凉'),('踈','疎'),('鐘','鍾'),('壯','壮'),('採','采'),('顏','顔'),
       ('遊','游'),('溫','温'),('禿','秃'),('祿','禄'),('眇','眇'),('茲','兹'),('嘆','歎'),
       ('蓋','葢'),('群','羣'),('闢','辟'),('鬱','欝'),('會','㑹'),('德','徳'),('峨','峩'),
       ('墮','堕'),('沒','没'),('柳','栁'),('陰','隂'),('黃','黄'),('懷','懐'),('德','徳'),
       ('嘗','甞'),('將','将'),('匆','怱'),('點','㸃'),('汙','汚'),('歲','嵗'),('強','强'),
       ('複','復'),('己','已'),('葬','葬'),('聯','聨'),('遠','逺'),('綠','緑')}


def variant_only(x, y):
    if len(x) != len(y):
        return False
    return all(a == b or (a, b) in VAR or (b, a) in VAR for a, b in zip(x, y))


def main():
    found = json.load(open('wlc-mojib.json', encoding='utf-8'))
    var, ids, moj = [], [], []
    for f in found:
        x, y = f['bad'], f['good']
        if variant_only(x, y):
            var.append(f)
        elif IDS.search(x):
            ids.append(f)
        else:
            moj.append(f)
    print('① 四庫本异体字形，整理本无误  %d 处（不动）' % len(var))
    for f in var:
        print('     卷%-3d 【%s】↔四庫【%s】' % (f['vol'], f['bad'], f['good']))
    print()
    print('② 拆字存形，证人给出真字  %d 处' % len(ids))
    for f in ids:
        print('     卷%-3d 【%s】→【%s】  %s' % (f['vol'], f['bad'], f['good'], f['ctx']))
    print()
    print('③ 乱码  %d 处' % len(moj))
    json.dump({'var': var, 'ids': ids, 'moj': moj},
              open('wlc-class.json', 'w', encoding='utf-8'), ensure_ascii=False)


if __name__ == '__main__':
    main()
