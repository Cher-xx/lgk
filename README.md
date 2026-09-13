# 素材灵感库 · React + Vite

基于现有 HTML 视觉与素材数据搭建，优先适配 PC，内容版心最大 1700px。

## 运行

需要 Node.js 20.19+ 或 22.12+，安装依赖后启动：

```sh
npm install
npm run dev
```

也可使用 `pnpm install`、`pnpm dev`。打开终端显示的本地地址。此电脑可双击「启动React预览.cmd」。

## 构建

```sh
npm run build
npm run preview
```

构建产物在 `dist`，仅包含网站所需文件。开发服务以 `web` 为根目录，不向浏览器开放原始项目目录。

## GitHub 与 Cloudflare

可以把本项目整个文件夹提交到 GitHub。`.gitignore` 已排除 `node_modules`、构建产物和 `private-data` 中的本机 API 密钥、Excel 与缓存。

首次部署到 Cloudflare 前，登录 Wrangler：

```sh
pnpm dlx wrangler@4 login
pnpm deploy
```

部署名称由 `wrangler.jsonc` 的 `name` 决定；如该名称已被占用，可自行改为唯一名称。Cloudflare 会将 `dist` 作为静态站点发布。

## 已实现

- 全屏图片首页，标题「让好灵感随时有迹可循」。
- 固定半透明导航与探索入口。
- 原比例图片、最短列瀑布流，搜索、来源、标签、方向筛选与排序。
- 左图右文详情，图片固定显示，右侧信息独立滚动，支持 Esc 与遮罩关闭。
- 收藏与个人收藏视图；逐图片评论、空评论校验、1000 字限制。
- 收藏和评论保存在当前浏览器 localStorage，无需登录；本版本没有服务器评论同步，不同设备之间不共享。

## 更新素材

将影刀图片放入 `image`，将 `landscape.xlsx` 和 `API KEY.txt` 放入 `private-data`，再双击 `更新素材.cmd`。它会完成去重、AI 打标、更新 `materials.js`，并同步 React 网站数据；GitHub Desktop 中提交 `image` 与 `materials.js` 的变更即可。

React 页面代码位于 `web/src.jsx`，新增样式位于 `web/site.css`。同步脚本只复制 materials 数据、图片与旧样式，不复制工作目录内其他文件。
