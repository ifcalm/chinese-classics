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

const ctype = (k) => k.endsWith('.json') ? 'application/json; charset=utf-8' : k.endsWith('.md') ? 'text/markdown; charset=utf-8' : k.endsWith('.xml') ? 'application/xml; charset=utf-8' : 'application/octet-stream'

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

// ── IndexNow：把本次真正上传成功的 key 映射回页面 URL 推给 Bing 等参与引擎，
//    新增/改动的收录延迟从天级降到小时级。推送失败只记日志，不影响上传结果。
//    key 文件托管在 public/<KEY>.txt(Worker 静态资产)，与此处常量须一致。
const SITE = 'https://www.chinese-classics.org'
const INDEXNOW_KEY = 'ddeed9f50cd0a63cc3e51d7b6a882666'
const keyToPage = (k) =>
  k.startsWith('text/') && k.endsWith('.md') ? `${SITE}/read/${k.slice(5, -3)}`
  : k.startsWith('book/') && k.endsWith('.json') ? `${SITE}/book/${k.slice(5, -5)}`
  : k.startsWith('catalog/') && k.endsWith('.json') ? `${SITE}/category/${k.slice(8, -5)}`
  : k === 'manifest.json' ? `${SITE}/`
  : null // sitemap/.files 等非页面产物不推
const pages = [...new Set(toUpload.filter((k) => uploaded[k] === current[k]).map(keyToPage).filter(Boolean))]
for (let i = 0; i < pages.length; i += 10000) { // 协议单次上限 1 万
  const batch = pages.slice(i, i + 10000)
  try {
    const r = await fetch('https://api.indexnow.org/indexnow', {
      method: 'POST',
      headers: { 'content-type': 'application/json; charset=utf-8' },
      body: JSON.stringify({
        host: 'www.chinese-classics.org', key: INDEXNOW_KEY,
        keyLocation: `${SITE}/${INDEXNOW_KEY}.txt`, urlList: batch,
      }),
    })
    console.log(`IndexNow: 推送 ${batch.length} URL → HTTP ${r.status}`)
  } catch (e) {
    console.log(`IndexNow: 推送失败(不影响上传): ${e.cause?.message ?? e.message}`)
  }
}

if (up.fail) process.exit(1)
