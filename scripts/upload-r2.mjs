#!/usr/bin/env node
// 按「内容哈希」增量上传 dist-content 到 R2：只传新增/改动的文件，跳过未变的。
// 状态记录在 .r2-uploaded.json（随仓库提交），所以补录时一眼看清传了哪些。
//
// 用法：node scripts/upload-r2.mjs [桶名=chinese-classics] [并发=3]
//   先跑 build-content.mjs 生成 dist-content/.files.json。
//   用 .env.local 的 CLOUDFLARE_API_TOKEN 鉴权（走 Cloudflare API，限流约 4/s，故并发压低）。

import fs from 'node:fs'
import { execFile } from 'node:child_process'

const BUCKET = process.argv[2] || 'chinese-classics'
const PAR = Number(process.argv[3] || 3)
const OUT = 'dist-content'
const FILES = `${OUT}/.files.json`
const UPLOADED = '.r2-uploaded.json'
const WR = 'node_modules/.bin/wrangler'

// 载入 .env.local
for (const line of fs.readFileSync('.env.local', 'utf8').split('\n')) {
  const m = line.match(/^([A-Z_]+)=(.*)$/)
  if (m) process.env[m[1]] = m[2]
}
process.env.CI = '1'
process.env.WRANGLER_SEND_METRICS = 'false'

if (!fs.existsSync(FILES)) { console.error(`缺 ${FILES}，先跑 build-content.mjs`); process.exit(1) }
const current = JSON.parse(fs.readFileSync(FILES, 'utf8'))
const uploaded = fs.existsSync(UPLOADED) ? JSON.parse(fs.readFileSync(UPLOADED, 'utf8')) : {}

const toUpload = Object.keys(current).filter((k) => current[k] !== uploaded[k])
const toDelete = Object.keys(uploaded).filter((k) => !(k in current))
console.log(`增量：上传 ${toUpload.length}（新增/改动）· 删除 ${toDelete.length} · 跳过未变 ${Object.keys(current).length - toUpload.length}`)
if (toUpload.length === 0 && toDelete.length === 0) { console.log('R2 已是最新，无需上传。'); process.exit(0) }

const run = (args) => new Promise((res) => execFile(WR, args, { cwd: process.cwd() }, (err) => res(!err)))
const save = () => fs.writeFileSync(UPLOADED, JSON.stringify(uploaded, null, 2) + '\n')

async function putOne(key) {
  for (let n = 1; n <= 6; n++) {
    if (await run(['r2', 'object', 'put', `${BUCKET}/${key}`, '--file', `${OUT}/${key}`, '--remote'])) {
      uploaded[key] = current[key]; return true
    }
    await new Promise((r) => setTimeout(r, n * 3000)) // 退避，避让 971 限流
  }
  return false
}
async function delOne(key) {
  if (await run(['r2', 'object', 'delete', `${BUCKET}/${key}`, '--remote'])) { delete uploaded[key]; return true }
  return false
}

// 简单并发池
async function pool(items, worker) {
  let i = 0, ok = 0, fail = 0, done = 0
  await Promise.all(Array.from({ length: PAR }, async () => {
    while (i < items.length) {
      const it = items[i++]
      ;(await worker(it)) ? ok++ : fail++
      if (++done % 100 === 0) { save(); process.stdout.write(`\r  进度 ${done}/${items.length}`) }
    }
  }))
  return { ok, fail }
}

const up = await pool(toUpload, putOne)
const del = toDelete.length ? await pool(toDelete, delOne) : { ok: 0, fail: 0 }
save()
console.log(`\n完成：上传 ${up.ok} 成功/${up.fail} 失败 · 删除 ${del.ok} · 状态写入 ${UPLOADED}`)
if (up.fail) { console.log('有失败，重跑本脚本即可续传（已成功的会跳过）。'); process.exit(1) }
