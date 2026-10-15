import assets from '../public/media/hd-asset-sources.json';
export default function AssetCredits(){return <details className="lab-details credits"><summary>素材与许可</summary>
 <p>纸纹使用高清纸面实拍，营造宣纸般的底色；红印为专门生成的装饰图。封面线香由 AI 生成，上升烟雾由程序绘制。论文图表直接从 V5 矢量原图导出。</p>
 <p>书法字体：<a href="https://github.com/google/fonts/tree/main/ofl/mashanzheng">Ma Shan Zheng</a>（SIL Open Font License）。交互参考：<a href="https://amicro.vercel.app/">Amicro</a>、<a href="https://skiper-ui.com/">Skiper UI</a>；保存动效：<a href="https://dotmatrix.zzzzshawn.cloud/">Dot Matrix</a>。</p>
 <p>古籍扫描来自 CADAL／Wikimedia Commons，公有领域。馆藏香具来自大都会艺术博物馆开放获取项目（CC0）。图片保留原貌，网页仅缩放显示。</p>
 <ul className="asset-source-list">{assets.map(asset=><li key={asset.file}><a href={asset.source} target="_blank" rel="noreferrer">{({'paper-hd.jpg':'高清纸纹','benzoin-hd.jpg':'安息香 · Midori · CC BY-SA 3.0','agarwood-hd.jpg':'沉香 · Hafizmuar · CC BY-SA 3.0','chen-volume-3.jpg':'《陈氏香谱》卷三 · 陈敬','chen-volume-4.jpg':'《陈氏香谱》卷四 · 陈敬','wang-xiangpu.jpg':'《香谱》· 王黼','bronze-censer-hd.jpg':'铜香炉 · 2024.553.22','jade-censer-hd.jpg':'白玉盖炉 · 02.18.537a, b','jade-stand-hd.jpg':'玉香炉与座 · 21.175.45a–c'} as Record<string,string>)[asset.file]}</a></li>)}</ul>
 <p><a href="https://commons.wikimedia.org/wiki/File:Frankincense.JPG">乳香</a>：Gaius Cornelius，公有领域；<a href="https://commons.wikimedia.org/wiki/File:Clove_close_up.jpg">丁香</a>：Sanjay Acharya，CC BY-SA 4.0。<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC BY-SA 3.0</a> · <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a>。</p>
 <p>底本文字来自维基文库（CC BY-SA 4.0），记录保留固定版本出处。</p>
 </details>;}
