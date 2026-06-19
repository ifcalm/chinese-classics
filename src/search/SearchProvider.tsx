import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import SearchOverlay from './SearchOverlay'

interface SearchContextValue {
  open: () => void
  close: () => void
}

const SearchContext = createContext<SearchContextValue | null>(null)

export function SearchProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false)

  const open = () => setIsOpen(true)
  const close = () => setIsOpen(false)

  // 快捷键：/ 或 ⌘K 打开，Esc 关闭
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsOpen(false)
      const typing = ['INPUT', 'TEXTAREA'].includes(
        (e.target as HTMLElement)?.tagName ?? ''
      )
      if (!typing && (e.key === '/' || (e.key === 'k' && (e.metaKey || e.ctrlKey)))) {
        e.preventDefault()
        setIsOpen(true)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  return (
    <SearchContext.Provider value={{ open, close }}>
      {children}
      {isOpen && <SearchOverlay onClose={close} />}
    </SearchContext.Provider>
  )
}

export function useSearch() {
  const ctx = useContext(SearchContext)
  if (!ctx) throw new Error('useSearch must be used within SearchProvider')
  return ctx
}
