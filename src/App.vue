<script setup>
import { ref, onMounted, computed } from 'vue'
import { supabase } from './supabase'
import UserAuth from './components/UserAuth.vue'
import MilkChart from './components/MilkChart.vue'

// ==== 全局状态 ====
const session = ref(null)
const activeTab = ref('milk')
const loading = ref(false)
const expandedDates = ref([]) // 喝奶页面的展开记录
const expandedActDates = ref([]) // 日常页面的展开记录

function getCurrentDateTime() {
  const now = new Date()
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset())
  return now.toISOString().slice(0, 16)
}

// 切换折叠状态 (通用逻辑)
// 切换折叠状态 (修复版)
function toggleFold(dateKey, targetList) {
  // 因为从 template 传进来的已经是解包后的数组，所以不需要加 .value
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

  // 3天折叠阈值
  const now = new Date()
  const todayOffset = new Date(now.getTime() - 9 * 60 * 60 * 1000)
  const threeDaysAgo = new Date(todayOffset)
  threeDaysAgo.setDate(threeDaysAgo.getDate() - 3)
  const thresholdKey = threeDaysAgo.toISOString().split('T')[0]

  amountList.value.forEach((log) => {
    const date = new Date(log.created_at)
    const offsetDate = new Date(date.getTime() - 9 * 60 * 60 * 1000)
    const dateKey = offsetDate.toISOString().split('T')[0]
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
  const todayKey = todayOffset.toISOString().split('T')[0]
  const todayGroup = groupedLogs.value.find((g) => g.dateKey === todayKey)
  const todayTotal = todayGroup ? todayGroup.total : 0
  const pastGroups = groupedLogs.value.filter((g) => g.dateKey < todayKey)
  if (pastGroups.length === 0) return null
  const recent7Groups = pastGroups.slice(0, 7)
  const pastTotal = recent7Groups.reduce((sum, g) => sum + g.total, 0)
  const pastAverage = Math.round(pastTotal / recent7Groups.length)
  const diff = pastAverage - todayTotal
  return { todayTotal, average: pastAverage, diff: diff > 0 ? diff : 0, isAchieved: diff <= 0 }
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
  if (!window.confirm(`确认${actionName}奶粉记录？`)) return
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

  // 5 天折叠阈值
  const now = new Date()
  const fiveDaysAgo = new Date(now)
  fiveDaysAgo.setDate(fiveDaysAgo.getDate() - 5)
  const thresholdKey = fiveDaysAgo.toISOString().split('T')[0]

  activityList.value.forEach((log) => {
    const date = new Date(log.created_at)
    const dateKey = date.toISOString().split('T')[0]
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
  if (!window.confirm(`确认保存日常记录吗？`)) return
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
        <div class="status-board" :class="hasTakenVitaminToday ? 'status-ok' : 'status-warn'">
          <div class="status-left">
            <div class="main-status">
              <span class="status-icon">{{ hasTakenVitaminToday ? '✅' : '⚠️' }}</span>
              <span class="status-text">{{
                hasTakenVitaminToday ? '今日已吃维生素' : '今日还没吃维生素哦'
              }}</span>
            </div>
            <div class="sub-status" v-if="milkTargetStats">
              <span class="sub-icon">{{ milkTargetStats.isAchieved ? '🎉' : '🍼' }}</span>
              <span>{{
                milkTargetStats.isAchieved
                  ? `今日奶量 ${milkTargetStats.todayTotal}ml，已达标！`
                  : `距7日均线(${milkTargetStats.average}ml)还差 ${milkTargetStats.diff}ml`
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
                      new Date(log.created_at).toLocaleTimeString('zh-CN', {
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
                      new Date(log.created_at).toLocaleTimeString('zh-CN', {
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
.header h1 {
  font-size: 1.3rem;
  color: #2c3e50;
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
</style>
