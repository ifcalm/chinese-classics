// 占位书目数据。结构贴近未来真实数据，后续接入 R2 时替换来源即可。
// 正文取自公有领域古籍节选，仅用于撑起 UI。

export interface Chapter {
  id: string
  title: string
  text: string
  note?: string
}

export interface Book {
  id: string
  title: string
  author: string
  dynasty: string
  categoryId: string
  intro: string
  chapters: Chapter[]
}

export const books: Book[] = [
  {
    id: 'daodejing',
    title: '道德经',
    author: '老子',
    dynasty: '春秋',
    categoryId: 'dao',
    intro: '道家根本经典，分道、德两篇，凡八十一章，五千余言。',
    chapters: [
      {
        id: '1',
        title: '第一章',
        text:
          '道可道，非常道；名可名，非常名。无名天地之始，有名万物之母。故常无欲，以观其妙；常有欲，以观其徼。此两者，同出而异名，同谓之玄。玄之又玄，众妙之门。',
        note: '可以言说的道，便非恒常之道；可以命名的名，便非恒常之名。',
      },
      {
        id: '2',
        title: '第二章',
        text:
          '天下皆知美之为美，斯恶已；皆知善之为善，斯不善已。故有无相生，难易相成，长短相形，高下相倾，音声相和，前后相随。是以圣人处无为之事，行不言之教。',
        note: '美丑善恶相互依存，圣人因任自然，行不言之教。',
      },
      {
        id: '8',
        title: '第八章',
        text:
          '上善若水。水善利万物而不争，处众人之所恶，故几于道。居善地，心善渊，与善仁，言善信，正善治，事善能，动善时。夫唯不争，故无尤。',
        note: '至善之人如水，利万物而不争，故近于道。',
      },
    ],
  },
  {
    id: 'zhuangzi',
    title: '庄子',
    author: '庄周',
    dynasty: '战国',
    categoryId: 'dao',
    intro: '又称《南华经》，分内、外、杂篇，汪洋恣肆，寓言为体。',
    chapters: [
      {
        id: '1',
        title: '逍遥游',
        text:
          '北冥有鱼，其名为鲲。鲲之大，不知其几千里也。化而为鸟，其名为鹏。鹏之背，不知其几千里也；怒而飞，其翼若垂天之云。',
        note: '以鲲鹏之大起兴，喻精神之逍遥无待。',
      },
    ],
  },
  {
    id: 'liezi',
    title: '列子',
    author: '列御寇',
    dynasty: '战国',
    categoryId: 'dao',
    intro: '又称《冲虚经》，多寓言故事，愚公移山、杞人忧天皆出于此。',
    chapters: [
      {
        id: '1',
        title: '天瑞',
        text:
          '子列子居郑圃，四十年人无识者。国不足，将嫁于卫。弟子曰：先生往无反期，弟子敢有所谒。',
      },
    ],
  },
  {
    id: 'lunyu',
    title: '论语',
    author: '孔子弟子',
    dynasty: '春秋',
    categoryId: 'jing',
    intro: '记孔子及其弟子言行，儒家核心经典，凡二十篇。',
    chapters: [
      {
        id: '1',
        title: '学而第一',
        text:
          '子曰：学而时习之，不亦说乎？有朋自远方来，不亦乐乎？人不知而不愠，不亦君子乎？',
        note: '开篇言为学、交友、修养三事，皆君子日用之常。',
      },
      {
        id: '2',
        title: '为政第二',
        text:
          '子曰：为政以德，譬如北辰，居其所而众星共之。子曰：吾十有五而志于学，三十而立，四十而不惑，五十而知天命。',
        note: '以德为政，如北辰居所而群星环拱。',
      },
    ],
  },
  {
    id: 'zhouyi',
    title: '周易',
    author: '佚名',
    dynasty: '先秦',
    categoryId: 'jing',
    intro: '群经之首，六十四卦，言变化之道。',
    chapters: [
      {
        id: '1',
        title: '乾卦',
        text: '乾：元，亨，利，贞。初九：潜龙勿用。九二：见龙在田，利见大人。',
      },
    ],
  },
  {
    id: 'shijing',
    title: '诗经',
    author: '佚名',
    dynasty: '先秦',
    categoryId: 'jing',
    intro: '中国最早的诗歌总集，分风、雅、颂，凡三百零五篇。',
    chapters: [
      {
        id: '1',
        title: '关雎',
        text: '关关雎鸠，在河之洲。窈窕淑女，君子好逑。参差荇菜，左右流之。窈窕淑女，寤寐求之。',
      },
    ],
  },
  {
    id: 'xinjing',
    title: '心经',
    author: '玄奘 译',
    dynasty: '唐',
    categoryId: 'fo',
    intro: '《般若波罗蜜多心经》，般若部精要，二百六十字摄大乘空义。',
    chapters: [
      {
        id: '1',
        title: '心经',
        text:
          '观自在菩萨，行深般若波罗蜜多时，照见五蕴皆空，度一切苦厄。舍利子，色不异空，空不异色，色即是空，空即是色，受想行识，亦复如是。',
        note: '五蕴本空，照见此理，即度一切苦厄。',
      },
    ],
  },
  {
    id: 'jingangjing',
    title: '金刚经',
    author: '鸠摩罗什 译',
    dynasty: '后秦',
    categoryId: 'fo',
    intro: '《金刚般若波罗蜜经》，般若部要典，言无相布施、应无所住。',
    chapters: [
      {
        id: '1',
        title: '法会因由分',
        text: '如是我闻：一时，佛在舍卫国祇树给孤独园，与大比丘众千二百五十人俱。',
      },
    ],
  },
  {
    id: 'shiji',
    title: '史记',
    author: '司马迁',
    dynasty: '西汉',
    categoryId: 'shi',
    intro: '二十四史之首，纪传体通史，上起黄帝，下迄汉武。',
    chapters: [
      {
        id: '1',
        title: '五帝本纪',
        text: '黄帝者，少典之子，姓公孙，名曰轩辕。生而神灵，弱而能言，幼而徇齐，长而敦敏，成而聪明。',
      },
    ],
  },
  {
    id: 'neijing',
    title: '黄帝内经',
    author: '佚名',
    dynasty: '先秦至汉',
    categoryId: 'yi',
    intro: '中医理论奠基之作，分《素问》《灵枢》两部。',
    chapters: [
      {
        id: '1',
        title: '上古天真论',
        text:
          '昔在黄帝，生而神灵，弱而能言。乃问于天师曰：余闻上古之人，春秋皆度百岁，而动作不衰；今时之人，年半百而动作皆衰者，时世异耶？',
      },
    ],
  },
  {
    id: 'chuci',
    title: '楚辞',
    author: '屈原 等',
    dynasty: '战国',
    categoryId: 'ji-shen',
    intro: '楚地歌辞总集，开浪漫主义先河，《离骚》为其冠冕。',
    chapters: [
      {
        id: '1',
        title: '离骚',
        text: '帝高阳之苗裔兮，朕皇考曰伯庸。摄提贞于孟陬兮，惟庚寅吾以降。',
      },
    ],
  },
  {
    id: 'shanhaijing',
    title: '山海经',
    author: '佚名',
    dynasty: '先秦',
    categoryId: 'ji-shen',
    intro: '上古地理博物与神话总集，记山川、异兽、远国。',
    chapters: [
      {
        id: '1',
        title: '南山经',
        text: '南山经之首曰䧿山。其首曰招摇之山，临于西海之上，多桂，多金玉。',
      },
    ],
  },
]

export function getBook(id: string): Book | undefined {
  return books.find((b) => b.id === id)
}

export function getBooksByCategory(categoryId: string): Book[] {
  return books.filter((b) => b.categoryId === categoryId)
}
