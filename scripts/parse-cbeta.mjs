// CBETA TEI-P5 XML → base-data markdown。已收:经藏43+论藏批ABC29+律藏批DE10+三藏收官批6=88部;密教11部已撤收待前端小字注样式,配置保留可随时重收。
// XML 来源:https://raw.githubusercontent.com/cbeta-org/xml-p5/master/T/<册>/<册n经号>.xml → 存本目录 cbeta/ 下。
// 底本:CBETA 电子佛典(大正藏本,大正藏底本高丽藏)。繁体+新式标点,与站内既有经藏一致。
// node parse-cbeta.mjs [--write] [T号过滤...]
import { readFileSync, writeFileSync, mkdirSync, rmSync } from 'node:fs'
import { join } from 'node:path'

const S = new URL('./cbeta/', import.meta.url).pathname
const BASE = '/Users/lishuaishuai/Projects/githubProjects/chinese-classics/base-data/buddha'
const WRITE = process.argv.includes('--write')
const only = process.argv.slice(2).filter((a) => /^T\d/.test(a))
const han = (s) => (s.match(/[㐀-鿿]/g) || []).length

const numToHan = (n) => {
  const d = '零一二三四五六七八九'
  if (n === 100) return '一百'
  if (n <= 10) return n === 10 ? '十' : d[n]
  if (n < 20) return '十' + d[n % 10]
  return d[Math.floor(n / 10)] + '十' + (n % 10 ? d[n % 10] : '')
}

