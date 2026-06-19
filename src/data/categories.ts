// 真实的 7 大门类（对应 ifcalm-books 的 README 分类）。
// 数据模型后续会随收录增多而调整，这里先作为首页与书目页的来源。

export interface Category {
  id: string
  name: string
  subtitle: string
  badge?: string
  /** bento 网格占列数：2 = 大卡，1 = 小卡 */
  span: 1 | 2
}

export const categories: Category[] = [
  { id: 'fo', name: '佛学', subtitle: '经藏 · 律藏 · 论藏 · 宗派', badge: '体量最大', span: 2 },
  { id: 'jing', name: '经部', subtitle: '易 · 诗 · 书 · 礼　16 部', badge: '儒家经典', span: 2 },
  { id: 'dao', name: '道家', subtitle: '丹道 · 仙传', span: 1 },
  { id: 'shi', name: '二十四史', subtitle: '历代正史', span: 1 },
  { id: 'yi', name: '医家', subtitle: '岐黄典籍', span: 1 },
  { id: 'ji-shen', name: '集部 · 神话', subtitle: '诗文 · 志怪', span: 1 },
]

export function getCategory(id: string): Category | undefined {
  return categories.find((c) => c.id === id)
}
