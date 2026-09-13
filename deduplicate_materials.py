"""Scan all image files; optionally remove exact duplicates after verification."""
from pathlib import Path
import hashlib
import json
import struct
import argparse
from datetime import datetime, timezone

import openpyxl
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
PRIVATE = ROOT / 'private-data'
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff'}


def pixel_hash(path):
    with Image.open(path) as image:
        pixels = ImageOps.exif_transpose(image).convert('RGBA')
        return hashlib.sha256(struct.pack('>II', *pixels.size) + pixels.tobytes()).hexdigest()


def delete_duplicates(inventory, root=ROOT):
    image_root = (Path(root) / 'image').resolve()
    deleted = []
    for group in inventory['groups']:
        keeper = (image_root / group['representative']).resolve()
        if keeper.parent != image_root or pixel_hash(keeper) != group['hash']:
            raise RuntimeError('保留图片已发生变化，停止删除，请等待爬取结束后重试。')
        for name in group['files'][1:]:
            target = (image_root / name).resolve()
            if target.parent != image_root or target == keeper:
                raise RuntimeError('删除路径不在图片目录内，已停止。')
            if pixel_hash(target) != group['hash']:
                raise RuntimeError('待删除图片已发生变化，已停止。')
            entry = {'time': datetime.now(timezone.utc).isoformat(), 'deleted': name,
                     'kept': keeper.name, 'hash': group['hash']}
            # Open the log before deleting so permission failures do not lose the audit.
            PRIVATE.mkdir(exist_ok=True)
            with (PRIVATE / '去重删除记录.jsonl').open('a', encoding='utf-8') as log:
                target.unlink()
                log.write(json.dumps(entry, ensure_ascii=False) + '\n')
                log.flush()
            deleted.append(entry)
            print(f'保留 {keeper.name}，已删除重复图片 {name}')
    return deleted


def build_inventory(root=ROOT):
    root = Path(root)
    files = {p.name.casefold(): p for p in (root / 'image').iterdir()
             if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS}
    by_stem = {}
    for path in files.values():
        by_stem.setdefault(path.stem.casefold(), []).append(path)
    workbook = openpyxl.load_workbook(PRIVATE / 'landscape.xlsx', read_only=True, data_only=True)
    groups, hashes, missing, ambiguous = {}, {}, [], []
    try:
        for row_number, row in enumerate(workbook.active.iter_rows(min_row=2, values_only=True), 2):
            if not row or row[0] is None:
                continue
            key = str(row[0]).strip()
            if isinstance(row[0], float) and row[0].is_integer():
                key = str(int(row[0]))
            name = Path(key).name
            exact = files.get(name.casefold())
            matches = [exact] if exact else by_stem.get(Path(name).stem.casefold(), [])
            if not matches:
                missing.append({'row': row_number, 'filename': key})
                continue
            if len(matches) != 1:
                ambiguous.append({'row': row_number, 'filename': key,
                                  'matches': [p.name for p in matches]})
                continue
            path = matches[0]
            if path.name not in hashes:
                # Pixel hash ignores JPEG metadata but retains exact visual pixels.
                # Similar-looking pictures with different pixels remain separate.
                hashes[path.name] = pixel_hash(path)
            digest = hashes[path.name]
            group = groups.setdefault(digest, {'hash': digest, 'representative': path.name, 'files': [], 'rows': []})
            if path.name not in group['files']:
                group['files'].append(path.name)
            group['rows'].append(row_number)
    finally:
        workbook.close()
    # Excel determines which existing material to keep first, but never limits
    # the scan: Explorer copies and new files without rows must also be hashed.
    unlisted = sorted((path for path in files.values() if path.name not in hashes),
                      key=lambda path: (path.stat().st_ctime_ns, path.name.casefold()))
    for path in unlisted:
        digest = pixel_hash(path)
        hashes[path.name] = digest
        group = groups.setdefault(digest, {'hash': digest, 'representative': path.name,
                                          'files': [], 'rows': []})
        group['files'].append(path.name)
    return {'algorithm': 'sha256-exif-oriented-rgba-pixels-v1',
            'matched_files': len(hashes), 'unique_images': len(groups),
            'duplicate_files': sum(len(g['files']) - 1 for g in groups.values()),
            'groups': list(groups.values()), 'missing': missing, 'ambiguous': ambiguous}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--delete', action='store_true', help='扫描整个 image 文件夹，优先保留表格中的原图，删除完全重复的副本')
    args = parser.parse_args()
    inventory = build_inventory()
    if args.delete:
        inventory['deleted'] = delete_duplicates(inventory)
    PRIVATE.mkdir(exist_ok=True)
    output = PRIVATE / '素材去重报告.json'
    temporary = output.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(output)
    print(f"扫描 {inventory['matched_files']} 张图片，保留 {inventory['unique_images']} 份独立素材，识别 {inventory['duplicate_files']} 张重复图片。")
    print('Excel 保留原始记录。' if args.delete else '仅生成去重清单，未删除原图、未修改 Excel 或网站数据。')
    if inventory['missing'] or inventory['ambiguous']:
        print('部分记录缺少图片或存在同名文件，请查看 private-data/素材去重报告.json。')


if __name__ == '__main__':
    main()
