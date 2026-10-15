import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const modelPath = new URL("../app/data/model_output.json", import.meta.url);
const materialsPath = new URL("../app/data/materials.json", import.meta.url);
const clientPath = new URL("../app/IncenseApp.tsx", import.meta.url);
const layoutPath = new URL("../app/layout.tsx", import.meta.url);
const stylesPath = new URL("../app/globals.css", import.meta.url);

test("ships exactly 30 normalized reconstruction hypotheses", async () => {
  const model = JSON.parse(await readFile(modelPath, "utf8"));
  assert.equal(model.targets.length, 30);
  assert.equal(model.recorded_recipe_count, 44);
  assert.equal(model.unseen_test_count, 11);
  assert.ok(model.metrics.top1 > model.baseline_metrics.top1);
  assert.ok(model.metrics.recall5 > model.baseline_metrics.recall5);
  assert.ok(model.metrics.weighted_jaccard > model.baseline_metrics.weighted_jaccard);
  for (const target of model.targets) {
    assert.ok(target.name);
    assert.ok(target.excerpt);
    assert.ok(target.formula.length >= 5 && target.formula.length <= 6, target.name);
    assert.equal(target.formula.reduce((sum, part) => sum + part.percent, 0), 100, target.name);
    for (const part of target.formula) assert.equal(part.percent % 5, 0, `${target.name}: ${part.material}`);
  }
});

test("material vectors and interface dimensions stay aligned", async () => {
  const materials = JSON.parse(await readFile(materialsPath, "utf8"));
  assert.equal(materials.dimensions.length, 12);
  assert.ok(materials.materials.length >= 20);
  for (const material of materials.materials) assert.equal(material.vector.length, materials.dimensions.length);
});

test("interface exposes exact-ingredient reconstruction, archive and method audit", async () => {
  const source = await readFile(clientPath, "utf8");
  for (const label of ["首页", "三十香方", "预测香", "香方资料库", "公开方法"]) assert.match(source, new RegExp(label));
  assert.doesNotMatch(source, /不是还原唯一答案/);
  assert.match(source, /incense-smoke\.mp4/);
  assert.match(source, /materialName\(part\.material\)/);
  assert.match(source, /predictDescription/);
  assert.match(source, /\/api\/entries/);
  assert.doesNotMatch(source, /selected\.alternatives/);
  assert.doesNotMatch(source, /不把|不虚构|不模拟|不要远离|化学边界|GC–MS/);
  const styles = await readFile(stylesPath, "utf8");
  assert.match(styles, /\.home-film[^}]+object-fit:contain/);
  assert.match(styles, /\.home-film[^}]+mask-image:linear-gradient/);
  assert.match(styles, /STIX Two Math/);
  assert.doesNotMatch(await readFile(layoutPath, "utf8"), /og\.png/);
});
