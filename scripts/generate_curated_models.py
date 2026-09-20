#!/usr/bin/env python3
"""生成精选模型榜单：最前沿 / 最热门 / 最实用，而不是模型垃圾堆。"""

import json
import os
import re
import urllib.request
from datetime import datetime, timezone

try:
    from scripts.icon_resolver import resolve_icon
except ModuleNotFoundError:  # script execution from repo root
    from icon_resolver import resolve_icon

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
MODELS_PATH = os.path.join(DATA_DIR, 'models.json')
OUTPUT_PATH = os.path.join(DATA_DIR, 'models_curated.json')
OPENROUTER_URL = 'https://openrouter.ai/api/v1/models'

CATEGORY_ORDER = [
    ('top', '🔥 顶级通用大模型', '现在最值得关注、综合能力最强的一线模型'),
    ('coding', '💻 编程最强模型', '写代码、改代码、做 Agent 开发最常用的一批模型'),
    ('multimodal', '👁️ 多模态主力模型', '图文理解、视觉问答、复杂输入处理的主力模型'),
    ('image', '🎨 图像生成主力', '当前最常用、效果最稳的一线生图模型'),
    ('video', '🎬 视频生成主力', '当下最值得关注的视频生成模型与工作流主力'),
    ('open', '🌍 开源旗舰模型', '社区采用度高、真正有人用的开源主力模型'),
    ('watch', '🧪 值得关注的新锐模型', '还在快速爬升、值得盯着看的新一代模型'),
]

