# AGENTS.md

`xixi` 宝宝喝奶/日常记录应用。根目录是 Vue 3 + Vite 前端；后端在 `xixi_app_docker/`
（FastAPI，同时托管 REST API 和打包后的 `dist/` 前端），数据存在 PostgreSQL。

## 常用命令

- `npm install` / `npm run dev` / `npm run build`
- `npm run build` = `vite build` + 自动把 `dist/` 同步到 `xixi_app_docker/dist/`
  （`scripts/copy-dist.mjs`）；只想出根目录产物时用 `npm run build:web`
- `npm run lint` = `lint:oxlint` + `lint:eslint`，两者都带 `--fix`，**会直接改写文件**
- `npm run format` = prettier 只格式化 `src/`
- 无测试框架。Vue 3 通过 package.json `overrides` 锁在 `beta` 分支，属有意为之，不要改动版本

## 部署与运行方式（前端不与后端分离）

- 前端所有数据都来自 FastAPI 后端（`xixi_app_docker/main.py`），`/api` 前缀 + axios，
  **不经过 Supabase**（见下方陷阱）。后端连的是局域网 PostgreSQL
  `192.168.100.67:5432`（库 `xixi_frontend`，表 `baby_accounts`/`milk_logs`/`food_logs`/`activity_logs`/`growth_logs`/`milestones`），
  连接配置硬编码在 `xixi_app_docker/main.py` 里，注意别泄密。
- vite.config.js 已配置 dev proxy：`npm run dev` 时 `/api` 会转发到
  `http://localhost:8001`，**前提是后端已在本机 8001 端口运行**；否则一样连不上。
  dev 流程：`cd xixi_app_docker && .venv/bin/uvicorn main:app --port 8001`（另一终端）→ `npm run dev`。
  生产流程：`npm run build`（会自动把 dist 同步到 `xixi_app_docker/dist/`）→
  `cd xixi_app_docker && .venv/bin/uvicorn main:app --port 8001`（或 `docker` 构建）。
- Docker：`xixi_app_docker/Dockerfile` 用 `COPY . .` 把整个目录（含 dist）打进镜箱，
  监听 8001；后端兜底返回 `index.html` 交给前端路由。`dist/` 已被 .gitignore 忽略。
- Docker Hub 发布（镜像名 `loooost/xixi-app`，先 `npm run build` 同步 dist）：
  ```sh
  cd xixi_app_docker && docker build -t loooost/xixi-app:latest . && docker push loooost/xixi-app:latest
  ```
  `xixi_app_docker/.dockerignore` 已排除 `xixi-app-v1.tar`/`__pycache__`/`.venv`，别删。

## 本地运行与测试

1. 首次准备后端环境（系统可能没有全局 uvicorn，用 venv）：
   ```sh
   cd xixi_app_docker
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```
   `.venv/` 已在 .gitignore 里。
2. 终端 A：起后端（依赖局域网 PostgreSQL 192.168.100.67 可达，否则 API 报错）：
   ```sh
   cd xixi_app_docker && .venv/bin/uvicorn main:app --port 8001
   ```
3. 终端 B：起前端 `npm run dev`，浏览器打开 vite 打印的地址（如 http://localhost:5174/），
   登录/注册即完成全链路（前端 → vite proxy `/api` → 后端 8001 → PostgreSQL）。
4. 快速验证 proxy 是否转发（后端未起时应为 502，起了应 -> FastAPI 响应）：
   ```sh
   curl -X POST http://localhost:5174/api/login -H 'Content-Type: application/json' \
     -d '{"login_name":"x","password":"y"}'
   ```

## 容易踩坑的点

- `src/api.js` 是统一 API 客户端（axios）和登录态（localStorage `currentAccount`）封装，
  指向本地 FastAPI 的 `/api`。应用从不使用 Supabase，别引入真 Supabase。
- “按天分组/统计”用的是**北京时间（UTC+9）**：`App.vue` 和 `MilkChart.vue` 里都是
  `new Date(x) - 9h` 后用 `toLocaleDateString('sv-SE')` 取 `YYYY-MM-DD`。这是有意为之，
  别当 bug“修”成本地时区。
- 几乎所有 UI/逻辑都在 `src/App.vue` 单文件里（`activeTab` ref 切换
  'milk'/'other'/'growth'/'milestone' 四个 tab）。
  `src/router/index.js` routes 为空，不要引入路由式导航。
- PWA：`main.js` import `virtual:pwa-register`，manifest 在 vite.config.js 里定义，
  图标在 `public/`；只在 `vite build` 时生成 sw。
- 登录/注册密码明文比对、无鉴权后端——现状如此，改动前需明确这是已知的简略实现。