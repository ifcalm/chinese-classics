import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { errText, getManifest } from '../data/content'
import { getRandomQuote } from '../data/quotes'
import type { CategoryMeta, Quote } from '../data/types'
import { SITE_TITLE } from '../seo/meta'

export default function Home() {
  const [cats, setCats] = useState<CategoryMeta[] | null>(null)
  const [err, setErr] = useState<string>()
  const [quote, setQuote] = useState<Quote | null>(null)

  useEffect(() => {
    getManifest()
      .then((m) => setCats(m.categories))
      .catch((e) => setErr(errText(e)))
  }, [])

  // 名句异步淡入，不阻塞首屏；取不到就保持隐藏
  useEffect(() => {
    let alive = true
    void getRandomQuote().then((q) => {
      if (alive && q) setQuote(q)
    })
    return () => {
      alive = false
    }
  }, [])

  const nextQuote = () => {
    void getRandomQuote(quote?.id).then((q) => {
      if (q) setQuote(q)
    })
  }

  // 从内页返回首页时还原默认标题
  useEffect(() => {
    document.title = SITE_TITLE
  }, [])

  const total = cats?.reduce((s, c) => s + c.bookCount, 0) ?? 0

  return (
    <main className="page">
      <section className="hero">
        <h1 className="hero__title">
          读经典，<span className="accent">不必正襟危坐。</span>
        </h1>
        <p className="hero__sub">
          {cats ? `${cats.length} 门类 · ${total} 部典籍 · 书名可搜` : '载入中…'}
        </p>
      </section>

      {err && <p className="empty">内容加载失败：{err}</p>}

      <section className={`quote-box${quote ? ' quote-box--in' : ''}`} aria-label="典籍名句">
        {quote && (
          <blockquote className="quote-box__inner">
            <p className="quote-box__text">{quote.text}</p>
            <footer className="quote-box__meta">
              <Link className="quote-box__src" to={`/read/${quote.chapterId}`}>
                —— {quote.source}
              </Link>
              <button type="button" className="quote-box__next" onClick={nextQuote}>
                换一句
              </button>
            </footer>
          </blockquote>
        )}
      </section>

      <section className="bento" aria-label="门类导航">
        {(cats ?? []).map((c, i) => (
          <Link
            key={c.id}
            to={`/category/${c.id}`}
            className={`cat-card cat-card--span${i < 2 ? 2 : 1}`}
          >
            <span className="cat-card__badge" aria-hidden="true">
              {c.badge ?? c.name[0]}
            </span>
            <span className="cat-card__bottom">
              <span className="cat-card__name">{c.name}</span>
              <span className="cat-card__sub">{c.subtitle ?? `${c.bookCount} 部`}</span>
            </span>
          </Link>
        ))}
      </section>
    </main>
  )
}
