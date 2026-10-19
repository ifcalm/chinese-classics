import { useEffect, useRef, useState } from 'react'

// 邮箱拆开存放、点击时才拼出：直出 HTML 与 DOM 初始状态里都没有完整地址，避开简单的邮箱采集器
const MAIL_USER = 'contact'
const MAIL_HOST = 'chinese-classics.org'
const MAIL_SUBJECT = '【古典文库】'

/** 页脚：版权一行 + 「联系」浮层(显示地址 / 复制 / 发邮件)。
    inline：嵌在已有 .page 容器内(阅读页)，不再套一层版心。
    Worker 直出的页脚结构见 seo/pages.ts 的 FOOTER_HTML，改动须两边同步。 */
export default function Footer({ inline = false }: { inline?: boolean }) {
  const [open, setOpen] = useState(false)
  const [copied, setCopied] = useState(false)
  const wrapRef = useRef<HTMLDivElement>(null)
  const addrRef = useRef<HTMLElement>(null)

  // 点外面 / Esc 关闭
  useEffect(() => {
    if (!open) return
    const onDown = (e: PointerEvent) => {
      if (!wrapRef.current?.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('pointerdown', onDown)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('pointerdown', onDown)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  useEffect(() => {
    if (!copied) return
    const t = setTimeout(() => setCopied(false), 1600)
    return () => clearTimeout(t)
  }, [copied])

  const addr = open ? `${MAIL_USER}@${MAIL_HOST}` : ''

  const copy = () => {
    const selectAddr = () => {
      const el = addrRef.current
      if (!el) return
      const range = document.createRange()
      range.selectNodeContents(el)
      const sel = window.getSelection()
      sel?.removeAllRanges()
      sel?.addRange(range)
    }
    // 剪贴板 API 在旧内核 / 非安全上下文可能缺失：退化为选中地址，用户自行复制
    if (typeof navigator.clipboard?.writeText !== 'function') return selectAddr()
    navigator.clipboard.writeText(addr).then(() => setCopied(true), selectAddr)
  }

  return (
    <footer className="site-footer">
      <div className={`site-footer__inner${inline ? '' : ' page'}`}>
        <span className="site-footer__copy">© 古典文库</span>
        <div className="site-footer__contact" ref={wrapRef}>
          <button
            type="button"
            className="site-footer__btn"
            aria-expanded={open}
            aria-haspopup="dialog"
            onClick={() => setOpen((v) => !v)}
          >
            联系
          </button>
          {open && (
            <div className="contact-pop" role="dialog" aria-label="联系">
              <p className="contact-pop__tip">版权、合作、建议，或其他事宜，请发邮件。</p>
              <code className="contact-pop__addr" ref={addrRef}>
                {addr}
              </code>
              <div className="contact-pop__actions">
                <button type="button" className="contact-pop__act" onClick={copy}>
                  {copied ? '已复制' : '复制'}
                </button>
                <a
                  className="contact-pop__act contact-pop__act--main"
                  href={`mailto:${addr}?subject=${encodeURIComponent(MAIL_SUBJECT)}`}
                >
                  发邮件
                </a>
              </div>
            </div>
          )}
        </div>
      </div>
    </footer>
  )
}
