import { useEffect, useMemo, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { errText, getBook, getChapterText, flattenBook, resolveBookId } from '../data/content'
import type { BookDetail, BookText } from '../data/types'
import { useTheme } from '../theme/ThemeProvider'
import { ChevronLeftIcon } from '../components/Icons'

const FONT_MIN = 16
const FONT_MAX = 24

/** 轻量 md 渲染：空行分段，识别标题与代码块；正文以纯文本为主。 */
function renderText(md: string) {
  const blocks = md.split(/\n{2,}/)
  const out: React.ReactNode[] = []
  for (let i = 0; i < blocks.length; i++) {
    const b = blocks[i].trim()
    if (!b) continue
    if (b.startsWith('```')) {
      out.push(
        <pre key={i} className="reader__pre">
          {b.replace(/^```[a-z]*\n?/, '').replace(/```$/, '')}
        </pre>
      )
    } else if (/^#{1,6}\s/.test(b)) {
      out.push(
        <h3 key={i} className="reader__h">
          {b.replace(/^#{1,6}\s/, '')}
        </h3>
      )
    } else {
      out.push(
        <p key={i} className="reader__text">
          {b}
        </p>
      )
    }
  }
  return out
}

export default function Reader() {
  const { '*': chapterId = '' } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const { theme, toggle } = useTheme()

  const stateBookId = (location.state as { bookId?: string })?.bookId
  const [bookId, setBookId] = useState<string>(stateBookId ?? '')
  const [book, setBook] = useState<BookDetail | null>(null)
  const [text, setText] = useState<string | null>(null)
  const [err, setErr] = useState<string>()

  // 解析 bookId：优先 router state，否则按 chapterId 探测
  useEffect(() => {
    if (stateBookId) { setBookId(stateBookId); return }
    resolveBookId(chapterId).then(setBookId).catch((e) => setErr(errText(e)))
  }, [chapterId, stateBookId])

  const [fontSize, setFontSize] = useState(() => Number(localStorage.getItem('cc-fontsize')) || 18)
  const [vertical, setVertical] = useState(() => localStorage.getItem('cc-vertical') === '1')
  const [tocOpen, setTocOpen] = useState(false)
  const [progress, setProgress] = useState(0)

  useEffect(() => localStorage.setItem('cc-fontsize', String(fontSize)), [fontSize])
  useEffect(() => localStorage.setItem('cc-vertical', vertical ? '1' : '0'), [vertical])

  // 载入书目录树
  useEffect(() => {
    if (!bookId) return
    setErr(undefined)
    getBook(bookId).then(setBook).catch((e) => setErr(errText(e)))
  }, [bookId])

  const flat = useMemo(() => (book ? flattenBook(book.nodes) : []), [book])
  const index = flat.findIndex((c) => c.id === chapterId)
  const chapter: BookText | undefined = index >= 0 ? flat[index] : undefined
  const prev = index > 0 ? flat[index - 1] : undefined
  const next = index >= 0 && index < flat.length - 1 ? flat[index + 1] : undefined

  // 载入当前篇正文
  useEffect(() => {
    setText(null)
    if (!chapter) return
    getChapterText(chapter.src).then(setText).catch((e) => setErr(errText(e)))
  }, [chapter?.src])

  // 阅读进度
  useEffect(() => {
    const onScroll = () => {
      const h = document.documentElement.scrollHeight - window.innerHeight
      setProgress(h > 0 ? Math.min(1, window.scrollY / h) : 1)
    }
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [chapterId, text])

  useEffect(() => window.scrollTo(0, 0), [chapterId])

  // Esc 关闭目录抽屉
  useEffect(() => {
    if (!tocOpen) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setTocOpen(false)
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [tocOpen])

  const go = (cid: string) => navigate(`/read/${cid}`, { state: { bookId } })

  if (err) {
    return (
      <div className="reader">
        <div className="page reader__bar">
          <Link to="/" className="reader__back" aria-label="返回首页">
            <ChevronLeftIcon size={18} />
          </Link>
          <span className="reader__crumb">加载出错</span>
          <span style={{ width: 18 }} />
        </div>
        <p className="empty">{err}，<Link to="/" className="accent">返回首页</Link>。</p>
      </div>
    )
  }

  return (
    <div className={`reader ${vertical ? 'reader--vertical' : ''}`}>
      <div className="reader__progress">
        <span style={{ width: `${Math.round(progress * 100)}%` }} />
      </div>

      <div className="page reader__bar">
        <Link to={`/book/${bookId}`} className="reader__back" aria-label="返回目录">
          <ChevronLeftIcon size={18} />
        </Link>
        <span className="reader__crumb">
          {book?.title ?? '…'}
          {chapter && ` · ${chapter.title}`}
        </span>
        <button className="reader__toc-btn" onClick={() => setTocOpen(true)} aria-label="目录">
          目录
        </button>
      </div>

      <article className="page reader__body">
        {!chapter ? (
          <p className="empty">{book ? '未找到该篇。' : '载入中…'}</p>
        ) : (
          <>
            <h1 className="reader__chapter">{chapter.title}</h1>
            <div className="reader__rule" aria-hidden="true" />
            {/* 用户字号以 rem 应用，随根字号一同适配屏幕 */}
            <div className="reader__flow" style={{ fontSize: `${fontSize / 15}rem` }}>
              {text == null ? <p className="reader__text">载入中…</p> : renderText(text)}
            </div>

            <nav className="reader__nav">
              {prev ? (
                <button onClick={() => go(prev.id)} className="reader__nav-btn">
                  ← {prev.title}
                </button>
              ) : (
                <span />
              )}
              {next ? (
                <button onClick={() => go(next.id)} className="reader__nav-btn">
                  {next.title} →
                </button>
              ) : (
                <span />
              )}
            </nav>
          </>
        )}
      </article>

      <div className="reader__tools" role="toolbar" aria-label="阅读设置">
        <button
          className="reader__tool"
          onClick={() => setFontSize((f) => Math.max(FONT_MIN, f - 1))}
          aria-label="缩小字号"
        >
          A−
        </button>
        <button
          className="reader__tool"
          onClick={() => setFontSize((f) => Math.min(FONT_MAX, f + 1))}
          aria-label="放大字号"
        >
          A+
        </button>
        <span className="reader__tool-sep" />
        <button
          className={`reader__tool ${vertical ? 'is-on' : ''}`}
          onClick={() => setVertical((v) => !v)}
        >
          竖排
        </button>
        <button className="reader__tool" onClick={toggle}>
          {theme === 'light' ? '夜读' : '日间'}
        </button>
      </div>

      {tocOpen && book && (
        <div className="drawer" onClick={() => setTocOpen(false)}>
          <aside className="drawer__panel" onClick={(e) => e.stopPropagation()}>
            <div className="drawer__head">
              <span className="drawer__title">{book.title}</span>
              <button className="drawer__close" onClick={() => setTocOpen(false)} aria-label="关闭">
                ✕
              </button>
            </div>
            <ul className="drawer__list">
              {flat.map((c) => (
                <li key={c.id}>
                  <button
                    className={`drawer__item ${c.id === chapterId ? 'is-current' : ''}`}
                    onClick={() => {
                      go(c.id)
                      setTocOpen(false)
                    }}
                  >
                    {c.title}
                  </button>
                </li>
              ))}
            </ul>
          </aside>
        </div>
      )}
    </div>
  )
}
