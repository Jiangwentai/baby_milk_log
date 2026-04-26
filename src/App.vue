<script setup>
import { ref, onMounted, computed } from 'vue'
import { supabase } from './supabase'
import UserAuth from './components/UserAuth.vue'
import MilkChart from './components/MilkChart.vue'

// 状态管理
const session = ref(null)
const amountList = ref([])
const loading = ref(false)

// 表单数据
const newAmount = ref('')
const newNotes = ref('')
const logTime = ref(getCurrentDateTime())
const editingId = ref(null) // 👈 新增：记录当前正在编辑的 ID

function getCurrentDateTime() {
  const now = new Date()
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset())
  return now.toISOString().slice(0, 16)
}

// 数据分组逻辑 (按9:00偏移)
const groupedLogs = computed(() => {
  if (!amountList.value.length) return []
  const groups = {}
  amountList.value.forEach((log) => {
    const date = new Date(log.created_at)
    const offsetDate = new Date(date)
    offsetDate.setHours(offsetDate.getHours() - 9)
    const dateKey = offsetDate.toLocaleDateString('zh-CN', { month: 'long', day: 'numeric' })
    if (!groups[dateKey]) groups[dateKey] = []
    groups[dateKey].push(log)
  })
  return Object.keys(groups).map((date) => ({
    date,
    logs: groups[date],
    total: groups[date].reduce((sum, item) => sum + item.amount_ml, 0),
  }))
})

async function fetchLogs() {
  const { data, error } = await supabase
    .from('milk_logs')
    .select('*')
    .order('created_at', { ascending: false })
  if (!error) amountList.value = data
}

// 👈 选中某条记录进入编辑模式
function selectForEdit(log) {
  editingId.value = log.id // 注意：这是为了教学演示，实际应为 editingId.value
  editingId.value = log.id
  newAmount.value = log.amount_ml
  newNotes.value = log.notes || ''

  // 转换存储的时间为本地输入框格式
  const date = new Date(log.created_at)
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset())
  logTime.value = date.toISOString().slice(0, 16)

  // 自动滚动到顶部输入框
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// 👈 取消编辑
function cancelEdit() {
  editingId.value = null
  newAmount.value = ''
  newNotes.value = ''
  logTime.value = getCurrentDateTime()
}

// 👈 保存数据 (新增或更新)
// 保存数据 (新增或更新)
async function saveLog() {
  if (!newAmount.value) return alert('请输入奶量')

  // 👉 新增的确认逻辑开始
  const actionName = editingId.value ? '修改' : '新增'
  const timeString = new Date(logTime.value).toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })

  // 弹出确认框，展示即将保存的详细信息
  const isConfirmed = window.confirm(
    `请确认${actionName}信息：\n\n` +
      `时间：${timeString}\n` +
      `奶量：${newAmount.value} ml\n` +
      `备注：${newNotes.value || '无'}\n\n` +
      `确定要保存吗？`,
  )

  // 如果用户点击了“取消”，则直接中断，不向服务器发送请求
  if (!isConfirmed) {
    return
  }
  // 👉 确认逻辑结束

  loading.value = true

  const payload = {
    amount_ml: parseInt(newAmount.value),
    notes: newNotes.value,
    created_at: new Date(logTime.value).toISOString(),
  }

  let error
  if (editingId.value) {
    // 编辑模式
    const { error: err } = await supabase
      .from('milk_logs')
      .update(payload)
      .eq('id', editingId.value)
    error = err
  } else {
    // 新增模式
    const { error: err } = await supabase.from('milk_logs').insert([payload])
    error = err
  }

  if (!error) {
    cancelEdit()
    fetchLogs()
  } else {
    alert('操作失败: ' + error.message)
  }
  loading.value = false
}

// 👈 删除记录
async function deleteLog(id) {
  if (confirm('确定要删除这条记录吗？')) {
    const { error } = await supabase.from('milk_logs').delete().eq('id', id)
    if (!error) fetchLogs()
  }
}

const handleLogout = async () => {
  await supabase.auth.signOut()
}

onMounted(() => {
  supabase.auth.getSession().then(({ data }) => {
    session.value = data.session
    if (session.value) fetchLogs()
  })
  supabase.auth.onAuthStateChange((_event, _session) => {
    session.value = _session
    if (_session) fetchLogs()
  })
})
</script>

