<script setup>
import { ref, onMounted } from 'vue'
import { supabase } from './supabase'
// 1. 引入改名后的组件
import UserAuth from './components/UserAuth.vue'
import MilkChart from './components/MilkChart.vue'

// 响应式状态
const session = ref(null)
const amountList = ref(false) // 初始设为 false 用于显示加载状态
const newAmount = ref('')
const newNotes = ref('')
const loading = ref(false)

// 获取历史记录 (Supabase 会根据 RLS 自动过滤当前用户的数据)
async function fetchLogs() {
  const { data, error } = await supabase
    .from('milk_logs')
    .select('*')
    .order('created_at', { ascending: false })

  if (error) {
    console.error('获取数据失败:', error)
  } else {
    amountList.value = data
  }
}

// 添加新记录
async function addLog() {
  if (!newAmount.value || isNaN(newAmount.value)) {
    alert('请输入有效的奶粉毫升数！')
    return
  }

  loading.value = true
  // 注意：user_id 会由 Supabase 数据库通过 auth.uid() 自动填充
  const { error } = await supabase
    .from('milk_logs')
    .insert([{ amount_ml: parseInt(newAmount.value), notes: newNotes.value }])

  if (error) {
    alert('保存失败: ' + error.message)
  } else {
    newAmount.value = ''
    newNotes.value = ''
    fetchLogs() // 刷新列表
  }
  loading.value = false
}

// 退出登录
async function handleLogout() {
  if (confirm('确定要退出登录吗？')) {
    await supabase.auth.signOut()
  }
}

// 格式化时间显示
function formatTime(isoString) {
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// 初始化：检查登录状态并监听变化
onMounted(() => {
  // 获取当前会话
  supabase.auth.getSession().then(({ data }) => {
    session.value = data.session
    if (session.value) fetchLogs()
  })

  // 监听登录/登出事件
  supabase.auth.onAuthStateChange((_event, _session) => {
    session.value = _session
    if (_session) {
      fetchLogs()
    } else {
      amountList.value = [] // 登出后清空列表
    }
  })
})
</script>

<template>
  <div class="app-wrapper">
    <div v-if="!session" class="auth-screen">
      <UserAuth />
    </div>

    <main v-else class="container">
      <header class="header">
        <h1>🍼 xixi 喝奶记录</h1>
        <button @click="handleLogout" class="btn-logout">退出</button>
      </header>

      <section class="chart-card">
        <h3>近 7 日趋势 (9:00起计)</h3>
        <MilkChart v-if="amountList && amountList.length > 0" :logs="amountList" />
        <div v-else-if="amountList === false" class="empty-chart">数据加载中...</div>
        <div v-else class="empty-chart">暂无统计数据，快去记录吧！</div>
      </section>

      <section class="input-card">
        <div class="input-group">
          <input type="number" v-model="newAmount" placeholder="奶量 (ml)" inputmode="numeric" />
          <input type="text" v-model="newNotes" placeholder="备注 (可选，如：睡前)" />
        </div>
        <button @click="addLog" :disabled="loading" class="btn-submit">
          {{ loading ? '记录中...' : '确认提交' }}
        </button>
      </section>

      <section class="list-section">
        <h3>最近记录</h3>
        <div v-if="amountList === false" class="status-text">加载中...</div>
        <ul v-else-if="amountList.length > 0">
          <li v-for="log in amountList" :key="log.id" class="log-item">
            <div class="log-main">
              <span class="amount">{{ log.amount_ml }}<small>ml</small></span>
              <span class="time">{{ formatTime(log.created_at) }}</span>
            </div>
            <p class="notes" v-if="log.notes">{{ log.notes }}</p>
          </li>
        </ul>
        <div v-else class="status-text">今天还没有记录哦~</div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.app-wrapper {
  min-height: 100vh;
  background-color: #f5f7f9;
  color: #2c3e50;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.container {
  max-width: 500px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h1 {
  font-size: 1.5rem;
  margin: 0;
  color: #42b883;
}

.btn-logout {
  background: none;
  border: 1px solid #ff4d4d;
  color: #ff4d4d;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 0.8rem;
  cursor: pointer;
}

/* 输入卡片样式 */
.input-card {
  background: white;
  padding: 15px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  margin-bottom: 25px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 12px;
}

input {
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
  outline: none;
}

input:focus {
  border-color: #42b883;
}

.btn-submit {
  width: 100%;
  padding: 12px;
  background: #42b883;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
}

.btn-submit:disabled {
  background: #a0d8c0;
}

/* 列表样式 */
.log-item {
  background: white;
  margin-bottom: 10px;
  padding: 12px 15px;
  border-radius: 8px;
  list-style: none;
}

.log-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.amount {
  font-size: 1.2rem;
  font-weight: bold;
  color: #2c3e50;
}
.amount small {
  font-size: 0.8rem;
  margin-left: 2px;
  color: #7f8c8d;
}
.time {
  font-size: 0.85rem;
  color: #95a5a6;
}
.notes {
  margin: 8px 0 0 0;
  font-size: 0.9rem;
  color: #7f8c8d;
  border-top: 1px dashed #eee;
  padding-top: 5px;
}

.status-text {
  text-align: center;
  color: #95a5a6;
  margin-top: 40px;
}

.chart-card {
  background: white;
  padding: 15px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  margin-bottom: 20px;
}

.chart-card h3 {
  margin: 0 0 10px 0;
  font-size: 0.9rem;
  color: #7f8c8d;
}

.empty-chart {
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #bdc3c7;
  font-size: 0.8rem;
}
</style>
