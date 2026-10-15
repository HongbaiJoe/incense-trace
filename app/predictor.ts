import modelData from "./data/model_output.json";
import materialData from "./data/materials.json";

export type FormulaPart = {
  material_id: string;
  material: string;
  percent: number;
  role: string;
  reason: string;
};

export type ParsedDescription = {
  vector: number[];
  family: string;
  anchors: string[];
  matched: string[];
};

const dimNames: Record<string, string> = {
  woody: "木质", resinous: "树脂香", sweet: "甜润", floral: "花香", spicy: "辛香", herbal: "草本",
  fresh: "清凉", earthy: "土质", smoky: "烟熏", musky: "麝香感", fruity: "果香", tenacity: "留香",
};

const lexicon: Array<[string[], number, number]> = [
  [["木质", "木头", "木柜", "木屑", "木香", "檀木", "沉木", "松木", "干木"], 0, .48],
  [["树脂", "香脂", "松脂", "乳香", "安息香", "琥珀感"], 1, .58],
  [["甜", "甜润", "蜜", "蜂蜜", "奶", "香草", "糖"], 2, .48],
  [["花", "花香", "梅", "兰", "桂花", "木犀", "茉莉", "玫瑰", "蔷薇", "白花"], 3, .55],
  [["辛", "辛香", "辣", "丁香", "肉桂", "桂皮", "胡椒", "刺激"], 4, .55],
  [["草", "草本", "药", "药香", "叶", "青草", "植物"], 5, .48],
  [["清", "清凉", "冰", "冷", "薄荷", "樟脑", "通透", "明亮"], 6, .52],
  [["土", "泥土", "土质", "根", "根茎", "潮湿", "苔藓", "地下室"], 7, .58],
  [["烟", "烟熏", "燃烧", "烧", "灰", "焦", "炭", "寺庙"], 8, .55],
  [["麝", "动物", "皮革", "毛皮", "温热肌肤"], 9, .62],
  [["果", "果香", "梨", "杏", "荔枝", "桃", "柑橘", "熟果"], 10, .55],
  [["留香", "持久", "悠长", "绵长", "扩散", "远", "萦绕", "不散"], 11, .62],
];

const familyRules: Array<[string, string[]]> = [
  ["plum", ["梅", "寒梅", "雪后"]],
  ["orchid", ["兰", "幽", "空谷"]],
  ["osmanthus", ["桂花", "木犀", "金粟"]],
  ["spring", ["春", "花园", "明亮", "新鲜花"]],
  ["quiet", ["静", "古寺", "夜", "书斋", "冷", "幽暗"]],
];

const explicitAliases: Record<string, string[]> = {
  agarwood: ["沉香", "伽南", "伽罗"], sandalwood: ["檀香", "白檀"], pine_resin: ["松香", "松脂"],
  frankincense: ["乳香", "薰陆"], benzoin: ["安息香", "金颜香"], borneol: ["龙脑", "冰片", "羯布罗"],
  clove: ["丁香", "鸡舌香"], cassia: ["肉桂", "桂皮"], nard: ["甘松", "多伽罗"], patchouli: ["藿香"],
  calamus: ["菖蒲", "杜若"], lingling: ["零陵香"], cyperus: ["香附子"], angelica: ["白芷"],
  costus: ["青木香", "木香"], rose: ["蔷薇", "玫瑰"], jasmine: ["茉莉", "末利", "野悉密"],
  osmanthus: ["木犀", "桂花"], musk: ["麝香"], styrax: ["苏合香"], jiangzhen: ["降真香"],
  anise: ["茴香"], turmeric: ["郁金"], chuanxiong: ["川芎", "芎藭"], ferula: ["阿魏"],
};

const dot = (a: number[], b: number[]) => a.reduce((s, x, i) => s + x * b[i], 0);
const normalize = (a: number[]) => {
  const positive = a.map((x) => Math.max(0, x));
  const total = positive.reduce((s, x) => s + x, 0) || 1;
  return positive.map((x) => x / total);
};
const cosine = (a: number[], b: number[]) => {
  const den = Math.sqrt(dot(a, a) * dot(b, b));
  return den ? dot(a, b) / den : 0;
};

export function parseDescription(text: string): ParsedDescription {
  const vector = Array(12).fill(.04);
  const matched: string[] = [];
  for (const [words, index, weight] of lexicon) {
    let hits = 0;
    for (const word of words) {
      if (!text.includes(word)) continue;
      const negated = text.includes(`不${word}`) || text.includes(`不要${word}`) || text.includes(`无${word}`);
      if (negated) vector[index] = .01;
      else { hits += 1; matched.push(word); }
    }
    if (hits) vector[index] = Math.min(1, vector[index] + weight + Math.min(.24, (hits - 1) * .08));
  }

  const anchors = Object.entries(explicitAliases)
    .filter(([, aliases]) => aliases.some((alias) => text.includes(alias)))
    .map(([id]) => id);

  // Explicitly named materials add their measured material-level odor vector.
  for (const id of anchors) {
    const material = materialData.materials.find((m) => m.id === id);
    if (material) material.vector.forEach((value, i) => { vector[i] = Math.min(1, vector[i] + value * .28); });
  }

  let family = "";
  let bestHits = 0;
  for (const [candidate, words] of familyRules) {
    const hits = words.filter((word) => text.includes(word)).length;
    if (hits > bestHits) { bestHits = hits; family = candidate; }
  }
  if (Math.max(...vector) <= .05) {
    vector[0] = .55; vector[1] = .4; vector[11] = .55;
  }
  return { vector, family, anchors, matched: [...new Set(matched)] };
}

