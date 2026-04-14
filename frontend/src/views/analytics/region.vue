<script setup>
import { ref, watch, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, PieChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { getRegionDistribution } from '@/api/analytics'

use([CanvasRenderer, BarChart, PieChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const currentYear = new Date().getFullYear()
const selectedYear = ref(currentYear.toString())

const yearOptions = Array.from({ length: 5 }, (_, i) => (currentYear - i).toString())

const loading = ref({
  overview: true,
  bar: true,
  pie: true
})

const overviewOption = ref({})
const barOption = ref({})
const pieOption = ref({})
const overviewEmpty = ref(false)
const barEmpty = ref(false)
const pieEmpty = ref(false)

const loadOverview = async () => {
  loading.value.overview = true
  overviewEmpty.value = false
  try {
    const res = await getRegionDistribution({ year: selectedYear.value })
    const data = res.data
    if (!data || !data.regions?.length) {
      overviewEmpty.value = true
      return
    }
    overviewOption.value = {
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255, 255, 255, 0.96)',
        borderColor: '#F2F3F5',
        borderWidth: 1,
        textStyle: { color: '#4E5969', fontSize: 13 },
        axisPointer: { type: 'shadow' }
      },
      legend: {
        top: 0,
        right: 0,
        textStyle: { color: '#86909C', fontSize: 13 }
      },
      grid: { left: '3%', right: '4%', bottom: '3%', top: '14%', containLabel: true },
      xAxis: {
        type: 'category',
        data: data.regions || [],
        axisLine: { lineStyle: { color: '#E5E6EB' } },
        axisTick: { show: false },
        axisLabel: { color: '#86909C', fontSize: 12, rotate: data.regions.length > 8 ? 30 : 0 }
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
          name: '合同金额',
          type: 'bar',
          data: data.counts || [],
          itemStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: '#165DFF' },
                { offset: 1, color: '#4080FF' }
              ]
            },
            borderRadius: [6, 6, 0, 0]
          },
          barWidth: '45%',
          emphasis: {
            itemStyle: {
              color: {
                type: 'linear',
                x: 0, y: 0, x2: 0, y2: 1,
                colorStops: [
                  { offset: 0, color: '#0E42D2' },
                  { offset: 1, color: '#165DFF' }
                ]
              }
            }
          }
        }
      ]
    }
  } catch {
    overviewEmpty.value = true
  } finally {
    loading.value.overview = false
  }
}

const loadBar = async () => {
  loading.value.bar = true
  barEmpty.value = false
  try {
    const res = await getRegionDistribution({ year: selectedYear.value })
    const data = res.data
    if (!data || !data.regions?.length) {
      barEmpty.value = true
      return
    }
    const paired = (data.regions || []).map((r, i) => ({ name: r, value: (data.counts || [])[i] || 0 }))
    paired.sort((a, b) => a.value - b.value)
    const names = paired.map(p => p.name)
    const values = paired.map(p => p.value)
    barOption.value = {
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255, 255, 255, 0.96)',
        borderColor: '#F2F3F5',
        borderWidth: 1,
        textStyle: { color: '#4E5969', fontSize: 13 },
        axisPointer: { type: 'shadow' }
      },
      grid: { left: '3%', right: '4%', bottom: '3%', top: '6%', containLabel: true },
      xAxis: {
        type: 'value',
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#86909C', fontSize: 12 },
        splitLine: { lineStyle: { color: '#F2F3F5', type: 'dashed' } }
      },
      yAxis: {
        type: 'category',
        data: names,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#4E5969', fontSize: 12 }
      },
      series: [
        {
          name: '签约金额',
          type: 'bar',
          data: values,
          itemStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 1, y2: 0,
              colorStops: [
                { offset: 0, color: '#4080FF' },
                { offset: 1, color: '#165DFF' }
              ]
            },
            borderRadius: [0, 4, 4, 0]
          },
          barWidth: '55%'
        }
      ]
    }
  } catch {
    barEmpty.value = true
  } finally {
    loading.value.bar = false
  }
}

