<script setup>
import { ref } from 'vue'
import { supabase } from '../supabase'

const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMsg = ref('')

const handleLogin = async () => {
  // 1. 前端第一层拦截：检查是否是专属密码 xixi
  if (username.value !== 'xixi' || password.value !== 'xixi') {
    errorMsg.value = '口令错误，这不是 xixi 的专属记录本哦！'
    return
  }

  loading.value = true
  errorMsg.value = ''

  // 2. 后台静默登录：映射到真实的 Supabase 凭证
  const { error } = await supabase.auth.signInWithPassword({
    email: 'xixi@gmail.com', // 替换为你刚才在后台创建的邮箱
    password: 'xixi20260128', // 替换为你刚才在后台创建的密码
  })

  if (error) {
    errorMsg.value = '服务器连接失败，请检查配置'
    console.error('Supabase 登录失败:', error)
  }

  loading.value = false
}
</script>

<template>
  <div class="auth-container">
    <h2>🍼 xixi 专属记录</h2>
    <input v-model="username" type="text" placeholder="请输入用户名" />
    <input v-model="password" type="password" placeholder="请输入密码" />

    <p v-if="errorMsg" class="error">{{ errorMsg }}</p>

    <button @click="handleLogin" :disabled="loading">
      {{ loading ? '进入中...' : '登录' }}
    </button>
  </div>
</template>

<style scoped>
.auth-container {
  display: flex;
  flex-direction: column;
  gap: 15px;
  max-width: 300px;
  margin: 80px auto;
  text-align: center;
}
input {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
}
button {
  padding: 10px;
  background: #42b883;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
}
button:disabled {
  background: #a0d8c0;
}
.error {
  color: #ff4d4d;
  font-size: 0.9em;
  margin: 0;
}
</style>