// ── 43 部书配置:file→{简体题,slug,目标目录,weight,summary,分册?} ──
const BOOKS = [
  // 批② 本缘部(接法句经80之后,按译出年代)
  ['T04n0200', '撰集百缘经', 'zhuan-ji-bai-yuan-jing', 'jingzang/benyuan', 90, '三国吴支谦译，十卷百缘，记佛世因缘果报故事。'],
  ['T03n0152', '六度集经', 'liu-du-ji-jing', 'jingzang/benyuan', 100, '三国吴康僧会译，八卷九十一章，依六度编次佛本生故事。'],
  ['T03n0154', '生经', 'sheng-jing', 'jingzang/benyuan', 110, '西晋竺法护译，五卷五十五经，佛及弟子本生因缘。'],
  ['T04n0211', '法句譬喻经', 'fa-ju-pi-yu-jing', 'jingzang/benyuan', 120, '西晋法炬、法立共译，四卷，法句偈颂配缘起譬喻。'],
  ['T04n0212', '出曜经', 'chu-yao-jing', 'jingzang/benyuan', 130, '姚秦竺佛念译，三十卷，法句偈颂广释，缘喻宏富。'],
  ['T04n0192', '佛所行赞', 'fo-suo-xing-zan', 'jingzang/benyuan', 140, '马鸣菩萨造，北凉昙无谶译，五卷二十八品，五言偈颂佛传长诗。'],
  ['T03n0157', '悲华经', 'bei-hua-jing', 'jingzang/benyuan', 150, '北凉昙无谶译，十卷，说释迦牟尼秽土成佛之大悲本愿。'],
  ['T04n0202', '贤愚经', 'xian-yu-jing', 'jingzang/benyuan', 160, '元魏慧觉等在高昌译，十三卷六十九品，因缘故事集。'],
  ['T04n0203', '杂宝藏经', 'za-bao-zang-jing', 'jingzang/benyuan', 170, '元魏吉迦夜共昙曜译，十卷百二十一章，因缘譬喻故事集。'],
  ['T03n0190', '佛本行集经', 'fo-ben-xing-ji-jing', 'jingzang/benyuan', 180, '隋闍那崛多译，六十卷六十品，集诸部佛传之大成。'],
  // 批③ 般若部译系(大般若10之后、金刚经20之前;能断金刚21)
  ['T08n0224', '道行般若经', 'dao-xing-bo-re-jing', 'jingzang/bore', 11, '后汉支娄迦谶译于洛阳（179年），十卷三十品，现存最早汉译般若经。'],
  ['T08n0225', '大明度经', 'da-ming-du-jing', 'jingzang/bore', 12, '三国吴支谦译，六卷三十品，道行般若之异译，文辞简约。'],
  ['T08n0222', '光赞经', 'guang-zan-jing', 'jingzang/bore', 13, '西晋竺法护译（286年），十卷二十七品，大品般若之初译。'],
  ['T08n0221', '放光般若经', 'fang-guang-bo-re-jing', 'jingzang/bore', 14, '西晋无罗叉共竺叔兰译（291年），二十卷九十品，两晋般若学所宗。'],
  ['T08n0232', '文殊师利所说摩诃般若波罗蜜经', 'wen-shu-bo-re-jing', 'jingzang/bore', 15, '梁曼陀罗仙译，二卷，文殊般若，一行三昧出此。'],
  ['T08n0231', '胜天王般若波罗蜜经', 'sheng-tian-wang-bo-re-jing', 'jingzang/bore', 16, '陈月婆首那译，七卷十六品。'],
  ['T08n0239', '佛说能断金刚般若波罗蜜多经', 'fo-shuo-neng-duan-jin-gang-jing', 'jingzang/bore', 21, '唐义净译（703年），一卷，金刚经最后一译。'],
  // 批④ 经集部要典(仁王经系110之后)
  ['T15n0642', '佛说首楞严三昧经', 'fo-shuo-shou-leng-yan-san-mei-jing', 'jingzang/jingji', 120, '姚秦鸠摩罗什译，二卷，说首楞严三昧健行不坏之力。'],
  ['T15n0586', '思益梵天所问经', 'si-yi-fan-tian-suo-wen-jing', 'jingzang/jingji', 130, '姚秦鸠摩罗什译，四卷十八品，网明菩萨与思益梵天问答实相。'],
  ['T15n0639', '月灯三昧经', 'yue-deng-san-mei-jing', 'jingzang/jingji', 140, '高齐那连提耶舍译，十卷，即三昧王经，禅门多所援引。'],
  ['T15n0643', '佛说观佛三昧海经', 'fo-shuo-guan-fo-san-mei-hai-jing', 'jingzang/jingji', 150, '东晋佛陀跋陀罗译，十卷十二品，说观佛相好之法。'],
  ['T16n0666', '大方等如来藏经', 'da-fang-deng-ru-lai-zang-jing', 'jingzang/jingji', 160, '东晋佛陀跋陀罗译，一卷，九喻显众生皆具如来藏。'],
  ['T16n0668', '佛说不增不减经', 'fo-shuo-bu-zeng-bu-jian-jing', 'jingzang/jingji', 170, '元魏菩提流支译，一卷，说众生界不增不减，如来藏系要典。'],
  ['T16n0681', '大乘密严经', 'da-cheng-mi-yan-jing', 'jingzang/jingji', 180, '唐地婆诃罗译，三卷八品，会如来藏与阿赖耶识。'],
  ['T15n0650', '诸法无行经', 'zhu-fa-wu-xing-jing', 'jingzang/jingji', 190, '姚秦鸠摩罗什译，二卷，说诸法性空、贪恚痴即道。'],
  ['T14n0482', '持世经', 'chi-shi-jing', 'jingzang/jingji', 200, '姚秦鸠摩罗什译，四卷，说菩萨观五阴十八性因缘之法。'],
  ['T15n0653', '佛藏经', 'fo-zang-jing', 'jingzang/jingji', 210, '姚秦鸠摩罗什译，三卷十品，说诸法无相、破戒不受供之诫。'],
  ['T17n0721', '正法念处经', 'zheng-fa-nian-chu-jing', 'jingzang/jingji', 220, '元魏瞿昙般若流支译，七十卷，广明六道业果，义净推为修行者要典。'],
  // 批④ 禅经组(jingji/chanjing 子目录, dir weight 230)
  ['T15n0606', '修行道地经', 'xiu-xing-dao-di-jing', 'jingzang/jingji/chanjing', 10, '西晋竺法护译，七卷三十品，众护菩萨造，汉传禅观早期要籍。'],
  ['T15n0614', '坐禅三昧经', 'zuo-chan-san-mei-jing', 'jingzang/jingji/chanjing', 20, '姚秦鸠摩罗什译，二卷，五门禅法，江东禅业之始。'],
  ['T15n0613', '禅秘要法经', 'chan-mi-yao-fa-jing', 'jingzang/jingji/chanjing', 30, '姚秦鸠摩罗什译，三卷，说白骨观等三十观法。'],
  ['T15n0616', '禅法要解', 'chan-fa-yao-jie', 'jingzang/jingji/chanjing', 40, '姚秦鸠摩罗什译，二卷，释四禅四无量四无色定之修法。'],
  ['T15n0618', '达摩多罗禅经', 'da-mo-duo-luo-chan-jing', 'jingzang/jingji/chanjing', 50, '东晋佛陀跋陀罗译于庐山，二卷十七品，说安般不净诸观。'],
  // 批⑤ 查漏
  ['T02n0100', '别译杂阿含经', 'bie-yi-za-ahan-jing', 'jingzang/ahan', 35, '失译（约三秦时期），十六卷三百六十四经，杂阿含之别行古译。'],
  ['T01n0024', '起世经', 'qi-shi-jing', 'jingzang/ahan', 50, '隋闍那崛多等译，十卷十二品，说世界成坏、诸趣居处。'],
  ['T12n0387', '大方等无想经', 'da-fang-deng-wu-xiang-jing', 'jingzang/niepan', 90, '北凉昙无谶译，六卷，即大云经，说佛性常住、大云密藏。'],
  ['T12n0390', '佛临涅槃记法住经', 'fo-lin-nie-pan-ji-fa-zhu-jing', 'jingzang/niepan', 100, '唐玄奘译（652年），一卷，记正法住灭一千年之相。'],
  ['T12n0396', '佛说法灭尽经', 'fo-shuo-fa-mie-jin-jing', 'jingzang/niepan', 110, '刘宋时失译，一卷，说法欲灭时诸恶乱象与月光出世。'],
  ['T13n0423', '僧伽吒经', 'seng-qie-zha-jing', 'jingzang/daji/danxing', 70, '元魏月婆首那译，四卷，说僧伽吒法门闻者灭罪之力。'],
  ['T09n0273', '金刚三昧经', 'jin-gang-san-mei-jing', 'jingzang/fahua', 60, '失译（北凉录），说一味实际无相观法，元晓《金刚三昧经论》所疏。'],
  ['T09n0270', '大法鼓经', 'da-fa-gu-jing', 'jingzang/fahua', 70, '刘宋求那跋陀罗译，二卷，说一乘常住、如来藏义。'],
  ['T12n0323', '郁迦罗越问菩萨行经', 'yu-jia-luo-yue-wen-pu-sa-xing-jing', 'jingzang/baoji/yiyi', 100, '西晋竺法护译，一卷，说在家出家菩萨戒行，大宝积经郁伽长者会之异译。'],
  ['T12n0371', '观世音菩萨授记经', 'guan-shi-yin-pu-sa-shou-ji-jing', 'jingzang/baoji/yiyi', 110, '刘宋昙无竭译，一卷，记观世音、得大势二菩萨往因与授记。'],
  // 批① 密教部(按大正藏经号序;楞严经既有,weight 改 60)
  ['T18n0848', '大毗卢遮那成佛神变加持经', 'da-pi-lu-zhe-na-cheng-fo-shen-bian-jia-chi-jing', 'jingzang/mijiao', 10, '唐善无畏共一行译，七卷三十六品，即《大日经》，胎藏界根本经典。'],
  ['T18n0865', '金刚顶一切如来真实摄大乘现证大教王经', 'jin-gang-ding-da-jiao-wang-jing', 'jingzang/mijiao', 20, '唐不空译，三卷，即《金刚顶经》，金刚界根本经典。'],
  ['T18n0893a', '苏悉地羯罗经', 'su-xi-di-jie-luo-jing', 'jingzang/mijiao', 30, '唐输波迦罗（善无畏）译，三卷，说三部悉地成就法，与大日、金刚顶并称密教三大部。'],
  ['T18n0895a', '苏婆呼童子请问经', 'su-po-hu-tong-zi-qing-wen-jing', 'jingzang/mijiao', 40, '唐输波迦罗（善无畏）译，三卷，说持诵者律仪轨范，密教受持之律。'],
  ['T18n0897', '蕤呬耶经', 'rui-xi-ye-jing', 'jingzang/mijiao', 50, '唐不空译，三卷，说择地造坛、供养奉请之通则。'],
  ['T19n0967', '佛顶尊胜陀罗尼经', 'fo-ding-zun-sheng-tuo-luo-ni-jing', 'jingzang/mijiao', 70, '唐佛陀波利译（683年），一卷，说尊胜陀罗尼灭罪延寿之力，经幢刻此殆遍天下。'],
  ['T19n0982', '佛母大孔雀明王经', 'fo-mu-da-kong-que-ming-wang-jing', 'jingzang/mijiao', 80, '唐不空译，三卷，说孔雀明王真言除灾祛毒护国之法。'],
  ['T19n1022A', '一切如来心秘密全身舍利宝箧印陀罗尼经', 'bao-qie-yin-tuo-luo-ni-jing', 'jingzang/mijiao', 90, '唐不空译，一卷，说宝箧印陀罗尼，塔藏经咒之制多出于此。'],
  ['T20n1050', '佛说大乘庄严宝王经', 'fo-shuo-da-cheng-zhuang-yan-bao-wang-jing', 'jingzang/mijiao', 100, '宋天息灾译，四卷，说观自在菩萨功德与六字大明陀罗尼（唵嘛呢叭咪吽）之所出。'],
  ['T20n1060', '千手千眼观世音菩萨广大圆满无碍大悲心陀罗尼经', 'da-bei-xin-tuo-luo-ni-jing', 'jingzang/mijiao', 110, '唐伽梵达摩译，一卷，说千手观音大悲心陀罗尼（大悲咒）及其十大愿力。'],
  ['T20n1076', '七俱胝佛母所说准提陀罗尼经', 'zhun-ti-tuo-luo-ni-jing', 'jingzang/mijiao', 120, '唐不空译，一卷，说准提陀罗尼持诵仪则。'],
  // 论藏批A 唯识中观名论(瑜伽唯识部接摄论释70之后;中观部插百论/肇论间;因明二论入论集部)
  ['T31n1602', '显扬圣教论', 'xian-yang-sheng-jiao-lun', 'lunzang/yujia', 80, '无著造，唐玄奘译，二十卷十一品，撮举瑜伽师地论要义以显扬圣教。'],
  ['T31n1604', '大乘庄严经论', 'da-cheng-zhuang-yan-jing-lun', 'lunzang/yujia', 90, '无著造（本颂传为弥勒），唐波罗颇蜜多罗译（630年），十三卷二十四品，庄严大乘经义之瑜伽要典。'],
  ['T31n1605', '大乘阿毘达磨集论', 'da-cheng-a-pi-da-mo-ji-lun', 'lunzang/yujia', 100, '无著造，唐玄奘译，七卷，集大乘对法要义，法相学纲要。'],
  ['T31n1600', '辩中边论', 'bian-zhong-bian-lun', 'lunzang/yujia', 110, '弥勒颂、世亲释，唐玄奘译，三卷七品，辨中道远离二边之义。'],
  ['T31n1612', '大乘五蕴论', 'da-cheng-wu-yun-lun', 'lunzang/yujia', 120, '世亲造，唐玄奘译，一卷，依五蕴门略摄法相，唯识入门小论。'],
  ['T31n1624', '观所缘缘论', 'guan-suo-yuan-yuan-lun', 'lunzang/yujia', 130, '陈那造，唐玄奘译，一卷，论所缘缘义，唯识与因明合流之作。'],
  ['T32n1631', '回诤论', 'hui-zheng-lun', 'lunzang/zhongguan', 25, '龙树造，后魏毘目智仙共瞿昙流支译，一卷，答实有论者之难，申一切法无自性义。'],
  ['T30n1578', '大乘掌珍论', 'da-cheng-zhang-zhen-lun', 'lunzang/zhongguan', 35, '清辨造，唐玄奘译，二卷，立「真性有为空」比量成中观义。'],
  ['T32n1628', '因明正理门论本', 'yin-ming-zheng-li-men-lun-ben', 'lunzang/lunji', 20, '陈那造，唐玄奘译，一卷，新因明体系奠基之作。'],
  ['T32n1630', '因明入正理论', 'yin-ming-ru-zheng-li-lun', 'lunzang/lunji', 30, '商羯罗主造，唐玄奘译，一卷，因明纲要之作，汉传因明学根本教本。'],
  // 论藏批B 毘昙与部派(毘昙部接俱舍论10之后;异部宗轮入毘昙部;解脱道论入论集部)
  ['T26n1544', '阿毘达磨发智论', 'a-pi-da-mo-fa-zhi-lun', 'lunzang/pitan', 20, '迦多衍尼子造，唐玄奘译，二十卷八蕴，说一切有部根本论，与六足论并称「一身六足」。'],
  ['T26n1536', '阿毘达磨集异门足论', 'a-pi-da-mo-ji-yi-men-zu-lun', 'lunzang/pitan', 30, '舍利子说，唐玄奘译，二十卷，依增一法门集释法数，六足论之一。'],
  ['T26n1537', '阿毘达磨法蕴足论', 'a-pi-da-mo-fa-yun-zu-lun', 'lunzang/pitan', 40, '大目乾连造，唐玄奘译，十二卷二十一品，六足论之一，有部教义早期结集。'],
  ['T26n1542', '阿毘达磨品类足论', 'a-pi-da-mo-pin-lei-zu-lun', 'lunzang/pitan', 50, '世友造，唐玄奘译，十八卷八品，五法分别之纲领，六足论之一。'],
  ['T28n1550', '阿毘昙心论', 'a-pi-tan-xin-lun', 'lunzang/pitan', 60, '法胜造，东晋僧伽提婆共慧远译于庐山，四卷，偈颂摄毘昙要义，毘昙学入门。'],
  ['T28n1552', '杂阿毘昙心论', 'za-a-pi-tan-xin-lun', 'lunzang/pitan', 70, '法救造，刘宋僧伽跋摩译，十一卷，广释阿毘昙心论，南朝毘昙师所宗。'],
  ['T28n1554', '入阿毘达磨论', 'ru-a-pi-da-mo-lun', 'lunzang/pitan', 80, '塞建陀罗造，唐玄奘译，二卷，有部义学入门纲要。'],
  ['T49n2031', '异部宗轮论', 'yi-bu-zong-lun-lun', 'lunzang/pitan', 90, '世友造，唐玄奘译，一卷，记佛灭后部派分裂谱系与各部宗义，部派佛教史纲要。'],
  ['T32n1648', '解脱道论', 'jie-tuo-dao-lun', 'lunzang/lunji', 40, '优波底沙造，梁僧伽婆罗译，十二卷十二品，戒定慧三学次第，南传《清净道论》之先声，上座部系统唯一古汉译道论。'],
  // 论藏批C 修学行门论(论集部续 40 之后按译出年代;法华/遗教二论入释经论部;法界无差别入如来藏部)
  ['T32n1670B', '那先比丘经', 'na-xian-bi-qiu-jing', 'lunzang/lunji', 50, '失译（东晋录），三卷，那先与弥兰王问答佛法大义，即巴利《弥兰陀王问经》之古汉译。'],
  ['T32n1659', '发菩提心经论', 'fa-pu-ti-xin-jing-lun', 'lunzang/lunji', 60, '世亲造，姚秦鸠摩罗什译，二卷十二品，劝发菩提心、明六度四摄之行。'],
  ['T30n1577', '大丈夫论', 'da-zhang-fu-lun', 'lunzang/lunji', 70, '提婆罗造，北凉道泰译，二卷二十九品，广赞悲心布施之行。'],
  ['T32n1634', '入大乘论', 'ru-da-cheng-lun', 'lunzang/lunji', 80, '坚意造，北凉道泰译，二卷，劝入大乘，通释疑难。'],
  ['T32n1656', '宝行王正论', 'bao-xing-wang-zheng-lun', 'lunzang/lunji', 90, '龙树造，陈真谛译，一卷五品，为王说正法宝行，即《宝鬘论》古汉译。'],
  ['T32n1660', '菩提资粮论', 'pu-ti-zi-liang-lun', 'lunzang/lunji', 100, '龙树本颂、自在比丘释，隋达磨笈多译，六卷，集福智二种菩提资粮。'],
  ['T32n1662', '菩提行经', 'pu-ti-xing-jing', 'lunzang/lunji', 110, '寂天造，宋天息灾译，四卷八品，即《入菩萨行论》唯一古汉译，大乘行门诗颂名著。'],
  ['T26n1519', '妙法莲华经忧波提舍', 'miao-fa-lian-hua-jing-you-bo-ti-she', 'lunzang/shijing', 23, '世亲造，后魏菩提流支共昙林等译，二卷，即《法华经论》，天台判教多所依据。'],
  ['T26n1529', '遗教经论', 'yi-jiao-jing-lun', 'lunzang/shijing', 24, '世亲造，陈真谛译，一卷，释《佛遗教经》修心离过之义。'],
  ['T31n1626', '大乘法界无差别论', 'da-cheng-fa-jie-wu-cha-bie-lun', 'lunzang/rulaizang', 3, '坚慧造，唐提云般若译，一卷，明菩提心与法界如来藏无差别义。'],
  // 律藏批D 大乘律与戒本(四分律10/梵网经20 既有;10-16 留给广律,18 声闻戒本,20-28 大乘律)
  ['T22n1430', '四分僧戒本', 'si-fen-seng-jie-ben', 'luzang', 18, '后秦佛陀耶舍译，一卷，四分律比丘戒条之布萨诵本。'],
  ['T24n1485', '菩萨璎珞本业经', 'pu-sa-ying-luo-ben-ye-jing', 'luzang', 22, '姚秦竺佛念译，二卷八品，说菩萨四十二贤圣阶位与三聚净戒，汉传菩萨戒所依。'],
  ['T24n1500', '菩萨戒本', 'pu-sa-jie-ben', 'luzang', 24, '出《菩萨地持经》，北凉昙无谶译，一卷，四重四十三轻，汉地菩萨戒本之祖。'],
  ['T24n1488', '优婆塞戒经', 'you-po-sai-jie-jing', 'luzang', 26, '北凉昙无谶译，七卷二十八品，为善生长者说在家菩萨戒行，在家佛教第一要典。'],
  ['T24n1476', '佛说优婆塞五戒相经', 'you-po-sai-wu-jie-xiang-jing', 'luzang', 28, '刘宋求那跋摩译，一卷，分别在家五戒犯相轻重之律。'],
  // 律藏批E 广律(按译出年代插四分律10前后)+律学
  ['T23n1435', '十诵律', 'shi-song-lv', 'luzang', 8, '后秦弗若多罗共鸠摩罗什译（404年起），六十一卷，萨婆多部广律，汉译诸律之最早出。'],
  ['T22n1425', '摩诃僧祇律', 'mo-he-seng-qi-lv', 'luzang', 12, '东晋佛陀跋陀罗共法显译（416年），四十卷，大众部广律，法显自天竺赍归。'],
  ['T22n1421', '弥沙塞部和醯五分律', 'wu-fen-lv', 'luzang', 14, '刘宋佛陀什共竺道生等译（423年），三十卷，化地部广律。'],
  ['T24n1463', '毘尼母经', 'pi-ni-mu-jing', 'luzang', 40, '失译（秦录），八卷，释律藏犍度诸义之母论。'],
  ['T23n1440', '萨婆多毘尼毘婆沙', 'sa-po-duo-pi-ni-pi-po-sha', 'luzang', 42, '失译（秦录），九卷，释十诵律之义疏，律学要籍。'],
  // 三藏收官批(佛地经论入释经论部;鼻奈耶 w6 居广律之首;善见律入律学区;三足论补齐六足)
  ['T26n1530', '佛地经论', 'fo-di-jing-lun', 'lunzang/shijing', 25, '亲光等造，唐玄奘译（649年），七卷，释《佛地经》五种法相，法相宗所依要论。'],
  ['T24n1464', '鼻奈耶', 'bi-nai-ye', 'luzang', 6, '前秦竺佛念译（384年），十卷，现存最早之汉译广律。'],
  ['T24n1462', '善见律毘婆沙', 'shan-jian-lv-pi-po-sha', 'luzang', 44, '萧齐僧伽跋陀罗译（489年），十八卷，南传《一切善见律注》之古汉译，记三次结集与阿育王传法事。'],
  ['T26n1538', '施设论', 'shi-she-lun', 'lunzang/pitan', 42, '宋法护等译，七卷，六足论之一《施设足论》之因施设门汉译。'],
  ['T26n1539', '阿毘达磨识身足论', 'a-pi-da-mo-shi-shen-zu-lun', 'lunzang/pitan', 44, '提婆设摩造，唐玄奘译，十六卷，六足论之一，辨识身诸门。'],
  ['T26n1540', '阿毘达磨界身足论', 'a-pi-da-mo-jie-shen-zu-lun', 'lunzang/pitan', 46, '世友造，唐玄奘译，三卷，六足论之一，明心所诸界相摄。'],
]

