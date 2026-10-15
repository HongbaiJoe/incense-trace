"use client";

import { useEffect, useMemo, useState } from "react";
import modelData from "./data/model_output.json";
import materialData from "./data/materials.json";
import { FormulaPart, predictDescription } from "./predictor";

type Tab = "home" | "results" | "lab" | "database" | "method";
type Entry = { id: number; name: string; excerpt: string; notes: string; created_at: string };
type Target = (typeof modelData.targets)[number];
type TargetPart = Target["formula"][number];

const dimNames: Record<string, string> = {
  woody: "木质", resinous: "树脂", sweet: "甜润", floral: "花香", spicy: "辛香", herbal: "草本",
  fresh: "清凉", earthy: "土质", smoky: "烟熏", musky: "麝香感", fruity: "果香", tenacity: "留香",
};
const roleNames: Record<string, string> = { top: "前调", heart: "中调", base: "基调" };
const examples = [
  "雨后木柜里刚削开的檀木，清凉、不甜，尾调有树脂和一点烟，留香很久。",
  "柔软的桂花与熟杏气味，微甜，下面压着温暖木香和少量辛香。",
  "古寺里冷而干燥的草药根茎，带泥土、烟和持久的沉香感。",
];

function materialName(name: string) {
  return name.replace(/（仅历史；现代测试用合成麝香气味代理）/g, "");
}

function FormulaList({ formula }: { formula: Array<TargetPart | FormulaPart> }) {
  return <div className="formula-list">{formula.map((part) => (
    <div className="formula-line" key={part.material_id}>
      <div><b>{materialName(part.material)}</b><small>{roleNames[part.role] ?? part.role}{"reason" in part ? ` · ${part.reason}` : ""}</small></div>
      <strong>{part.percent}%</strong>
      <i style={{ transform: `scaleX(${part.percent / 100})` }} />
    </div>
  ))}</div>;
}

