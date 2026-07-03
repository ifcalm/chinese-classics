import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from 'react'
import SearchOverlay from './SearchOverlay'

interface SearchContextValue {
  open: () => void
  close: () => void
  /** Header 的内联搜索框挂载时注册；快捷键优先聚焦它，卸载(阅读页)则回退浮层。 */
  registerInput: (el: HTMLInputElement | null) => void
}

const SearchContext = createContext<SearchContextValue | null>(null)

export function SearchProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false)
  const inputRef = useRef<HTMLInputElement | null>(null)

  const open = () => setIsOpen(true)
  const close = () => setIsOpen(false)
  const registerInput = (el: HTMLInputElement | null) => {
    inputRef.current = el
  }

  // 快捷键：/ 或 ⌘K 聚焦头部搜索框(无则弹浮层)，Esc 关闭浮层
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsOpen(false)
      const typing = ['INPUT', 'TEXTAREA'].includes(
        (e.target as HTMLElement)?.tagName ?? ''
      )
      if (!typing && (e.key === '/' || (e.key === 'k' && (e.metaKey || e.ctrlKey)))) {
        e.preventDefault()
        if (inputRef.current?.isConnected) {
          inputRef.current.focus()
          inputRef.current.select()
        } else {
          setIsOpen(true)
        }
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  return (
    <SearchContext.Provider value={{ open, close, registerInput }}>
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