CURATED_ITEMS = [
    # 顶级通用
    {'category': 'top', 'source': 'openrouter-latest', 'provider_prefix': 'openai', 'family': 'gpt', 'variant': 'base', 'label': '综合王者', 'why': 'OpenAI 最新一线通用主力，推理、写作、执行力都很强'},
    {'category': 'top', 'source': 'openrouter', 'id': 'anthropic/claude-fable-5.1', 'label': '长文与复杂任务', 'why': 'Anthropic 当前旗舰，2026-09-01 发布，复杂任务稳定性强，长上下文和专业写作很能打'},
    {'category': 'top', 'source': 'openrouter', 'id': 'z-ai/glm-5.3', 'label': '国产主力', 'why': '智谱当前一代通用模型，2026-08-18 发布，编程能力较 5.2 明显提升'},
    {'category': 'top', 'source': 'openrouter', 'id': 'deepseek/deepseek-v4.1-flash', 'label': '国产旗舰', 'why': 'DeepSeek 当前主力：官方已把 V4-Pro 的请求全部路由到 V4.1-Flash，速度与性价比更优'},
    {'category': 'top', 'source': 'openrouter', 'id': 'minimax/minimax-m3', 'label': '国产长上下文主力', 'why': 'MiniMax 最新 M3，2026-05-31 发布，国产一线主力'},
    {'category': 'top', 'source': 'openrouter', 'id': 'qwen/qwen3.8-max-0902', 'label': '国产编码主力', 'why': '通义千问当前旗舰，2026-09-03 的 3.8 Max 快照，1M 上下文，代码与通用兼顾'},
    {'category': 'top', 'source': 'openrouter', 'id': 'google/gemini-3.8-flash', 'label': '谷歌新锐', 'why': 'Google 当前最新 Flash 线，2026-09-02 发布，速度快、单价低'},

    # 编程
    {'category': 'coding', 'source': 'openrouter-latest', 'provider_prefix': 'openai', 'family': 'gpt', 'variant': 'pro', 'label': '重度编码', 'why': 'OpenAI 最新 Pro 线，适合复杂工程任务和严肃编程场景'},
    {'category': 'coding', 'source': 'openrouter', 'id': 'anthropic/claude-sonnet-5', 'label': '开发者高频', 'why': 'Claude Code 生态当前底座，2026-06-30 发布，真实开发采用广'},
    {'category': 'coding', 'source': 'openrouter', 'id': 'moonshotai/kimi-k2.7-code', 'label': 'Kimi 编程线', 'why': '月之暗面编码专用线当前版本（2026-06-12），通用旗舰 K3 见开源榜'},
    {'category': 'coding', 'source': 'huggingface', 'url': 'https://huggingface.co/Qwen/Qwen3-Coder-Next', 'label': '开源代码旗舰', 'why': '开源阵营里实用度高，开发者关注度高'},

    # 多模态
    {'category': 'multimodal', 'source': 'openrouter-latest', 'provider_prefix': 'openai', 'family': 'gpt', 'variant': 'image', 'label': '图文一体', 'why': 'OpenAI 最新图像/多模态模型，适合复杂多模态工作流'},
    {'category': 'multimodal', 'source': 'openrouter', 'id': 'z-ai/glm-5v-turbo', 'label': '视觉国产主力', 'why': '国产视觉多模态里很值得关注'},
    {'category': 'multimodal', 'source': 'huggingface', 'url': 'https://huggingface.co/google/gemma-4-31B-it', 'label': '开源多模态热门', 'why': 'Google 阵营近期开源关注度很高'},
    {'category': 'multimodal', 'source': 'huggingface', 'url': 'https://huggingface.co/tencent/HY-Embodied-0.5', 'label': '具身方向', 'why': '具身智能方向里值得盯的代表模型'},

    # 图像生成
    {'category': 'image', 'source': 'openrouter-latest', 'provider_prefix': 'openai', 'family': 'gpt', 'variant': 'image', 'label': '最新 GPT 图像', 'why': 'OpenAI 最新图像生成模型，文字渲染和综合生成能力都很强'},
    {'category': 'image', 'source': 'huggingface', 'url': 'https://huggingface.co/Tongyi-MAI/Z-Image-Turbo', 'label': '开源生图新主力', 'why': '通义新一代开源生图模型，是当前开源图像方向更值得看的一档'},
    {'category': 'image', 'source': 'huggingface', 'url': 'https://huggingface.co/black-forest-labs/FLUX.1-Kontext-dev', 'label': '编辑工作流主力', 'why': 'Kontext 系列更贴近当前图像编辑与工作流场景，实用性高'},
    {'category': 'image', 'source': 'openrouter', 'id': 'google/gemini-3-pro-image', 'label': '谷歌图像主力', 'why': 'Nano Banana Pro，Google 图像生成主力线，国内用户视角不能缺'},
    {'category': 'image', 'source': 'openrouter', 'id': 'google/gemini-3.1-flash-image', 'label': '轻量图像快模', 'why': 'Nano Banana 2，适合轻量快速出图与产品化场景'},

    # 视频生成
    {'category': 'video', 'source': 'manual', 'name': 'Seedance 2.5', 'provider': 'ByteDance Seed', 'url': 'https://seed.bytedance.com/', 'freshness': '', 'badge': '最新视频王炸', 'why': '字节当前视频主力，2026-08 上线，单次可生成 30 秒连续片段', 'meta': '官方发布', 'tags': ['视频生成', '原生音频']},
    {'category': 'video', 'source': 'manual', 'name': 'Kling 3.0', 'provider': '快手可灵', 'url': 'https://app.klingai.com/global/', 'freshness': '', 'badge': '国内视频主力', 'why': '可灵当前 3.0，智能分镜与原生音画同步，国内使用面很大', 'meta': '官网可用', 'tags': ['视频生成']},
    {'category': 'video', 'source': 'manual', 'name': 'Runway Gen-4.5', 'provider': 'Runway', 'url': 'https://runway.com/research/introducing-runway-gen-4.5', 'freshness': '', 'badge': '国际视频主力', 'why': 'Runway 当前最新视频模型，运动质量与提示遵循度都有提升', 'meta': '官方发布', 'tags': ['视频生成']},
    {'category': 'video', 'source': 'huggingface', 'url': 'https://huggingface.co/Lightricks/LTX-2.5', 'label': '开源视频新锐', 'why': 'Lightricks 当前开源视频线，2026-08 发布，开源阵营里热度最高的一档'},

    # 开源旗舰（只放当前代际仍在被广泛采用的开源模型，换代后被替换）
    {'category': 'open', 'source': 'huggingface', 'url': 'https://huggingface.co/Qwen/Qwen3.8-27B', 'label': '开源通用王者', 'why': 'Qwen 当前代际开源主力，点赞与采用度都是新模型里最高的一档'},
    {'category': 'open', 'source': 'huggingface', 'url': 'https://huggingface.co/moonshotai/Kimi-K3', 'label': '开源新热门', 'why': '月之暗面最新开源线，讨论度与关注度都很高'},
    {'category': 'open', 'source': 'huggingface', 'url': 'https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash', 'label': '开源推理主力', 'why': 'DeepSeek 开源线当前主力（V4-Pro 已被官方路由到 V4.1-Flash）'},
    {'category': 'open', 'source': 'huggingface', 'url': 'https://huggingface.co/openai/gpt-oss-120b', 'label': 'OpenAI 开源线', 'why': 'OpenAI 的开放权重模型，社区采用面很大'},
    {'category': 'open', 'source': 'huggingface', 'url': 'https://huggingface.co/microsoft/VibeVoice-ASR', 'label': '语音识别新标杆', 'why': '接替 Whisper 成为当前开源 ASR 里更值得看的一档'},

    # 新锐关注
    {'category': 'watch', 'source': 'openrouter', 'id': 'openrouter/fusion', 'label': 'OpenRouter 新线', 'why': 'OpenRouter 自研 Fusion 模型，2026-06-13 发布，值得关注'},
    {'category': 'watch', 'source': 'openrouter', 'id': 'stepfun/step-3.7-flash', 'label': '阶跃星辰新锐', 'why': '阶跃星辰最新 Step 3.7 Flash，2026-05-28 发布'},
    {'category': 'watch', 'source': 'openrouter', 'id': 'nvidia/nemotron-3.5-lightning', 'label': 'NVIDIA 新动向', 'why': 'NVIDIA 最新开源线，2026-08-11 发布，面向常驻 Agent 场景'},
    {'category': 'watch', 'source': 'openrouter', 'id': 'z-ai/glm-5.3-flashx', 'label': '国产最新发布', 'why': '智谱 2026-09-18 刚发布的 FlashX 线，值得盯着看'},
    {'category': 'watch', 'source': 'huggingface', 'url': 'https://huggingface.co/Qwen/Qwen3.8-Flash-Next', 'label': 'Qwen 新代际', 'why': 'Qwen3.8 开源线里最新发布的一档，热度上升中'},
]

