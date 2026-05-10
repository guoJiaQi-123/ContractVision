<script setup>
import { ref, watch, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { getContractTrend } from '@/api/analytics'
import DESIGN_COLORS from '@/utils/colors'
use([CanvasRenderer, LineChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const timeGranularity = ref('month')
const dateRange = ref([])

const loading = ref({
  trend: true,
  yoy: true,
  mom: true
})

const trendOption = ref({})
const yoyOption = ref({})
const momOption = ref({})
const trendEmpty = ref(false)
const yoyEmpty = ref(false)
const momEmpty = ref(false)

const buildParams = () => {
  const params = { granularity: timeGranularity.value }
  if (dateRange.value && dateRange.value.length === 2) {
    params.start_date = dateRange.value[0]
    params.end_date = dateRange.value[1]
  }
  return params
}

const loadTrend = async () => {
  loading.value.trend = true
  trendEmpty.value = false
  try {
    const res = await getContractTrend(buildParams())
    const data = res.data
    if (!data || (!data.labels?.length && !data.revenue?.length)) {
      trendEmpty.value = true
      return
    }
    trendOption.value = {
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255, 255, 255, 0.96)',
        borderColor: '#F2F3F5',
        borderWidth: 1,
        textStyle: { color: '#4E5969', fontSize: 13 },
        axisPointer: { type: 'cross', crossStyle: { color: '#C9CDD4' } }
      },
      legend: {
        top: 0,
        right: 0,
        textStyle: { color: '#86909C', fontSize: 13 }
      },
      grid: { left: '3%', right: '4%', bottom: '3%', top: '14%', containLabel: true },
      xAxis: {
        type: 'category',
        data: data.labels || [],
        axisLine: { lineStyle: { color: '#E5E6EB' } },
        axisTick: { show: false },
        axisLabel: { color: '#86909C', fontSize: 12 }
      },
      yAxis: {
        type: 'value',
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#86909C', fontSize: 12 },
        splitLine: { lineStyle: { color: '#F2F3F5', type: 'dashed' } }
      },
      series: [
        {
          name: '实际金额',
          type: 'line',
          smooth: true,
          data: data.revenue || [],
          itemStyle: { color: DESIGN_COLORS.primary },
          lineStyle: { width: 2.5 },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(22, 93, 255, 0.18)' },
                { offset: 1, color: 'rgba(22, 93, 255, 0.01)' }
              ]
            }
          },
          symbol: 'circle',
          symbolSize: 6,
          emphasis: { focus: 'series' }
        },
        {
          name: '目标金额',
          type: 'line',
          smooth: true,
          data: data.target || [],
          itemStyle: { color: '#86909C' },
          lineStyle: { width: 2, type: 'dashed' },
          symbol: 'circle',
          symbolSize: 5,
          emphasis: { focus: 'series' }
        }
      ]
    }
  } catch {
    trendEmpty.value = true
  } finally {
    loading.value.trend = false
  }
}

const loadYoy = async () => {
  loading.value.yoy = true
  yoyEmpty.value = false
  try {
    const params = { ...buildParams(), compare: 'yoy' }
    const res = await getContractTrend(params)
    const data = res.data
    if (!data || (!data.labels?.length && !data.revenue?.length)) {
      yoyEmpty.value = true
      return
    }
    yoyOption.value = {
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255, 255, 255, 0.96)',
        borderColor: '#F2F3F5',
        borderWidth: 1,
        textStyle: { color: '#4E5969', fontSize: 13 }
      },
      legend: {
        top: 0,
        right: 0,
        textStyle: { color: '#86909C', fontSize: 13 }
      },
      grid: { left: '3%', right: '4%', bottom: '3%', top: '14%', containLabel: true },
      xAxis: {
        type: 'category',
        data: data.labels || [],
        axisLine: { lineStyle: { color: '#E5E6EB' } },
        axisTick: { show: false },
        axisLabel: { color: '#86909C', fontSize: 12 }
      },
      yAxis: {
        type: 'value',
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#86909C', fontSize: 12 },
        splitLine: { lineStyle: { color: '#F2F3F5', type: 'dashed' } }
      },
      series: [
        {
          name: '本期',
          type: 'line',
          smooth: true,
          data: data.revenue || [],
          itemStyle: { color: DESIGN_COLORS.primary },
          lineStyle: { width: 2.5 },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(22, 93, 255, 0.15)' },
                { offset: 1, color: 'rgba(22, 93, 255, 0.01)' }
              ]
            }
          },
          symbol: 'circle',
          symbolSize: 5
        },
        {
          name: '同期',
          type: 'line',
          smooth: true,
          data: data.target || [],
          itemStyle: { color: DESIGN_COLORS.warning },
          lineStyle: { width: 2 },
          symbol: 'circle',
          symbolSize: 5
        }
      ]
    }
  } catch {
    yoyEmpty.value = true
  } finally {
    loading.value.yoy = false
  }
}

