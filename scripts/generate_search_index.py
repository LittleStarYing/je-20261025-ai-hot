#!/usr/bin/env python3
"""生成前端异步加载的数据文件（site/static/ 下）

页面原先用 Hugo 的 `jsonify` 把完整 data/*.json 内嵌进 HTML：news.json 涨到
35MB 后首页 HTML 接近 70MB、搜索页 36MB，移动端基本打不开。改成按需 fetch：
首屏 HTML 保持轻量，数据异步拉取，页面体积也就不再随数据量增长。

输出两类文件：
  search-index.json  首页/搜索页/新闻列表翻页用的精简字段索引
  tools-full.json    对比页与工具跳转页需要的工具完整字段
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Windows 控制台默认 GBK，直接打印 ✓ 会抛 UnicodeEncodeError，
# 这里固定 UTF-8 输出，保证本地也能运行（Linux CI 行为不变）。
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
SITE_STATIC = ROOT / 'site' / 'static'
OUTPUT = SITE_STATIC / 'search-index.json'
TOOLS_FULL_OUTPUT = SITE_STATIC / 'tools-full.json'
# 用固定 UTC+8 而不是 ZoneInfo("Asia/Shanghai")：中国不实行夏令时，
# 结果一致，同时避免 Windows 本地缺 tzdata 时脚本直接报错。
SH_TZ = timezone(timedelta(hours=8))

# 字段白名单：必须覆盖站内所有前端搜索脚本读取的字段，
# 漏字段会直接导致搜索/随机推荐功能退化。
FIELD_KEYS = {
    'tools': ('id', 'name', 'description', 'category', 'pricing', 'tags', 'stars', 'url'),
    'models': ('name', 'display_name', 'author', 'pipeline_tag', 'url', 'likes'),
    'agents': ('name', 'description', 'type', 'pricing', 'url', 'stars'),
    # 新闻列表页翻页时也用这份索引渲染后续页，字段要与模板输出对齐
    'news': ('id', 'title', 'title_zh', 'summary', 'source', 'published', 'url', 'ai_summary'),
}

# 索引里保留的新闻条数上限，保证 search-index.json 体积恒定。
# layouts/_default/list.html 的翻页范围依赖同一个数字（有测试校验一致性）。
NEWS_INDEX_LIMIT = 5000


def load_items(filename):
    path = DATA_DIR / filename
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding='utf-8'))
    if isinstance(data, dict):
        data = data.get('items') or []
    return data if isinstance(data, list) else []


def compact(items, keys):
    """按白名单裁剪字段，跳过空值，避免把 null 写进索引。"""
    records = []
    for item in items:
        if not isinstance(item, dict):
            continue
        record = {}
        for key in keys:
            value = item.get(key)
            if value is None or value == '' or value == [] or value == {}:
                continue
            record[key] = value
        if record:
            records.append(record)
    return records


def generate_search_index():
    news_items = compact(load_items('news.json'), FIELD_KEYS['news'])
    # 索引由前端异步加载，必须有个恒定上限：否则新闻累积会让它无限变大
    # （4400 条约 2MB，2 万条就是 10MB）。只保留最近的，旧新闻仍可通过
    # sitemap-news.xml 被搜索引擎发现。
    # 注意：layouts/_default/list.html 里的 $newsIndexLimit 必须与此一致。
    news_items = news_items[:NEWS_INDEX_LIMIT]

    index = {
        'generated_at': datetime.now(SH_TZ).strftime('%Y-%m-%d %H:%M:%S'),
        'tools': compact(load_items('tools.json'), FIELD_KEYS['tools']),
        'models': compact(load_items('models.json'), FIELD_KEYS['models']),
        'agents': compact(load_items('agents.json'), FIELD_KEYS['agents']),
        'news': news_items,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(index, ensure_ascii=False, separators=(',', ':')),
        encoding='utf-8',
    )

    # 对比页 / 工具跳转页需要工具的完整字段（优缺点、免费额度、适用人群等），
    # 同样走异步加载，避免内嵌进 HTML 后随工具数量增长把页面撑大。
    tools_full = load_items('tools.json')
    TOOLS_FULL_OUTPUT.write_text(
        json.dumps(tools_full, ensure_ascii=False, separators=(',', ':')),
        encoding='utf-8',
    )

    size_kb = OUTPUT.stat().st_size / 1024
    print(f'  ✓ 搜索索引: 工具 {len(index["tools"])} / 模型 {len(index["models"])} '
          f'/ Agent {len(index["agents"])} / 新闻 {len(index["news"])}')
    print(f'  ✓ 工具完整数据 tools-full.json: {len(tools_full)} 条 '
          f'({TOOLS_FULL_OUTPUT.stat().st_size / 1024:.0f}KB)')
    return f'搜索索引 {size_kb:.0f}KB（工具 {len(index["tools"])} 模型 {len(index["models"])} Agent {len(index["agents"])} 新闻 {len(index["news"])}）'


if __name__ == '__main__':
    print(generate_search_index())
