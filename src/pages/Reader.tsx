import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { getBook } from '../data/books'
import { useTheme } from '../theme/ThemeProvider'
import { ChevronLeftIcon } from '../components/Icons'

const FONT_MIN = 16
const FONT_MAX = 24

export default function Reader() {
  const { bookId = '', chapterId = '' } = useParams()
  const navigate = useNavigate()
  const { theme, toggle } = useTheme()

  const book = getBook(bookId)
  const index = book?.chapters.findIndex((c) => c.id === chapterId) ?? -1
  const chapter = index >= 0 ? book!.chapters[index] : undefined

  const [fontSize, setFontSize] = useState(() =>
    Number(localStorage.getItem('cc-fontsize')) || 18
  )
  const [vertical, setVertical] = useState(() => localStorage.getItem('cc-vertical') === '1')
  const [showNotes, setShowNotes] = useState(() => localStorage.getItem('cc-notes') !== '0')
  const [tocOpen, setTocOpen] = useState(false)
  const [progress, setProgress] = useState(0)

  useEffect(() => localStorage.setItem('cc-fontsize', String(fontSize)), [fontSize])
  useEffect(() => localStorage.setItem('cc-vertical', vertical ? '1' : '0'), [vertical])
  useEffect(() => localStorage.setItem('cc-notes', showNotes ? '1' : '0'), [showNotes])

  // 滚动阅读进度
  useEffect(() => {
    const onScroll = () => {
      const h = document.documentElement.scrollHeight - window.innerHeight
      setProgress(h > 0 ? Math.min(1, window.scrollY / h) : 1)
    }
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [chapterId])

  // 切章回到顶部
  useEffect(() => window.scrollTo(0, 0), [chapterId])

  if (!book || !chapter) {
    return (
      <div className="reader">
        <div className="page reader__bar">
          <Link to="/" className="reader__back" aria-label="返回首页">
            <ChevronLeftIcon size={18} />
          </Link>
          <span className="reader__crumb">未找到该篇</span>
          <span style={{ width: 18 }} />
        </div>
        <p className="empty">内容不存在，<Link to="/" className="accent">返回首页</Link>。</p>
      </div>
    )
  }

  const prev = index > 0 ? book.chapters[index - 1] : undefined
  const next = index < book.chapters.length - 1 ? book.chapters[index + 1] : undefined
  const go = (cid: string) => navigate(`/read/${book.id}/${cid}`)

  return (
    <div className={`reader ${vertical ? 'reader--vertical' : ''}`}>
      <div className="reader__progress">
        <span style={{ width: `${Math.round(progress * 100)}%` }} />
      </div>

      <div className="page reader__bar">
        <Link to={`/category/${book.categoryId}`} className="reader__back" aria-label="返回书目">
          <ChevronLeftIcon size={18} />
        </Link>
        <span className="reader__crumb">
          {book.title} · {chapter.title}
        </span>
        <button className="reader__toc-btn" onClick={() => setTocOpen(true)} aria-label="目录">
          目录
        </button>
      </div>

      <article className="page reader__body">
        <h1 className="reader__chapter">{chapter.title}</h1>
        <div className="reader__rule" aria-hidden="true" />
        <div className="reader__flow">
          <p className="reader__text" style={{ fontSize }}>
            {chapter.text}
          </p>
          {showNotes && chapter.note && (
            <p className="reader__note" style={{ fontSize: Math.max(13, fontSize - 4) }}>
              <span className="reader__note-tag">注</span>
              {chapter.note}
            </p>
          )}
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
      </article>

      {/* 悬浮工具条 */}
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
        <button
          className={`reader__tool ${showNotes ? 'is-on' : ''}`}
          onClick={() => setShowNotes((s) => !s)}
        >
          注释
        </button>
        <button className="reader__tool" onClick={toggle}>
          {theme === 'light' ? '夜读' : '日间'}
        </button>
      </div>

      {/* 目录抽屉 */}
      {tocOpen && (
        <div className="drawer" onClick={() => setTocOpen(false)}>
          <aside className="drawer__panel" onClick={(e) => e.stopPropagation()}>
            <div className="drawer__head">
              <span className="drawer__title">{book.title}</span>
              <button className="drawer__close" onClick={() => setTocOpen(false)} aria-label="关闭">
                ✕
              </button>
            </div>
            <ul className="drawer__list">
              {book.chapters.map((c) => (
                <li key={c.id}>
                  <button
                    className={`drawer__item ${c.id === chapter.id ? 'is-current' : ''}`}
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
