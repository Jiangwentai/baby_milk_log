<script setup>
import { ref, onMounted, computed } from 'vue'
import { supabase } from './supabase'
import UserAuth from './components/UserAuth.vue'
import MilkChart from './components/MilkChart.vue'

// ==== 全局状态 ====
const session = ref(null)
const activeTab = ref('milk') // 当前标签：'milk' 或 'other'
const loading = ref(false)

function getCurrentDateTime() {
  const now = new Date()
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset())
  return now.toISOString().slice(0, 16)
}

// ==========================================
// 🍼 模块一：喝奶记录相关的状态与方法
// ==========================================
const amountList = ref([])
const newAmount = ref('')
const newNotes = ref('')
const logTime = ref(getCurrentDateTime())
const editingId = ref(null)

const groupedLogs = computed(() => {
  if (!amountList.value.length) return []
  const groups = {}
  amountList.value.forEach((log) => {
    const date = new Date(log.created_at)
    // 统一减去 9 小时，归入前一天
    const offsetDate = new Date(date.getTime() - 9 * 60 * 60 * 1000)
    const dateKey = offsetDate.toISOString().split('T')[0]

    if (!groups[dateKey]) groups[dateKey] = []
    groups[dateKey].push(log)
  })

  return Object.keys(groups)
    .sort()
    .reverse()
    .map((date) => {
      // 将 YYYY-MM-DD 转换为更友好的中文显示
      const d = new Date(date)
      return {
        date: `${d.getMonth() + 1}月${d.getDate()}日`,
        logs: groups[date],
        total: groups[date].reduce((sum, item) => sum + item.amount_ml, 0),
      }
    })
})

async function fetchLogs() {
  const { data } = await supabase
    .from('milk_logs')
    .select('*')
    .order('created_at', { ascending: false })
  if (data) amountList.value = data
}

function selectForEdit(log) {
  editingId.value = log.id
  newAmount.value = log.amount_ml
  newNotes.value = log.notes || ''
  const date = new Date(log.created_at)
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset())
  logTime.value = date.toISOString().slice(0, 16)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function cancelEdit() {
  editingId.value = null
  newAmount.value = ''
  newNotes.value = ''
  logTime.value = getCurrentDateTime()
}

async function saveLog() {
  if (!newAmount.value) return alert('请输入奶量')

  const actionName = editingId.value ? '修改' : '新增'
  const timeString = new Date(logTime.value).toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
  if (
    !window.confirm(
      `请确认${actionName}信息：\n时间：${timeString}\n奶量：${newAmount.value} ml\n备注：${newNotes.value || '无'}\n\n确定要保存吗？`,
    )
  )
    return

  loading.value = true
  const payload = {
    amount_ml: parseInt(newAmount.value),
    notes: newNotes.value,
    created_at: new Date(logTime.value).toISOString(),
  }

  const { error } = editingId.value
    ? await supabase.from('milk_logs').update(payload).eq('id', editingId.value)
    : await supabase.from('milk_logs').insert([payload])

  if (!error) {
    cancelEdit()
    fetchLogs()
  } else alert('操作失败: ' + error.message)
  loading.value = false
}

async function deleteLog(id) {
  if (confirm('确定要删除这条记录吗？')) {
    await supabase.from('milk_logs').delete().eq('id', id)
    fetchLogs()
  }
}

// ==========================================
// 🌟 模块二：日常活动相关的状态与方法
// ==========================================
const activityList = ref([])
const actTime = ref(getCurrentDateTime())
const actType = ref('💊 维生素')
const actNotes = ref('')
const actEditingId = ref(null)

const activityOptions = ['💊 维生素', '🏊 游泳', '💩 换尿布', '🛁 洗澡', '🌡️ 体温/生病', '📝 其他']

// 👉 维生素提醒状态计算
const hasTakenVitaminToday = computed(() => {
  if (!activityList.value.length) return false
  const todayString = new Date().toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
  return activityList.value.some((log) => {
    if (log.type !== '💊 维生素') return false
    const logDate = new Date(log.created_at).toLocaleDateString('zh-CN', {
      month: 'numeric',
      day: 'numeric',
    })
    return logDate === todayString
  })
})

