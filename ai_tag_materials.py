"""Qwen vision tagging with validated, resumable per-image cache."""
from pathlib import Path
import base64
import hashlib
import io
import json
import re
import sys
import urllib.request
import urllib.error
from urllib.parse import urlparse
from PIL import Image, ImageOps
from deduplicate_materials import pixel_hash, IMAGE_EXTENSIONS

ROOT = Path(__file__).resolve().parent
PRIVATE = ROOT / 'private-data'
MODEL = 'qwen3-vl-plus'
LABELS = {
    '景观类型': '城市公园、滨水景观、住宅庭院、商业广场、社区花园、校园景观、屋顶花园、生态湿地'.split('、'),
    '设计风格': '现代简约、自然主义、新中式园林、日式禅意、英式自然花园、野趣生态、工业遗址景观'.split('、'),
    '材料与植物': '天然石材、透水铺装、木平台、耐候钢、砾石、景观水体、乡土乔木、观赏草、多年生花境、水生植物'.split('、'),
    '色彩与季相': '自然绿调、大地色系、低饱和配色、银灰叶色、春季繁花、夏季浓荫、秋季暖色、冬季枝干线条'.split('、'),
    '空间功能': '入口迎宾、林下休憩、步行漫游、滨水观景、儿童游乐、户外社交、运动健身、雨水花园、自然教育'.split('、')
}

def config():
    path = PRIVATE / 'API KEY.txt'
    if not path.is_file():
        raise ValueError('缺少 private-data/API KEY.txt，请按 API配置示例.txt 创建配置后再运行。')
    text = path.read_text(encoding='utf-8-sig')
    key = re.search(r'sk-[A-Za-z0-9_.~+/=-]+', text)
    url = re.search(r'https://[^\s\"\'<>]+', text)
    if not key or not url:
        raise ValueError('请在 private-data/API KEY.txt 填写 API_KEY=sk-… 和 BASE_URL=https://…（OpenAI 兼容接口）。')
    endpoint = url.group().rstrip('/,，;；')
    host = urlparse(endpoint).hostname or ''
    if not (host == 'dashscope.aliyuncs.com' or host.endswith('.aliyuncs.com')):
        raise ValueError('URL 必须是阿里云 HTTPS 接口地址。')
    if not endpoint.endswith('/chat/completions'):
        endpoint += '/chat/completions'
    return key.group(), endpoint

def validate(value):
    if not isinstance(value, dict) or set(value) != set(LABELS):
        raise ValueError('模型输出必须恰好包含五个标签维度。')
    for dimension, allowed in LABELS.items():
        tags = value[dimension]
        if not isinstance(tags, list) or len(tags) > 3 or any(not isinstance(t, str) or t not in allowed for t in tags) or len(set(tags)) != len(tags):
            raise ValueError('模型输出含不合法标签、重复标签或超过三个标签。')
    return value

def signature(prompt):
    return hashlib.sha256((MODEL + '\n' + prompt + '\nimage-only-v1').encode()).hexdigest()

def load_cache():
    path = PRIVATE / 'AI打标缓存.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}

def save_cache(cache):
    PRIVATE.mkdir(exist_ok=True)
    path = PRIVATE / 'AI打标缓存.json.tmp'
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding='utf-8')
    path.replace(PRIVATE / 'AI打标缓存.json')

