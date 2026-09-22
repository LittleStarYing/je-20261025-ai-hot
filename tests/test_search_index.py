import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import generate_search_index as gsi

ROOT = Path(__file__).resolve().parents[1]


class SearchIndexTests(unittest.TestCase):
    def _generate(self, files):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        data_dir = root / 'data'
        data_dir.mkdir(parents=True, exist_ok=True)
        for name, payload in files.items():
            (data_dir / name).write_text(
                json.dumps(payload, ensure_ascii=False), encoding='utf-8'
            )
        output = root / 'site' / 'static' / 'search-index.json'
        tools_full = root / 'site' / 'static' / 'tools-full.json'
        # 两个输出路径都要 isolate：漏掉任何一个都会把仓库里的真实产物写坏
        with mock.patch.object(gsi, 'DATA_DIR', data_dir), \
                mock.patch.object(gsi, 'OUTPUT', output), \
                mock.patch.object(gsi, 'TOOLS_FULL_OUTPUT', tools_full):
            gsi.generate_search_index()
        return json.loads(output.read_text(encoding='utf-8'))

    def test_drops_heavy_fields_and_keeps_search_fields(self):
        index = self._generate({
            'news.json': [{
                'id': 'n1',
                'title': '标题',
                'summary': '摘要',
                'source': '来源',
                'published': '2026-01-01',
                'url': 'https://example.com/a',
                'ai_summary': 'AI 摘要',
                # 这些字段让 news.json 涨到 35MB，绝不能进索引
                'content_text': 'x' * 5000,
                'content_excerpt': 'y' * 5000,
                'content_zh': 'z' * 5000,
            }],
        })
        news = index['news'][0]
        self.assertEqual(news['title'], '标题')
        self.assertEqual(news['id'], 'n1')
        for heavy in ('content_text', 'content_excerpt', 'content_zh'):
            self.assertNotIn(heavy, news)

    def test_skips_empty_values(self):
        index = self._generate({
            'tools.json': [{'id': 't1', 'name': '工具', 'description': '', 'tags': [], 'pricing': None}],
        })
        tool = index['tools'][0]
        self.assertEqual(tool, {'id': 't1', 'name': '工具'})

    def test_all_categories_present_even_when_data_missing(self):
        index = self._generate({})
        self.assertEqual(
            sorted(k for k in index if k != 'generated_at'),
            ['agents', 'models', 'news', 'tools'],
        )

    def test_supports_dict_wrapped_items(self):
        index = self._generate({
            'agents.json': {'items': [{'name': 'Agent', 'url': 'https://example.com'}]},
        })
        self.assertEqual(index['agents'][0]['name'], 'Agent')


class SearchIndexTemplateGuardTests(unittest.TestCase):
    """首页/搜索页内嵌完整 news.json 会让页面膨胀到 70MB，这里守住回归。"""

    TEMPLATES = ('index.html', '_default/search.html')

    def _read(self, name):
        return (ROOT / 'site' / 'layouts' / name).read_text(encoding='utf-8')

    def test_templates_do_not_inline_data_files(self):
        for name in self.TEMPLATES:
            text = self._read(name)
            for pattern in ('site.Data.news | jsonify', 'site.Data.tools | jsonify',
                            'site.Data.models | jsonify', 'site.Data.agents | jsonify'):
                self.assertNotIn(pattern, text, f'{name} 又把大数据内嵌进 HTML 了')

    def test_templates_load_search_index(self):
        for name in self.TEMPLATES:
            self.assertIn('search-index.json', self._read(name))
            self.assertIn('ensureSearchIndex', self._read(name))


class PageWeightGuardTests(unittest.TestCase):
    """守住两个曾经把页面撑大的回归点。"""

    def _list_template(self):
        return (ROOT / 'site' / 'layouts' / '_default' / 'list.html').read_text(encoding='utf-8')

    def _hugo_config(self):
        return (ROOT / 'site' / 'hugo.toml').read_text(encoding='utf-8')

    def test_news_list_only_renders_initial_pages_server_side(self):
        """4000+ 条新闻全量渲染会让 /news/ 达到 2MB 以上。"""
        text = self._list_template()
        self.assertIn('first $initialCount hugo.Data.news', text)
        self.assertNotIn('range $index, $item := hugo.Data.news', text)

    def test_news_list_falls_back_to_search_index(self):
        text = self._list_template()
        self.assertIn('ensureNewsIndex', text)
        self.assertIn('search-index.json', text)

    def test_news_index_carries_title_zh_for_later_pages(self):
        """翻页时用索引渲染，字段缺了会和首屏内容不一致。"""
        index = json.loads(
            (ROOT / 'site' / 'static' / 'search-index.json').read_text(encoding='utf-8')
        )
        self.assertGreater(sum(1 for x in index['news'] if x.get('title_zh')), 0)

    def test_hugo_config_disables_builtin_sitemap(self):
        """static/sitemap.xml（脚本生成的 sitemapindex）不能被 Hugo 自动 sitemap 覆盖。"""
        config = self._hugo_config()
        self.assertIn('disableKinds', config)
        # 必须是顶层键：TOML 中出现在第一个表头之后就会被归进该表而失效
        top_level = []
        for line in config.splitlines():
            if line.lstrip().startswith('['):
                break
            top_level.append(line)
        self.assertIn('disableKinds', '\n'.join(top_level))


if __name__ == '__main__':
    unittest.main()
