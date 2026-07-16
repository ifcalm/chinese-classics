// 正文 md → HTML 字符串，供 Worker 边缘渲染。
// 块级规则与 Reader.tsx 的 renderText 一一对应(空行分段/围栏/标题/引用)，
// class 名沿用阅读页样式，无 JS 时爬虫与用户看到的是同一套排版。

export function escapeHtml(s: string): string {
  return s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]!)
}

/** 韵文判定(诗/词)，与 Reader 同一份实现(Reader 从这里 import)。
    全篇为纯文本短段(无标题、无代码块)，段数 ≥ 3 且每段最长行 ≤ 30 字。 */
export function isVerse(md: string): boolean {
  const blocks = md.split(/\n{2,}/).map((b) => b.trim()).filter(Boolean)
  const hasNonPlain = blocks.some((b) => b.startsWith('```') || b.startsWith('>') || /^#{1,6}\s/.test(b))
  if (hasNonPlain || blocks.length < 3) return false
  return blocks.every((b) => b.split('\n').every((line) => line.trim().length <= 30))
}

export function mdToHtml(md: string): string {
  const blocks = md.split(/\n{2,}/)
  const out: string[] = []
  for (let i = 0; i < blocks.length; i++) {
    const b = blocks[i].trim()
    if (!b) continue
    if (b.startsWith('```')) {
      // 与 Reader 一致：闭合围栏后紧跟的余文(如「坤下坎上」)单独成段
      const m = /^```[a-z]*\n?([\s\S]*?)\n?```(?:\n([\s\S]*))?$/.exec(b)
      const pre = m ? m[1] : b.replace(/^```[a-z]*\n?/, '').replace(/```$/, '')
      out.push(`<pre class="reader__pre">${escapeHtml(pre)}</pre>`)
      const rest = m?.[2]?.trim()
      if (rest) out.push(`<p class="reader__text">${escapeHtml(rest)}</p>`)
    } else if (/^#{1,6}\s/.test(b)) {
      out.push(`<h3 class="reader__h">${escapeHtml(b.replace(/^#{1,6}\s/, ''))}</h3>`)
    } else if (b.startsWith('> ')) {
      const quotes = [b]
      while (i + 1 < blocks.length && blocks[i + 1].trim().startsWith('> ')) quotes.push(blocks[++i].trim())
      const ps = quotes.map((q) => `<p>${escapeHtml(q.replace(/^>\s?/gm, ''))}</p>`).join('')
      out.push(`<blockquote class="reader__quote">${ps}</blockquote>`)
    } else {
      out.push(`<p class="reader__text">${escapeHtml(b)}</p>`)
    }
  }
  return out.join('\n')
}