def existing_material_labels():
    """Recover validated labels already published in materials.js without another API call."""
    path = ROOT / 'materials.js'
    if not path.is_file():
        return {}
    try:
        raw = path.read_text(encoding='utf-8-sig')
        records = json.loads(raw.split('=', 1)[1].strip().rstrip(';'))
        return {item['filename']: validate(item['ai_labels']) for item in records
                if isinstance(item, dict) and isinstance(item.get('filename'), str) and 'ai_labels' in item}
    except (ValueError, KeyError, IndexError, json.JSONDecodeError):
        return {}

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def tag(path, prompt, key, endpoint, correction=False):
    if correction:
        prompt += '\n严格纠正：上一轮标签不合规。请逐字从以下白名单选取，每维最多3项，不要组合或改写标签。白名单：' + json.dumps(LABELS, ensure_ascii=False)
        prompt += '\n必须使用这些精确字段，无法确定就保留空数组：' + json.dumps({k: [] for k in LABELS}, ensure_ascii=False) + '\n注意：“材料与植物”是一个字段，“色彩与季相”是一个字段。不要拆分字段。每一项必须是一个独立字符串，不要在字符串内用顿号拼接多个标签。'
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image).convert('RGB')
        image.thumbnail((1600, 1600))
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=90)
    data_url = 'data:image/jpeg;base64,' + base64.b64encode(buffer.getvalue()).decode('ascii')
    body = {'model': MODEL, 'messages': [
        {'role': 'system', 'content': prompt},
        {'role': 'user', 'content': [{'type': 'image_url', 'image_url': {'url': data_url}}, {'type': 'text', 'text': '请对这张图片进行标注，只返回 JSON。'}]}],
        'temperature': 0, 'max_tokens': 1000, 'response_format': {'type': 'json_object'}}
    request = urllib.request.Request(endpoint, data=json.dumps(body).encode(), headers={
        'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=90) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 401:
            raise RuntimeError('阿里云认证失败（HTTP 401）：请在百炼控制台复制有效的 API Key，并确认 BASE_URL 与该密钥的地域、业务空间及套餐类型一致。配置格式通过不代表密钥有效。') from None
        raise RuntimeError(f'阿里云接口返回 HTTP {error.code}，请检查地域、密钥、URL、模型权限或额度。') from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError('网络连接失败或超时，请检查网络后重新运行；已成功的打标会保留。') from None
    try:
        return validate(json.loads(result['choices'][0]['message']['content']))
    except ValueError:
        if not correction:
            print('标签格式未通过检查，自动纠正重试一次……', flush=True)
            return tag(path, prompt, key, endpoint, correction=True)
        value = json.loads(result['choices'][0]['message']['content'])
        if isinstance(value, dict) and set(value) == set(LABELS) and all(isinstance(v, list) for v in value.values()):
            cleaned = {k: list(dict.fromkeys(t for t in value[k] if isinstance(t, str) and t in allowed))[:3] for k, allowed in LABELS.items()}
            print('已移除白名单外、重复或超量标签，只保留模型给出的有效标签。', flush=True)
            return validate(cleaned)
        raise ValueError('模型重试后标签仍不合规，请重新运行。') from None
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        raise ValueError('模型未返回规定的 JSON，未保存该结果，请重新运行。') from None

def main():
    key, endpoint = config()
    if '--check-config' in sys.argv:
        print('AI 配置格式检查通过（未发起请求）。')
        return
    prompt = (ROOT / '提示词.txt').read_text(encoding='utf-8-sig')
    version = signature(prompt)
    cache = load_cache()
    published = existing_material_labels()
    paths = sorted(p for p in (ROOT / 'image').iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS)
    for index, path in enumerate(paths, 1):
        digest = pixel_hash(path)
        cache_key = version + ':' + digest
        if cache_key in cache:
            validate(cache[cache_key]['labels'])
            print(f'[{index}/{len(paths)}] 复用已打标：{path.name}', flush=True)
            continue
        if path.name in published:
            cache[cache_key] = {'model': 'existing-materials', 'hash': digest, 'labels': published[path.name]}
            save_cache(cache)
            print(f'[{index}/{len(paths)}] 复用网站已有标签：{path.name}', flush=True)
            continue
        print(f'[{index}/{len(paths)}] AI 打标：{path.name}', flush=True)
        labels = tag(path, prompt, key, endpoint)
        cache[cache_key] = {'model': MODEL, 'hash': digest, 'labels': labels}
        save_cache(cache)
    print('AI 打标完成。', flush=True)

if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # Never echo credentials, request bodies or raw server responses.
        message = str(error) if isinstance(error, (ValueError, RuntimeError)) else '打标失败，请检查配置文件、图片及缓存是否可读。'
        print(message, file=sys.stderr)
        sys.exit(1)
