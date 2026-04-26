import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  base: '/baby_milk_log/', // 例如 '/baby-milk-tracker/'
  plugins: [
    vue(),
    // 👉 2. 配置 PWA 插件
    VitePWA({
      registerType: 'autoUpdate', // 发现新版本时自动更新后台缓存
      includeAssets: ['/public/pwa-512x512.png'], // 其他静态资源
      manifest: {
        name: 'xixi 记录本',
        short_name: 'xixi记录本',
        description: '专属宝宝的喝奶记录工具',
        theme_color: '#42b883', // 手机状态栏的颜色
        background_color: '#f0f2f5', // 启动时的启动屏背景色
        display: 'standalone', // 关键！这会让它看起来像个独立 App，隐藏浏览器 UI
        icons: [
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable', // 适配安卓的自适应图标形状
          },
        ],
      },
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
})
