import { useEffect, useMemo, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { errText, getBook, getChapterText, flattenBook, resolveBookId } from '../data/content'
import type { BookDetail, BookText } from '../data/types'
import { useTheme } from '../theme/ThemeProvider'
import { ChevronLeftIcon } from '../components/Icons'

const FONT_MIN = 16
const FONT_MAX = 24

/** 韵文判定(诗/词)：全篇为纯文本短段(无标题、无代码块)，
    段数 ≥ 3 且每段最长行 ≤ 30 字。散文段落远超此长度，不会误判。
    将来 build 在 book.json 写入体裁标记后，可改为只信数据。 */
function isVerse(md: string): boolean {
  const blocks = md.split(/\n{2,}/).map((b) => b.trim()).filter(Boolean)
  const hasNonPlain = blocks.some((b) => b.startsWith('```') || b.startsWith('>') || /^#{1,6}\s/.test(b))
  if (hasNonPlain || blocks.length < 3) return false
  return blocks.every((b) => b.split('\n').every((line) => line.trim().length <= 30))
}

/** 轻量 md 渲染：空行分段，识别标题与代码块；正文以纯文本为主。 */
function renderText(md: string) {
  const blocks = md.split(/\n{2,}/)
  const out: React.ReactNode[] = []
  for (let i = 0; i < blocks.length; i++) {
    const b = blocks[i].trim()
    if (!b) continue
    if (b.startsWith('```')) {
      // 易经卦象等处，闭合围栏后紧跟正文(如「坤下坎上」)且源本无空行相隔，与围栏同属一段。
      // 故显式切出围栏内容与其后余文；不可只剥段尾围栏(段尾是余文，围栏会漏出且余文被吞进 pre)。
      const m = /^```[a-z]*\n?([\s\S]*?)\n?```(?:\n([\s\S]*))?$/.exec(b)
      out.push(
        <pre key={i} className="reader__pre">
          {m ? m[1] : b.replace(/^```[a-z]*\n?/, '').replace(/```$/, '')}
        </pre>
      )
      const rest = m?.[2]?.trim()
      if (rest) {
        out.push(
          <p key={`${i}-rest`} className="reader__text">
            {rest}
          </p>
        )
      }
    } else if (/^#{1,6}\s/.test(b)) {
      out.push(
        <h3 key={i} className="reader__h">
          {b.replace(/^#{1,6}\s/, '')}
        </h3>
      )
    } else if (b.startsWith('> ')) {
      // 引用块(如僧传卷首传目):相邻引用段并入同一块
      const quotes = [b]
      while (i + 1 < blocks.length && blocks[i + 1].trim().startsWith('> ')) quotes.push(blocks[++i].trim())
      out.push(
        <blockquote key={i} className="reader__quote">
          {quotes.map((q, k) => (
            <p key={k}>{q.replace(/^>\s?/gm, '')}</p>
          ))}
        </blockquote>
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

  // 失败重试：错误页点「重试」递增，驱动各加载 effect 重跑(失败请求不缓存，会真正重发)
  const [retryTick, setRetryTick] = useState(0)

  // 解析 bookId：优先 router state，否则按 chapterId 探测
  useEffect(() => {
    if (stateBookId) { setBookId(stateBookId); return }
    resolveBookId(chapterId).then(setBookId).catch((e) => setErr(errText(e)))
  }, [chapterId, stateBookId, retryTick])

  const [fontSize, setFontSize] = useState(() => Number(localStorage.getItem('cc-fontsize')) || 18)
  const [vertical, setVertical] = useState(() => localStorage.getItem('cc-vertical') === '1')
  const [tocOpen, setTocOpen] = useState(false)
  const [progress, setProgress] = useState(0)

  // effect 一律用块体：箭头隐式返回会把 API 返回值当成清理函数，
  // 遇到被扩展/polyfill 覆写过的宿主 API(返回非 undefined) 即 "x is not a function"
  useEffect(() => {
    localStorage.setItem('cc-fontsize', String(fontSize))
  }, [fontSize])
  useEffect(() => {
    localStorage.setItem('cc-vertical', vertical ? '1' : '0')
  }, [vertical])

  // 载入书目录树
  useEffect(() => {
    if (!bookId) return
    setErr(undefined)
    getBook(bookId).then(setBook).catch((e) => setErr(errText(e)))
  }, [bookId, retryTick])

  const flat = useMemo(() => (book ? flattenBook(book.nodes) : []), [book])
  const index = flat.findIndex((c) => c.id === chapterId)
  const chapter: BookText | undefined = index >= 0 ? flat[index] : undefined
  const prev = index > 0 ? flat[index - 1] : undefined
  const next = index >= 0 && index < flat.length - 1 ? flat[index + 1] : undefined

  // 载入当前篇正文；过期守卫防止快速翻页时旧响应覆盖新内容
  useEffect(() => {
    setText(null)
    if (!chapter) return
    let stale = false
    getChapterText(chapter.src)
      .then((t) => { if (!stale) setText(t) })
      .catch((e) => { if (!stale) setErr(errText(e)) })
    return () => { stale = true }
  }, [chapter?.src, retryTick])

  // 顺序阅读预取下一篇，翻页即现；失败静默，届时正式请求会重试
  useEffect(() => {
    if (text != null && next) getChapterText(next.src).catch(() => {})
  }, [text, next?.src])

  const verse = useMemo(() => (text != null ? isVerse(text) : false), [text])

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

  useEffect(() => { window.scrollTo(0, 0) }, [chapterId])

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
        <p className="empty">
          {err}，
          <button
            className="reader__retry"
            onClick={() => {
              setErr(undefined)
              setRetryTick((t) => t + 1)
            }}
          >
            重试
          </button>
          {' '}或 <Link to="/" className="accent">返回首页</Link>。
        </p>
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
            <div
              className={`reader__flow${verse ? ' reader__flow--verse' : ''}`}
              style={{ fontSize: `${fontSize / 15}rem` }}
            >
              {text == null ? (
                <p className="reader__text">载入中…</p>
              ) : text.trim() === '' ? (
                <p className="empty">本篇暂无正文。</p>
              ) : verse ? (
                // 诗词整块居中：外层居中，内层按最宽行收缩、行间左对齐
                <div className="reader__verse">{renderText(text)}</div>
              ) : (
                renderText(text)
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
