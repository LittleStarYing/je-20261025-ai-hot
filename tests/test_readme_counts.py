import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import update_readme_links as readme_mod

SAMPLE = (
    '[![工具](https://img.shields.io/badge/工具-171-orange)](https://aihot.bt199.com/tools/) '
    '[![模型](https://img.shields.io/badge/模型-87-lightgrey)](https://aihot.bt199.com/models/) '
    '[![Agent](https://img.shields.io/badge/Agent-52-purple)](https://aihot.bt199.com/agents/) '
    '[![新闻](https://img.shields.io/badge/新闻-151-red)](https://aihot.bt199.com/news/)'
    '\n\n- [🛠️ AI工具（171）](https://aihot.bt199.com/tools/)'
    '\n- [🧠 AI模型（87）](https://aihot.bt199.com/models/)'
    '\n- [🤖 AI Agent（52）](https://aihot.bt199.com/agents/)'
    '\n- [📰 AI新闻（151）](https://aihot.bt199.com/news/)'
    '\n- [🏢 AI提供商（22）](https://aihot.bt199.com/providers/)'
)


class ReadmeCountSyncTests(unittest.TestCase):
    def _sync(self, counts):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        data_dir = Path(tmp.name)
        for filename, total in counts.items():
            items = [{'id': f'{filename}-{i}'} for i in range(total)]
            (data_dir / filename).write_text(
                json.dumps(items, ensure_ascii=False), encoding='utf-8'
            )
        with mock.patch.object(readme_mod, 'DATA_DIR', data_dir):
            return readme_mod._sync_counts(SAMPLE)

    def test_badges_and_category_entries_use_live_counts(self):
        text = self._sync({
            'tools.json': 3,
            'models.json': 12,
            'agents.json': 7,
            'news.json': 250,
            'providers.json': 5,
        })
        self.assertIn('badge/工具-3-orange', text)
        self.assertIn('badge/模型-12-lightgrey', text)
        self.assertIn('badge/Agent-7-purple', text)
        self.assertIn('badge/新闻-250-red', text)
        self.assertIn('AI工具（3）', text)
        self.assertIn('AI模型（12）', text)
        self.assertIn('AI Agent（7）', text)
        self.assertIn('AI新闻（250）', text)
        self.assertIn('AI提供商（5）', text)
        # 旧数字不能残留
        for stale in ('badge/模型-87', 'AI模型（87）', 'badge/新闻-151', 'AI新闻（151）'):
            self.assertNotIn(stale, text)

    def test_keeps_links_and_non_count_text(self):
        text = self._sync({'tools.json': 1})
        self.assertIn('](https://aihot.bt199.com/tools/)', text)
        # 未提供数据文件的分类保持原样，不会被清空
        self.assertIn('AI模型（87）', text)

    def test_supports_dict_wrapped_items(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        data_dir = Path(tmp.name)
        (data_dir / 'tools.json').write_text(
            json.dumps({'items': [{'id': 'a'}, {'id': 'b'}]}), encoding='utf-8'
        )
        with mock.patch.object(readme_mod, 'DATA_DIR', data_dir):
            text = readme_mod._sync_counts(SAMPLE)
        self.assertIn('badge/工具-2-orange', text)
        self.assertIn('AI工具（2）', text)


if __name__ == '__main__':
    unittest.main()
