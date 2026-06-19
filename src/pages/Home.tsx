import { Link } from 'react-router-dom'
import { categories } from '../data/categories'

export default function Home() {
  return (
    <main className="page">
      <section className="hero">
        <h1 className="hero__title">
          读经典，<span className="accent">不必正襟危坐。</span>
        </h1>
        <p className="hero__sub">257 部典籍 · 6437 篇 · 全文可搜</p>
      </section>

      <section className="bento" aria-label="门类导航">
        {categories.map((c) => (
          <Link
            key={c.id}
            to={`/category/${c.id}`}
            className={`cat-card cat-card--span${c.span}`}
          >
            {c.badge && <span className="cat-card__badge">{c.badge}</span>}
            <span className="cat-card__bottom">
              <span className="cat-card__name">{c.name}</span>
              <span className="cat-card__sub">{c.subtitle}</span>
            </span>
          </Link>
        ))}
      </section>
    </main>
  )
}