BANNED_HF_AUTHORS = {
    'alwaysgood', 'apocalypseparty', 'quixiai', 'mats-10-sprint-cs-jb', 'flwrlabs', 'rta-ailabs', 'z-lab'
}

MIN_HF_LIKES = 300

OPENROUTER_ALLOWED_IDS = {item['id'] for item in CURATED_ITEMS if item['source'] == 'openrouter'}
HF_ALLOWED_URLS = {item['url'] for item in CURATED_ITEMS if item['source'] == 'huggingface'}



def fetch_openrouter_models():
    fixture = os.environ.get('OPENROUTER_MODELS_FIXTURE')
    if fixture:
        with open(fixture, 'r', encoding='utf-8') as f:
            payload = json.load(f)
        data = payload.get('data', payload) if isinstance(payload, dict) else payload
        return {m['id']: m for m in data}

    req = urllib.request.Request(OPENROUTER_URL, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)['data']

    # Keep a local snapshot so deployment/cron runs never regress to stale or fake data
    # when OpenRouter is briefly unavailable, and so site/data stays in sync.
    snapshot_path = os.path.join(DATA_DIR, 'openrouter_models_snapshot.json')
    with open(snapshot_path, 'w', encoding='utf-8') as f:
        json.dump({'data': data, 'updated_at': datetime.now(timezone.utc).isoformat()}, f, ensure_ascii=False, indent=2)
    return {m['id']: m for m in data}


def load_local_models():
    with open(MODELS_PATH, 'r', encoding='utf-8') as f:
        items = json.load(f)

    filtered = []
    for m in items:
        author = (m.get('author') or '').lower()
        likes = m.get('likes', 0) or 0
        url = m.get('url')
        if url in HF_ALLOWED_URLS:
            filtered.append(m)
            continue
        if author in BANNED_HF_AUTHORS:
            continue
        if likes < MIN_HF_LIKES:
            continue
        filtered.append(m)

    return {m.get('url'): m for m in filtered}


def fmt_date(ts):
    if not ts:
        return ''
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%Y-%m-%d')


def clean_name(name, provider=None):
    # OpenRouter 的模型名会带 "<厂商>: " 前缀，例如 "OpenRouter: Fusion"、
    # "StepFun: Step 3.7 Flash"。按实际 provider 剥离可覆盖任意厂商，
    # 不必维护固定前缀列表。
    out = name or ''
    if provider and out.lower().startswith(provider.lower() + ':'):
        out = out[len(provider) + 1:]
    prefixes = ['OpenAI: ', 'Anthropic: ', 'Google: ', 'DeepSeek: ', 'Qwen: ', 'Baidu: ', 'ByteDance Seed: ', 'MoonshotAI: ', 'Z.ai: ', 'MiniMax: ', 'Xiaomi: ', 'Mistral: ', 'Meta: ', 'xAI: ', 'NVIDIA: ', 'Amazon: ']
    for p in prefixes:
        if out.startswith(p):
            out = out[len(p):]
            break
    return out.replace('  ', ' ').strip()


