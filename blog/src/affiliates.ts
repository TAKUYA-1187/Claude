// アフィリエイト案件の一覧。記事では [表示テキスト](aff:ID) と書く。
//
// - url が空のあいだはリンクにならず、表示テキストだけが出る（提携前でも記事を書いておける）
// - ASP で提携が承認されたら、管理画面の「広告リンク」「テキストリンク」の URL を url に入れる
// - A8.net のテキストリンクに付いてくる 1x1 の計測用画像は、その画像の src を pixel に入れる
// - url が入った案件を1つでも含む記事には、PR表記が自動で付く（ステマ規制対応）
// - 記事にない ID を書くとビルドが止まる（打ち間違い防止）

export interface AffiliateProgram {
  /** 管理用の名前 */
  name: string;
  /** 申請先の ASP */
  asp: 'A8.net' | 'もしもアフィリエイト' | 'その他';
  /** 承認後に貼る広告リンク URL。空なら未提携 */
  url: string;
  /** A8.net の計測用画像 URL（任意） */
  pixel?: string;
}

export const AFFILIATES: Record<string, AffiliateProgram> = {
  // 梱包資材（もしもアフィリエイト経由の Amazon / 楽天市場。実際に使っている商品のリンクを入れる）
  'pack-box': { name: '宅配用ダンボール', asp: 'もしもアフィリエイト', url: '' },
  'pack-cushion': { name: '緩衝材（エアークッション）', asp: 'もしもアフィリエイト', url: '' },
  'pack-tape': { name: '梱包用テープ', asp: 'もしもアフィリエイト', url: '' },
  'pack-scale': { name: 'デジタルスケール（重さの確認用）', asp: 'もしもアフィリエイト', url: '' },
};
