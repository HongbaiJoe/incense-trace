# 投稿方案与最后的作者确认

核对日期：2026-09-30。建议首投 **Applied Sciences，Computing and Artificial Intelligence 方向，Article**。已经使用官方 MDPI ACS 模板，`mdpi.cls` v6.5a（2026-09-11），以 `applsci,article,submit,oneauthor` 编译。

## 为什么选它

论文的核心是跨来源集合补全、统计评价和可部署的计算工具，适合应用计算方向。化学信息是辅助分析；文稿不将材料共现模型包装成燃烧或分子气味模拟。

| 期刊 | 官方速度信息 | 适配判断 |
|---|---|---|
| Applied Sciences | 首次决定中位数约 15 天；接收后出版约 2.9 天，统计期为 2026 年上半年 | 本轮首选：SCIE、计算方法与应用范围兼容 |
| Informatics | 首次决定约 32.7 天；接收后出版约 3.8 天，2026 年上半年 | 计算与文化信息学契合，但官方列为 ESCI，且首次决定较慢 |
| Heritage | 官网显示出版中位时间 53 天，未在该页面同时说明统计期 | 文化遗产方向更直接，速度口径与前两者不同，不能直接相减比较 |

首次决定可能是拒稿或修改意见，不等于接收；两个中位数也不能相加得到总发表时间。公开数据无法支持“稳收”或保证一次接收。本轮选择是在已核对期刊中兼顾范围、索引和速度，不是对全球所有期刊做绝对最快排名。Applied Sciences 官方页面列出的 APC 为 CHF 2400，实际费用、减免与税费以投稿时确认为准，尚未支付或授权支出。

官方依据：

- https://www.mdpi.com/journal/applsci
- https://www.mdpi.com/journal/applsci/sections/Computing_Artificial_Intelligence
- https://www.mdpi.com/journal/applsci/instructions
- https://www.mdpi.com/journal/informatics
- https://www.mdpi.com/journal/heritage
- https://www.mdpi.com/apc
- https://www.mdpi.com/authors/latex
- https://mdpi-res.com/data/MDPI_template_ACS.zip
- https://blog.mdpi.com/2026/09/10/preparing-your-research-paper-submission/

部分期刊正文页面访问返回 403/429；速度及范围使用官方搜索索引与可访问的官方页面交叉核对，模板 ZIP 实际下载并编译。没有把受限页面描述为已逐条阅读。

## 已处理

官方期刊类、标题作者单位、摘要关键词、连续公式编号、可编辑 TikZ 图、三线表、图注、文献、补充材料说明、数据声明、真实 AI 辅助范围和完整复现源文件。数学符号置于数学模式，检查了编译日志、页边界和全部页面。

## 提交前仍须作者完成

1. 提供通讯邮箱；当前没有编造邮箱，LaTeX 已留对应 `\corres` 命令。作者需核对姓名、单位和邮编。
2. 阅读并确认方法、结果、作者贡献、无外部资助与无利益冲突的陈述。AI 使用说明应保留实际辅助范围，不能宣称此次新增数学和代码均无 AI 参与。
3. 在投稿系统确认原创性、非一稿多投及 APC/减免条件；这些声明和付款必须由作者决定。
4. 将复现 ZIP 上传 Supplementary Materials，或先存入作者控制的公开数据仓库并补上真实 DOI。网站权限目前沿用原来的仅本人访问，向学会共享需明确设置访问范围。

未向期刊提交、未发送邀请、未付款。网站可部署与论文有可编译投稿格式，不等于作者确认已经完成。
