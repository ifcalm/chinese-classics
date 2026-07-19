#!/usr/bin/env node
// 名句库 D1 同步：data/quotes.json(git 源) → Cloudflare D1(服务副本)。
// 数据小，采用幂等全量重建；D1 只是 /api/quotes/random 的查询层，
// 唯一源永远是 git 里的 data/quotes.json——改名句请改源文件并重跑：
//   python3 scripts/check-integrity.py   # 逐字命中出处的保真闸
//   node scripts/sync-quotes-d1.mjs      # 远端 D1（加 --local 灌 wrangler dev 本地库）

import fs from 'node:fs'
import { execFileSync } from 'node:child_process'

const DB = 'chinese-classics-quotes'
const SQL_FILE = '.quotes-d1.sql'
const esc = (s) => s.replace(/'/g, "''")

const { quotes } = JSON.parse(fs.readFileSync('data/quotes.json', 'utf8'))
if (!quotes?.length) {
  console.error('data/quotes.json 无名句，拒绝清空 D1。')
  process.exit(1)
}
const rows = quotes.map((q) =>
  `('${esc(q.id)}','${esc(q.text)}','${esc(q.source)}','${esc(q.chapterId)}','${esc(q.chapterId.split('/')[0])}')`)
const sql = [
  'DROP TABLE IF EXISTS quotes;',
  'CREATE TABLE quotes (id TEXT PRIMARY KEY, text TEXT NOT NULL, source TEXT NOT NULL, chapter_id TEXT NOT NULL, category TEXT NOT NULL);',
  `INSERT INTO quotes (id, text, source, chapter_id, category) VALUES\n${rows.join(',\n')};`,
].join('\n')
fs.writeFileSync(SQL_FILE, sql)

const mode = process.argv.includes('--local') ? '--local' : '--remote'
try {
  execFileSync('npx', ['wrangler', 'd1', 'execute', DB, mode, `--file=${SQL_FILE}`, '-y'], { stdio: 'inherit' })
} finally {
  fs.unlinkSync(SQL_FILE)
}
console.log(`D1 同步完成：${quotes.length} 条名句（${mode.slice(2)}）`)
