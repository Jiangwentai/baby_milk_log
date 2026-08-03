<script setup>
import { ref, onMounted, watch, onUnmounted, shallowRef } from 'vue'
import * as echarts from 'echarts'

const props = defineProps(['logs'])
const heightChartRef = ref(null)
const weightChartRef = ref(null)
const heightInstance = shallowRef(null)
const weightInstance = shallowRef(null)

const buildDailyData = () => {
  const heightByDay = {}
  const weightByDay = {}
  props.logs.forEach((log) => {
    const date = new Date(log.created_at)
    date.setHours(date.getHours() - 9)
    const dateKey = date.toLocaleDateString('sv-SE')
    if (log.height_cm != null) heightByDay[dateKey] = log.height_cm
    if (log.weight_kg != null) weightByDay[dateKey] = log.weight_kg
  })
  return { heightByDay, weightByDay }
}

const renderSeries = (instanceRef, domRef, data, dates, name, unit, color) => {
  if (!dates.length) return
  if (!instanceRef.value) {
    instanceRef.value = echarts.init(domRef.value)
  }
  const option = {
    color: [color],
    title: {
      text: `${name}趋势`,
      left: 'center',
      textStyle: { fontSize: 13, color: '#7f8c8d' },
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const p = params[0]
        const dateKey = dates[p.dataIndex]
        return `<div style="font-weight:bold">${dateKey}</div><div>${p.marker}${name}: <strong>${p.value}</strong> ${unit}</div>`
      },
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
      borderColor: color,
      textStyle: { color: '#2c3e50' },
    },
    grid: {
      left: '6%',
      right: '8%',
      bottom: '5%',
      top: '14%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates.map((d) => d.slice(5)),
      axisLine: { lineStyle: { color: '#ddd' } },
      axisLabel: { color: '#7f8c8d' },
    },
    yAxis: {
      type: 'value',
      name: unit,
      nameTextStyle: { color },
      axisLabel: { color },
      splitLine: { lineStyle: { type: 'dashed', color: '#eee' } },
    },
    series: [
      {
        name,
        type: 'line',
        smooth: 0.4,
        data,
        connectNulls: false,
        itemStyle: { color },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: `${color}73` },
            { offset: 1, color: `${color}08` },
          ]),
        },
      },
    ],
  }
  instanceRef.value.setOption(option)
}

const renderChart = () => {
  if (!props.logs || props.logs.length === 0) return
  const { heightByDay, weightByDay } = buildDailyData()

  const today = new Date(new Date().getTime() - 9 * 60 * 60 * 1000)
  let end = new Date(today)
  let start = new Date(today)
  props.logs.forEach((log) => {
    const d = new Date(log.created_at)
    d.setHours(d.getHours() - 9)
    if (d > end) end = d
    if (d < start) start = d
  })

  const spanDays = Math.round((end - start) / (24 * 60 * 60 * 1000))
  const from = new Date(end)
  if (spanDays + 1 > 180) {
    from.setDate(from.getDate() - 179)
  } else {
    from.setTime(start.getTime())
  }
  const lo = new Date(from.getFullYear(), from.getMonth(), from.getDate(), 12)
  const hi = new Date(end.getFullYear(), end.getMonth(), end.getDate(), 12)

  const dates = []
  const cur = new Date(lo)
  while (cur <= hi) {
    dates.push(cur.toLocaleDateString('sv-SE'))
    cur.setDate(cur.getDate() + 1)
  }

  const fillSeries = (dayMap) => {
    let last = null
    return dates.map((d) => {
      const real = dayMap[d] != null
      if (real) last = dayMap[d]
      if (last == null) return null
      return real ? { value: last, symbol: 'circle', symbolSize: 9 } : { value: last, symbol: 'none' }
    })
  }

  renderSeries(heightInstance, heightChartRef, fillSeries(heightByDay), dates, '身高', 'cm', '#8e44ad')
  renderSeries(weightInstance, weightChartRef, fillSeries(weightByDay), dates, '体重', 'kg', '#e67e22')
}

watch(
  () => props.logs,
  () => renderChart(),
  { deep: true },
)

const handleResize = () => {
  if (heightInstance.value) heightInstance.value.resize()
  if (weightInstance.value) weightInstance.value.resize()
}

let resizeObserver = null

onMounted(() => {
  renderChart()
  if (window.ResizeObserver) {
    resizeObserver = new ResizeObserver(() => {
      handleResize()
    })
    resizeObserver.observe(heightChartRef.value)
    resizeObserver.observe(weightChartRef.value)
  }
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  window.removeEventListener('resize', handleResize)
  if (heightInstance.value) heightInstance.value.dispose()
  if (weightInstance.value) weightInstance.value.dispose()
})
</script>

<template>
  <div class="chart-container">
    <div ref="heightChartRef" class="chart-dom"></div>
    <div ref="weightChartRef" class="chart-dom"></div>
  </div>
</template>

<style scoped>
.chart-container {
  width: 100%;
  margin-top: 10px;
}

.chart-dom {
  width: 100%;
  height: 220px;
}

.chart-dom + .chart-dom {
  margin-top: 8px;
}
</style>