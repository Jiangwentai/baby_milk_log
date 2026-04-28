import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  base: '/baby_milk_log/',
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      // 👉 修改 1：因为你没有 favicon 和 apple-touch-icon，所以先把这里清空，防止打包报错
      includeAssets: [],
      manifest: {
        name: 'xixi 记录本',
        short_name: 'xixi记录本',
        description: '专属宝宝的喝奶记录工具',
        theme_color: '#42b883',
        background_color: '#f0f2f5',
        display: 'standalone',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png',
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable',
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

  // server: {
  //   host: '0.0.0.0', // 监听所有局域网地址
  // },
})
