import { useEffect, useMemo, useState } from 'react'
import { getAllBooks } from '../data/content'
import type { BookRef } from '../data/types'

export type IndexedBook = BookRef & { categoryName: string }

// 书名级检索：汇总各门类目录(有缓存)后按书名/作者/简介包含匹配。
// 全文检索待预建索引(Pagefind / KV)后接入，见 docs/data-architecture.md。
function search(q: string, books: IndexedBook[]): IndexedBook[] {
  const query = q.trim()
  if (!query) return []
  const hits: IndexedBook[] = []
  for (const b of books) {
    const haystack = `${b.title} ${b.author ?? ''} ${b.summary ?? ''} ${b.categoryName}`
    if (haystack.includes(query)) hits.push(b)
    if (hits.length >= 30) break
  }
  return hits
}

/** 头部下拉与阅读页浮层共用的检索状态：books 为 null 表示书目仍在载入。 */
export function useBookSearch(q: string) {
  const [books, setBooks] = useState<IndexedBook[] | null>(null)

  useEffect(() => {
    getAllBooks().then(setBooks).catch(() => setBooks([]))
  }, [])

  const hits = useMemo(() => (books ? search(q, books) : []), [q, books])
  return { books, hits }
}
