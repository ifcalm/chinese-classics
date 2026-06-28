#!/usr/bin/env node
// 把 base-data 的 markdown 转成 R2 内容布局：manifest + catalog + book(JSON) + text(纯 md)。
// 设计见 docs/data-architecture.md；类型合约见 src/data/types.ts。
//
// 用法：node scripts/build-content.mjs confucius buddha ...   （不传则报错，避免误跑全量）
//
// 书边界规则（§5.1，统管深浅门类）：折叠数字分批目录后，一个目录是「书」当且仅当
//   它所有子项(子目录/文件)的标题都带本目录标题前缀（目录标题为空则看子项共同前缀）；
//   否则是 nav 层（子目录递归为 collection，散落 md = 单文件书）。
//   `_index.md` 的 `kind: book|nav` 可强制覆盖。

import fs from 'node:fs'
import path from 'node:path'
import crypto from 'node:crypto'

const SRC = 'base-data'
const OUT = 'dist-content'
const STATE_FILE = 'content-state.json'
const SCHEMA_VERSION = 1
const NOW = new Date().toISOString().replace(/\.\d+Z$/, 'Z')

// 时间戳持久化状态：{ bookId: { hash, createdAt, updatedAt } }，见 §5.3
const sha = (s) => crypto.createHash('sha256').update(s).digest('hex').slice(0, 16)
const prevState = fs.existsSync(STATE_FILE) ? JSON.parse(fs.readFileSync(STATE_FILE, 'utf8')) : {}
const nextState = { ...prevState }
function stamp(bookId, hash) {
  const p = prevState[bookId]
  let createdAt, updatedAt
  if (!p) createdAt = updatedAt = NOW
  else if (p.hash !== hash) { createdAt = p.createdAt; updatedAt = NOW }
  else { createdAt = p.createdAt; updatedAt = p.updatedAt }
  nextState[bookId] = { hash, createdAt, updatedAt }
  return { createdAt, updatedAt }
}

const categories = process.argv.slice(2)
if (categories.length === 0) {
  console.error('用法: node scripts/build-content.mjs <门类> [<门类> ...]')
  process.exit(1)
}

const issues = []
const warn = (m) => issues.push(m)

