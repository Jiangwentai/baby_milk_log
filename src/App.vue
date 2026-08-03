<script setup>
import { ref, onMounted, computed } from 'vue'
import { getCurrentAccount, clearCurrentAccount } from './supabase'
import UserAuth from './components/UserAuth.vue'
import MilkChart from './components/MilkChart.vue'
import axios from 'axios'

const API_BASE_URL = '/api'

// ==== 全局状态 ====
const session = ref(null)
const currentAccount = ref(null)
const activeTab = ref('milk')
const loading = ref(false)
const expandedDates = ref([])
const expandedActDates = ref([])

function getCurrentDateTime() {
  const now = new Date()
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset())
  return now.toISOString().slice(0, 16)
}

function toggleFold(dateKey, targetList) {
  const index = targetList.indexOf(dateKey)
  if (index > -1) {
    targetList.splice(index, 1)
  } else {
    targetList.push(dateKey)
  }
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
  const now = new Date()
  const todayOffset = new Date(now.getTime() - 9 * 60 * 60 * 1000)
  const threeDaysAgo = new Date(todayOffset)
  threeDaysAgo.setDate(threeDaysAgo.getDate() - 3)
  const thresholdKey = threeDaysAgo.toLocaleDateString('sv-SE')

  amountList.value.forEach((log) => {
    const date = new Date(log.created_at)
    const offsetDate = new Date(date.getTime() - 9 * 60 * 60 * 1000)
    const dateKey = offsetDate.toLocaleDateString('sv-SE')
    if (!groups[dateKey]) groups[dateKey] = []
    groups[dateKey].push(log)
  })

  return Object.keys(groups)
    .sort()
    .reverse()
    .map((dateKey) => {
      const d = new Date(dateKey)
      return {
        dateKey,
        displayDate: `${d.getMonth() + 1}月${d.getDate()}日`,
        logs: groups[dateKey],
        total: groups[dateKey].reduce((sum, item) => sum + item.amount_ml, 0),
        isOld: dateKey < thresholdKey,
      }
    })
})

const milkTargetStats = computed(() => {
  if (!groupedLogs.value || groupedLogs.value.length === 0) return null
  const now = new Date()
  const todayOffset = new Date(now.getTime() - 9 * 60 * 60 * 1000)
  const todayKey = todayOffset.toLocaleDateString('sv-SE')
  const todayGroup = groupedLogs.value.find((g) => g.dateKey === todayKey)
  const todayTotal = todayGroup ? todayGroup.total : 0
  const pastGroups = groupedLogs.value.filter((g) => g.dateKey < todayKey)
  if (pastGroups.length === 0) return null
  const recent7Groups = pastGroups.slice(0, 5)
  const pastTotal = recent7Groups.reduce((sum, g) => sum + g.total, 0)
  const pastAverage = Math.round(pastTotal / recent7Groups.length)
  const diff = pastAverage - todayTotal
  return { todayTotal, average: pastAverage, diff: diff > 0 ? diff : 0, isAchieved: diff <= 0 }
})

async function fetchLogs() {
  if (!currentAccount.value) return
  try {
    const res = await axios.get(`${API_BASE_URL}/milk_logs/${currentAccount.value.account_id}`)
    if (res.data && res.data.data) {
      amountList.value = res.data.data
    }
  } catch (err) {
    console.error('获取喝奶记录失败', err)
  }
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
  if (!window.confirm(`确认${actionName}奶粉记录？`)) return
  loading.value = true

  try {
    if (editingId.value) {
      // 修改
      await axios.put(`${API_BASE_URL}/milk_logs/${editingId.value}`, {
        amount_ml: parseInt(newAmount.value),
        notes: newNotes.value,
        created_at: new Date(logTime.value).toISOString(),
      })
    } else {
      // 新增（必须带上 account_id 保证多租户隔离）
      await axios.post(`${API_BASE_URL}/milk_logs`, {
        account_id: currentAccount.value.account_id,
        amount_ml: parseInt(newAmount.value),
        notes: newNotes.value,
        created_at: new Date(logTime.value).toISOString(),
      })
    }
    cancelEdit()
    fetchLogs()
  } catch (err) {
    alert('操作失败: ' + (err.response?.data?.detail || err.message))
  }
  loading.value = false
}

async function deleteLog(id) {
  if (confirm('确定要删除这条记录吗？')) {
    try {
      await axios.delete(`${API_BASE_URL}/milk_logs/${id}`)
      fetchLogs()
    } catch (err) {
      alert('删除失败')
    }
  }
}