const groupedActivities = computed(() => {
  if (!activityList.value.length) return []
  const groups = {}
  activityList.value.forEach((log) => {
    const date = new Date(log.created_at)
    // 日常活动按自然日统计
    const dateKey = date.toISOString().split('T')[0]
    if (!groups[dateKey]) groups[dateKey] = []
    groups[dateKey].push(log)
  })

  return Object.keys(groups)
    .sort()
    .reverse()
    .map((date) => {
      const d = new Date(date)
      return {
        date: `${d.getMonth() + 1}月${d.getDate()}日`,
        logs: groups[date],
      }
    })
})

async function fetchActivities() {
  const { data } = await supabase
    .from('activity_logs')
    .select('*')
    .order('created_at', { ascending: false })
  if (data) activityList.value = data
}

function selectForEditAct(log) {
  actEditingId.value = log.id
  actType.value = log.type
  actNotes.value = log.notes || ''
  const date = new Date(log.created_at)
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset())
  actTime.value = date.toISOString().slice(0, 16)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function cancelEditAct() {
  actEditingId.value = null
  actType.value = '💊 维生素'
  actNotes.value = ''
  actTime.value = getCurrentDateTime()
}

async function saveActivity() {
  loading.value = true
  const payload = {
    type: actType.value,
    notes: actNotes.value,
    created_at: new Date(actTime.value).toISOString(),
  }

  const { error } = actEditingId.value
    ? await supabase.from('activity_logs').update(payload).eq('id', actEditingId.value)
    : await supabase.from('activity_logs').insert([payload])

  if (!error) {
    cancelEditAct()
    fetchActivities()
  } else alert('操作失败: ' + error.message)
  loading.value = false
}

async function deleteActivity(id) {
  if (confirm('确定要删除这条记录吗？')) {
    await supabase.from('activity_logs').delete().eq('id', id)
    fetchActivities()
  }
}

// ==========================================
// 🚀 初始化
// ==========================================
const handleLogout = async () => {
  await supabase.auth.signOut()
}

onMounted(() => {
  supabase.auth.getSession().then(({ data }) => {
    session.value = data.session
    if (session.value) {
      fetchLogs()
      fetchActivities()
    }
  })
  supabase.auth.onAuthStateChange((_event, _session) => {
    session.value = _session
    if (_session) {
      fetchLogs()
      fetchActivities()
    }
  })
})
</script>

<template>
  <div class="app-wrapper">
    <div v-if="!session" class="auth-screen"><UserAuth /></div>

    <main v-else class="container">
      <header class="header">
        <h1>{{ activeTab === 'milk' ? '🍼 喝奶记录' : '🌟 日常记录' }}</h1>
        <button @click="handleLogout" class="btn-logout">退出</button>
      </header>

      <div v-show="activeTab === 'milk'" class="tab-content">
        <div class="vitamin-status" :class="hasTakenVitaminToday ? 'status-ok' : 'status-warn'">
          <span class="status-icon">{{ hasTakenVitaminToday ? '✅' : '⚠️' }}</span>
          <span class="status-text">
            {{ hasTakenVitaminToday ? '今日已补充维生素' : '今日尚未补充维生素' }}
          </span>
        </div>

        <section class="card chart-section">
          <MilkChart v-if="amountList.length" :logs="amountList" />
        </section>

        <section class="card input-section" :class="{ 'editing-mode': editingId }">
          <div class="form-header">
            <h3>{{ editingId ? '📝 修改奶粉记录' : '➕ 新增奶粉记录' }}</h3>
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
      </div>

      <div v-show="activeTab === 'other'" class="tab-content">
        <section class="card input-section" :class="{ 'editing-mode': actEditingId }">
          <div class="form-header">
            <h3>{{ actEditingId ? '📝 修改日常记录' : '➕ 新增日常记录' }}</h3>
            <button v-if="actEditingId" @click="cancelEditAct" class="btn-text">取消</button>
          </div>
          <div class="form-row">
            <div class="input-item">
              <label>时间</label>
              <input type="datetime-local" v-model="actTime" />
            </div>
          </div>
          <div class="form-row">
            <div class="input-item">
              <label>活动项目</label>
              <select v-model="actType" class="act-select">
                <option v-for="opt in activityOptions" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="input-item">
              <label>详细备注 (建议填写)</label>
              <input type="text" v-model="actNotes" placeholder="例如：游了15分钟" />
            </div>
          </div>
          <button
            @click="saveActivity"
            :disabled="loading"
            class="btn-primary"
            style="background-color: #3498db"
          >
            {{ loading ? '处理中...' : actEditingId ? '保存修改' : '确认提交' }}
          </button>
        </section>

        <section class="history-section">
          <div v-for="group in groupedActivities" :key="group.date" class="date-group">
            <div class="group-header">
              <span class="group-date">{{ group.date }}</span>
              <span class="group-total">{{ group.logs.length }} 项记录</span>
            </div>
            <div class="log-grid">
              <div
                v-for="log in group.logs"
                :key="log.id"
                class="log-cell act-cell"
                @click="selectForEditAct(log)"
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
                  <button @click.stop="deleteActivity(log.id)" class="btn-del">×</button>
                </div>
                <div class="log-amount act-title">{{ log.type }}</div>
                <div v-if="log.notes" class="log-note">💬 {{ log.notes }}</div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>

    <nav class="bottom-nav" v-if="session">
      <div class="nav-item" :class="{ active: activeTab === 'milk' }" @click="activeTab = 'milk'">
        <span class="nav-icon">🍼</span>
        <span class="nav-text">喝奶</span>
      </div>
      <div class="nav-item" :class="{ active: activeTab === 'other' }" @click="activeTab = 'other'">
        <span class="nav-icon">🌟</span>
        <span class="nav-text">日常</span>
      </div>
    </nav>
  </div>
