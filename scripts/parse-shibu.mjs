// 史部批:水经注/洛阳伽蓝记/华阳国志/史通 ← 维基文库整理本(繁体新式标点,与史部既有体例一致)。
// 体例:水经注 经文→引用块、郦注→正文(经注体分层);伽蓝记 {{*|}}=杨衒之自注→（）保留;
//      华阳国志 {{*|}}=校勘记→剥离,==数字== 科段号(近现代编者所加)→剥;史通 ==篇题==→##。
// 模板:{{另|A|B}}/{{!|A|IDS}} 取 A;YL/ProperNoun/專名號 取内文;嵌套由内向外多轮解。
// 贞观政要站内已有(w300);徐霞客游记缓收(殆知阁源为四库白文,双重不合格)。
// node parse-shibu.mjs [--write]
import { readFileSync, writeFileSync, mkdirSync, rmSync } from 'node:fs'
import { join } from 'node:path'

const S = new URL('./ws/', import.meta.url).pathname
const HIST = '/Users/lishuaishuai/Projects/githubProjects/chinese-classics/base-data/history'
const WRITE = process.argv.includes('--write')
const han = (s) => (s.match(/[㐀-鿿]/g) || []).length
const numToHan = (n) => {
  const d = '零一二三四五六七八九'
  if (n <= 10) return n === 10 ? '十' : d[n]
  if (n < 20) return '十' + d[n % 10]
  return d[Math.floor(n / 10)] + '十' + (n % 10 ? d[n % 10] : '')
}
const fm = (o) => '---\n' + Object.entries(o).map(([k, v]) => `${k}: ${typeof v === 'number' ? v : JSON.stringify(v)}`).join('\n') + '\n---\n'
const readWiki = (slug) => JSON.parse(readFileSync(join(S, slug + '.json'), 'utf8')).parse.wikitext['*']
const headerSection = (raw) => (raw.match(/\|\s*section\s*=\s*([^\n|]+)/) || [, ''])[1].replace(/\[\[[^\]|]*\|/g, '').replace(/[\[\]]/g, '').trim()

const unknownTpl = new Set()
// 按 {{ }} 深度平衡剥除指定模板(header 可能单行结尾或含嵌套,正则不可靠)
function stripTplBalanced(s, nameRe) {
  const re = new RegExp('\\{\\{(?:' + nameRe + ')', 'gi')
  let m
  while ((m = re.exec(s))) {
    let d = 0, cut = -1
    for (let j = m.index; j < s.length - 1; j++) {
      if (s[j] === '{' && s[j + 1] === '{') { d++; j++ }
      else if (s[j] === '}' && s[j + 1] === '}') { d--; j++; if (d === 0) { cut = j + 1; break } }
    }
    if (cut < 0) break
    s = s.slice(0, m.index) + s.slice(cut)
    re.lastIndex = 0
  }
  return s
}
// 通用清洗。star: 'paren'=原书自注转（） | 'drop'=校勘记剥离
function clean(s, star) {
  let t = stripTplBalanced(s, '[Hh]eader2?[\\s|\\n]|footer|PD-old')
    .replace(/<!--[\s\S]*?-->/g, '')
    .replace(/<ref[^>]*\/>/g, '').replace(/<ref[^>]*>[\s\S]*?<\/ref>/g, '')
    .replace(/__[A-Z]+__/g, '') // MediaWiki 魔术字(__FORCETOC__ 等)
    .replace(/<\/?(?:onlyinclude|noinclude|includeonly)>/g, '') // 换写标签
    .replace(/<s>[\s\S]*?<\/s>/g, '') // 删除线=整理本错简/衍文移除标记,正字已在〔〕
    .replace(/<\/?(?:small|big|font|center|span|div|u)[^>]*>/g, '') // 装饰性标签(徐霞客卷四六季梦良按语外套、专名划线)
  // 由内向外多轮:先解已知取文模板,再按 star 处理 {{*|}},反复以解嵌套
  for (let i = 0; i < 8; i++) {
    t = t
      .replace(/\{\{annotate\|[^{}]*\}\}/gi, '') // 近现代编者按语,弃收
      .replace(/\{\{PUA\|([^{}|]*)[^{}]*\}\}/g, (_, p) => p || '□') // 缺字占位
      .replace(/\{\{CJK-New-Char\|([0-9A-Fa-f]+)[^{}]*\}\}/gi, (_, h) => { try { return String.fromCodePoint(parseInt(h, 16)) } catch { return '□' } })
      .replace(/\{\{YL\|([^{}|]*)(?:\|[^{}]*)?\}\}/g, '$1')
      .replace(/\{\{(?:ProperNoun|專名號|专名号)\|([^{}]*)\}\}/g, '$1')
      .replace(/\{\{另\|([^{}|]*)(?:\|[^{}]*)?\}\}/g, '$1')
      .replace(/\{\{!\|([^{}|]*)(?:\|[^{}]*)?\}\}/g, '$1')
      .replace(/\{\{quote\|([^{}]*)\}\}/gi, '$1') // 引文块(伽蓝记卷五宋云行纪等):留全文
      .replace(/\{\{\+\|([^{}]*)\}\}/g, '$1') // 华阳国志卷十:赞文正文大字标记,保留
      .replace(/-\{[^{}|]*\|([^{}|]*)\}-/g, '$1').replace(/-\{([^{}|]*)\}-/g, '$1')
    // 注文自带（）者不再重裹(徐霞客「（以下缺）」等);〔〕开头=校补正文(据他本补入,连读),原样保留不裹（）
    if (star === 'paren') t = t.replace(/\{\{\*\|([^{}]*)\}\}/g, (_, p) => (p.startsWith('〔') || /^（[^（）]*）$/.test(p)) ? p : `（${p}）`)
    else if (star === 'drop') t = t.replace(/\{\{\*\|[^{}]*\}\}/g, '')
  }
  // 源笔误兜底:{{*|…} 单括号闭合(史通卷十八「一無觀字」处)
  if (star === 'paren') t = t.replace(/\{\{\*\|([^{}]*)\}(?!\})/g, '（$1）')
  else if (star === 'drop') t = t.replace(/\{\{\*\|[^{}]*\}(?!\})/g, '')
  t = t
    .replace(/'''?/g, '')
    .replace(/\[\[[Cc]ategory:[^\]]*\]\]/g, '')
    .replace(/\[\[[^\]|]*\|([^\]]*)\]\]/g, '$1').replace(/\[\[([^\]]*)\]\]/g, '$1')
  // 兜底删除未知模板前先记名,防静默丢字
  for (const m of t.matchAll(/\{\{([^|{}\n]+)[|}]/g)) unknownTpl.add(m[1].trim())
  for (let i = 0; i < 3; i++) t = t.replace(/\{\{[^{}]*\}\}/g, '')
  return t
}
const toBlocks = (s, headRe) => s.split(/\r?\n/).map((l) => l.trim()).filter(Boolean)
  .flatMap((l) => {
    const h = l.match(/^==+([^=]+)==+$/)
    if (h) {
      const inner = h[1].trim()
      if (headRe && headRe.test(inner)) return [] // 科段号剥离
      return ['## ' + inner.replace(/[【】]/g, '')]
    }
    return [l]
  })

const books = []

// 1) 水经注:原序+40卷。经文(平文行)→引用块;郦注(:{{*|…}})→正文段。
{
  const chapters = [{ slug: '000-xu', title: '原序', weight: 0, blocks: toBlocks(clean(readWiki('sjz-xu'), 'paren')) }]
  for (let i = 1; i <= 40; i++) {
    const raw = readWiki('sjz-' + String(i).padStart(2, '0'))
      .replace(/^\{\{CJK-New-Char\|2AA58\|block=C\}\}\n/, '') // 卷34 Header 前游离缺字,源杂质
    const sec = headerSection(raw)
    const pre = stripTplBalanced(raw, '[Hh]eader2?[\\s|\\n]').replace(/<!--[\s\S]*?-->/g, '')
    const blocks = []
    for (const line0 of pre.split(/\r?\n/)) {
      const line = line0.replace(/\s+$/, '')
      if (!line.trim()) continue
      if (/^:/.test(line)) { // 注文:剥外层 {{*|}},内层自注转（）
        let t = clean(line.replace(/^:+\s*/, '').replace(/^\{\{\*\|/, '').replace(/\}\}\s*$/, ''), 'paren').trim()
        if (t) blocks.push(t)
      } else if (/^==+[^=]+==+$/.test(line.trim())) { // 篇内水名标题
        const h = clean(line.trim().replace(/^==+([^=]+)==+$/, '$1'), 'paren').trim()
        if (h) blocks.push('## ' + h)
      } else {
        const t = clean(line, 'paren').trim()
        if (t) blocks.push('> ' + t)
      }
    }
    chapters.push({ slug: String(i).padStart(3, '0'), title: `卷${numToHan(i)}·${sec || ''}`.replace(/·$/, ''), weight: i, blocks })
  }
  books.push({
    dir: 'shui-jing-zhu', title: '水经注', weight: 294, chapters,
    summary: '北魏·郦道元撰，四十卷，因《水经》而注，记千余条水道所经山川城邑、风物故实，地理名著而兼六朝散文之胜。维基文库整理本（繁体新式标点），经文以引块示别，郦注为正文。',
  })
}

// 2) 洛阳伽蓝记:序+5卷。{{*|}}=杨氏自注→（）。
{
  const chapters = [{ slug: '00-xu', title: '序', weight: 0, blocks: toBlocks(clean(readWiki('lyqlj-xu'), 'paren')) }]
  for (let i = 1; i <= 5; i++) {
    const raw = readWiki('lyqlj-' + i)
    const sec = headerSection(raw)
    chapters.push({ slug: String(i).padStart(2, '0'), title: `卷${numToHan(i)}·${sec || ''}`.replace(/·$/, ''), weight: i, blocks: toBlocks(clean(raw, 'paren')) })
  }
  books.push({
    dir: 'luo-yang-qie-lan-ji', title: '洛阳伽蓝记', weight: 296, chapters,
    summary: '东魏·杨衒之撰（547年），五卷，追记北魏洛阳佛寺园林之盛衰，兼载朝野轶闻，与《水经注》并称北朝文学双璧。维基文库整理本，杨氏自注以（）存录。',
  })
}

// 3) 华阳国志:12卷。{{*|}}=校勘记→剥;==数字==/【譔】科段处理。
{
  const chapters = []
  for (let i = 1; i <= 12; i++) {
    const raw = readWiki('hygz-' + String(i).padStart(2, '0'))
      // 源笔误定点:卷一「甘𡉙」后校记缺 {{*| 开头
      .replace('甘𡉙張、吳、何、王本作柑。古今字。}}', '甘𡉙{{*|張、吳、何、王本作柑。古今字。}}')
    const sec = headerSection(raw)
    const blocks = toBlocks(clean(raw, 'drop'), /^[零一二三四五六七八九十百\d\s]+$/)
    chapters.push({ slug: String(i).padStart(2, '0'), title: `卷${numToHan(i)}·${sec || ''}`.replace(/·$/, ''), weight: i, blocks })
  }
  books.push({
    dir: 'hua-yang-guo-zhi', title: '华阳国志', weight: 292, chapters,
    summary: '东晋·常璩撰（约354年），十二卷，记巴蜀滇黔历史地理与人物，现存最早的地方志专书。维基文库整理本（繁体新式标点，校勘记已汰）。',
  })
}

// 4) 史通:20卷49篇。==篇题==→##。
{
  const chapters = []
  for (let i = 1; i <= 20; i++) {
    const raw = readWiki('st-' + String(i).padStart(2, '0'))
    const sec = headerSection(raw)
    const nei = i <= 10 ? '内篇' : '外篇'
    chapters.push({ slug: String(i).padStart(2, '0'), title: `卷${numToHan(i)}·${nei}${sec ? '·' + sec : ''}`, weight: i, blocks: toBlocks(clean(raw, 'paren')) })
  }
  books.push({
    dir: 'shi-tong', title: '史通', weight: 298, chapters,
    summary: '唐·刘知几撰（710年），二十卷四十九篇，内篇论史体源流、外篇评史官史书得失，中国第一部史学理论专著。维基文库整理本（繁体新式标点）。',
  })
}


// 5) 徐霞客游记:52篇(维基文库整理本,现代注在 ref 中已剥)。日记体:年/月标题→##,日期(===)并入次段(仿通行本连排)。
{
  const t2s={'遊':'游','記':'记','嶽':'岳','彜':'彝','粵':'粤','雞':'鸡','麗':'丽','閩':'闽','廬':'庐','鯉':'鲤','華':'华','臺':'台','後':'后','隨':'随','筆':'笔','兩':'两','則':'则','盤':'盘','騰':'腾','諸':'诸','說':'说','緣':'缘','起':'起','溯':'溯','紀':'纪','源':'源','恒':'恒','顏':'颜'};
  const simp=(x)=>[...x].map(c=>t2s[c]||c).join('');
  const toc=JSON.parse(readFileSync(join(S,'../xxk/toc.json'),'utf8'));
  const chapters=[];
  toc.forEach((name,idx)=>{
    const raw=JSON.parse(readFileSync(join(S,'../xxk/'+String(idx+1).padStart(3,'0')+'.json'),'utf8')).parse.wikitext['*'];
    const cleaned=clean(raw,'paren')
      .replace(/（公元[０-９0-9]+年）/g,'') // 整理者所加公元纪年,现代注,剥
      .replace(/　　+/g,'　'); // 源排版双全角空格归一
    const blocks=[]; let pendingDay='';
    for (const l0 of cleaned.split(/\r?\n/)) {

      const l=l0.trim(); if(!l) continue;
      const m3=l.match(/^===([^=]+)===$/), m12=l.match(/^==?([^=]+?)==?$/);
      if (m3) { pendingDay=m3[1].trim(); continue }
      if (m12) { const h=m12[1].trim(); if(h && !/^[注註][释釋]$/.test(h)) blocks.push('## '+h); continue }
      blocks.push(pendingDay ? pendingDay+'　'+l : l); pendingDay='';
    }
    if (pendingDay) blocks.push(pendingDay);
    chapters.push({ slug: String(idx+1).padStart(3,'0'), title: simp(name), weight: idx+1, blocks });
  });
  books.push({
    dir: 'xu-xia-ke-you-ji', title: '徐霞客游记', weight: 310, chapters,
    summary: '明·徐弘祖撰（1613—1639 年间日记），五十二篇，以日记体记三十年游历山川地貌、岩溶洞穴之考察，中国古代游记与地学名著。维基文库整理本（繁体新式标点，季会明本系统篇目），现代注释已汰。',
  })
}

for (const b of books) {
  const h = b.chapters.reduce((s, c) => s + han(c.blocks.join('')), 0)
  const heads = b.chapters.reduce((s, c) => s + c.blocks.filter((x) => x.startsWith('## ')).length, 0)
  const quotes = b.chapters.reduce((s, c) => s + c.blocks.filter((x) => x.startsWith('> ')).length, 0)
  const residue = b.chapters.flatMap((c) => c.blocks.filter((x) => /\{\{|\}\}|\[\[|'''|<ref/.test(x)))
  console.log(`${b.title}: ${b.chapters.length}章 汉字:${h} 标题:${heads} 引块:${quotes} 残留:${residue.length}${residue.length ? ' → ' + residue[0].slice(0, 50) : ''}`)
  if (!WRITE) continue
  const dir = join(HIST, b.dir)
  rmSync(dir, { recursive: true, force: true })
  mkdirSync(dir, { recursive: true })
  writeFileSync(join(dir, '_index.md'), fm({ title: b.title, weight: b.weight, kind: 'book', summary: b.summary }))
  for (const c of b.chapters) {
    writeFileSync(join(dir, c.slug + '.md'), fm({ title: `${b.title} ${c.title}`, weight: c.weight }) + '\n' + c.blocks.join('\n\n') + '\n')
  }
}
if (unknownTpl.size) console.log('⚠ 兜底删除的模板:', [...unknownTpl].join(' '))
if (WRITE) console.log('已写入', HIST)
