import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getManifest } from '../data/content'
import type { CategoryMeta } from '../data/types'

export default function Home() {
  const [cats, setCats] = useState<CategoryMeta[] | null>(null)
  const [err, setErr] = useState<string>()

  useEffect(() => {
    getManifest()
      .then((m) => setCats(m.categories))
      .catch((e) => setErr(String(e)))
  }, [])

  const total = cats?.reduce((s, c) => s + c.bookCount, 0) ?? 0

  return (
    <main className="page">
      <section className="hero">
        <h1 className="hero__title">
          读经典，<span className="accent">不必正襟危坐。</span>
        </h1>
        <p className="hero__sub">
          {cats ? `${cats.length} 门类 · ${total} 部典籍 · 全文可搜` : '载入中…'}
        </p>
      </section>

      {err && <p className="empty">内容加载失败：{err}</p>}

      <section className="bento" aria-label="门类导航">
        {(cats ?? []).map((c, i) => (
          <Link
            key={c.id}
            to={`/category/${c.id}`}
            className={`cat-card cat-card--span${i < 2 ? 2 : 1}`}
          >
            {c.badge && <span className="cat-card__badge">{c.badge}</span>}
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