def provider_label_from_model(model):
    name = model.get('name') or ''
    if ':' in name:
        return name.split(':', 1)[0].strip()
    model_id = model.get('id') or ''
    prefix = model_id.split('/')[0] if '/' in model_id else model_id
    return prefix.replace('-', ' ').title()



ARCHIVE_VARIANT_KEYWORDS = {
    'pro': ['pro'],
    'plus': ['plus'],
    'flash': ['flash'],
    'image': ['image'],
    'base': [],
}

STALE_VARIANT_KEYWORDS = ['mini', 'nano', 'chat', 'audio', 'codex', 'flash']

# OpenRouter 用 ":batch" 表示批量 API 变体（离线批处理、单价更低），它不是独立
# 模型。这些变体的 created 时间常常不晚于标准版，按时间倒序会被误当成「最新
# 模型」选进榜单，所以任何槽位都要提前排除。
NON_MODEL_VARIANT_KEYWORDS = [':batch', '(batch)']


def openrouter_created(model):
    return model.get('created') or 0


def resolve_latest_openrouter_id(openrouter_map, provider_prefix, family='gpt', variant='base'):
    provider_prefix = provider_prefix.lower().rstrip('/')
    family = family.lower()
    variant = variant.lower()
    wanted = ARCHIVE_VARIANT_KEYWORDS.get(variant, [])
    candidates = []
    for model_id, model in openrouter_map.items():
        low_id = model_id.lower()
        low_name = (model.get('name') or '').lower()
        blob = f"{low_id} {low_name}"
        if not low_id.startswith(provider_prefix + '/'):
            continue
        if family not in blob:
            continue
        if any(k in blob for k in NON_MODEL_VARIANT_KEYWORDS):
            continue
        if variant == 'base' and any(k in blob for k in STALE_VARIANT_KEYWORDS + ['pro', 'image']):
            continue
        if wanted and not any(k in blob for k in wanted):
            continue
        candidates.append((openrouter_created(model), model_id))
    if not candidates:
        return None
    return max(candidates)[1]


def materialize_latest_specs(specs, openrouter_map):
    out = []
    for spec in specs:
        if spec.get('source') != 'openrouter-latest':
            out.append(spec)
            continue
        model_id = resolve_latest_openrouter_id(
            openrouter_map,
            spec['provider_prefix'],
            spec.get('family', ''),
            spec.get('variant', 'base'),
        )
        if not model_id:
            continue
        resolved = dict(spec)
        resolved['source'] = 'openrouter'
        resolved['id'] = model_id
        resolved['auto_resolved'] = True
        out.append(resolved)
    return out


def archive_superseded_openrouter_specs(specs, openrouter_map):
    latest_by_slot = {}
    for spec in specs:
        if spec.get('source') != 'openrouter':
            continue
        mid = spec.get('id', '')
        provider = mid.split('/')[0] if '/' in mid else ''
        name_blob = f"{mid} {(openrouter_map.get(mid) or {}).get('name', '')}".lower()
        if provider == 'openai' and 'gpt' in name_blob:
            if 'image' in name_blob:
                slot = ('openai', 'gpt', 'image')
            elif 'pro' in name_blob:
                slot = ('openai', 'gpt', 'pro')
            elif any(k in name_blob for k in STALE_VARIANT_KEYWORDS):
                continue
            else:
                slot = ('openai', 'gpt', 'base')
            current = latest_by_slot.get(slot)
            if current is None or openrouter_created(openrouter_map.get(mid, {})) > openrouter_created(openrouter_map.get(current, {})):
                latest_by_slot[slot] = mid
    archived = []
    for spec in specs:
        mid = spec.get('id', '')
        if spec.get('source') != 'openrouter' or not mid.startswith('openai/'):
            archived.append(spec)
            continue
        name_blob = f"{mid} {(openrouter_map.get(mid) or {}).get('name', '')}".lower()
        slot = None
        if 'gpt' in name_blob:
            if 'image' in name_blob:
                slot = ('openai', 'gpt', 'image')
            elif 'pro' in name_blob:
                slot = ('openai', 'gpt', 'pro')
            elif any(k in name_blob for k in STALE_VARIANT_KEYWORDS):
                slot = None
            else:
                slot = ('openai', 'gpt', 'base')
        if slot and latest_by_slot.get(slot) and latest_by_slot[slot] != mid:
            continue
        archived.append(spec)
    return archived