const loadMom = async () => {
  loading.value.mom = true
  momEmpty.value = false
  try {
    const params = { ...buildParams(), compare: 'mom' }
    const res = await getContractTrend(params)
    const data = res.data
    if (!data || (!data.labels?.length && !data.revenue?.length)) {
      momEmpty.value = true
      return
    }
    const revenue = data.revenue || []
    const target = data.target || []
    const rateData = revenue.map((v, i) => {
      const prev = target[i]
      if (!prev) return null
      return +((v - prev) / prev * 100).toFixed(1)
    })
    momOption.value = {
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255, 255, 255, 0.96)',
        borderColor: '#F2F3F5',
        borderWidth: 1,
        textStyle: { color: '#4E5969', fontSize: 13 },
        formatter: (params) => {
          let html = `<div style="font-weight:600;margin-bottom:4px">${params[0].axisValue}</div>`
          params.forEach(p => {
            const val = p.seriesName === '环比增长率' ? `${p.value}%` : p.value
            html += `<div style="display:flex;align-items:center;gap:6px;margin:2px 0">
              <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${p.color}"></span>
              <span>${p.seriesName}：${val}</span>
            </div>`
          })
          return html
        }
      },
      legend: {
        top: 0,
        right: 0,
        textStyle: { color: '#86909C', fontSize: 13 }
      },
      grid: { left: '3%', right: '4%', bottom: '3%', top: '14%', containLabel: true },
      xAxis: {
        type: 'category',
        data: data.labels || [],
        axisLine: { lineStyle: { color: '#E5E6EB' } },
        axisTick: { show: false },
        axisLabel: { color: '#86909C', fontSize: 12 }
      },
      yAxis: [
        {
          type: 'value',
          axisLine: { show: false },
          axisTick: { show: false },
          axisLabel: { color: '#86909C', fontSize: 12 },
          splitLine: { lineStyle: { color: '#F2F3F5', type: 'dashed' } }
        },
        {
          type: 'value',
          axisLine: { show: false },
          axisTick: { show: false },
          axisLabel: { color: '#86909C', fontSize: 12, formatter: '{value}%' },
          splitLine: { show: false }
        }
      ],
      series: [
        {
          name: '本期金额',
          type: 'line',
          smooth: true,
          data: revenue,
          itemStyle: { color: DESIGN_COLORS.primary },
          lineStyle: { width: 2.5 },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(22, 93, 255, 0.15)' },
                { offset: 1, color: 'rgba(22, 93, 255, 0.01)' }
              ]
            }
          },
          symbol: 'circle',
          symbolSize: 5
        },
        {
          name: '环比增长率',
          type: 'line',
          smooth: true,
          yAxisIndex: 1,
          data: rateData,
          itemStyle: { color: DESIGN_COLORS.success },
          lineStyle: { width: 2, type: 'dashed' },
          symbol: 'diamond',
          symbolSize: 7
        }
      ]
    }
  } catch {
    momEmpty.value = true
  } finally {
    loading.value.mom = false
  }
}

const loadAll = () => {
  loadTrend()
  loadYoy()
  loadMom()
}

watch([timeGranularity, dateRange], () => {
  loadAll()
})

onMounted(() => {
  loadAll()
})
</script>

<template>
  <div class="analytics-trend-container">
    <div class="page-header">
      <div>
        <h1>趋势分析</h1>
        <p class="text-muted" style="margin-top: 4px;">合同金额趋势与目标对比分析</p>
      </div>
      <div class="header-actions">
        <el-radio-group v-model="timeGranularity" size="small">
          <el-radio-button value="week">按周</el-radio-button>
          <el-radio-button value="month">按月</el-radio-button>
          <el-radio-button value="quarter">按季</el-radio-button>
          <el-radio-button value="year">按年</el-radio-button>
        </el-radio-group>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          style="margin-left: 12px; width: 260px"
        />
      </div>
    </div>

    <div class="card chart-card">
      <div class="card-header">
        <h3>合同金额趋势</h3>
      </div>
      <div v-if="loading.trend" v-loading="true" class="chart-loading"></div>
      <el-empty v-else-if="trendEmpty" description="暂无趋势数据" />
      <v-chart v-else :option="trendOption" class="chart" autoresize />
    </div>

    <el-row :gutter="16" class="chart-section">
      <el-col :xs="24" :lg="12">
        <div class="card chart-card">
          <div class="card-header">
            <h3>同比分析</h3>
          </div>
          <div v-if="loading.yoy" v-loading="true" class="chart-loading"></div>
          <el-empty v-else-if="yoyEmpty" description="暂无同比数据" />
          <v-chart v-else :option="yoyOption" class="chart" autoresize />
        </div>
      </el-col>
      <el-col :xs="24" :lg="12">
        <div class="card chart-card">
          <div class="card-header">
            <h3>环比分析</h3>
          </div>
          <div v-if="loading.mom" v-loading="true" class="chart-loading"></div>
          <el-empty v-else-if="momEmpty" description="暂无环比数据" />
          <v-chart v-else :option="momOption" class="chart" autoresize />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<style lang="scss" scoped>
.analytics-trend-container {
  padding: 0;
  min-height: 100%;
  background: var(--bg-color);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border-light);

  h1 {
    font-size: var(--fs-xl);
    font-weight: 600;
    color: var(--text-primary);
    line-height: 1.4;
  }

  .text-muted {
    color: var(--text-muted);
    font-size: var(--fs-sm);
  }

  .header-actions {
    display: flex;
    align-items: center;
    flex-shrink: 0;
    gap: 12px;
  }
}

.card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
}

.chart-card {
  padding: 24px;
  margin-bottom: 16px;
  transition: box-shadow var(--transition-normal), border-color var(--transition-normal);

  &:hover {
    box-shadow: var(--shadow-md);
    border-color: var(--primary-light);
  }

  .card-header {
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;

    h3 {
      font-size: var(--fs-md);
      font-weight: 600;
      color: var(--text-primary);
      position: relative;
      padding-left: 12px;

      &::before {
        content: '';
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 3px;
        height: 16px;
        background: var(--primary);
        border-radius: 2px;
      }
    }
  }

  .chart {
    height: 340px;
    width: 100%;
  }

  .chart-loading {
    height: 340px;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

.chart-section {
  margin-bottom: 16px;

  .el-col {
    margin-bottom: 0;
  }
}
</style>
