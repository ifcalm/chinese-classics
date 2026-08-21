# -*- coding: utf-8 -*-
"""樂府詩集·抓取。維基《樂府詩集》100卷，子頁形如 /001卷。"""
import subprocess, json, time, os
UA='chinese-classics-bot/1.0 (ifcalm.ok@gmail.com)'
API='https://zh.wikisource.org/w/api.php'
S=os.environ.get('YF_CACHE_DIR', os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(S,'yfcache.json')

def q(params):
    cmd=['curl','-4','-s','--max-time','120','-H','User-Agent: '+UA, API]
    for k,v in params.items(): cmd+=['--data-urlencode','%s=%s'%(k,v)]
    r=subprocess.run(cmd,capture_output=True,text=True); time.sleep(1.4)
    return json.loads(r.stdout)

pages = json.load(open(OUT)) if os.path.exists(OUT) else {}
titles = ['樂府詩集'] + ['樂府詩集/%03d卷' % i for i in range(1, 101)]
todo=[t for t in titles if t not in pages]
print('待抓 %d/%d'%(len(todo),len(titles)))
for i in range(0,len(todo),20):
    batch=todo[i:i+20]
    d=q({'action':'query','prop':'revisions','rvprop':'content','rvslots':'main',
         'titles':'|'.join(batch),'format':'json','formatversion':'2'})
    for p in d['query']['pages']:
        if p.get('missing'): print('  缺页:',p['title']); continue
        pages[p['title']]=p['revisions'][0]['slots']['main']['content']
    print('  已抓 %d'%len(pages))
    json.dump(pages,open(OUT,'w'),ensure_ascii=False)
print('完成，共 %d 页'%len(pages))
