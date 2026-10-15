import MaterialStack from './MaterialStack';
import AssetCredits from './AssetCredits';

export default function ResearchMethod(){return <>
 <header className="lab-heading"><h1>方法</h1><a href="/downloads/xiangji_v5.pdf" target="_blank" rel="noreferrer">阅读全文</a></header>
 <article className="research-reading">
  <section className="method-opening">
   <h2>从留下的香材，寻找缺失的搭配。</h2>
   <p>一份残方仍有白檀与沉香，接下来该补什么，又该各占多少？香迹把这个问题分成三步：寻找与已知材料相配的香材，估计全方的材料数，再分配份量。搭配关系来自古籍中有出处、可核对的香方。</p>
   <p>论文的核心方法是来源稳定条件提升度（SSCL）：先在每部书里学习搭配，再汇合不同书的证据。这样既能利用共同的配伍习惯，也能追踪某种关联是否只集中在一部书中。</p>
  </section>
  <div className="method-evidence"><MaterialStack variant="research" label="论文图表"/></div>
  <section className="reading-section"><h2>资料如何进入模型</h2>
   <p>研究整理了 592 条带出处的候选记录，其中 296 条可解析出组成。逐条核对后，91 份香方构成主要参考集，分属六个文献组，包含 81 种芳香材料。单方材料数为 2—17 种，中位数为 6 种。</p>
   <p>另外 59 条记录属于这 91 方的同源传本，建模时予以排除；剩下的 146 条作为弱监督扩充数据单独测试。固定版本链接、材料规范名与比例随记录一并保存。</p>
   <details className="lab-details"><summary>查看六个文献组</summary><div className="research-table-wrap"><table className="research-table"><thead><tr><th>文献组</th><th>核对香方</th><th>参与测试</th></tr></thead><tbody>{[['陈氏香谱',38,38],['洪氏香谱',6,6],['晦斋香谱',10,9],['列香新谱',6,6],['墨娥小录',2,2],['香乘辑录',29,29]].map(row=><tr key={row[0]}>{row.map((v,i)=>i===0?<th scope="row" key={i}>{v}</th>:<td key={i}>{v}</td>)}</tr>)}</tbody></table></div><p>一份晦斋香方在对应训练词表中不足两种可用材料，因此不进入遮盖测试。最终评估 90 方，每方采用五组固定遮盖，共 450 次查询。</p></details>
  </section>
  <section className="reading-section"><h2>搭配、数量与比例</h2>
   <p>模型先比较“出现香材 a 时，香材 b 有多常见”和“b 在这部书里本来有多常见”。这个差值能区分普遍使用的材料与特定搭配。各书得到的关联经过平滑与加权合并，再扣除跨书波动，形成缺失香材的排序依据。</p>
   <details className="lab-details theory-details"><summary>展开数学表达</summary>
    <div className="math-line" role="math" aria-label="关联强度等于各书条件对数优势提升度的加权均值减去波动惩罚">L<sub>ab</sub> = ∑<sub>d</sub> q<sub>d</sub> ℓ<sub>ab,d</sub> − γσ<sub>ab</sub></div>
    <p>ℓ 是每部书内经过平滑的条件对数优势提升度，q 是归一化权重，σ 是跨书标准差，γ 控制惩罚强度。论文公式 7—11 给出各项定义；命题 1 说明这一惩罚可以解释为指定不确定集合内的最坏情形关联值。</p>
    <p>论文还用 Beta 后验的均值与方差，把小样本造成的估计噪声和书际差异分开。后验扩展的 F1 为 0.4266，与原 SSCL 的 0.4263 基本相当。</p>
   </details>
   <p>残方通常没有写明丢了多少材料。网站对可能的保留比例积分，再依据训练集中的方剂大小分布，估计全方材料数。若总数或保留质量占比已有文献依据，可以直接填写。</p>
   <details className="lab-details theory-details"><summary>数量与质量守恒</summary>
    <div className="math-line" role="math" aria-label="在均匀保留率先验下，方剂大小后验正比于训练先验除以总材料数加一">p(K ∣ m) ∝ p<sub>train</sub>(K) / (K + 1),　K &gt; m</div>
    <p>m 为已知材料数，K 为全方材料数。对均匀保留率先验积分后得到上式，模型以截断后验的中位数估计 K。</p>
    <div className="math-line" role="math" aria-label="缺失材料的质量等于剩余质量乘以归一化参考权重">x<sub>b</sub> = (1 − M) r<sub>b</sub> / ∑<sub>j ∈ H</sub> r<sub>j</sub></div>
    <p>M 是已知部分占全方的质量，H 是选出的缺失材料集合，r 是参考香方给出的质量权重。已知材料之间的比例保持不变，新增材料分配剩余质量，最终组成之和为 1。论文将这个过程写成带约束的 KL 投影。</p>
   </details>
  </section>
  <section className="reading-section"><h2>换一部书，还能补对多少？</h2>
   <p>每轮测试留出一整部书，另外五部用于训练。参数选择也只在训练书内完成。下表采用保留一半材料的基准设置，并提供已知材料的原始质量占比；每部书先独立汇总，再对六书等权平均。</p>
   <div className="research-table-wrap"><table className="research-table"><caption>跨书补全结果 · 论文主实验</caption><thead><tr><th>方法</th><th>缺失材料 F1</th><th>加权 Jaccard</th></tr></thead><tbody>{[['频率基线','0.378','0.451'],['有向搭配图','0.426','0.470'],['SSCL','0.426','0.472'],['EASE','0.423','0.473'],['SLIM','0.387','0.455'],['PPR','0.412','0.459']].map(row=><tr key={row[0]} data-highlight={row[0]==='SSCL'}><th scope="row">{row[0]}</th><td>{row[1]}</td><td>{row[2]}</td></tr>)}</tbody></table></div>
   <p>F1 同时衡量补入的材料是否正确、缺失的材料是否找全；加权 Jaccard 进一步比较整个配方的质量比例。SSCL 相比频率基线提高 0.048，在五部书中改善，一部持平。有向搭配图达到相近水平，跨书波动惩罚在这六组资料上没有带来额外提升。</p>
   <details className="lab-details"><summary>统计检验与实际残方设置</summary><p>SSCL 与频率基线的书级双侧精确符号翻转检验 p = 0.0625，90% 区间为 0.013—0.088；五个非零差值决定了这个检验可达到的最小 p 值。</p><p>进一步隐藏保留比例和已知质量占比后，F1 为 0.394，加权 Jaccard 为 0.384，材料总数的平均绝对误差为 1.732。这组设置更接近网站处理残方时掌握的信息。</p></details>
  </section>
  <section className="reading-section"><h2>哪些证据真正有帮助</h2>
   <p>增加 146 条弱记录后，SSCL 的 F1 从 0.426 降至 0.407。记录数量本身没有转化成更准确的补全，来源一致性与逐方校核更重要。另一组嵌套校准实验将 Brier 分数从 0.0427 降至 0.0340，改善了概率与实际命中频率的对应。</p>
   <p>剩余错误主要集中在稀有香材。下一步最有价值的资料扩充，是为这些材料增加跨书、有比例且可核对的实例，并由香文化研究者记录候选方的文献校订过程。</p>
  </section>
  <section className="reading-section research-downloads"><h2>论文与数据</h2><p><a href="/downloads/xiangji_v5.pdf" target="_blank" rel="noreferrer">论文 PDF</a><a href="/downloads/research-formulas.json" download>91 方数据</a><a href="/legacy">气味检索旧版</a></p><p>每条香方附固定版本出处。比例按芳香材料干重归一；网站保存候选组成与校订记录，便于后续比对。</p></section>
 </article>
 <AssetCredits/>
 </>;}