const loadPie = async () => {
  loading.value.pie = true
  pieEmpty.value = false
  try {
    const res = await getRegionDistribution({ year: selectedYear.value })
    const data = res.data
    if (!data || !data.regions?.length) {
      pieEmpty.value = true
      return
    }
    const pieData = (data.regions || []).map((r, i) => ({
      name: r,
      value: (data.counts || [])[i] || 0
    }))
    pieOption.value = {
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(255, 255, 255, 0.96)',
        borderColor: '#F2F3F5',
        borderWidth: 1,
        textStyle: { color: '#4E5969', fontSize: 13 },
        formatter: '{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        right: '5%',
        top: 'center',
        textStyle: { color: '#86909C', fontSize: 12 }
      },
      series: [
        {
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['35%', '50%'],
          data: pieData,
          itemStyle: {
            borderRadius: 6,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: { show: false },
          emphasis: {
            itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.15)' },
            label: { show: true, fontSize: 14, fontWeight: 600 }
          }
        }
      ],
      color: ['#165DFF', '#00B42A', '#FF7D00', '#F53F3F', '#722ED1', '#0FC6C2', '#F77234', '#3491FA']
    }
  } catch {
    pieEmpty.value = true
  } finally {
    loading.value.pie = false
  }
}

const loadAll = () => {
  loadOverview()
  loadBar()
  loadPie()
}

watch(selectedYear, () => {
  loadAll()
})

onMounted(() => {
  loadAll()
})
</script>

<template>
  <div class="analytics-region-container">
    <div class="page-header">
      <div>
        <h1>区域分析</h1>
        <p class="text-muted" style="margin-top: 4px;">各区域合同金额分布与占比分析</p>
      </div>
      <el-select v-model="selectedYear" placeholder="选择年份" style="width: 120px">
        <el-option v-for="y in yearOptions" :key="y" :label="`${y}年`" :value="y" />
      </el-select>
    </div>

    <div class="card chart-card">
      <div class="card-header">
        <h3>区域合同金额分布</h3>
      </div>
      <div v-if="loading.overview" v-loading="true" class="chart-loading"></div>
      <el-empty v-else-if="overviewEmpty" description="暂无区域数据" />
      <v-chart v-else :option="overviewOption" class="chart chart-large" autoresize />
    </div>

    <el-row :gutter="16" class="chart-section">
      <el-col :xs="24" :lg="12">
        <div class="card chart-card">
          <div class="card-header">
            <h3>区域合同金额排名</h3>
          </div>
          <div v-if="loading.bar" v-loading="true" class="chart-loading"></div>
          <el-empty v-else-if="barEmpty" description="暂无排名数据" />
          <v-chart v-else :option="barOption" class="chart" autoresize />
        </div>
      </el-col>
      <el-col :xs="24" :lg="12">
        <div class="card chart-card">
          <div class="card-header">
            <h3>区域合同占比</h3>
          </div>
          <div v-if="loading.pie" v-loading="true" class="chart-loading"></div>
          <el-empty v-else-if="pieEmpty" description="暂无占比数据" />
          <v-chart v-else :option="pieOption" class="chart" autoresize />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<style lang="scss" scoped>
.analytics-region-container {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;

  h1 {
    font-size: 24px;
    font-weight: 600;
    color: var(--text-primary);
  }
}

.card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
}

.chart-card {
  padding: 20px;
  margin-bottom: 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

  &:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  }

  .card-header {
    margin-bottom: 16px;

    h3 {
      font-size: 16px;
      font-weight: 600;
      color: var(--text-primary);
    }
  }

  .chart {
    height: 300px;
    width: 100%;
  }

  .chart-large {
    height: 360px;
  }

  .chart-loading {
    height: 300px;
    width: 100%;
  }
}

.chart-section {
  margin-bottom: 16px;
}
</style>