export default function IncenseApp() {
  const [tab, setTab] = useState<Tab>("home");
  const [selected, setSelected] = useState<Target>(modelData.targets[0]);
  const [query, setQuery] = useState("");
  const [description, setDescription] = useState(examples[0]);
  const initialPrediction = useMemo(() => predictDescription(examples[0]), []);
  const [prediction, setPrediction] = useState(initialPrediction);
  const [entries, setEntries] = useState<Entry[]>([]);
  const [form, setForm] = useState({ name: "", excerpt: "", notes: "" });
  const [saveStatus, setSaveStatus] = useState("");

  const filtered = useMemo(() => modelData.targets.filter((target) => target.name.includes(query) || target.excerpt.includes(query)), [query]);
  useEffect(() => {
    fetch("/api/entries").then((response) => response.ok ? response.json() : []).then(data=>setEntries(data as Entry[])).catch(() => setEntries([]));
  }, []);

  function navigate(next: Tab) {
    setTab(next);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function runPrediction(text = description) {
    setDescription(text);
    setPrediction(predictDescription(text));
  }

  async function saveEntry(event: React.FormEvent) {
    event.preventDefault(); setSaveStatus("保存中");
    const response = await fetch("/api/entries", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(form) });
    if (!response.ok) { setSaveStatus("保存失败"); return; }
    const created = await response.json() as Entry;
    setEntries((old) => [created, ...old]); setForm({ name: "", excerpt: "", notes: "" }); setSaveStatus("已保存");
  }

  function exportData() {
    const blob = new Blob([JSON.stringify({ model: modelData, custom_entries: entries }, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob); const anchor = document.createElement("a");
    anchor.href = url; anchor.download = "incense-trace-database.json"; anchor.click(); URL.revokeObjectURL(url);
  }

  return <main className={tab === "home" ? "is-home" : ""}>
    <header className={`masthead ${tab === "home" ? "masthead-home" : ""}`}>
      <button className="wordmark" onClick={() => navigate("home")}><span>香迹</span></button>
      <nav>{([
        ["home", "首页"], ["results", "香方"], ["lab", "预测香（复原）"], ["database", "资料库"], ["method", "公开方法"],
      ] as [Tab, string][]).map(([id, label]) => <button key={id} className={tab === id ? "active" : ""} onClick={() => navigate(id)}>{label}</button>)}</nav>
    </header>

    {tab === "home" && <section className="home-hero">
      <video className="home-film" autoPlay muted loop playsInline preload="metadata" aria-label="燃烧中的线香与烟雾">
        <source src="/incense-smoke.mp4" type="video/mp4" />
      </video>
      <div className="home-wash" />
      <div className="home-content">
        <h1>香迹</h1>
        <p className="home-subtitle">线香复原实验室</p>
        <div className="home-sections">
          <button onClick={() => navigate("results")}><b>香方</b><span>↗</span></button>
          <button onClick={() => navigate("lab")}><b>预测香</b><span>↗</span></button>
          <button onClick={() => navigate("database")}><b>资料库</b><span>↗</span></button>
          <button onClick={() => navigate("method")}><b>公开方法</b><span>↗</span></button>
        </div>
      </div>
    </section>}

    {tab === "results" && <section className="results-page">
      <aside className="catalog">
        <div className="page-title"><h2>三十香方</h2></div>
        <button className="quick-link" onClick={() => navigate("lab")}>预测一个香味 <span>↗</span></button>
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索香名或原文" />
        <div className="target-list">{filtered.map((target) => <button className={selected.id === target.id ? "selected" : ""} key={target.id} onClick={() => setSelected(target)}><b>{target.name}</b><em>{target.formula.length} 味</em></button>)}</div>
      </aside>
      <article className="formula-detail">
        <div className="detail-top">
          <div className="detail-heading"><h2>{selected.name}</h2><p>候选配方 · {selected.formula.length}味 · 总比100%</p></div>
          <figure className="manuscript-thumb"><img src="/media/chen-incense-manuscript.png" alt="《陈氏香谱》四库全书影印页"/><figcaption>《陈氏香谱》卷一影印页</figcaption></figure>
        </div>
        <blockquote>“{selected.excerpt}”<cite>{selected.source}</cite></blockquote>
        <FormulaList formula={selected.formula} />
        <div className="evidence">
          <div><h3>原文线索</h3>{selected.clues.map((clue) => <p key={clue}>{clue}</p>)}</div>
          <div><h3>气味映射</h3>{Object.entries(selected.labels).sort((a, b) => b[1] - a[1]).map(([key, value]) => <p key={key}><span>{dimNames[key]}</span><b>{Math.round(value * 100)}</b></p>)}</div>
        </div>
      </article>
    </section>}

    {tab === "lab" && <section className="lab-page">
      <div className="lab-input">
        <div className="page-title"><h2>预测香</h2></div>
        <p className="page-lede">写下你闻到的质感、冷暖、扩散和留香。结果直接给出具体香材与比例。</p>
        <textarea value={description} onChange={(event) => setDescription(event.target.value)} aria-label="香味描述" />
        <div className="example-list">{examples.map((example, index) => <button key={example} onClick={() => runPrediction(example)}>示例 {index + 1}</button>)}</div>
        <button className="run" onClick={() => runPrediction()}>生成候选配方</button>
      </div>
      <div className="lab-result">
        <div className="result-head"><span>候选配方</span><b>{prediction.formula.length} 味 / 100%</b><button className="inline-link" onClick={() => navigate("results")}>查看三十香方</button></div>
        <FormulaList formula={prediction.formula} />
        <div className="readout">
          <span>识别到的气味</span>
          <p>{prediction.parsed.matched.length ? prediction.parsed.matched.slice(0, 9).join("、") : "木质、树脂、留香"}</p>
        </div>
        <div className="material-strip">
          <figure><img src="/media/frankincense.jpg" alt="乳香树脂颗粒"/><figcaption>乳香 · 树脂相</figcaption></figure>
          <figure><img src="/media/clove.jpg" alt="丁香香料特写"/><figcaption>丁香 · eugenol</figcaption></figure>
          <figure><img src="/media/indian-sandalwood.jpg" alt="印度檀香植物"/><figcaption>檀香 · santalols</figcaption></figure>
        </div>
      </div>
    </section>}

    {tab === "database" && <section className="archive-page">
      <div className="archive-head"><div className="page-title"><h2>香方资料库</h2></div><button onClick={exportData}>导出 JSON</button></div>
      <div className="archive-visual">
        <figure><img src="/media/chinese-incense-burner.jpg" alt="十九世纪中国瓷香炉"/><figcaption>中国瓷香炉 · Walters Art Museum</figcaption></figure>
        <figure><img src="/media/chen-incense-manuscript.png" alt="《陈氏香谱》影印页"/><figcaption>《钦定四库全书》本《陈氏香谱》</figcaption></figure>
        <div><strong>{modelData.recorded_recipe_count}</strong><span>历史类方</span><strong>{materialData.materials.length}</strong><span>香材化学条目</span></div>
      </div>
      <form className="entry-form" onSubmit={saveEntry}>
        <input required placeholder="香名" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
        <textarea required placeholder="古籍原文与出处" value={form.excerpt} onChange={(event) => setForm({ ...form, excerpt: event.target.value })} />
        <textarea placeholder="气味词、异文或材料备注" value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} />
        <button className="run">保存条目</button><span>{saveStatus}</span>
      </form>
      <div className="archive-grid">
        <div><h3>香材 · {materialData.materials.length}</h3>{materialData.materials.map((material) => <details key={material.id}><summary>{materialName(material.zh)}<small>{material.latin}</small></summary><p>{material.note}</p><div>{material.molecules.slice(0, 4).map((molecule) => <span key={String(molecule[0])}>{molecule[0]}</span>)}</div></details>)}</div>
        <div><h3>新增条目 · {entries.length}</h3>{entries.length === 0 ? <p className="empty">尚未添加条目。</p> : entries.map((entry) => <article className="saved" key={entry.id}><b>{entry.name}</b><p>{entry.excerpt}</p><small>{entry.notes || "无附注"} · {entry.created_at}</small></article>)}</div>
      </div>
    </section>}

    {tab === "method" && <section className="method-page">
      <div className="method-intro">
        <div className="page-title"><h2>公开方法</h2></div>
        <p>古籍气味描述先转成十二维气味向量，再结合香材的挥发物信息与历史类方，反推可能的香材组成和比例。</p>
      </div>
      <div className="chemistry-flow">
        <article><h3>气味向量</h3><code>t ∈ [0, 1]¹²</code><p>古代气味词映射到木质、树脂、甜、花、辛、草本、清凉、土质、烟熏、麝香感、果香和留香十二个维度。原文提到的香材作为锚点进入计算。</p></article>
        <article><h3>香材矩阵</h3><code>A ∈ ℝ¹²×²⁵</code><p>模型从GC-MS报告的主要挥发物建立香材轮廓。檀香对应α/β-santalol，丁香对应eugenol，乳香则以单萜类成分为主，再由实验气味词连接到十二个维度。</p></article>
        <article><h3>历史先验</h3><code>Ŷ = XB + λ‖B‖²</code><p>44张配料明确的历史类方用于训练多输出Ridge模型。λ由五折交叉验证选择，香材共现图记录旧方中常见的材料组合。</p></article>
        <article><h3>比例优化</h3><code>m = Aw</code><p>在w≥0且Σw=1的条件下，算法寻找最接近目标气味的材料权重，并参考历史先验和香材共现关系，最终把比例量化到5%步长。</p></article>
      </div>
      <section className="objective">
        <div><span>目标函数</span><code>min 1.7‖Aw−t‖² + 0.65‖w−p‖² − 0.05wᵀCw + 0.018Σwᵢlog(wᵢ)</code></div>
        <p><b>Aw−t</b>衡量气味拟合，<b>w−p</b>衡量候选配方与历史类方的距离，<b>C</b>记录香材共现关系，熵项调节权重的集中程度。</p>
      </section>
      <div className="model-limits">
        <figure><img src="/media/frankincense.jpg" alt="乳香树脂颗粒"/><figcaption>树脂材料的化学型会随物种、产地和提取方式改变</figcaption></figure>
        <div><h3>模型假设</h3><p>当前版本用近似线性混合估算整体气味。受体层面的竞争结合、遮蔽和协同，需要混合物实测数据才能进一步建模。</p><p>配方搜索采用常温香材轮廓，GC-MS数据负责筛选候选材料。燃烧温度、热裂解与烟气组成可在实测阶段另行记录。</p></div>
      </div>
      <div className="metrics">
        <div><span>主料 Top-1</span><strong>{(modelData.metrics.top1 * 100).toFixed(1)}%</strong><small>频率基线 {(modelData.baseline_metrics.top1 * 100).toFixed(1)}%</small></div>
        <div><span>Recall@5</span><strong>{(modelData.metrics.recall5 * 100).toFixed(1)}%</strong><small>频率基线 {(modelData.baseline_metrics.recall5 * 100).toFixed(1)}%</small></div>
        <div><span>加权 Jaccard</span><strong>{(modelData.metrics.weighted_jaccard * 100).toFixed(1)}%</strong><small>频率基线 {(modelData.baseline_metrics.weighted_jaccard * 100).toFixed(1)}%</small></div>
        <div><span>比例 MAE</span><strong>{modelData.metrics.ratio_mae.toFixed(3)}</strong><small>频率基线 {modelData.baseline_metrics.ratio_mae.toFixed(3)}</small></div>
      </div>
      <p className="method-note">交叉验证中，比例MAE与频率基线仍有差距，因此预测比例更适合作为嗅闻测试的初始值。</p>
      <div className="source-list"><h3>公开资料与依据</h3>
        <a href="https://pubmed.ncbi.nlm.nih.gov/42465471/" target="_blank" rel="noreferrer"><span>mixture perception</span>Odors Smell Like Their Components: A Linear Framework for Decoding Odor Mixtures</a>
        <a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC6511041/" target="_blank" rel="noreferrer"><span>receptor model</span>Competitive binding predicts nonlinear responses of olfactory receptors</a>
        {Object.values(materialData.source_registry).map((source) => <a href={source.url} target="_blank" rel="noreferrer" key={source.url}><span>{source.type.replaceAll("_", " ")}</span>{source.title}</a>)}
      </div>
    </section>}

    {tab !== "home" && <footer><div><a href="https://ctext.org/library.pl?if=gb&remap=gb&res=110286" target="_blank" rel="noreferrer">香谱影印：CText / CADAL</a><a href="https://commons.wikimedia.org/wiki/File:Chinese_-_Incense_Burner_-_Walters_49727.jpg" target="_blank" rel="noreferrer">香炉：Walters Art Museum</a><a href="https://commons.wikimedia.org/wiki/File:Frankincense.JPG" target="_blank" rel="noreferrer">乳香：Gaius Cornelius</a><a href="https://commons.wikimedia.org/wiki/File:Clove_close_up.jpg" target="_blank" rel="noreferrer">丁香：Sanjay Acharya</a><a href="https://commons.wikimedia.org/wiki/File:Indian_Sandalwood.jpg" target="_blank" rel="noreferrer">檀香：Nativeplants garden</a></div></footer>}
  </main>;
}
