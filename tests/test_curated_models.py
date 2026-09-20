import json
import re
import unittest
from pathlib import Path

from scripts import generate_curated_models as gcm

ROOT = Path(__file__).resolve().parents[1]


class ResolveLatestOpenRouterIdTests(unittest.TestCase):
    """OpenRouter 的 :batch 是批量 API 变体，不是独立模型，任何槽位都不能选中。"""

    def _models(self, *entries):
        return {
            mid: {'id': mid, 'name': name, 'created': created}
            for mid, name, created in entries
        }

    def test_base_slot_skips_batch_variant(self):
        models = self._models(
            ('openai/gpt-6-astra:batch', 'OpenAI: GPT-6 Astra (batch)', 200),
            ('openai/gpt-6-astra', 'OpenAI: GPT-6 Astra', 100),
        )
        self.assertEqual(
            gcm.resolve_latest_openrouter_id(models, 'openai', 'gpt', 'base'),
            'openai/gpt-6-astra',
        )

    def test_pro_slot_skips_batch_variant(self):
        models = self._models(
            ('openai/gpt-6-astra-pro:batch', 'OpenAI: GPT-6 Astra Pro (batch)', 200),
            ('openai/gpt-6-astra-pro', 'OpenAI: GPT-6 Astra Pro', 100),
        )
        self.assertEqual(
            gcm.resolve_latest_openrouter_id(models, 'openai', 'gpt', 'pro'),
            'openai/gpt-6-astra-pro',
        )

    def test_returns_none_when_only_batch_exists(self):
        models = self._models(
            ('openai/gpt-6-astra:batch', 'OpenAI: GPT-6 Astra (batch)', 200),
        )
        self.assertIsNone(gcm.resolve_latest_openrouter_id(models, 'openai', 'gpt', 'base'))

    def test_picks_newest_standard_variant(self):
        models = self._models(
            ('openai/gpt-5', 'OpenAI: GPT-5', 100),
            ('openai/gpt-6-astra', 'OpenAI: GPT-6 Astra', 300),
        )
        self.assertEqual(
            gcm.resolve_latest_openrouter_id(models, 'openai', 'gpt', 'base'),
            'openai/gpt-6-astra',
        )


class CleanNameTests(unittest.TestCase):
    def test_strips_arbitrary_provider_prefix(self):
        self.assertEqual(gcm.clean_name('OpenRouter: Fusion', 'OpenRouter'), 'Fusion')
        self.assertEqual(gcm.clean_name('StepFun: Step 3.7 Flash', 'StepFun'), 'Step 3.7 Flash')

    def test_keeps_name_without_prefix(self):
        self.assertEqual(gcm.clean_name('Kimi-K3', 'moonshotai'), 'Kimi-K3')

    def test_falls_back_to_known_prefix_list(self):
        self.assertEqual(gcm.clean_name('OpenAI: GPT-6 Astra'), 'GPT-6 Astra')


class CuratedOutputRegressionTests(unittest.TestCase):
    """守住已发布的精选榜：不再出现批量变体，也不残留 "<厂商>: " 前缀。"""

    def _items(self):
        path = ROOT / 'data' / 'models_curated.json'
        return json.loads(path.read_text(encoding='utf-8'))['items']

    def test_no_batch_variants(self):
        offenders = [i['name'] for i in self._items() if '(batch)' in i['name'] or ':batch' in i['url']]
        self.assertEqual(offenders, [])

    def test_no_uncooked_provider_prefix(self):
        offenders = [
            i['name'] for i in self._items()
            if re.match(r'^[A-Za-z0-9.\- ]+: ', i['name'])
        ]
        self.assertEqual(offenders, [])

    def test_no_duplicate_urls(self):
        urls = [i['url'] for i in self._items()]
        self.assertEqual(len(urls), len(set(urls)))

    def test_models_required_by_quality_gate_present(self):
        blobs = [f"{i['name']} {i['url']}".lower() for i in self._items()]
        for key in ('gpt-5', 'glm-5.2', 'minimax-m3', 'qwen3.7'):
            self.assertTrue(any(key in b for b in blobs), f'缺少 required 模型: {key}')


if __name__ == '__main__':
    unittest.main()