// ── 缺字表:charDecl → {id映射, PUA码位反查} ──
const isPua = (u) => (u >= 0xe000 && u <= 0xf8ff) || (u >= 0xf0000 && u <= 0x10fffd)
function gaijiMap(xml) {
  const m = {}, rev = {}
  const cd = xml.match(/<charDecl>[\s\S]*?<\/charDecl>/)
  if (!cd) return { m, rev }
  for (const c of cd[0].matchAll(/<char xml:id="([^"]+)">([\s\S]*?)<\/char>/g)) {
    const id = c[1], body = c[2]
    const uni = [...body.matchAll(/<mapping[^>]*type="unicode"[^>]*>U\+([0-9A-Fa-f]+)<\/mapping>/g)].map((x) => parseInt(x[1], 16))
    const norm = body.match(/<mapping[^>]*type="normal_unicode"[^>]*>U\+([0-9A-Fa-f]+)<\/mapping>/)
    const roman = body.match(/<localName>Romanized form in CBETA transcription<\/localName>\s*<value>([^<]*)<\/value>/)
    const comp = body.match(/<value>([^<]*)<\/value>/)
    const normChar = body.match(/<charProp>\s*<localName>normalized form<\/localName>\s*<value>([^<]*)<\/value>/)
    // 优先:非 PUA unicode > normal_unicode > 罗马转写(悉昙) > normalized form > 组字式
    // 悉昙/兰札(SD/RJ)专则:字体 hack 借用的 CJK 码位无意义,无转写时以「·」示位
    const real = uni.find((u) => !isPua(u))
    const sidd = /^(SD|RJ)-/.test(id)
    let v
    if (real && !sidd) v = String.fromCodePoint(real)
    else if (sidd) v = real ? String.fromCodePoint(real) : (roman ? roman[1] : '·')
    else if (norm && !isPua(parseInt(norm[1], 16))) v = String.fromCodePoint(parseInt(norm[1], 16))
    else if (roman) v = roman[1]
    else if (normChar) v = normChar[1]
    else v = comp ? comp[1] : '□'
    m[id] = v
    // 反查:CBETA 正文有时直接内嵌 PUA 码位而非 <g> 引用
    for (const p of body.matchAll(/<mapping[^>]*type="PUA"[^>]*>U\+([0-9A-Fa-f]+)<\/mapping>/g)) rev[parseInt(p[1], 16)] = v
  }
  return { m, rev }
}
// 剥标签后兜底:反查内嵌 PUA;无从反查者以 □ 占位
function fixPua(s, rev) {
  return [...s].map((ch) => {
    const u = ch.codePointAt(0)
    return isPua(u) ? (rev[u] ?? '□') : ch
  }).join('')
}

