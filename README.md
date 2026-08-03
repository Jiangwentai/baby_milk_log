# baby_milk_log

This template should help get you started developing with Vue 3 in Vite.

## Recommended IDE Setup

[VS Code](https://code.visualstudio.com/) + [Vue (Official)](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Recommended Browser Setup

- Chromium-based browsers (Chrome, Edge, Brave, etc.):
  - [Vue.js devtools](https://chromewebstore.google.com/detail/vuejs-devtools/nhdogjmejiglipccpnnnanhbledajbpd)
  - [Turn on Custom Object Formatter in Chrome DevTools](http://bit.ly/object-formatters)
- Firefox:
  - [Vue.js devtools](https://addons.mozilla.org/en-US/firefox/addon/vue-js-devtools/)
  - [Turn on Custom Object Formatter in Firefox DevTools](https://fxdx.dev/firefox-devtools-custom-object-formatters/)

## 本地运行与测试

本应用前后端不分离：后端（`xixi_app_docker/`，FastAPI）同时提供 `/api` 接口和前端页面。
前端所有数据都通过 `/api` + axios 走本地后端，**不依赖 Supabase**。

1. 安装前端依赖：`npm install`
2. 首次准备后端环境（`xixi_app_docker/.venv/` 已在 .gitignore）：
   ```sh
   cd xixi_app_docker
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```
3. 终端 A：起后端（依赖局域网 PostgreSQL `192.168.100.67:5432` 可达，否则 API 报错）：
   ```sh
   cd xixi_app_docker && .venv/bin/uvicorn main:app --port 8001
   ```
4. 终端 B：起前端 `npm run dev`，浏览器打开 vite 打印的地址（如 `http://localhost:5174/`），
   登录/注册即完成全链路（前端 → vite proxy `/api` → 后端 8001 → PostgreSQL）。
   后端没开会显示“连接服务器失败”。

快速验证 proxy 转发（后端未起时应为 502）：
```sh
curl -X POST http://localhost:5174/api/login -H 'Content-Type: application/json' \
  -d '{"login_name":"x","password":"y"}'
```

## Customize configuration

See [Vite Configuration Reference](https://vite.dev/config/).

## Project Setup

```sh
npm install
```

### Compile and Hot-Reload for Development

```sh
npm run dev
```

### Compile and Minify for Production

```sh
npm run build
```

### Lint with [ESLint](https://eslint.org/)

```sh
npm run lint
```
