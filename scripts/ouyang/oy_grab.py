# -*- coding: utf-8 -*-
"""欧阳修集·抓取。维基《歐陽修集》153卷+附录，全为 /卷NNN 子页。"""
import subprocess, json, time, os, sys
UA='chinese-classics-bot/1.0 (ifcalm.ok@gmail.com)'
API='https://zh.wikisource.org/w/api.php'
OUT='oycache.json'

def q(params, post=False):
    cmd=['curl','-4','-s','--max-time','90','-H','User-Agent: '+UA]
    cmd += [API] if post else ['-G', API]
    for k,v in params.items(): cmd+=['--data-urlencode','%s=%s'%(k,v)]
    r=subprocess.run(cmd,capture_output=True,text=True); time.sleep(1.4)
    try: return json.loads(r.stdout)
    except Exception as e:
        print('PARSE FAIL', r.stdout[:200]); raise

def subs(pref):
    out=[];c=None
    while True:
        p={'action':'query','list':'allpages','apprefix':pref+'/','aplimit':'500',
           'format':'json','formatversion':'2'}
        if c: p['apcontinue']=c
        d=q(p); out+=[x['title'] for x in d['query']['allpages']]
        c=d.get('continue',{}).get('apcontinue')
        if not c: break
    return out

pages = json.load(open(OUT)) if os.path.exists(OUT) else {}
titles = ['歐陽修集'] + subs('歐陽修集')
todo=[t for t in titles if t not in pages]
print('子页 %d，待抓 %d' % (len(titles), len(todo)))
for i in range(0,len(todo),50):
    # 标题长时 GET 会 414，一律走 POST
    d=q({'action':'query','prop':'revisions','rvprop':'content','rvslots':'main',
         'titles':'|'.join(todo[i:i+50]),'format':'json','formatversion':'2'}, post=True)
    for p in d['query']['pages']:
        if p.get('missing'): print('  缺页', p['title']); continue
        pages[p['title']]=p['revisions'][0]['slots']['main']['content']
    json.dump(pages, open(OUT,'w'), ensure_ascii=False)
    print('  %d/%d' % (min(i+50,len(todo)), len(todo)))
print('共 %d 页' % len(pages))