const stripTags = (s) => s.replace(/<[^>]+>/g, '')
const decode = (s) => s.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&apos;/g, "'")

// ── 单文件解析 → {trad题, juans:[{n, blocks:[]}], warn} ──
function parseXml(file) {
  const xml = readFileSync(join(S, file + '.xml'), 'utf8')
  const { m: g, rev } = gaijiMap(xml)
  const tTitle = (xml.match(/<title[^>]*level="m"[^>]*>([^<]*)<\/title>/) || [])[1] || '?'
  let body = xml.slice(xml.indexOf('<body>'), xml.indexOf('<back>') > 0 ? xml.indexOf('<back>') : xml.indexOf('</body>'))

  // 行内层清理(顺序敏感)
  body = body
    .replace(/<anchor[^>]*\/>/g, '')
    .replace(/<pb[^>]*\/>/g, '')
    .replace(/<lb[^>]*\/>/g, '')
    .replace(/<caesura\/>/g, '')
    .replace(/<space[^>]*\/>/g, '　')
    .replace(/<g ref="#([^"]+)"\/>/g, (_, id) => g[id] ?? '□')
    .replace(/<cb:docNumber>[\s\S]*?<\/cb:docNumber>/g, '')
    .replace(/<cb:mulu[^>]*>[\s\S]*?<\/cb:mulu>/g, '')
    .replace(/<cb:mulu[^>]*\/>/g, '')
    .replace(/<figure>[\s\S]*?<\/figure>/g, '').replace(/<graphic[^>]*\/>/g, '')
    // cb:tt 汉梵对音对:取 zh 成员,弃梵文转写(密教部)
    .replace(/<cb:tt[^>]*>([\s\S]*?)<\/cb:tt>/g, (_, inner) => {
      const zh = inner.match(/<cb:t[^>]*xml:lang="zh[^"]*"[^>]*>([\s\S]*?)<\/cb:t>/)
      return zh ? zh[1] : stripTags(inner)
    })
    .replace(/<note place="inline">([\s\S]*?)<\/note>/g, (_, t) => '（' + stripTags(t) + '）')
    .replace(/<note[^>]*>[\s\S]*?<\/note>/g, '') // 其余 note 一律剥
    .replace(/<cb:juan[^>]*fun="open"[^>]*>[\s\S]*?<\/cb:juan>/g, '')
    .replace(/<cb:juan[^>]*fun="close"[^>]*>[\s\S]*?<\/cb:juan>/g, '')
    .replace(/<byline[^>]*>[\s\S]*?<\/byline>/g, '')
    .replace(/<title[^>]*>/g, '').replace(/<\/title>/g, '')

  // 按卷切分(属性顺序不定)
  body = body.replace(/<milestone\s+unit="juan"\s+n="(\d+)"\s*\/>/g, '<milestone n="$1" unit="juan"/>')
  const segs = body.split(/<milestone n="(\d+)" unit="juan"\/>/)
  // segs: [前置, n1, seg1, n2, seg2 ...]
  const juans = []
  const warn = []
  if (han(stripTags(segs[0])) > 0) warn.push(`卷前残文${han(stripTags(segs[0]))}字`)
  for (let i = 1; i < segs.length; i += 2) {
    const n = +segs[i]
    const seg = segs[i + 1]
    const blocks = []
    const re = /<head[^>]*>([\s\S]*?)<\/head>|<p[^>]*>([\s\S]*?)<\/p>|<lg[^>]*>([\s\S]*?)<\/lg>|<item[^>]*>([\s\S]*?)<\/item>/g
    let m, covered = 0
    while ((m = re.exec(seg))) {
      covered += han(stripTags(m[0]))
      if (m[1] != null) { // head → ## 品题
        const t = fixPua(decode(stripTags(m[1])), rev).replace(/\s+/g, '')
        if (t) blocks.push('## ' + t)
      } else if (m[3] != null) { // lg 偈颂:每 l 一行,硬换行
        const lines = [...m[3].matchAll(/<l[^>]*>([\s\S]*?)<\/l>/g)]
          .map((x) => fixPua(decode(stripTags(x[1])), rev).replace(/[\r\n\t]+/g, '').replace(/ {2,}/g, ' ').replace(/^[\s　]+|[\s　]+$/g, '')).filter(Boolean)
        if (lines.length) blocks.push(lines.join('  \n'))
      } else { // p / item
        const t = fixPua(decode(stripTags(m[2] ?? m[4])), rev).replace(/[\r\n]+/g, '').replace(/^\s+|\s+$/g, '')
        if (t) blocks.push(t)
      }
    }
    const total = han(stripTags(seg))
    if (total - covered > 5) warn.push(`卷${n}块外漏${total - covered}字`)
    juans.push({ n, blocks })
  }
  return { tTitle, juans, warn }
}