const isBatchDir = (n) => /^\d+-\d+$/.test(n)
const stripQuotes = (s) => s.replace(/^["']|["']$/g, '').trim()

function listDir(dir) {
  const dirs = [], files = []
  for (const n of fs.readdirSync(dir)) {
    if (n === '.DS_Store' || n === '_index.md' || n === '_meta.yml') continue
    if (fs.statSync(path.join(dir, n)).isDirectory()) dirs.push(n)
    else if (n.endsWith('.md')) files.push(n)
  }
  return { dirs, files }
}

function parseMd(file) {
  const raw = fs.readFileSync(file, 'utf8')
  const m = raw.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/)
  if (!m) return { fields: {}, body: raw }
  const fields = {}
  for (const line of m[1].split('\n')) {
    const mm = line.match(/^([A-Za-z_]+):\s*(.*)$/)
    if (mm) fields[mm[1]] = stripQuotes(mm[2])
  }
  return { fields, body: m[2].replace(/^\n+/, '').replace(/\s+$/, '') + '\n' }
}

function readIndex(dir) {
  const f = path.join(dir, '_index.md')
  return fs.existsSync(f) ? parseMd(f) : { fields: {} }
}
const titleOfFile = (file) => parseMd(file).fields.title || path.basename(file).replace(/\.md$/, '')
const titleOfDir = (dir) => readIndex(dir).fields.title || path.basename(dir)

function rawOrder(fields, name) {
  if (fields.weight != null && fields.weight !== '') {
    const w = Number(fields.weight)
    if (!Number.isNaN(w)) return w
  }
  const m = name.replace(/\.md$/, '').match(/(\d+)(?!.*\d)/)
  return m ? Number(m[1]) : null
}

const TRAD = ['學', '說', '萬', '爲', '與', '經', '國', '書', '體', '禮', '樂', '從', '無']
const SIMP = ['学', '说', '万', '为', '与', '经', '国', '书', '体', '礼', '乐', '从', '无']
function detectVariant(text) {
  let t = 0, s = 0
  for (const c of TRAD) if (text.includes(c)) t++
  for (const c of SIMP) if (text.includes(c)) s++
  if (t && s) return 'mixed'
  if (t) return 'trad'
  if (s) return 'simp'
  return undefined
}

function longestCommonPrefix(arr) {
  if (!arr.length) return ''
  let p = arr[0]
  for (const s of arr) {
    while (!s.startsWith(p)) p = p.slice(0, -1)
    if (!p) break
  }
  return p
}

function writeJson(rel, obj) {
  const full = path.join(OUT, rel)
  fs.mkdirSync(path.dirname(full), { recursive: true })
  fs.writeFileSync(full, JSON.stringify(obj, null, 2) + '\n')
}
function writeText(rel, body) {
  const full = path.join(OUT, rel)
  fs.mkdirSync(path.dirname(full), { recursive: true })
  fs.writeFileSync(full, body)
}

// ── 书边界判定 ────────────────────────────────────────
function looksLikeOneWork(titles, dirTitle) {
  if (titles.length === 0) return true
  if (dirTitle) return titles.every((t) => t.startsWith(dirTitle))
  return longestCommonPrefix(titles).length >= 2
}

function isBookDir(dir) {
  const idx = readIndex(dir)
  if (idx.fields.kind === 'book') return true
  if (idx.fields.kind === 'nav' || idx.fields.kind === 'section') return false

  const { dirs, files } = listDir(dir)
  const realDirs = dirs.filter((d) => !isBatchDir(d))
  const dirTitle = idx.fields.title || ''

  if (realDirs.length > 0) {
    const subTitles = realDirs.map((d) => titleOfDir(path.join(dir, d)))
    return looksLikeOneWork(subTitles, dirTitle)
  }
  if (files.length > 0) {
    const fileTitles = files.map((f) => titleOfFile(path.join(dir, f)))
    return looksLikeOneWork(fileTitles, dirTitle)
  }
  return true // 只有数字批次目录 → 单一作品的分页，是书
}

// ── 书内递归：建 nodes 树（collection/text），落正文 md ──
function walkBook(dir, idPrefix) {
  const { dirs, files } = listDir(dir)
  const nodes = []
  let leafCount = 0
  let hashInput = ''
  const variants = []

  const inlineFiles = files.map((f) => f)
  const realDirs = []
  for (const d of dirs) {
    if (isBatchDir(d)) for (const f of listDir(path.join(dir, d)).files) inlineFiles.push(path.join(d, f))
    else realDirs.push(d)
  }

  for (const f of inlineFiles) {
    const name = path.basename(f)
    const { fields, body } = parseMd(path.join(dir, f))
    const id = `${idPrefix}/${name.replace(/\.md$/, '')}`
    const src = `text/${id}.md`
    const v = detectVariant(body)
    if (v) variants.push(v)
    writeText(src, body)
    hashInput += id + '\n' + body + '\n'
    nodes.push({ type: 'text', id, title: fields.title || name.replace(/\.md$/, ''), _order: rawOrder(fields, name), _date: fields.date || '', src })
    leafCount++
  }
  for (const d of realDirs) {
    const idx = readIndex(path.join(dir, d))
    const child = walkBook(path.join(dir, d), `${idPrefix}/${d}`)
    nodes.push({ type: 'collection', title: idx.fields.title || d, _order: rawOrder(idx.fields, d), _date: idx.fields.date || '', children: child.nodes })
    leafCount += child.leafCount
    hashInput += child.hashInput
    variants.push(...child.variants)
  }
  sortNodes(nodes)
  for (const n of nodes) { delete n._order; delete n._date }
  return { nodes, leafCount, variants, hashInput }
}

function sortNodes(nodes) {
  const missing = nodes.filter((n) => n._order == null)
  if (missing.length) {
    missing.sort((a, b) => (a._date || '').localeCompare(b._date || '') || a.title.localeCompare(b.title))
    missing.forEach((n, i) => { n._order = 1000 + i })
  }
  nodes.sort((a, b) => a._order - b._order)
}

function rollupVariant(variants) {
  const set = new Set(variants.filter(Boolean))
  return set.size === 0 ? undefined : set.size === 1 ? [...set][0] : 'mixed'
}

// 产出一本「目录书」：写 book.json + 返回 catalog 的 book 引用
function emitBookFromDir(dir, bookId) {
  const idx = readIndex(dir)
  if (!fs.existsSync(path.join(dir, '_index.md'))) warn(`书缺 _index.md: ${bookId}`)
  if (!idx.fields.title) warn(`书目录标题为空(靠子项前缀判定): ${bookId}`)
  const { nodes, leafCount, variants, hashInput } = walkBook(dir, bookId)
  if (leafCount === 0) { warn(`书无正文，跳过: ${bookId}`); return null }
  const variant = rollupVariant(variants)
  const title = idx.fields.title || path.basename(dir)
  const ts = stamp(bookId, sha(JSON.stringify(nodes) + hashInput))
  writeJson(`book/${bookId}.json`, {
    schemaVersion: SCHEMA_VERSION, id: bookId, title,
    ...(idx.fields.summary ? { summary: idx.fields.summary } : {}),
    ...(variant ? { variant } : {}), createdAt: ts.createdAt, updatedAt: ts.updatedAt, nodes,
  })
  return bookRef(bookId, title, idx.fields.summary, leafCount, variant, rawOrder(idx.fields, path.basename(dir)), idx.fields.date, ts)
}

// 产出一本「单文件书」（nav 层散落的 md）
function emitSingleFileBook(file, bookId) {
  const { fields, body } = parseMd(file)
  const src = `text/${bookId}.md`
  writeText(src, body)
  const variant = detectVariant(body)
  const title = fields.title || path.basename(file).replace(/\.md$/, '')
  const ts = stamp(bookId, sha(body))
  writeJson(`book/${bookId}.json`, {
    schemaVersion: SCHEMA_VERSION, id: bookId, title,
    ...(fields.summary ? { summary: fields.summary } : {}),
    ...(variant ? { variant } : {}), createdAt: ts.createdAt, updatedAt: ts.updatedAt,
    nodes: [{ type: 'text', id: bookId, title, order: 1, src }],
  })
  return bookRef(bookId, title, fields.summary, 1, variant, rawOrder(fields, path.basename(file)), fields.date, ts)
}

function bookRef(id, title, summary, chapterCount, variant, order, date, ts) {
  return {
    type: 'book', id, title, ...(summary ? { summary } : {}), chapterCount,
    _order: order, _date: date || '', ...(variant ? { variant } : {}),
    createdAt: ts.createdAt, updatedAt: ts.updatedAt,
  }
}

// nav 层递归：返回 catalog 节点数组（collection | book），沿途产出 book.json
function classify(dir, idPrefix) {
  const { dirs, files } = listDir(dir)
  const nodes = []
  for (const f of files) {
    const ref = emitSingleFileBook(path.join(dir, f), `${idPrefix}/${f.replace(/\.md$/, '')}`)
    if (ref) nodes.push(ref)
  }
  for (const d of dirs.filter((x) => !isBatchDir(x))) {
    const sub = path.join(dir, d)
    const subId = `${idPrefix}/${d}`
    if (isBookDir(sub)) {
      const ref = emitBookFromDir(sub, subId)
      if (ref) nodes.push(ref)
    } else {
      const idx = readIndex(sub)
      nodes.push({ type: 'collection', title: idx.fields.title || d, _order: rawOrder(idx.fields, d), _date: idx.fields.date || '', children: classify(sub, subId) })
    }
  }
  sortNodes(nodes)
  for (const n of nodes) { delete n._order; delete n._date }
  return nodes
}

function countBooks(nodes) {
  let n = 0
  for (const x of nodes) n += x.type === 'book' ? 1 : countBooks(x.children)
  return n
}

// ── 主流程 ────────────────────────────────────────────
const manifestCategories = []
for (const cat of categories) {
  const catDir = path.join(SRC, cat)
  if (!fs.existsSync(catDir)) { warn(`门类目录不存在: ${catDir}`); continue }

  const catIdx = readIndex(catDir)
  let meta = {}
  const metaFile = path.join(catDir, '_meta.yml')
  if (fs.existsSync(metaFile)) for (const line of fs.readFileSync(metaFile, 'utf8').split('\n')) {
    const mm = line.match(/^([A-Za-z_]+):\s*(.*)$/); if (mm) meta[mm[1]] = stripQuotes(mm[2])
  }
  const tree = classify(catDir, cat)
  const bookCount = countBooks(tree)
  writeJson(`catalog/${cat}.json`, { schemaVersion: SCHEMA_VERSION, category: cat, tree })
  manifestCategories.push({
    id: cat, name: meta.name || catIdx.fields.title || cat,
    ...(meta.subtitle ? { subtitle: meta.subtitle } : {}),
    ...(meta.badge ? { badge: meta.badge } : {}),
    order: meta.order != null ? Number(meta.order) : Number(catIdx.fields.weight || 0), bookCount,
  })
  console.log(`✓ ${cat}：${bookCount} 本书`)
}

manifestCategories.sort((a, b) => a.order - b.order)
writeJson('manifest.json', { schemaVersion: SCHEMA_VERSION, generatedAt: NOW, categories: manifestCategories })

// 持久化时间戳状态（须随仓库保存，不进 dist-content）
fs.writeFileSync(STATE_FILE, JSON.stringify(nextState, null, 2) + '\n')

console.log('\n—— 校验报告 ——')
if (issues.length === 0) console.log('（无异常）')
else { for (const i of issues.slice(0, 40)) console.log('  • ' + i); if (issues.length > 40) console.log(`  …共 ${issues.length} 条`) }
console.log(`\n产物目录: ${OUT}/`)