// ==========================================
// 🌟 模块二：日常活动相关的状态与方法
// ==========================================
const activityList = ref([])
const actTime = ref(getCurrentDateTime())
const actType = ref('☀️ AD')
const actNotes = ref('')
const actEditingId = ref(null)
const activityOptions = [
  '☀️ AD',
  '🏊 游泳',
  '💩💩💩',
  '🛁 洗澡',
  '🌡️ 体温',
  '⚖️ 身高/体重',
  '📝 其他',
]

const hasTakenVitaminToday = computed(() => {
  if (!activityList.value.length) return false
  const todayString = new Date().toLocaleDateString('sv-SE', { month: 'numeric', day: 'numeric' })
  return activityList.value.some((log) => {
    if (log.type !== '☀️ AD') return false
    const logDate = new Date(log.created_at).toLocaleDateString('sv-SE', {
      month: 'numeric',
      day: 'numeric',
    })
    return logDate === todayString
  })
})

const groupedActivities = computed(() => {
  if (!activityList.value.length) return []
  const groups = {}
  const now = new Date()
  const fiveDaysAgo = new Date(now)
  fiveDaysAgo.setDate(fiveDaysAgo.getDate() - 5)
  const thresholdKey = fiveDaysAgo.toLocaleDateString('sv-SE')

  activityList.value.forEach((log) => {
    const date = new Date(log.created_at)
    const dateKey = date.toLocaleDateString('sv-SE')
    if (!groups[dateKey]) groups[dateKey] = []
    groups[dateKey].push(log)
  })

  return Object.keys(groups)
    .sort()
    .reverse()
    .map((dateKey) => {
      const d = new Date(dateKey)
      return {
        dateKey,
        displayDate: `${d.getMonth() + 1}月${d.getDate()}日`,
        logs: groups[dateKey],
        isOld: dateKey < thresholdKey,
      }
    })
})

async function fetchActivities() {
  if (!currentAccount.value) return
  try {
    const res = await axios.get(`${API_BASE_URL}/activity_logs/${currentAccount.value.account_id}`)
    if (res.data && res.data.data) {
      activityList.value = res.data.data
    }
  } catch (err) {
    console.error('获取日常活动失败', err)
  }
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
  actType.value = '☀️ AD'
  actNotes.value = ''
  actTime.value = getCurrentDateTime()
}

async function saveActivity() {
  if (!window.confirm(`确认保存日常记录吗？`)) return
  loading.value = true
  try {
    if (actEditingId.value) {
      await axios.put(`${API_BASE_URL}/activity_logs/${actEditingId.value}`, {
        type: actType.value,
        notes: actNotes.value,
        created_at: new Date(actTime.value).toISOString(),
      })
    } else {
      await axios.post(`${API_BASE_URL}/activity_logs`, {
        account_id: currentAccount.value.account_id,
        type: actType.value,
        notes: actNotes.value,
        created_at: new Date(actTime.value).toISOString(),
      })
    }
    cancelEditAct()
    fetchActivities()
  } catch (err) {
    alert('操作失败')
  }
  loading.value = false
}

async function deleteActivity(id) {
  if (confirm('确定要删除这条记录吗？')) {
    try {
      await axios.delete(`${API_BASE_URL}/activity_logs/${id}`)
      fetchActivities()
    } catch (err) {
      alert('删除失败')
    }
  }
}

const daysOld = computed(() => {
  // 如果没获取到账户信息，或者该账户(旧账户)没有填生日，默认显示 0
  if (!currentAccount.value || !currentAccount.value.birthday) return 0

  const birthDate = new Date(currentAccount.value.birthday)
  const today = new Date()

  // 将时间都归零到午夜，避免因为时分秒导致的天数误差
  birthDate.setHours(0, 0, 0, 0)
  today.setHours(0, 0, 0, 0)

  const diffTime = today - birthDate
  return Math.floor(diffTime / (1000 * 60 * 60 * 24)) + 1 // 加 1 代表出生当天算第 1 天 (视你的习惯可去掉)
})

// ==========================================
// 🚀 初始化与登出
// ==========================================
const handleLogout = () => {
  clearCurrentAccount()
  session.value = null
  currentAccount.value = null
  window.location.reload()
}

onMounted(() => {
  const account = getCurrentAccount()
  if (account) {
    currentAccount.value = account
    session.value = true
    fetchLogs()
    fetchActivities()
  }
})
</script>