// ── 落盘 ──
const fmDate = '2026-07-03'
function fm(o) {
  const lines = ['---']
  for (const [k, v] of Object.entries(o)) {
    if (Array.isArray(v)) lines.push(`${k}: [${v.map((x) => JSON.stringify(x)).join(', ')}]`)
    else if (typeof v === 'number' || typeof v === 'boolean') lines.push(`${k}: ${v}`)
    else lines.push(`${k}: ${JSON.stringify(v)}`)
  }
  lines.push('---')
  return lines.join('\n') + '\n'
}
const chFm = (book, n) => fm({
  title: `${book} 卷第${numToHan(n)}`, date: fmDate, tags: [book], draft: true,
  summary: `${book}卷第${numToHan(n)}`, showToc: false, tocOpen: false, ShowShareButtons: false, weight: n,
})
const idxFm = (title, summary, weight, extra) => fm({
  title, date: fmDate, tags: [title], categories: ['佛学'], draft: true,
  summary, showToc: false, tocOpen: false, ShowShareButtons: false, weight, ...extra,
})

let grand = 0, grandJ = 0
for (const [file, title, slug, section, weight, note] of BOOKS) {
  if (only.length && !only.some((o) => file.startsWith(o))) continue
  const { tTitle, juans, warn } = parseXml(file)
  const nJ = juans.length
  const h = juans.reduce((s, j) => s + han(j.blocks.join('')), 0)
  grand += h; grandJ += nJ
  console.log(`${file} ${title}(${tTitle}) 卷:${nJ} 汉字:${h}${warn.length ? '  ⚠ ' + warn.join('; ') : ''}`)
  if (!WRITE) continue

  const dir = join(BASE, section, slug)
  const summary = `${title}${nJ > 1 ? numToHan(nJ) + '卷' : '一卷'}。${note}据 CBETA 电子佛典（大正藏本）。`
  if (nJ === 1) { // 单卷 → 单文件
    const out = join(BASE, section, slug + '.md')
    writeFileSync(out, idxFm(title, summary, weight) + '\n' + juans[0].blocks.join('\n\n') + '\n')
    continue
  }
  rmSync(dir, { recursive: true, force: true })
  mkdirSync(dir, { recursive: true })
  writeFileSync(join(dir, '_index.md'), idxFm(title, summary, weight) + `\n收录《${title}》${numToHan(nJ)}卷。\n`)
  const chunk = nJ > 30 ? 30 : 0
  for (const j of juans) {
    let d = dir
    if (chunk) {
      const lo = Math.floor((j.n - 1) / chunk) * chunk + 1
      const hi = Math.min(lo + chunk - 1, nJ)
      d = join(dir, `${String(lo).padStart(3, '0')}-${String(hi).padStart(3, '0')}`)
      mkdirSync(d, { recursive: true })
      const ci = join(d, '_index.md')
      writeFileSync(ci, fm({
        title: `${title} 卷第${numToHan(lo)}至卷第${numToHan(hi)}`, date: fmDate, tags: [title], categories: ['佛学'],
        draft: true, summary: `${title}卷第${numToHan(lo)}至卷第${numToHan(hi)}`,
        showToc: false, tocOpen: false, ShowShareButtons: false, weight: lo,
      }))
    }
    writeFileSync(join(d, `${slug}-${String(j.n).padStart(3, '0')}.md`), chFm(title, j.n) + '\n' + j.blocks.join('\n\n') + '\n')
  }
}
console.log(`合计 汉字:${grand}  卷:${grandJ}${WRITE ? '  已写入' : '  (dry-run)'}`)
