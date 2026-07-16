#!/usr/bin/env node
// 从 dist-content 派生 sitemap：pages(首页+门类) + 每门类一片(书目页+全部章节页)，
// 外加 sitemap index。lastmod 取 book.json 的 updatedAt(构建状态维护的内容时间)。
// 产物写进 dist-content/sitemap/ 并登记 .files.json，随 content:upload 增量上 R2；
// Worker 把 /sitemap.xml、/sitemap/*.xml 映射到这些 key。
// 新增书目走正常 content:build 即自动进 sitemap —— 本脚本挂在 content:build 链上。

import fs from 'node:fs'
import path from 'node:path'
import crypto from 'node:crypto'

const OUT = 'dist-content'
const SITE = 'https://www.chinese-classics.org'
const MAX_URLS = 40000 // 单片上限(规范 50k)，超出自动分片

const sha = (s) => crypto.createHash('sha256').update(s).digest('hex').slice(0, 16)
const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
const day = (iso) => (iso ?? '').slice(0, 10) || undefined

const readJson = (rel) => JSON.parse(fs.readFileSync(path.join(OUT, rel), 'utf8'))

function urlset(urls) {
  const body = urls
    .map((u) => `<url><loc>${esc(SITE + u.path)}</loc>${u.lastmod ? `<lastmod>${u.lastmod}</lastmod>` : ''}</url>`)
    .join('\n')
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${body}\n</urlset>\n`
}

const flattenTree = (nodes, pick) =>
  nodes.flatMap((n) => (n.type === pick ? [n] : n.children ? flattenTree(n.children, pick) : []))

const manifest = readJson('manifest.json')
const files = {} // rel → xml 内容
const shards = [] // { name, count } 供 index 与日志

for (const cat of manifest.categories) {
  const catalog = readJson(`catalog/${cat.id}.json`)
  const books = flattenTree(catalog.tree, 'book')
  const urls = []
  for (const b of books) {
    const book = readJson(`book/${b.id}.json`)
    const lastmod = day(book.updatedAt)
    urls.push({ path: `/book/${b.id}`, lastmod })
    for (const ch of flattenTree(book.nodes, 'text')) urls.push({ path: `/read/${ch.id}`, lastmod })
  }
  for (let i = 0; i * MAX_URLS < urls.length; i++) {
    const name = i === 0 ? `${cat.id}.xml` : `${cat.id}-${i + 1}.xml`
    files[`sitemap/${name}`] = urlset(urls.slice(i * MAX_URLS, (i + 1) * MAX_URLS))
    shards.push({ name, count: Math.min(urls.length - i * MAX_URLS, MAX_URLS) })
  }
}

// 首页 + 门类页
files['sitemap/pages.xml'] = urlset([
  { path: '/', lastmod: day(manifest.generatedAt) },
  ...manifest.categories.map((c) => ({ path: `/category/${c.id}`, lastmod: day(manifest.generatedAt) })),
])
shards.unshift({ name: 'pages.xml', count: manifest.categories.length + 1 })

files['sitemap/index.xml'] = `<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${shards
  .map((s) => `<sitemap><loc>${SITE}/sitemap/${s.name}</loc></sitemap>`)
  .join('\n')}\n</sitemapindex>\n`

// 落盘 + 登记 .files.json(供上传脚本做内容级增量；先清掉旧 sitemap 条目防残留)
const hashesPath = path.join(OUT, '.files.json')
const hashes = JSON.parse(fs.readFileSync(hashesPath, 'utf8'))
for (const k of Object.keys(hashes)) if (k.startsWith('sitemap/')) delete hashes[k]
fs.rmSync(path.join(OUT, 'sitemap'), { recursive: true, force: true })
fs.mkdirSync(path.join(OUT, 'sitemap'), { recursive: true })
for (const [rel, content] of Object.entries(files)) {
  fs.writeFileSync(path.join(OUT, rel), content)
  hashes[rel] = sha(content)
}
fs.writeFileSync(hashesPath, JSON.stringify(hashes, null, 2) + '\n')

const total = shards.reduce((s, x) => s + x.count, 0)
console.log(`sitemap: ${shards.length} 片 · ${total} URL`)
for (const s of shards) console.log(`  ${s.name}: ${s.count}`)
