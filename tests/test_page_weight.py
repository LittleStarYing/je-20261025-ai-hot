import json
import re
import tempfile
import unittest
from pathlib import Path

from scripts import check_page_weight as cpw
from scripts import generate_search_index as gsi

ROOT = Path(__file__).resolve().parents[1]


class NoInlineGrowthGuardTests(unittest.TestCase):
    """页面体积必须与数据量解耦：任何内嵌全量数据的地方都会随数据增长。"""

    def _read(self, rel):
        return (ROOT / 'site' / 'layouts' / rel).read_text(encoding='utf-8')

    def test_compare_and_tool_do_not_inline_tools(self):
        for rel in ('_default/compare.html', '_default/tool.html'):
            text = self._read(rel)
            self.assertNotIn(
                'hugo.Data.tools | jsonify', text,
                f'{rel} 又把整个工具库内嵌进 HTML 了（会随工具数量增长）'
            )
            self.assertIn('tools-full.json', text)

    def test_homepage_limits_news_scan(self):
        """首页挑选「必读」时不应遍历全量新闻，否则构建时间随新闻数线性增长。"""
        text = self._read('index.html')
        self.assertIn('range first 800 $news', text)
        self.assertNotIn('range $news }}', text)

    def test_news_index_limit_matches_list_template(self):
        """索引上限与列表页翻页范围必须一致，否则翻到后面取不到数据。"""
        match = re.search(r'\$newsIndexLimit := (\d+)', self._read('_default/list.html'))
        self.assertIsNotNone(match, 'list.html 缺少 $newsIndexLimit')
        self.assertEqual(int(match.group(1)), gsi.NEWS_INDEX_LIMIT)

    def test_shipped_index_respects_news_limit(self):
        index = json.loads(
            (ROOT / 'site' / 'static' / 'search-index.json').read_text(encoding='utf-8')
        )
        self.assertLessEqual(len(index['news']), gsi.NEWS_INDEX_LIMIT)

    def test_generated_data_files_exist_and_are_bounded(self):
        static = ROOT / 'site' / 'static'
        for name in ('search-index.json', 'tools-full.json'):
            path = static / name
            self.assertTrue(path.exists(), f'{name} 未生成（页面异步加载会 404）')
            self.assertLess(path.stat().st_size / 1024, cpw.ASSET_LIMITS_KB[name])


class CheckPageWeightTests(unittest.TestCase):
    """体积门禁本身要能拦住超大页面，也要在正常产物上通过。"""

    def _root(self, overrides=None, skip=()):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        names = list(cpw.PAGE_LIMITS_KB) + list(cpw.ASSET_LIMITS_KB)
        for rel in names:
            if rel in skip:
                continue
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(overrides.get(rel, 'ok') if overrides else 'ok', encoding='utf-8')
        return root

    def test_passes_on_normal_output(self):
        errors, _ = cpw.check(self._root())
        self.assertEqual(errors, [])

    def test_flags_oversized_page(self):
        limit = cpw.PAGE_LIMITS_KB['index.html']
        root = self._root({'index.html': 'x' * int((limit + 50) * 1024)})
        errors, _ = cpw.check(root)
        self.assertTrue(any('index.html' in e for e in errors), errors)

    def test_flags_missing_key_page(self):
        errors, _ = cpw.check(self._root(skip=('index.html',)))
        self.assertTrue(any('缺失' in e for e in errors), errors)

    def test_flags_oversized_asset(self):
        limit = cpw.ASSET_LIMITS_KB['search-index.json']
        root = self._root({'search-index.json': 'x' * int((limit + 100) * 1024)})
        errors, _ = cpw.check(root)
        self.assertTrue(any('search-index.json' in e for e in errors), errors)


if __name__ == '__main__':
    unittest.main()
