# 贡献指南

感谢你愿意为 AI热榜 补充内容。先读这一页能省掉一轮返工。

## 收录 AI 工具 / Agent

**改数据源，不要改生成产物。**

| 想加的东西 | 应该改 | 不要改 |
|---|---|---|
| AI 工具 | `data/tools.json` | `site/content/tools/*.md` |
| AI Agent | `data/agents.json` | `site/data/*.json` |
| 精选模型 | `scripts/generate_curated_models.py` 里的 `CURATED_ITEMS` | `data/models_curated.json` |

原因：

- `site/content/tools/*.md` 由 `scripts/generate_tool_pages.py` 从 `data/tools.json`
  生成；
- `site/data/*.json` 是构建时从 `data/` 同步出来的副本，不入库；
- `data/models_curated.json` 由脚本按 OpenRouter 实时数据生成。

改这些文件会在下一次数据聚合（每 6 小时一次）时被覆盖，改动等于白做。

## 工具条目字段

```json
{
  "id": "example-tool",
  "name": "Example Tool",
  "url": "https://example.com/",
  "description": "一句话说明它是什么、解决什么问题",
  "category": "编程",
  "pricing": "免费 + Pro $20/月",
  "free_quota": "每月 100 次",
  "difficulty": 1,
  "tags": ["#coding", "#cli"],
  "use_cases": "适用场景一、场景二",
  "pros": ["优点一", "优点二"],
  "cons": ["缺点一", "缺点二"],
  "best_for": ["目标用户"],
  "alternatives": ["cursor", "github-copilot"],
  "icon_url": "https://www.google.com/s2/favicons?domain=example.com&sz=64"
}
```

必填：`id` / `name` / `url` / `description` / `category` / `pricing` / `icon_url`

注意事项：

- `id` 用小写英文与短横线，且不能与现有条目重复；
- `category` 请**复用** `data/tools.json` 里已有的分类。如果要新增分类，必须同时在
  `site/layouts/_default/list.html` 的 `$categories` 里登记图标，否则该分类下的工具
  不会出现在工具页上；
- `icon_url` 统一用 `https://www.google.com/s2/favicons?domain=<域名>&sz=64`；
- 描述与优缺点请用中文，写事实、不要写广告词。

## 提交前自检

```bash
python -m unittest discover -s tests -p 'test_*.py'
python scripts/quality_gate.py
```

## 只想提建议、不想改代码

直接开 Issue，写清「名称 + 官网 + 一句话介绍」即可，维护者会核验后录入。

本站会对收录建议做人工核验：链接需可访问、产品定位需在收录范围内。批量群发的
外链推广类提交会被忽略。

## 关于页面体积

站点有 CI 体积门禁（`scripts/check_page_weight.py`）把守：**页面体积不得随数据量
线性增长**。如果你新增的模板需要渲染一批数据，请改为分页或异步加载（可参考
`site/static/search-index.json` 的做法），而不是直接内联进 HTML。
