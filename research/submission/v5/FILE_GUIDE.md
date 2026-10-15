# V5 文件用途

## 投稿正文

- `xiangji_v5.tex`：唯一正文入口；公式、表格、图和文献均在其中。
- `xiangji_v5.pdf`：已检查的 28 页阅读版。
- `Definitions/mdpi.cls`：2026-09-11 官方类文件，未修改。
- `Definitions/logo-mdpi.pdf`：用于兼容 XeTeX/Tectonic 的矢量标志。
- `editable_figures/`：7 张独立矢量 PDF、TikZ 源文件和绘图坐标；正文直接包含同一套 TikZ 图。

`Definitions` 中的 `.bst`、APA/Chicago 样式、ORCID/updates 标志、期刊名表与 Unicode 辅助文件来自官方模板。当前正文使用内嵌文献，不需要另跑 BibTeX；保留这些文件是为维护模板完整性，并非要求分别上传到投稿系统。

## 复现和审阅

- `build_manuscript.py`、`reconcile_weak.py`、`mathematical_extension.tex`：由 V4、数学扩展和真实实验输出生成 V5。重建脚本需在完整复现包的 `research/submission/v5` 中运行。
- `export_figures.py`：导出正文中可编辑的图及坐标。
- `verify_pdf.py`、`pdf_verification.json`：PDF 结构与文字检查。
- `REPRODUCE.md`：从环境安装到模型复测的命令。
- `CHANGES_AND_FIVE_ANSWERS.md`：五个原始数据问题的答案及本次修改。
- `build_manifest.json`：原稿和生成源码的哈希。

## 作者操作说明

- `JOURNAL_AND_SUBMISSION.md`：期刊依据、费用和必须由作者确认的内容。
- `COVER_LETTER.md`：投稿信草稿，尚未发送。
- `RELEASE_STATUS.md`：测试与发布记录。

完整复现包额外保留 `original_v4.tex/pdf`，它们是原始输入备份，不是投稿正文。`submission/latex`、早期 Word/PDF 和旧图中随包保留的文件是历史回归测试的精确依赖，不是本次投稿文件。旧实验输出仅用于追溯；V5 弱标签结果以 `v5_weak_fixed_masks.json` 为准。LaTeX 投稿包不包含旧稿、临时截图和编译缓存。
