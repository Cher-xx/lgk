import { mkdir, copyFile, readFile, writeFile } from 'node:fs/promises';
const base = new URL('../', import.meta.url);
const raw = await readFile(new URL('materials.js', base), 'utf8');
const items = JSON.parse(raw.slice(raw.indexOf('=') + 1).trim().replace(/;$/, ''));
await mkdir(new URL('web/public/image/', base), { recursive: true });
for (const item of items) {
  if (!/^image\/[\w.-]+$/.test(item.src)) throw new Error('Invalid image path');
  await copyFile(new URL(item.src, base), new URL('web/public/' + item.src, base));
}
await writeFile(new URL('web/materials.json', base), JSON.stringify(items));
await copyFile(new URL('style.css', base), new URL('web/legacy.css', base));
console.log(`已同步 ${items.length} 张灵感素材`);
