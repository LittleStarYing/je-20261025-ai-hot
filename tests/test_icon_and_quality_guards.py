import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.generate_curated_models as gm
from scripts.icon_resolver import resolve_icon


class IconAndQualityGuardTests(unittest.TestCase):
    def test_openrouter_model_uses_provider_icon_not_openrouter_favicon(self):
        item = {
            'name': 'Ling-2.6 1T (free)',
            'provider': 'InclusionAI',
            'url': 'https://openrouter.ai/inclusionai/ling-2.6-1t:free',
        }
        icon = resolve_icon(item, 'model')
        self.assertIn('inclusionai.com', icon)
        self.assertNotIn('openrouter.ai/favicon', icon)

    def test_github_project_uses_owner_avatar_not_github_favicon(self):
        item = {'name': 'Example', 'url': 'https://github.com/owner/repo'}
        self.assertEqual(resolve_icon(item, 'tool'), 'https://github.com/owner.png?size=128')

    def test_provider_uses_curated_provider_icon_not_url_fallback(self):
        item = {'id': 'baidu', 'name': 'Baidu Qianfan', 'url': 'https://cloud.baidu.com/product/wenxinworkshop'}
        icon = resolve_icon(item, 'provider')
        self.assertIn('yiyan.baidu.com', icon)
        self.assertNotIn('aihot.bt199.com/favicon', icon)

    def test_unresolved_item_does_not_hide_regression_with_site_favicon(self):
        item = {'name': 'Unknown Internal', 'url': 'https://example.invalid/no-brand'}
        self.assertNotIn('aihot.bt199.com/favicon', resolve_icon(item, 'model'))

    def test_generate_curated_models_has_ling_and_real_icons_from_fixture_without_mutating_repo_data(self):
        fixture = {
            'data': [
                {'id': 'openai/gpt-6-astra', 'name': 'OpenAI: GPT-6 Astra', 'created': 900, 'context_length': 1000000, 'architecture': {'input_modalities': ['text', 'image'], 'output_modalities': ['text']}},
                {'id': 'openai/gpt-6-astra-pro', 'name': 'OpenAI: GPT-6 Astra Pro', 'created': 910, 'context_length': 1000000, 'architecture': {'input_modalities': ['text', 'image'], 'output_modalities': ['text']}},
                {'id': 'openai/gpt-5.4-image-2', 'name': 'OpenAI: GPT-5.4 Image 2', 'created': 220, 'context_length': 64000, 'architecture': {'input_modalities': ['text', 'image'], 'output_modalities': ['image']}},
                {'id': 'deepseek/deepseek-v3.2', 'name': 'DeepSeek: DeepSeek V3.2', 'created': 300, 'context_length': 128000, 'architecture': {'input_modalities': ['text'], 'output_modalities': ['text']}},
                {'id': 'deepseek/deepseek-v4.1-flash', 'name': 'DeepSeek: DeepSeek V4.1 Flash', 'created': 920, 'context_length': 128000, 'architecture': {'input_modalities': ['text'], 'output_modalities': ['text']}},
                {'id': 'qwen/qwen3.8-max-0902', 'name': 'Qwen: Qwen3.8 Max (0902)', 'created': 930, 'context_length': 1000000, 'architecture': {'input_modalities': ['text'], 'output_modalities': ['text']}},
                {'id': 'xiaomi/mimo-32b', 'name': 'Xiaomi: MiMo 32B', 'created': 300, 'context_length': 128000, 'architecture': {'input_modalities': ['text'], 'output_modalities': ['text']}},
                {'id': 'xiaomi/mimo-v2.5-pro', 'name': 'Xiaomi: MiMo V2.5 Pro', 'created': 500, 'context_length': 128000, 'architecture': {'input_modalities': ['text'], 'output_modalities': ['text']}},
                {'id': 'minimax/minimax-m3', 'name': 'MiniMax: MiniMax M3', 'created': 400, 'context_length': 1000000, 'architecture': {'input_modalities': ['text'], 'output_modalities': ['text']}},
                {'id': 'z-ai/glm-5.3', 'name': 'Z.ai: GLM 5.3', 'created': 940, 'context_length': 1000000, 'architecture': {'input_modalities': ['text'], 'output_modalities': ['text']}},
                {'id': 'z-ai/glm-5.3-flashx', 'name': 'Z.ai: GLM 5.3 FlashX', 'created': 950, 'context_length': 1000000, 'architecture': {'input_modalities': ['text'], 'output_modalities': ['text']}},
                {'id': 'z-ai/glm-5v-turbo', 'name': 'Z.ai: GLM 5V Turbo', 'created': 600, 'context_length': 1000000, 'architecture': {'input_modalities': ['text', 'image'], 'output_modalities': ['text']}},
                {'id': 'google/gemini-3.8-flash', 'name': 'Google: Gemini 3.8 Flash', 'created': 960, 'context_length': 1000000, 'architecture': {'input_modalities': ['text', 'image'], 'output_modalities': ['text']}},
                {'id': 'google/gemini-3-pro-image', 'name': 'Google: Nano Banana Pro (Gemini 3 Pro Image)', 'created': 700, 'context_length': 1000000, 'architecture': {'input_modalities': ['text', 'image'], 'output_modalities': ['image']}},
                {'id': 'google/gemini-3.1-flash-image', 'name': 'Google: Nano Banana 2 (Gemini 3.1 Flash Image)', 'created': 710, 'context_length': 1000000, 'architecture': {'input_modalities': ['text', 'image'], 'output_modalities': ['image']}},
                {'id': 'anthropic/claude-fable-5.1', 'name': 'Anthropic: Claude Fable 5.1', 'created': 970, 'context_length': 1000000, 'architecture': {'input_modalities': ['text'], 'output_modalities': ['text']}},
                {'id': 'anthropic/claude-sonnet-5', 'name': 'Anthropic: Claude Sonnet 5', 'created': 800, 'context_length': 1000000, 'architecture': {'input_modalities': ['text'], 'output_modalities': ['text']}},
                {'id': 'moonshotai/kimi-k2.7-code', 'name': 'MoonshotAI: Kimi K2.7 Code', 'created': 820, 'context_length': 256000, 'architecture': {'input_modalities': ['text'], 'output_modalities': ['text']}},
                {'id': 'nvidia/nemotron-3.5-lightning', 'name': 'NVIDIA: Nemotron 3.5 Lightning', 'created': 880, 'context_length': 128000, 'architecture': {'input_modalities': ['text'], 'output_modalities': ['text']}},
                {'id': 'stepfun/step-3.7-flash', 'name': 'StepFun: Step 3.7 Flash', 'created': 760, 'context_length': 256000, 'architecture': {'input_modalities': ['text'], 'output_modalities': ['text']}},
                {'id': 'openrouter/fusion', 'name': 'OpenRouter: Fusion', 'created': 780, 'context_length': 1000000, 'architecture': {'input_modalities': ['text'], 'output_modalities': ['text']}},
            ]
        }
        with tempfile.TemporaryDirectory() as td:
            temp_dir = Path(td)
            fixture_path = temp_dir / 'openrouter.json'
            fixture_path.write_text(json.dumps(fixture), encoding='utf-8')
            models_path = temp_dir / 'models.json'
            models_path.write_text(json.dumps([
                {'url': 'https://huggingface.co/Qwen/Qwen3-Coder-Next', 'author': 'Qwen', 'display_name': 'Qwen3-Coder-Next', 'created_at': '2026-01-30T00:00:00Z', 'likes': 1000, 'pipeline_tag': 'text-generation'},
                {'url': 'https://huggingface.co/google/gemma-4-31B-it', 'author': 'google', 'display_name': 'gemma-4-31B-it', 'created_at': '2026-03-11T00:00:00Z', 'likes': 800, 'pipeline_tag': 'image-text-to-text'},
                {'url': 'https://huggingface.co/tencent/HY-Embodied-0.5', 'author': 'tencent', 'display_name': 'HY-Embodied-0.5', 'created_at': '2026-04-02T00:00:00Z', 'likes': 700, 'pipeline_tag': 'image-text-to-text'},
                {'url': 'https://huggingface.co/Tongyi-MAI/Z-Image-Turbo', 'author': 'Tongyi-MAI', 'display_name': 'Z-Image-Turbo', 'created_at': '2025-11-25T00:00:00Z', 'likes': 900, 'pipeline_tag': 'text-to-image'},
                {'url': 'https://huggingface.co/Lightricks/LTX-2.5', 'author': 'Lightricks', 'display_name': 'LTX-2.5', 'created_at': '2026-07-23T00:00:00Z', 'likes': 600, 'pipeline_tag': 'image-to-video'},
                {'url': 'https://huggingface.co/Qwen/Qwen3.8-27B', 'author': 'Qwen', 'display_name': 'Qwen3.8-27B', 'created_at': '2026-08-05T00:00:00Z', 'likes': 8600, 'pipeline_tag': 'image-text-to-text'},
                {'url': 'https://huggingface.co/moonshotai/Kimi-K3', 'author': 'moonshotai', 'display_name': 'Kimi-K3', 'created_at': '2026-06-13T00:00:00Z', 'likes': 5500, 'pipeline_tag': 'image-text-to-text'},
                {'url': 'https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash', 'author': 'deepseek-ai', 'display_name': 'DeepSeek-V4-Flash', 'created_at': '2026-04-22T00:00:00Z', 'likes': 1200, 'pipeline_tag': 'text-generation'},
                {'url': 'https://huggingface.co/openai/gpt-oss-120b', 'author': 'openai', 'display_name': 'gpt-oss-120b', 'created_at': '2025-08-04T00:00:00Z', 'likes': 4800, 'pipeline_tag': 'text-generation'},
                {'url': 'https://huggingface.co/microsoft/VibeVoice-ASR', 'author': 'microsoft', 'display_name': 'VibeVoice-ASR', 'created_at': '2026-01-21T00:00:00Z', 'likes': 1090, 'pipeline_tag': 'automatic-speech-recognition'},
                {'url': 'https://huggingface.co/Qwen/Qwen3.8-Flash-Next', 'author': 'Qwen', 'display_name': 'Qwen3.8-Flash-Next', 'created_at': '2026-08-24T00:00:00Z', 'likes': 2900, 'pipeline_tag': 'image-text-to-text'},
                {'url': 'https://huggingface.co/Qwen/Qwen2.5-72B-Instruct', 'author': 'Qwen', 'display_name': 'Qwen2.5-72B-Instruct', 'created_at': '2024-09-01T00:00:00Z', 'likes': 4000, 'pipeline_tag': 'text-generation'},
                {'url': 'https://huggingface.co/deepseek-ai/DeepSeek-V3', 'author': 'deepseek-ai', 'display_name': 'DeepSeek-V3', 'created_at': '2024-12-01T00:00:00Z', 'likes': 5000, 'pipeline_tag': 'text-generation'},
            ], ensure_ascii=False), encoding='utf-8')
            output_path = temp_dir / 'models_curated.json'
            with patch.dict('os.environ', {'OPENROUTER_MODELS_FIXTURE': str(fixture_path)}), \
                 patch.object(gm, 'MODELS_PATH', str(models_path)), \
                 patch.object(gm, 'OUTPUT_PATH', str(output_path)):
                gm.generate_curated_models()

            data = json.loads(output_path.read_text(encoding='utf-8'))

        names = [x['name'] for x in data['items']]
        self.assertTrue(any('GLM 5.3' in name for name in names))
        self.assertIn('DeepSeek V4.1 Flash', names)
        self.assertNotIn('DeepSeek V3.2', names)
        self.assertNotIn('MiMo 32B', names)
        bad_icons = [x for x in data['items'] if 'openrouter.ai/favicon' in x.get('icon_url', '') or 'github.com/favicon' in x.get('icon_url', '')]
        self.assertFalse(bad_icons)


if __name__ == '__main__':
    unittest.main()