<template>
  <div class="app-wrapper">
    <div v-if="!session" class="auth-screen"><UserAuth /></div>

    <main v-else class="container">
<header class="header">
  <div class="title-group">
    <!-- 标题直接动态显示当前宝宝的昵称 -->
    <h1>{{ currentAccount?.display_name || '宝宝' }}健康成长 🍼👼🌿</h1>
    <h2>第 {{ daysOld }}天</h2>
    <h2>{{ activeTab === 'milk' ? '🍼 喝奶记录' : '🌟 日常记录' }}</h2>
  </div>
  <button @click="handleLogout" class="btn-logout">退出</button>
</header>

      <div v-show="activeTab === 'milk'" class="tab-content">
        <div class="status-board" :class="hasTakenVitaminToday ? 'status-ok' : 'status-warn'">
          <div class="status-left">
            <div class="main-status">
              <span class="status-icon">{{ hasTakenVitaminToday ? '✅' : '⚠️' }}</span>
              <span class="status-text">{{ hasTakenVitaminToday ? '今日已吃AD' : '今日还没吃AD哦' }}</span>
            </div>
            <div class="sub-status" v-if="milkTargetStats">
              <span class="sub-icon">{{ milkTargetStats.isAchieved ? '🎉' : '🍼' }}</span>
              <span>{{
                milkTargetStats.isAchieved
                  ? `今日奶量 ${milkTargetStats.todayTotal}ml，已达标！`
                  : `距5日平均(${milkTargetStats.average}ml)还差 ${milkTargetStats.diff}ml`
              }}</span>
            </div>
          </div>
        </div>

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
              <label>时间</label><input type="datetime-local" v-model="logTime" />
            </div>
          </div>
          <div class="form-row">
            <div class="input-item">
              <label>奶量(ml)</label><input type="number" v-model="newAmount" inputmode="numeric" />
            </div>
            <div class="input-item">
              <label>备注</label><input type="text" v-model="newNotes" placeholder="可选" />
            </div>
          </div>
          <button @click="saveLog" :disabled="loading" class="btn-primary">
            {{ loading ? '处理中...' : editingId ? '保存修改' : '确认提交' }}
          </button>
        </section>

        <section class="history-section">
          <div v-for="group in groupedLogs" :key="group.dateKey" class="date-group">
            <div
              class="group-header"
              @click="group.isOld && toggleFold(group.dateKey, expandedDates)"
              :class="{ clickable: group.isOld }"
            >
              <span class="group-date"
                >{{ group.displayDate }}
                <small v-if="group.isOld" class="fold-tag">{{
                  expandedDates.includes(group.dateKey) ? '🔼 收起' : '🔽 历史'
                }}</small></span
              >
              <span class="group-total">共 {{ group.total }}ml</span>
            </div>

            <div class="log-grid" v-if="!group.isOld || expandedDates.includes(group.dateKey)">
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
                      new Date(log.created_at).toLocaleTimeString('sv-SE', {
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                      })
                    }}</span
                  ><button @click.stop="deleteLog(log.id)" class="btn-del">×</button>
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
            <h3>{{ actEditingId ? '📝 修改记录' : '➕ 新增记录' }}</h3>
            <button v-if="actEditingId" @click="cancelEditAct" class="btn-text">取消</button>
          </div>
          <div class="form-row">
            <div class="input-item">
              <label>时间</label><input type="datetime-local" v-model="actTime" />
            </div>
          </div>
          <div class="form-row">
            <div class="input-item">
              <label>活动</label
              ><select v-model="actType" class="act-select">
                <option v-for="opt in activityOptions" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="input-item">
              <label>备注</label><input type="text" v-model="actNotes" placeholder="细节描述" />
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
          <div v-for="group in groupedActivities" :key="group.dateKey" class="date-group">
            <div
              class="group-header"
              @click="group.isOld && toggleFold(group.dateKey, expandedActDates)"
              :class="{ clickable: group.isOld }"
            >
              <span class="group-date">
                {{ group.displayDate }}
                <small v-if="group.isOld" class="fold-tag tag-blue">
                  {{ expandedActDates.includes(group.dateKey) ? '🔼 收起' : '🔽 历史' }}
                </small>
              </span>
              <span class="group-total">{{ group.logs.length }}项记录</span>
            </div>
            <div class="log-grid" v-if="!group.isOld || expandedActDates.includes(group.dateKey)">
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
                      new Date(log.created_at).toLocaleTimeString('sv-SE', {
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                      })
                    }}</span
                  ><button @click.stop="deleteActivity(log.id)" class="btn-del">×</button>
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
        <span class="nav-icon">🍼</span><span class="nav-text">喝奶</span>
      </div>
      <div class="nav-item" :class="{ active: activeTab === 'other' }" @click="activeTab = 'other'">
        <span class="nav-icon">🌟</span><span class="nav-text">日常</span>
      </div>
    </nav>
  </div>
