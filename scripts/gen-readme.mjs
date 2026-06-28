#!/usr/bin/env node
// 从 dist-content（manifest + catalog）自动生成 README.md 的收录目录与计数。
// 每次内容变动后跑一次，README 即保持最新。用法：node scripts/gen-readme.mjs

import fs from 'node:fs'

const OUT = 'dist-content'
const SITE = 'https://chinese-classics.org'

const manifest = JSON.parse(fs.readFileSync(`${OUT}/manifest.json`, 'utf8'))

const countBooks = (nodes) => nodes.reduce((s, n) => s + (n.type === 'book' ? 1 : countBooks(n.children)), 0)
const countChapters = (nodes) => nodes.reduce((s, n) => s + (n.type === 'book' ? n.chapterCount : countChapters(n.children)), 0)

// 渲染 catalog 树为嵌套列表：collection 加粗、book 列出篇数
function renderTree(nodes, depth = 0) {
  const pad = '  '.repeat(depth)
  let out = ''
  for (const n of nodes) {
    if (n.type === 'book') out += `${pad}- ${n.title} · ${n.chapterCount} 篇\n`
    else { out += `${pad}- **${n.title}**\n`; out += renderTree(n.children, depth + 1) }
  }
  return out
}

let totalBooks = 0, totalChapters = 0
const rows = []
const sections = []

for (const c of manifest.categories) {
  const cat = JSON.parse(fs.readFileSync(`${OUT}/catalog/${c.id}.json`, 'utf8'))
  const books = countBooks(cat.tree)
  const chapters = countChapters(cat.tree)
  totalBooks += books
  totalChapters += chapters
  rows.push(`| ${c.name} | ${books} | ${chapters.toLocaleString()} |`)
  sections.push(`### ${c.name} · ${books} 部 · ${chapters.toLocaleString()} 篇\n\n${renderTree(cat.tree)}`)
}

const date = (manifest.generatedAt || new Date().toISOString()).slice(0, 10)

const md = `# 古典文库 · Chinese Classics

> 读经典，不必正襟危坐。

在线阅读：**[${SITE}](${SITE})**

收录中国古典典籍，正文以 Markdown 维护，构建为 JSON + 纯文本 md 存于 Cloudflare R2，前端按需取读。
数据架构见 [docs/data-architecture.md](docs/data-architecture.md)。

> 本文件由 \`scripts/gen-readme.mjs\` 自动生成，请勿手改；内容变动后运行 \`npm run readme\` 刷新。

## 收录概况

**截至 ${date}：共 ${manifest.categories.length} 门类 · ${totalBooks} 部 · ${totalChapters.toLocaleString()} 篇**

| 门类 | 部数 | 篇数 |
|---|---:|---:|
${rows.join('\n')}
| **合计** | **${totalBooks}** | **${totalChapters.toLocaleString()}** |

## 典籍目录

${sections.join('\n')}
`

fs.writeFileSync('README.md', md)
console.log(`README.md 已生成：${manifest.categories.length} 门类 · ${totalBooks} 部 · ${totalChapters} 篇`)