</template>

<style scoped>
/* 全局与布局 */
.app-wrapper {
  min-height: 100vh;
  background: #f0f2f5;
  padding-bottom: 80px;
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
  color: #2c3e50;
  margin: 0;
}
.card {
  background: white;
  border-radius: 12px;
  padding: 15px;
  margin-bottom: 15px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}
.btn-logout {
  background: none;
  border: 1px solid #ccc;
  color: #999;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 0.7rem;
}

/* 维生素状态条 */
.vitamin-status {
  display: flex;
  align-items: center;
  padding: 12px 15px;
  border-radius: 12px;
  margin-bottom: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}
.status-ok {
  background-color: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
}
.status-warn {
  background-color: #fffbeb;
  border: 1px solid #fef08a;
  color: #b45309;
}
.status-icon {
  font-size: 1.2rem;
  margin-right: 10px;
}
.status-text {
  flex: 1;
  font-size: 0.9rem;
  font-weight: bold;
}

/* 表单输入区域 */
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
input,
select {
  padding: 10px;
  border: 1px solid #eee;
  border-radius: 8px;
  font-size: 1rem;
  background: #fafafa;
}
.act-select {
  appearance: none;
  background-color: white;
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

/* 历史记录 (单列布局) */
.date-group {
  margin-bottom: 25px;
}
.group-header {
  display: flex;
  justify-content: space-between;
  padding: 0 5px 8px;
  border-bottom: 2px solid #ccc;
  margin-bottom: 10px;
}
.group-date {
  font-weight: bold;
  color: #333;
}
.group-total {
  color: #888;
  font-size: 0.9rem;
}
.log-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 卡片样式 */
.log-cell {
  background: white;
  padding: 15px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
  border-left: 4px solid #42b883;
  cursor: pointer;
  position: relative;
  transition: all 0.2s;
}
.act-cell {
  border-left-color: #3498db;
}
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
.log-amount {
  font-size: 1.4rem;
  font-weight: bold;
  color: #2c3e50;
  text-align: left;
  margin: 5px 0;
}
.act-title {
  font-size: 1.1rem;
  color: #3498db;
}
.log-amount small {
  font-size: 0.9rem;
  color: #95a5a6;
  margin-left: 4px;
}
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

/* 底部导航栏 */
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  background: white;
  display: flex;
  justify-content: space-around;
  padding: 10px 0;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.05);
  z-index: 100;
  padding-bottom: env(safe-area-inset-bottom, 10px);
}
.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #bdc3c7;
  cursor: pointer;
  transition: color 0.3s;
}
.nav-icon {
  font-size: 1.4rem;
  margin-bottom: 3px;
  filter: grayscale(100%);
  opacity: 0.5;
  transition: all 0.3s;
}
.nav-text {
  font-size: 0.75rem;
  font-weight: 600;
}
.nav-item.active {
  color: #2c3e50;
}
.nav-item.active .nav-icon {
  filter: grayscale(0%);
  opacity: 1;
  transform: scale(1.1);
}
</style>
