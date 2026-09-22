#!/usr/bin/env python3
"""生成前端搜索索引 site/static/search-index.json

首页和搜索页原先用 Hugo 的 `jsonify` 把完整 data/*.json 内嵌进 HTML，
其中 news.json 已经涨到 35MB，导致首页 HTML 接近 70MB、搜索页 36MB，
移动端基本打不开。

这里只抽取前端搜索/随机推荐真正用到的字段，输出成独立静态 JSON，
页面改为异步 fetch 加载：首屏 HTML 保持轻量，搜索数据按需拉取。
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
OUTPUT = ROOT / 'site' / 'static' / 'search-index.json'
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
    index = {
        'generated_at': datetime.now(SH_TZ).strftime('%Y-%m-%d %H:%M:%S'),
        'tools': compact(load_items('tools.json'), FIELD_KEYS['tools']),
        'models': compact(load_items('models.json'), FIELD_KEYS['models']),
        'agents': compact(load_items('agents.json'), FIELD_KEYS['agents']),
        'news': compact(load_items('news.json'), FIELD_KEYS['news']),
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(index, ensure_ascii=False, separators=(',', ':')),
        encoding='utf-8',
    )

    size_kb = OUTPUT.stat().st_size / 1024
    print(f'  ✓ 搜索索引: 工具 {len(index["tools"])} / 模型 {len(index["models"])} '
          f'/ Agent {len(index["agents"])} / 新闻 {len(index["news"])}')
    return f'搜索索引 {size_kb:.0f}KB（工具 {len(index["tools"])} 模型 {len(index["models"])} Agent {len(index["agents"])} 新闻 {len(index["news"])}）'


if __name__ == '__main__':
    print(generate_search_index())
