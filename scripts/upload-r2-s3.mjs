#!/usr/bin/env node
// 走 R2 的 S3 接口(SigV4)按内容哈希增量上传 —— 无 Cloudflare API 的 ~4/s 限流,可高并发。
// 凭证取自 .env.local: R2_ACCOUNT_ID / R2_ACCESS_KEY_ID / R2_SECRET_ACCESS_KEY
// 用法: node scripts/upload-r2-s3.mjs [桶名=chinese-classics] [并发=24]

import fs from 'node:fs'
import { AwsClient } from 'aws4fetch'

const BUCKET = process.argv[2] || 'chinese-classics'
const PAR = Number(process.argv[3] || 24)
const OUT = 'dist-content'
const UPLOADED = '.r2-uploaded.json'

for (const line of fs.readFileSync('.env.local', 'utf8').split('\n')) {
  const m = line.match(/^([A-Z0-9_]+)=(.*)$/)
  if (m) process.env[m[1]] = m[2]
}
const ENDPOINT = `https://${process.env.R2_ACCOUNT_ID}.r2.cloudflarestorage.com`
const aws = new AwsClient({ accessKeyId: process.env.R2_ACCESS_KEY_ID, secretAccessKey: process.env.R2_SECRET_ACCESS_KEY, region: 'auto', service: 's3' })

const ctype = (k) => k.endsWith('.json') ? 'application/json; charset=utf-8' : k.endsWith('.md') ? 'text/markdown; charset=utf-8' : 'application/octet-stream'

const current = JSON.parse(fs.readFileSync(`${OUT}/.files.json`, 'utf8'))
const uploaded = fs.existsSync(UPLOADED) ? JSON.parse(fs.readFileSync(UPLOADED, 'utf8')) : {}
const toUpload = Object.keys(current).filter((k) => current[k] !== uploaded[k])
const toDelete = Object.keys(uploaded).filter((k) => !(k in current))
console.log(`增量(S3): 上传 ${toUpload.length} · 删除 ${toDelete.length} · 跳过 ${Object.keys(current).length - toUpload.length}`)
if (!toUpload.length && !toDelete.length) { console.log('R2 已是最新。'); process.exit(0) }

const save = () => fs.writeFileSync(UPLOADED, JSON.stringify(uploaded, null, 2) + '\n')
async function put(key) {
  const body = fs.readFileSync(`${OUT}/${key}`)
  for (let n = 1; n <= 4; n++) {
    try {
      const r = await aws.fetch(`${ENDPOINT}/${BUCKET}/${key}`, { method: 'PUT', body, headers: { 'content-type': ctype(key) } })
      if (r.ok) { uploaded[key] = current[key]; return true }
    } catch {}
    await new Promise((r) => setTimeout(r, n * 500))
  }
  return false
}
async function del(key) {
  try { const r = await aws.fetch(`${ENDPOINT}/${BUCKET}/${key}`, { method: 'DELETE' }); if (r.ok || r.status === 404) { delete uploaded[key]; return true } } catch {}
  return false
}
async function pool(items, worker) {
  let i = 0, ok = 0, fail = 0, done = 0
  await Promise.all(Array.from({ length: PAR }, async () => {
    while (i < items.length) { (await worker(items[i++])) ? ok++ : fail++; if (++done % 200 === 0) { save(); process.stdout.write(`\r  ${done}/${items.length}`) } }
  }))
  return { ok, fail }
}

const up = await pool(toUpload, put)
const dl = toDelete.length ? await pool(toDelete, del) : { ok: 0, fail: 0 }
save()
console.log(`\n完成: 上传 ${up.ok} 成功/${up.fail} 失败 · 删除 ${dl.ok}`)
if (up.fail) process.exit(1)
