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

const renderSeries = (instanceRef, domRef, dayMap, name, unit, color) => {
  const dates = Object.keys(dayMap)
    .sort()
    .slice(-30)
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
        symbol: 'circle',
        symbolSize: 7,
        data: dates.map((d) => dayMap[d]),
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
  renderSeries(heightInstance, heightChartRef, heightByDay, '身高', 'cm', '#8e44ad')
  renderSeries(weightInstance, weightChartRef, weightByDay, '体重', 'kg', '#e67e22')
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

onMounted(() => {
  renderChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
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