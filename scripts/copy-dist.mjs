import { rmSync, cpSync } from 'node:fs'

const target = 'xixi_app_docker/dist'
rmSync(target, { recursive: true, force: true })
cpSync('dist', target, { recursive: true })
console.log('synced dist/ -> xixi_app_docker/dist/')