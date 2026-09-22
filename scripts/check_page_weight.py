#!/usr/bin/env python3
"""构建产物体积门禁。

页面体积曾经随数据增长而失控：首页内嵌完整 news.json 达到 69MB、新闻列表页
全量渲染 4400+ 条达到 2.17MB。这类问题一旦上线就很难被察觉，所以这里在
「构建完成、发布之前」直接卡住：超标就让 CI 失败，站点保持上一个可用版本。

阈值按「当前条目数再涨 3 倍也不超标」留了余量，正常的数据增长不会误报；
真正需要担心的是模板里又出现了随数据线性增长的渲染。

用法：
  python scripts/check_page_weight.py            # 检查 site/public
  python scripts/check_page_weight.py --root X   # 检查指定产物目录
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PUBLIC = ROOT / 'site' / 'public'

# 关键页面（相对 public 的路径）→ 体积上限 KB
PAGE_LIMITS_KB = {
    'index.html': 150,
    'news/index.html': 150,
    'search/index.html': 120,
    'models/index.html': 150,
    'tools/index.html': 400,
    'agents/index.html': 400,
    'providers/index.html': 300,
    'compare/index.html': 200,
    'index.xml': 120,
    'sitemap.xml': 120,
}

# 前端异步加载的资源 → 体积上限 KB
ASSET_LIMITS_KB = {
    'search-index.json': 4000,
    'tools-full.json': 400,
}

# 任何单个 HTML 超过这个值都视为异常（正常详情页约 10-20KB）
SINGLE_PAGE_HARD_LIMIT_KB = 800

# 全站产物总量兜底（KB）；当前约 75MB，主要用于发现异常膨胀
TOTAL_LIMIT_KB = 600 * 1024


def kb(path):
    return path.stat().st_size / 1024


def check(public_dir):
    errors = []
    warnings = []

    if not public_dir.exists():
        return [f'构建产物目录不存在: {public_dir}'], []

    for rel, limit in PAGE_LIMITS_KB.items():
        path = public_dir / rel
        if not path.exists():
            errors.append(f'关键页面缺失: {rel}')
            continue
        size = kb(path)
        if size > limit:
            errors.append(f'{rel} 体积 {size:.0f}KB 超过上限 {limit}KB')

    for rel, limit in ASSET_LIMITS_KB.items():
        path = public_dir / rel
        if not path.exists():
            errors.append(f'关键资源缺失: {rel}')
            continue
        size = kb(path)
        if size > limit:
            errors.append(f'{rel} 体积 {size:.0f}KB 超过上限 {limit}KB')

    total_kb = 0.0
    biggest = (0, '')
    for path in public_dir.rglob('*.html'):
        size = kb(path)
        total_kb += size
        if size > biggest[0]:
            biggest = (size, str(path.relative_to(public_dir)))
        if size > SINGLE_PAGE_HARD_LIMIT_KB:
            errors.append(
                f'{path.relative_to(public_dir)} 单页 {size:.0f}KB '
                f'超过硬上限 {SINGLE_PAGE_HARD_LIMIT_KB}KB'
            )
    for path in public_dir.rglob('*.xml'):
        total_kb += kb(path)

    if total_kb > TOTAL_LIMIT_KB:
        errors.append(
            f'HTML/XML 产物合计 {total_kb / 1024:.0f}MB 超过上限 {TOTAL_LIMIT_KB / 1024:.0f}MB'
        )

    if biggest[0] > SINGLE_PAGE_HARD_LIMIT_KB * 0.5:
        warnings.append(f'最大页面 {biggest[1]} 已达 {biggest[0]:.0f}KB，接近硬上限')

    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description='构建产物体积门禁')
    parser.add_argument('--root', default=str(DEFAULT_PUBLIC), help='产物目录，默认 site/public')
    args = parser.parse_args()

    public_dir = Path(args.root)
    errors, warnings = check(public_dir)

    for warning in warnings:
        print('⚠️', warning)

    if errors:
        print('❌ 页面体积门禁未通过：')
        for err in errors:
            print('  -', err)
        print('\n提示：页面不应随数据量线性增长。若数据确实增长，请改为分页/异步加载，'
              '而不是放宽阈值。')
        return 1

    print('✅ 页面体积门禁通过')
    return 0


if __name__ == '__main__':
    sys.exit(main())