def _variant_signature(model_id):
    """抹掉版本号，只保留厂商与产品线结构，用于判断两个模型是否属于同一条线。
    claude-opus-4.8 与 claude-opus-5 同为 claude-opus-；
    gemini-3.5-flash 与 gemini-3.8-flash 同为 gemini--flash。
    """
    return re.sub(r'\d+(\.\d+)*', '', model_id.split('/')[-1].lower())


def find_superseded_items(items, openrouter_map):
    """列出已被同厂商同产品线更新版本取代的榜单条目。

    openrouter-latest 槽位会自动跟进厂商发版，写死 id 的条目不会；
    每轮生成时把这类条目报出来，避免榜单悄悄停在旧版本。
    """
    stale = []
    for item in items:
        url = item.get('url') or ''
        if 'openrouter.ai/' not in url:
            continue
        mid = url.split('openrouter.ai/', 1)[1]
        current = openrouter_map.get(mid)
        if not current:
            continue
        provider = mid.split('/')[0]
        signature = _variant_signature(mid)
        newer = [
            model for model in openrouter_map.values()
            if model['id'].startswith(provider + '/')
            and _variant_signature(model['id']) == signature
            and (model.get('created') or 0) > (current.get('created') or 0)
            and not any(k in model['id'].lower() for k in NON_MODEL_VARIANT_KEYWORDS)
        ]
        if newer:
            newest = max(newer, key=lambda model: model.get('created') or 0)
            stale.append(f"{item['name']} → {newest['id']} ({fmt_date(newest.get('created'))})")
    return stale


def auto_discovery_series_key(model_id, model):
    low = f"{model_id} {(model.get('name') or '')}".lower()
    prefix = model_id.split('/')[0] if '/' in model_id else model_id
    if prefix == 'xiaomi' or 'mimo' in low:
        return ('xiaomi', 'mimo')
    return (prefix, model_id.split('/')[-1].split('-')[0])


def build_auto_discovery_specs(openrouter_map):
    specs = []
    for model_id, model in openrouter_map.items():
        low = f"{model_id} {(model.get('name') or '')}".lower()
        if 'xiaomi/' in model_id or 'mimo' in low:
            specs.append({
                'category': 'watch',
                'source': 'openrouter',
                'id': model_id,
                'label': '自动发现',
                'why': '从 OpenRouter 自动发现的高关注国产模型，应该进入候选榜单',
            })
    specs.sort(key=lambda x: openrouter_map[x['id']].get('created', 0), reverse=True)
    dedup = []
    seen_ids = set()
    seen_series = set()
    for spec in specs:
        if spec['id'] in seen_ids:
            continue
        seen_ids.add(spec['id'])
        series = auto_discovery_series_key(spec['id'], openrouter_map[spec['id']])
        if series in seen_series:
            continue
        seen_series.add(series)
        dedup.append(spec)
    return dedup


def merge_curated_items(base_items, auto_items):
    merged = list(base_items)
    existing_or_ids = {item.get('id') for item in base_items if item.get('source') == 'openrouter'}
    existing_urls = {item.get('url') for item in base_items if item.get('source') == 'huggingface'}
    for item in auto_items:
        if item.get('source') == 'openrouter' and item.get('id') in existing_or_ids:
            continue
        if item.get('source') == 'huggingface' and item.get('url') in existing_urls:
            continue
        merged.append(item)
    return merged


def modalities_from_or(model):
    arch = model.get('architecture') or {}
    merged = set((arch.get('input_modalities') or []) + (arch.get('output_modalities') or []))
    labels = []
    if 'text' in merged:
        labels.append('文本')
    if 'image' in merged:
        labels.append('图像')
    if 'video' in merged:
        labels.append('视频')
    if 'audio' in merged:
        labels.append('音频')
    if len(merged) >= 2:
        labels.insert(0, '多模态')
    # dedupe keep order
    seen = set()
    out = []
    for x in labels:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out[:4]


