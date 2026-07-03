import type { IndexedBook } from './useBookSearch'

/** 检索结果列表，头部下拉与阅读页浮层共用。 */
export default function SearchHits({
  hits,
  activeIndex = -1,
  onPick,
}: {
  hits: IndexedBook[]
  activeIndex?: number
  onPick: (b: IndexedBook) => void
}) {
  return (
    <ul className="search-box__list">
      {hits.map((b, i) => (
        <li key={b.id}>
          <button
            className={`search-hit ${i === activeIndex ? 'is-active' : ''}`}
            onClick={() => onPick(b)}
          >
            <span className="search-hit__title">{b.title}</span>
            <span className="search-hit__snippet">
              {b.categoryName} · {b.chapterCount} 篇
              {b.summary ? ` · ${b.summary.slice(0, 24)}` : ''}
            </span>
          </button>
        </li>
      ))}
    </ul>
  )
}
