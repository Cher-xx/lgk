from pathlib import Path
import json, re
from urllib.parse import urlparse
import openpyxl
from PIL import Image
from ai_tag_materials import load_cache, signature, validate
from deduplicate_materials import pixel_hash

ROOT = Path(__file__).resolve().parent
PRIVATE = ROOT / 'private-data'
ai_cache = load_cache()
ai_version = signature((ROOT / '提示词.txt').read_text(encoding='utf-8-sig'))
book = openpyxl.load_workbook(PRIVATE / 'landscape.xlsx', read_only=True, data_only=True)
files = {p.stem: p for p in (ROOT / 'image').iterdir() if p.is_file()}
items, missing = [], []
removed_duplicates = set()
deletion_log = PRIVATE / '去重删除记录.jsonl'
if deletion_log.exists():
    for line in deletion_log.read_text(encoding='utf-8').splitlines():
        try:
            entry = json.loads(line)
            if (ROOT / 'image' / entry['kept']).is_file():
                removed_duplicates.add(Path(entry['deleted']).stem)
        except (ValueError, KeyError):
            continue
for row in book.active.iter_rows(min_row=2, values_only=True):
    if row[0] is None:
        continue
    key = str(row[0]).strip()
    path = files.get(Path(key).stem)
    if not path:
        if Path(key).stem not in removed_duplicates:
            missing.append(key)
        continue
    title, body, url = [str(v or '').replace('\ufeff', '') for v in row[1:4]]
    with Image.open(path) as im:
        width, height = im.size
    host = urlparse(url).hostname or ''
    source = '小红书' if host.endswith('xiaohongshu.com') else 'Pinterest' if 'pinterest.' in host or host == 'pin.it' else '其他'
    tags = list(dict.fromkeys(re.findall(r'#([^\s#\[，,]{2,24})', body)))
    text = title + ' ' + body
    topics = [label for label, words in {'花园庭院':['花园','庭院','竹园'], '建筑空间':['建筑','茶室'], '城市景观':['老街','公园','城市','街区'], '效果图表现':['效果图','渲染'], 'AI 灵感':['midjourney','banana','ai','人工智能']}.items() if any(word in text.lower() for word in words)]
    ai_labels = validate(ai_cache[ai_version + ':' + pixel_hash(path)]['labels'])
    tags = list(dict.fromkeys(tags + [tag for values in ai_labels.values() for tag in values]))
    items.append(dict(id=key, filename=path.name, src='image/'+path.name, title=title, body=body, url=url, source=source, tags=tags, topics=topics, ai_labels=ai_labels, width=width, height=height))
book.close()
temporary = ROOT / 'materials.js.tmp'
temporary.write_text('window.MATERIALS = '+json.dumps(items,ensure_ascii=False)+';\n',encoding='utf-8')
temporary.replace(ROOT / 'materials.js')
print(f'已更新 {len(items)} 张图片。')
if missing:
    print(f'注意：有 {len(missing)} 条记录找不到对应图片，本次未导入：')
    print('\n'.join(missing))
print('网页素材数据已更新，Excel 保留原始记录。')
