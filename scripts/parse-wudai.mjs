// 花间集+南唐二主词 ← chinese-poetry《五代诗词》JSON(简体)。
// 格式仿宋词三百首:作者子目录(出场序)、一词一文件、题作「词牌·首句」;现代注释(notes)与 [数字] 注标一律剥离;
// 繁体残字归一(陽/陰/後);卷五《西溪子》拆出误并的《中兴乐》,补《巫山一段云》(四库本白文,按词谱断句,朝朝莫莫→暮暮古今字归一);
// 作者名清洗(欧陽炯→欧阳炯,「尹鹗 六首」→尹鹗)。全书 499 首,与四库本卷数计数一致(卷九原为四十九首)。
// node parse-wudai.mjs [--write]
import { readFileSync, writeFileSync, mkdirSync, rmSync } from 'node:fs'
import { join } from 'node:path'

const S = new URL('./wudai/', import.meta.url).pathname
const LIT = '/Users/lishuaishuai/Projects/githubProjects/chinese-classics/base-data/literature'
const WRITE = process.argv.includes('--write')
const han = (s) => (s.match(/[㐀-鿿]/g) || []).length

const fixText = (s) => (s || '')
  .replace(/陽/g, '阳').replace(/陰/g, '阴').replace(/後/g, '后')
  .replace(/\[\d+\]/g, '')
  .replace(/\s+$/g, '')
const fixAuthor = (a) => fixText(a).replace(/\s*[一二三四五六七八九十]+首$/, '').trim()

const fm = (o) => '---\n' + Object.entries(o).map(([k, v]) => `${k}: ${typeof v === 'number' ? v : JSON.stringify(v)}`).join('\n') + '\n---\n'
// 题:词牌·首句(至第一个标点,去引号)
const pieceTitle = (rhythmic, paragraphs) => {
  const first = fixText((paragraphs[0] || '')).replace(/[「」『』]/g, '')
  const cut = first.split(/[，。？！；、]/)[0].slice(0, 12)
  return cut ? `${rhythmic}·${cut}` : rhythmic
}

let srcHan = 0, outHan = 0

// ── 花间集 ──
const juanFiles = ['1', '2', '3', '4', '5', '6', '7', '8', '9', 'x'].map((j) => `huajianji-${j}-juan.json`)
const stream = []
for (const f of juanFiles) {
  for (const p of JSON.parse(readFileSync(join(S, f), 'utf8'))) {
    srcHan += han((p.paragraphs || []).join(''))
    stream.push({ author: fixAuthor(p.author), rhythmic: fixText(p.rhythmic), paragraphs: p.paragraphs.map(fixText) })
  }
}
// 修复1:卷五《西溪子》误并《中兴乐》→ 拆分(嵌入的词牌行丢弃)
const xxz = stream.find((p) => p.rhythmic === '西溪子' && p.author === '毛文锡')
if (xxz && xxz.paragraphs.length === 8 && xxz.paragraphs[3] === '中兴乐') {
  const zxl = { author: '毛文锡', rhythmic: '中兴乐', paragraphs: xxz.paragraphs.slice(4) }
  xxz.paragraphs = xxz.paragraphs.slice(0, 3)
  stream.splice(stream.indexOf(xxz) + 1, 0, zxl)
} else console.error('⚠ 西溪子结构与预期不符,未拆分')
// 修复2:补《巫山一段云》(四库全书本白文,按词谱断句;莫莫→暮暮)
const hmz = stream.findIndex((p) => p.rhythmic === '河满子' && p.author === '毛文锡')
if (hmz >= 0) {
  stream.splice(hmz + 1, 0, {
    author: '毛文锡', rhythmic: '巫山一段云',
    paragraphs: ['雨霁巫山上，云轻映碧天。', '远风吹散又相连，十二晚峰前。', '暗湿啼猿树，高笼过客船。', '朝朝暮暮楚江边，几度降神仙。'],
  })
} else console.error('⚠ 未找到河满子,巫山一段云未补')

// 按作者(出场序)分组
const order = [], byAuthor = {}
for (const p of stream) {
  if (!byAuthor[p.author]) { byAuthor[p.author] = []; order.push(p.author) }
  byAuthor[p.author].push(p)
}
console.log(`花间集: ${stream.length} 首 · ${order.length} 家 (${order.map((a) => a + byAuthor[a].length).join(' ')})`)

// 序(剥现代注)
const pre = JSON.parse(readFileSync(join(S, 'huajianji-0-preface.json'), 'utf8'))[0]
const preBody = pre.paragraphs.map(fixText).filter(Boolean)
srcHan += han(pre.paragraphs.join('').replace(/\[\d+\]/g, ''))

// ── 南唐二主词 ──
const nt = JSON.parse(readFileSync(join(S, 'nantang-poetrys.json'), 'utf8'))
const ntOrder = [], ntBy = {}
for (const p of nt) {
  srcHan += han((p.paragraphs || []).join(''))
  const a = fixAuthor(p.author)
  if (!ntBy[a]) { ntBy[a] = []; ntOrder.push(a) }
  ntBy[a].push({ title: fixText(p.title), rhythmic: fixText(p.rhythmic), paragraphs: p.paragraphs.map(fixText) })
}
console.log(`南唐二主词: ${nt.length} 首 (${ntOrder.map((a) => a + ntBy[a].length).join(' ')})`)

// ── 落盘 ──
function writeBook(dir, indexFm, authors, getPieces, preface) {
  rmSync(dir, { recursive: true, force: true })
  mkdirSync(dir, { recursive: true })
  writeFileSync(join(dir, '_index.md'), indexFm)
  if (preface) writeFileSync(join(dir, '00-xu.md'), preface)
  authors.forEach((a, i) => {
    const d = join(dir, String(i + 1).padStart(2, '0'))
    mkdirSync(d)
    writeFileSync(join(d, '_index.md'), fm({ title: a, weight: i + 1 }))
    getPieces(a).forEach((p, k) => {
      const title = p.title || pieceTitle(p.rhythmic, p.paragraphs)
      const body = p.paragraphs.join('\n\n')
      outHan += han(body)
      writeFileSync(join(d, String(k + 1).padStart(2, '0') + '.md'), fm({ title, weight: k + 1 }) + '\n' + body + '\n')
    })
  })
}

if (WRITE) {
  writeBook(join(LIT, 'hua-jian-ji'),
    fm({ title: '花间集', weight: 25, kind: 'book', summary: '后蜀·赵崇祚编（940年），词总集之祖，录晚唐五代十八家词四百九十九首（与四库本计数同，卷九原为四十九首）。据 chinese-poetry 转录，缺佚两首依四库全书本补。' }),
    order, (a) => byAuthor[a],
    fm({ title: '花间集叙', weight: 0 }) + '\n' + preBody.join('\n\n') + '\n')
  outHan += han(preBody.join(''))
  writeBook(join(LIT, 'nan-tang-er-zhu-ci'),
    fm({ title: '南唐二主词', weight: 916, kind: 'book', summary: '南唐中主李璟、后主李煜词合集，后人所辑，四十五首（中主四首）。亡国之音哀以思，词至李后主而眼界始大。据 chinese-poetry 转录。' }),
    ntOrder, (a) => ntBy[a], null)
  console.log(`已写入 · 源汉字:${srcHan} 出:${outHan} 守恒:${((outHan / srcHan) * 100).toFixed(1)}%`)
} else {
  console.log('(dry-run) 源汉字:', srcHan)
}
