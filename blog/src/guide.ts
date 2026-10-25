// 入門ガイドの読む順番。/guide/ と各記事末の「次に読む」で使う。
// 記事を増やしたら、読む順番の位置に1行足す。
export const GUIDE: { slug: string; step: string; why: string }[] = [
  { slug: 'what-is-kaitori-sedori', step: '仕組みとリスクを知る', why: '始める前に、利益が出る理由と赤字になる原因をつかむ' },
  { slug: 'kaitori-sedori-profit-calc', step: '利益を計算する', why: '送料と価格下落まで入れて、仕入れてよいかを判断する' },
  { slug: 'kaitori-scanner-csv', step: '利益商品を探す', why: '買取価格の一覧から候補を見つけ、データの落とし穴を避ける' },
  { slug: 'kaitori-packing-shipping', step: '梱包して発送する', why: '同梱で送料を下げ、輸送中の傷による減額を防ぐ' },
  { slug: 'kaitori-price-drop', step: '減額・値下がりに備える', why: '起きたときの確認の順番と、次から防ぐ習慣を決めておく' },
];
