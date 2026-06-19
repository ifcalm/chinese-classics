import { useTheme } from '../theme/ThemeProvider'
import { MoonIcon, SunIcon } from './Icons'

export default function ThemeToggle() {
  const { theme, toggle } = useTheme()
  return (
    <button
      className="theme-toggle"
      onClick={toggle}
      aria-label={theme === 'light' ? '切换到暗色' : '切换到亮色'}
    >
      {theme === 'light' ? <MoonIcon size={15} /> : <SunIcon size={15} />}
    </button>
  )
}
