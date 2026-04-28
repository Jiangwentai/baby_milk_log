<script setup>
import { ref, onMounted, watch, onUnmounted, shallowRef } from 'vue'
import * as echarts from 'echarts'

const props = defineProps(['logs'])
const chartRef = ref(null)
const chartInstance = shallowRef(null)

const renderChart = () => {
  if (!props.logs || props.logs.length === 0) return

  // 初始化图表实例
  if (!chartInstance.value) {
    chartInstance.value = echarts.init(chartRef.value)
  }

  // --- 核心逻辑：按 9:00 偏移量统计 ---
  const dailyData = {}

  props.logs.forEach((log) => {
    const date = new Date(log.created_at)
    // 关键点：将时间减去 9 小时
    date.setHours(date.getHours() - 9)
    const dateString = date.toLocaleDateString('en-CA').split('T')[0] // 获取 YYYY-MM-DD

    dailyData[dateString] = (dailyData[dateString] || 0) + log.amount_ml
  })

  // 排序日期（取最近 7 天）
  const sortedDates = Object.keys(dailyData).sort().slice(-7)
  const chartValues = sortedDates.map((date) => dailyData[date])

  // ECharts 配置项
  const option = {
    // 触摸/鼠标悬浮时的提示框
    tooltip: {
      trigger: 'axis',
      formatter: '{b} <br/>总奶量: <strong>{c} ml</strong>',
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
      borderColor: '#42b883',
      textStyle: { color: '#2c3e50' },
    },
    // 调整图表边距，防止在手机上被遮挡
    grid: {
      left: '2%',
      right: '6%',
      bottom: '5%',
      top: '10%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: sortedDates.map((d) => d.slice(5)), // 仅显示 月-日
      axisLine: { lineStyle: { color: '#ddd' } },
      axisLabel: { color: '#7f8c8d' },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { type: 'dashed', color: '#eee' } },
      axisLabel: { color: '#7f8c8d' },
    },
    series: [
      {
        name: '日总奶量',
        type: 'line',
        smooth: 0.4, // 平滑曲线
        symbol: 'circle', // 数据点样式
        symbolSize: 8,
        itemStyle: { color: '#42b883' },
        // 阴影面积渐变色
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(66, 184, 131, 0.6)' }, // 顶部颜色
            { offset: 1, color: 'rgba(66, 184, 131, 0.05)' }, // 底部颜色
          ]),
        },
        data: chartValues,
      },
    ],
  }

  // 渲染图表
  chartInstance.value.setOption(option)
}

// 监听数据变化，实时更新图表
watch(
  () => props.logs,
  () => renderChart(),
  { deep: true },
)

// 监听窗口大小变化，让 ECharts 自适应容器
const handleResize = () => {
  if (chartInstance.value) chartInstance.value.resize()
}

onMounted(() => {
  renderChart()
  window.addEventListener('resize', handleResize)
})

// 组件销毁时释放内存
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance.value) chartInstance.value.dispose()
})
</script>

<template>
  <div class="chart-container">
    <div ref="chartRef" class="chart-dom"></div>
  </div>
</template>

<style scoped>
.chart-container {
  width: 100%;
  height: 220px;
  margin-top: 10px;
}

.chart-dom {
  width: 100%;
  height: 100%;
}
</style>
