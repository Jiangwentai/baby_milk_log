<script setup>
import { ref, onMounted } from 'vue'
import { supabase } from './supabase'

const amountList = ref([])
const newAmount = ref('')
const newNotes = ref('')
const loading = ref(false)

// 获取历史记录
async function fetchLogs() {
  const { data, error } = await supabase
    .from('milk_logs')
    .select('*')
    .order('created_at', { ascending: false })

  if (error) console.error('获取数据失败:', error)
  else amountList.value = data
}

// 添加新记录
async function addLog() {
  if (!newAmount.value || isNaN(newAmount.value)) {
    alert('请输入有效的奶粉毫升数！')
    return
  }

  loading.value = true
  const { error } = await supabase
    .from('milk_logs')
    .insert([
      { amount_ml: parseInt(newAmount.value), notes: newNotes.value }
    ])

  if (error) {
    console.error('添加失败:', error)
    alert('添加失败，请重试')
  } else {
    newAmount.value = ''
    newNotes.value = ''
    fetchLogs() // 刷新列表
  }
  loading.value = false
}

// 格式化时间
function formatTime(isoString) {
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(() => {
  fetchLogs()
})
</script>

<template>
  <main class="container">
    <h1>🍼 宝贝喝奶记录</h1>

    <div class="input-section">
      <input type="number" v-model="newAmount" placeholder="奶量 (ml)" />
      <input type="text" v-model="newNotes" placeholder="备注 (如: 睡前喝的)" />
      <button @click="addLog" :disabled="loading">
        {{ loading ? '记录中...' : '记录' }}
      </button>
    </div>

    <div class="list-section">
      <h2>历史记录</h2>
      <ul>
        <li v-for="log in amountList" :key="log.id">
          <strong>{{ log.amount_ml }} ml</strong>
          <span class="time">{{ formatTime(log.created_at) }}</span>
          <p class="notes" v-if="log.notes">{{ log.notes }}</p>
        </li>
      </ul>
      <p v-if="amountList.length === 0">今天还没有记录哦~</p>
    </div>
  </main>
</template>

<style scoped>
.container { max-width: 500px; margin: 0 auto; padding: 20px; font-family: sans-serif; }
.input-section { display: flex; gap: 10px; margin-bottom: 30px; }
input { padding: 8px; border: 1px solid #ccc; border-radius: 4px; flex: 1; }
button { padding: 8px 16px; background: #42b883; color: white; border: none; border-radius: 4px; cursor: pointer; }
button:disabled { background: #a0d8c0; }
ul { list-style: none; padding: 0; }
li { border-bottom: 1px solid #eee; padding: 10px 0; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; }
.time { color: #888; font-size: 0.9em; }
.notes { width: 100%; color: #666; font-size: 0.9em; margin-top: 5px; }
</style>
