import js from '@eslint/js'
import tseslint from 'typescript-eslint'
import reactHooks from 'eslint-plugin-react-hooks'

/**
 * 本项目专用规则：effect 的回调不得用箭头隐式返回。
 *
 * 缘由(2026-07-16 线上事故)：`useEffect(() => window.scrollTo(0, 0), [chapterId])`
 * 把 scrollTo 的返回值隐式 return 出去，React 拿它当清理函数(destroy)调用。原生 API 返回
 * undefined 故平时无事；一旦被扩展/polyfill 覆写成返回非 undefined，翻页即
 * "destroy is not a function"(压缩后 "l is not a function")。
 *
 * 通用规则 @typescript-eslint/no-confusing-void-expression 能抓，但会连
 * onClick={() => setX(1)} 一并报(实测 13 报仅 1 真)，信噪比不可用，故窄化到 effect。
 */
const effectNoImplicitReturn = {
  meta: {
    type: 'problem',
    docs: { description: 'effect 回调须用块体，隐式返回会被 React 当作清理函数' },
    messages: {
      implicitReturn:
        '{{hook}} 的回调不可用箭头隐式返回：返回值会被 React 当作清理函数调用。请加大括号。',
    },
    fixable: 'code',
    schema: [],
  },
  create(context) {
    return {
      CallExpression(node) {
        const name = node.callee.name ?? node.callee.property?.name
        if (name !== 'useEffect' && name !== 'useLayoutEffect' && name !== 'useInsertionEffect')
          return
        const cb = node.arguments[0]
        if (cb?.type !== 'ArrowFunctionExpression' || cb.body.type === 'BlockStatement') return
        context.report({
          node: cb.body,
          messageId: 'implicitReturn',
          data: { hook: name },
          fix: (fixer) => [fixer.insertTextBefore(cb.body, '{ '), fixer.insertTextAfter(cb.body, ' }')],
        })
      },
    }
  },
}

export default tseslint.config(
  { ignores: ['dist', 'dist-content', 'scripts', 'vite.config.js', 'vite.config.d.ts'] },
  js.configs.recommended,
  tseslint.configs.recommended,
  reactHooks.configs.flat.recommended,
  {
    files: ['src/**/*.{ts,tsx}'],
    plugins: { local: { rules: { 'effect-no-implicit-return': effectNoImplicitReturn } } },
    rules: {
      // 真不变量，违反即线上事故 → error
      'local/effect-no-implicit-return': 'error',
      // effect 内同步 setState 会多一轮渲染。现存 6 处均为有意(载入态清零/随 props 复位)，
      // 属性能重构而非缺陷，故降为 warn，不拦构建；日后收敛可再提 error。
      'react-hooks/set-state-in-effect': 'warn',
    },
  }
)