</template>

<style scoped>
/* 保持你原本优美的 CSS 样式不变 */
.app-wrapper {
  min-height: 100vh;
  background: #f0f2f5;
  padding-bottom: 90px;
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
.title-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.title-group h1 {
  text-align: center;
  font-size: 1.25rem;
  color: #2c3e50;
  margin: 0;
}
.title-group h2 {
  font-size: 0.85rem;
  color: #7f8c8d;
  margin: 0;
  font-weight: normal;
}
.card {
  background: white;
  border-radius: 12px;
  padding: 15px;
  margin-bottom: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}
.status-board {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 15px;
  border-radius: 12px;
  margin-bottom: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}
.status-ok {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
}
.status-warn {
  background: #fffbeb;
  border: 1px solid #fef08a;
  color: #b45309;
}
.status-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.main-status {
  display: flex;
  align-items: center;
  font-size: 0.9rem;
  font-weight: bold;
}
.sub-status {
  display: flex;
  align-items: center;
  font-size: 0.7rem;
  opacity: 0.8;
  margin-left: 2px;
}
.status-icon {
  margin-right: 8px;
}
.editing-mode {
  border: 2px solid #42b883;
}
.form-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
}
.form-header h3 {
  font-size: 0.95rem;
  margin: 0;
}
.form-row {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}
.input-item {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.input-item label {
  font-size: 0.75rem;
  color: #888;
  margin-bottom: 4px;
}
input,
select {
  padding: 10px;
  border: 1px solid #eee;
  border-radius: 8px;
  font-size: 1rem;
  width: 100%;
  box-sizing: border-box;
}
input[type='datetime-local'] {
  max-width: 100%;
  box-sizing: border-box;
  padding: 10px 2px;
  font-size: 0.9rem;
  -webkit-appearance: none;
  appearance: none;
  text-align: center;
}
.btn-primary {
  width: 100%;
  padding: 12px;
  background: #42b883;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: bold;
}
.group-header {
  display: flex;
  justify-content: space-between;
  padding: 10px 5px;
  border-bottom: 2px solid #eee;
  margin-bottom: 10px;
}
.clickable {
  cursor: pointer;
}
.group-date {
  font-weight: bold;
  display: flex;
  align-items: center;
}
.fold-tag {
  margin-left: 8px;
  font-size: 0.65rem;
  color: #42b883;
  background: #e8f5ee;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: normal;
}
.tag-blue {
  color: #3498db;
  background: #ebf5fb;
}
.group-total {
  color: #888;
  font-size: 0.85rem;
}
.log-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.log-cell {
  background: white;
  padding: 15px;
  border-radius: 12px;
  border-left: 4px solid #42b883;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
  cursor: pointer;
}
.act-cell {
  border-left-color: #3498db;
}
.log-cell-top {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
}
.log-time {
  color: #999;
  font-size: 0.8rem;
}
.btn-del {
  border: none;
  background: #fee;
  color: #f55;
  width: 22px;
  height: 22px;
  border-radius: 5px;
}
.log-amount {
  font-size: 1.3rem;
  font-weight: bold;
  color: #333;
}
.act-title {
  font-size: 1.1rem;
  color: #3498db;
}
.log-amount small {
  font-size: 0.8rem;
  color: #999;
  margin-left: 3px;
}
.log-note {
  margin-top: 8px;
  padding: 6px;
  background: #f9f9f9;
  border-radius: 6px;
  font-size: 0.85rem;
  color: #666;
}
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  background: white;
  display: flex;
  padding: 10px 0;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.05);
  padding-bottom: env(safe-area-inset-bottom, 10px);
}
.nav-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #ccc;
  cursor: pointer;
}
.nav-item.active {
  color: #2c3e50;
}
.nav-icon {
  font-size: 1.3rem;
  margin-bottom: 2px;
}
.nav-text {
  font-size: 0.7rem;
  font-weight: bold;
}
.btn-logout {
  background: #fee;
  color: #e74c3c;
  border: none;
  padding: 5px 10px;
  border-radius: 6px;
  font-size: 0.8rem;
  cursor: pointer;
}
</style>