def format_context_meta(context_length):
    if not context_length:
        return '商用主力模型'
    if context_length >= 1_000_000:
        m = context_length / 1_000_000
        if abs(m - round(m)) < 1e-9:
            return f"{int(round(m))}M 上下文"
        return f"{m:.1f}M 上下文"
    return f"{context_length // 1000}K 上下文"


def build_item(spec, openrouter_map, hf_map):
    if spec['source'] == 'openrouter':
        model = openrouter_map[spec['id']]
        provider = provider_label_from_model(model)
        item = {
            'category': spec['category'],
            'source': 'OpenRouter',
            'name': clean_name(model.get('name') or spec['id'], provider),
            'provider': provider,
            'url': f"https://openrouter.ai/{spec['id']}",
            'freshness': fmt_date(model.get('created')),
            'badge': spec['label'],
            'why': spec['why'],
            'meta': format_context_meta(model.get('context_length')),
            'tags': modalities_from_or(model),
        }
        item['icon_url'] = resolve_icon(item, 'model')
        return item

    if spec['source'] == 'manual':
        item = {
            'category': spec['category'],
            'source': '官方补充',
            'name': spec['name'],
            'provider': spec['provider'],
            'url': spec['url'],
            'freshness': spec.get('freshness', ''),
            'badge': spec['badge'],
            'why': spec['why'],
            'meta': spec.get('meta', '官方发布'),
            'tags': spec.get('tags', []),
        }
        item['icon_url'] = resolve_icon(item, 'model')
        return item

    hf = hf_map[spec['url']]
    tags = []
    if hf.get('pipeline_tag') == 'text-generation':
        tags.append('文本')
    elif hf.get('pipeline_tag') == 'text-to-image':
        tags.append('图像生成')
    elif hf.get('pipeline_tag') == 'image-text-to-text':
        tags.append('多模态')
    elif hf.get('pipeline_tag') == 'automatic-speech-recognition':
        tags.append('语音识别')
    elif hf.get('pipeline_tag') == 'image-to-video':
        tags.append('视频生成')
    elif hf.get('pipeline_tag') == 'image-to-3d':
        tags.append('3D')

    item = {
        'category': spec['category'],
        'source': 'HuggingFace',
        'name': hf.get('display_name') or hf.get('name', '').split('/')[-1],
        'provider': hf.get('author', ''),
        'url': hf.get('url'),
        'freshness': (hf.get('created_at') or '')[:10],
        'badge': spec['label'],
        'why': spec['why'],
        'meta': f"❤️ {hf.get('likes', 0)}" if hf.get('likes') else '开源热门模型',
        'tags': tags,
    }
    item['icon_url'] = resolve_icon(item, 'model')
    return item


def generate_curated_models():
    openrouter_map = fetch_openrouter_models()
    hf_map = load_local_models()

    base_specs = materialize_latest_specs(CURATED_ITEMS, openrouter_map)
    curated_specs = merge_curated_items(base_specs, build_auto_discovery_specs(openrouter_map))
    curated_specs = archive_superseded_openrouter_specs(curated_specs, openrouter_map)

    items = []
    for spec in curated_specs:
        try:
            items.append(build_item(spec, openrouter_map, hf_map))
        except KeyError:
            continue

    # 同一个模型可能被多个分类引用（例如 OpenAI 图像模型同时属于多模态和图像），
    # 按分类顺序去重，避免同一张卡片在页面上出现两次。
    seen_urls = set()
    deduped = []
    for item in items:
        url = item.get('url')
        if url in seen_urls:
            continue
        seen_urls.add(url)
        deduped.append(item)
    items = deduped

    superseded = find_superseded_items(items, openrouter_map)
    if superseded:
        print(f'  ⚠️ {len(superseded)} 条已被同厂商更新版本取代，建议跟进：')
        for line in superseded[:8]:
            print(f'     - {line}')

    out = {
        'updated_at': datetime.now().isoformat(),
        'total': len(items),
        'categories': [
            {
                'id': cid,
                'name': name,
                'subtitle': subtitle,
                'count': sum(1 for x in items if x['category'] == cid),
            }
            for cid, name, subtitle in CATEGORY_ORDER
            if any(x['category'] == cid for x in items)
        ],
        'items': items,
    }

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    summary = f'生成精选模型榜单 {len(items)} 条'
    if superseded:
        summary += f'（{len(superseded)} 条待跟进新版）'
    return summary


if __name__ == '__main__':
    print(generate_curated_models())
