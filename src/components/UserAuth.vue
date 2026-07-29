<script setup>
import { ref } from 'vue'
import { api } from '../supabase'

const isLoginMode = ref(true) 
const username = ref('')
const password = ref('')
const confirmPassword = ref('') 
const displayName = ref('') 
const birthday = ref('')
const loading = ref(false)
const errorMsg = ref('')

// 切换模式并清空状态
const toggleMode = () => {
  isLoginMode.value = !isLoginMode.value
  errorMsg.value = ''
  password.value = ''
  confirmPassword.value = ''
  birthday.value = ''
}

const handleSubmit = async () => {
  if (!username.value || !password.value) {
    errorMsg.value = '请输入用户名和密码'
    return
  }
  
  if (!isLoginMode.value) {
    if (!displayName.value || !birthday.value) {
      errorMsg.value = '请输入宝宝昵称并选择出生日期'
      return
    }
    if (password.value !== confirmPassword.value) {
      errorMsg.value = '两次输入的密码不一致，请重新输入'
      return
    }
  }

  loading.value = true
  errorMsg.value = ''

  let result
  if (isLoginMode.value) {
    result = await api.login(username.value, password.value)
  } else {
    result = await api.register(username.value, password.value, displayName.value, birthday.value)
  }

  if (result.error) {
    errorMsg.value = result.error.message || (isLoginMode.value ? '登录失败' : '注册失败')
  } else {
    window.location.reload()
  }

  loading.value = false
}
</script>

<template>
  <div class="auth-container">
    <h2>🍼 宝宝专属记录</h2>
    
    <div class="form-group">
      <input v-model="username" type="text" placeholder="设置账户名 (如 xixi)" />
      
      <input 
        v-if="!isLoginMode" 
        v-model="displayName" 
        type="text" 
        placeholder="输入显示昵称 (如: 小晞晞)" 
      />
      
      <input v-model="password" type="password" placeholder="请输入密码" />
      
      <input 
        v-if="!isLoginMode" 
        v-model="confirmPassword" 
        type="password" 
        placeholder="请再次确认密码" 
      />

      <input 
        v-if="!isLoginMode" 
        v-model="birthday" 
        type="date" 
        placeholder="请选择宝宝出生日期" 
      />
    </div>

    <p v-if="errorMsg" class="error">{{ errorMsg }}</p>

    <button @click="handleSubmit" :disabled="loading" class="btn-submit">
      {{ loading ? '处理中...' : (isLoginMode ? '登录' : '注册并进入') }}
    </button>

    <p class="toggle-mode" @click="toggleMode">
      {{ isLoginMode ? '没有账号？点击注册新账号' : '已有账号？点击返回登录' }}
    </p>
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
.form-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
input {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
}
.btn-submit {
  padding: 10px;
  background: #42b883;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
}
.btn-submit:disabled {
  background: #a0d8c0;
}
.error {
  color: #ff4d4d;
  font-size: 0.9em;
  margin: 0;
}
.toggle-mode {
  font-size: 0.85em;
  color: #3498db;
  cursor: pointer;
  margin-top: 5px;
  text-decoration: underline;
}
</style>