<template>
  <div class="app-wrapper">
    <div v-if="!session" class="auth-screen"><UserAuth /></div>

    <main v-else class="container">
      <header class="header">
        <h1>🍼 xixi 记录本</h1>
        <button @click="handleLogout" class="btn-logout">退出</button>
      </header>

      <section class="card chart-section">
        <MilkChart v-if="amountList.length" :logs="amountList" />
      </section>

      <section class="card input-section" :class="{ 'editing-mode': editingId }">
        <div class="form-header">
          <h3>{{ editingId ? '📝 修改记录' : '➕ 新增记录' }}</h3>
          <button v-if="editingId" @click="cancelEdit" class="btn-text">取消</button>
        </div>

        <div class="form-row">
          <div class="input-item">
            <label>时间</label>
            <input type="datetime-local" v-model="logTime" />
          </div>
        </div>
        <div class="form-row">
          <div class="input-item">
            <label>奶量 (ml)</label>
            <input type="number" v-model="newAmount" placeholder="0" inputmode="numeric" />
          </div>
          <div class="input-item">
            <label>备注</label>
            <input type="text" v-model="newNotes" placeholder="可选" />
          </div>
        </div>
        <button @click="saveLog" :disabled="loading" class="btn-primary">
          {{ loading ? '处理中...' : editingId ? '保存修改' : '确认提交' }}
        </button>
      </section>

      <section class="history-section">
        <div v-for="group in groupedLogs" :key="group.date" class="date-group">
          <div class="group-header">
            <span class="group-date">{{ group.date }}</span>
            <span class="group-total">共 {{ group.total }}ml</span>
          </div>
          <div class="log-grid">
            <div
              v-for="log in group.logs"
              :key="log.id"
              class="log-cell"
              @click="selectForEdit(log)"
            >
              <div class="log-cell-top">
                <span class="log-time"
                  >⏰
                  {{
                    new Date(log.created_at).toLocaleTimeString('zh-CN', {
                      hour: '2-digit',
                      minute: '2-digit',
                    })
                  }}</span
                >
                <button @click.stop="deleteLog(log.id)" class="btn-del">×</button>
              </div>

              <div class="log-amount">{{ log.amount_ml }}<small>ml</small></div>

              <div v-if="log.notes" class="log-note">💬 {{ log.notes }}</div>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
/* 之前的样式保持，新增/修改部分如下： */
.app-wrapper {
  min-height: 100vh;
  background: #f0f2f5;
  padding-bottom: 40px;
}
.container {
  max-width: 500px;
  margin: 0 auto;
  padding: 15px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}
.header h1 {
  font-size: 1.4rem;
  color: #42b883;
  margin: 0;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 15px;
  margin-bottom: 15px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

/* 编辑模式下的输入框高亮 */
.editing-mode {
  border: 2px solid #42b883;
}
.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.form-header h3 {
  margin: 0;
  font-size: 1rem;
  color: #333;
}
.btn-text {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
}

.form-row {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}
.input-item {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.input-item label {
  font-size: 0.8rem;
  color: #888;
  margin-bottom: 5px;
}
input {
  padding: 10px;
  border: 1px solid #eee;
  border-radius: 8px;
  font-size: 1rem;
  background: #fafafa;
}
.btn-primary {
  width: 100%;
  padding: 12px;
  background: #42b883;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
}

/* 历史记录分组容器 */
.date-group {
  margin-bottom: 25px;
}

/* 强制单列布局 */
.log-grid {
  display: flex;
  flex-direction: column; /* 纵向排列，形成单列 */
  gap: 12px;
}

/* 重新设计单列卡片：左右布局 */
.log-cell {
  background: white;
  padding: 15px;
  border-radius: 12px;
  display: flex;
  flex-direction: column; /* 内部依然纵向，但宽度撑满 */
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
  border-left: 4px solid #42b883; /* 绿色左边条 */
  cursor: pointer;
  position: relative;
  transition: all 0.2s;
}

.log-cell:active {
  transform: scale(0.98);
  background-color: #f9f9f9;
}

/* 卡片顶部：时间、删除按钮 */
.log-cell-top {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

.log-time {
  font-size: 0.85rem;
  color: #888;
  font-weight: 500;
}

/* 奶量主体：居左显示 */
.log-amount {
  font-size: 1.4rem;
  font-weight: bold;
  color: #2c3e50;
  text-align: left; /* 改为左对齐 */
  margin: 5px 0;
}

.group-total {
  font-size: 1.4rem;
  font-weight: bold;
  color: #2c3e50;
  text-align: left; /* 改为左对齐 */
  margin: 5px 0;
}

/* 备注部分：撑满宽度 */
.log-note {
  font-size: 0.9rem;
  color: #7f8c8d;
  background: #f8faf9;
  padding: 6px 10px;
  border-radius: 6px;
  margin-top: 8px;
  width: 100%;
  box-sizing: border-box;
}
.log-amount small {
  font-size: 1.2rem;
  color: #95a5a6;
  margin-left: 6px;
}

/* 优化删除按钮，让它在单列中更易点 */
.btn-del {
  border: none;
  background: #fee;
  color: #ff4d4d;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  cursor: pointer;
}
</style>