function projectWithFloor(values: number[], floor = .05) {
  const total = 1 - values.length * floor;
  const shifted = values.map((x) => x - floor);
  const sorted = [...shifted].sort((a, b) => b - a);
  let rho = 0;
  for (let i = 0; i < sorted.length; i++) {
    const theta = (sorted.slice(0, i + 1).reduce((s, x) => s + x, 0) - total) / (i + 1);
    if (sorted[i] - theta > 0) rho = i + 1;
  }
  const theta = (sorted.slice(0, rho).reduce((s, x) => s + x, 0) - total) / Math.max(1, rho);
  return shifted.map((x) => Math.max(0, x - theta) + floor);
}

function roundToFive(weights: number[]) {
  const raw = weights.map((x) => x * 20);
  const units = raw.map((x) => Math.max(1, Math.floor(x)));
  while (units.reduce((s, x) => s + x, 0) < 20) {
    const used = new Set<number>();
    let best = 0, bestRemainder = -Infinity;
    raw.forEach((x, i) => {
      const remainder = x - units[i];
      if (!used.has(i) && remainder > bestRemainder) { best = i; bestRemainder = remainder; }
    });
    units[best] += 1; used.add(best);
  }
  while (units.reduce((s, x) => s + x, 0) > 20) {
    let best = units.findIndex((x) => x > 1);
    for (let i = 0; i < units.length; i++) if (units[i] > units[best] && units[i] > 1) best = i;
    units[best] -= 1;
  }
  return units.map((x) => x * 5);
}

export function predictDescription(text: string): { formula: FormulaPart[]; parsed: ParsedDescription } {
  const parsed = parseDescription(text);
  const materials = materialData.materials;
  const familyIndex = modelData.families.indexOf(parsed.family);
  const feature = [...parsed.vector, ...modelData.families.map((_, i) => i === familyIndex ? 1 : 0)];
  const z = feature.map((value, i) => (value - modelData.ridge.mean[i]) / modelData.ridge.scale[i]);
  const learned = normalize(modelData.ridge.coef.map((row, i) => modelData.ridge.intercept[i] + dot(row, z)));
  const familyPrior = parsed.family
    ? modelData.family_priors[parsed.family as keyof typeof modelData.family_priors]
    : Array(materials.length).fill(0);
  const inverse = normalize(materials.map((material) => cosine(parsed.vector, material.vector)));
  const scores = materials.map((material, i) =>
    .42 * learned[i] + .36 * familyPrior[i] + .22 * inverse[i] + (parsed.anchors.includes(material.id) ? .35 : 0)
  );

  const selected: number[] = [];
  for (const id of parsed.anchors) {
    const index = materials.findIndex((material) => material.id === id);
    if (index >= 0 && !selected.includes(index) && selected.length < 6) selected.push(index);
  }
  while (selected.length < 6) {
    let best = -1, bestUtility = -Infinity;
    for (let i = 0; i < materials.length; i++) {
      if (selected.includes(i)) continue;
      const compatibility = selected.length
        ? selected.reduce((s, j) => s + modelData.cooccurrence[i][j], 0) / selected.length
        : 0;
      const utility = scores[i] + .10 * compatibility;
      if (utility > bestUtility) { best = i; bestUtility = utility; }
    }
    selected.push(best);
  }

  const matrix = parsed.vector.map((_, dim) => selected.map((i) => materials[i].vector[dim]));
  const prior = normalize(selected.map((i) => learned[i] + familyPrior[i] + .10 * scores[i]));
  let weights = Array(selected.length).fill(1 / selected.length);
  for (let step = 0; step < 320; step++) {
    const mixture = matrix.map((row) => dot(row, weights));
    const gradient = weights.map((weight, i) => {
      let perceptual = 0;
      for (let d = 0; d < parsed.vector.length; d++) perceptual += matrix[d][i] * (mixture[d] - parsed.vector[d]);
      perceptual *= 2 * 1.7 / parsed.vector.length;
      const historical = 2 * .65 * (weight - prior[i]) / weights.length;
      const graph = -.05 * weights.reduce((s, other, j) => j === i ? s : s + other * modelData.cooccurrence[selected[i]][selected[j]], 0);
      const diversity = .018 * (Math.log(Math.max(weight, 1e-7)) + 1);
      return perceptual + historical + graph + diversity;
    });
    const rate = .12 / (1 + step * .012);
    weights = projectWithFloor(weights.map((x, i) => x - rate * gradient[i]));
  }
  const percentages = roundToFive(weights);

  const formula = selected.map((materialIndex, i) => {
    const material = materials[materialIndex];
    const contributions = material.vector.map((value, d) => value * parsed.vector[d]);
    const strongest = contributions.indexOf(Math.max(...contributions));
    return {
      material_id: material.id,
      material: material.zh,
      percent: percentages[i],
      role: modelData.roles[material.id as keyof typeof modelData.roles] ?? "heart",
      reason: `${dimNames[materialData.dimensions[strongest]]}匹配`,
    };
  }).sort((a, b) => b.percent - a.percent);
  return { formula, parsed };
}
