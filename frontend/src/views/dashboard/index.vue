<script setup>
import { ref, computed, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart, BarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import { getDashboardStats, getContractTrend, getStatusDistribution, getRegionDistribution } from '@/api/analytics'
import { getContractList } from '@/api/contract'
import { TrendCharts, Document, Warning, CircleCheck, ArrowUp, ArrowDown, View } from '@element-plus/icons-vue'

use([
  CanvasRenderer,
  LineChart,
  PieChart,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

const stats = ref({
  totalContracts: 0,
  totalAmount: 0,
  monthlyNew: 0,
  pendingAlerts: 0
})

const trendOption = ref({})
const statusOption = ref({})
const regionOption = ref({})
const overdueList = ref([])
const overdueError = ref(false)

const loading = ref({
  stats: true,
  trend: true,
  status: true,
  region: true,
  overdue: true
})

const formatAmount = (val) => {
  if (!val && val !== 0) return '0.0'
  return (val / 10000).toFixed(1)
}

const statCards = computed(() => [
  {
    key: 'totalAmount',
    title: '累计合同金额',
    value: formatAmount(stats.value.totalAmount),
    unit: '万',
    icon: TrendCharts,
    color: '#165DFF',
    bgColor: 'rgba(22, 93, 255, 0.08)'
  },
  {
    key: 'monthlyNew',
    title: '本月新签合同',
    value: stats.value.monthlyNew,
    unit: '个',
    icon: Document,
    color: '#FF7D00',
    bgColor: 'rgba(255, 125, 0, 0.08)'
  },
  {
    key: 'pendingAlerts',
    title: '逾期合同数',
    value: stats.value.pendingAlerts,
    unit: '个',
    icon: Warning,
    color: '#F53F3F',
    bgColor: 'rgba(245, 63, 63, 0.08)'
  },
  {
    key: 'totalContracts',
    title: '合同总数',
    value: stats.value.totalContracts,
    unit: '个',
    icon: CircleCheck,
    color: '#00B42A',
    bgColor: 'rgba(0, 180, 42, 0.08)'
  }
])

const loadStats = async () => {
  try {
    const res = await getDashboardStats()
    stats.value = res.data
  } catch {
    stats.value = {
      totalContracts: 0,
      totalAmount: 0,
      monthlyNew: 0,
      pendingAlerts: 0
    }
  } finally {
    loading.value.stats = false
  }
}

const loadTrend = async () => {
  try {
    const res = await getContractTrend()
    const data = res.data
    trendOption.value = {
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'category',
        data: data.months || [],
        axisLine: { lineStyle: { color: '#F2F3F5' } },
        axisLabel: { color: '#86909C' }
      },
      yAxis: {
        type: 'value',
        axisLine: { show: false },
        axisLabel: { color: '#86909C' },
        splitLine: { lineStyle: { color: '#F2F3F5' } }
      },
      series: [
        {
          name: '实际金额',
          type: 'line',
          smooth: true,
          data: data.revenue || [],
          itemStyle: { color: '#165DFF' },
          lineStyle: { width: 2 },
          areaStyle: { color: 'rgba(22, 93, 255, 0.1)' },
          symbol: 'circle',
          symbolSize: 6
        },
        {
          name: '目标金额',
          type: 'line',
          smooth: true,
          data: data.target || [],
          itemStyle: { color: '#86909C' },
          lineStyle: { width: 2, type: 'dashed' },
          symbol: 'circle',
          symbolSize: 6
        }
      ]
    }
  } catch {
    trendOption.value = {}
  } finally {
    loading.value.trend = false
  }
}

const loadStatus = async () => {
  try {
    const res = await getStatusDistribution()
    const data = res.data
    statusOption.value = {
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { bottom: '0%', orient: 'horizontal' },
      series: [
        {
          type: 'pie',
          radius: ['45%', '70%'],
          center: ['50%', '45%'],
          data: data.items || [],
          itemStyle: {
            borderRadius: 4,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            show: true,
            formatter: '{b} {d}%'
          },
          emphasis: {
            itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.2)' }
          }
        }
      ],
      color: ['#165DFF', '#FF7D00', '#F53F3F', '#00B42A']
    }
  } catch {
    statusOption.value = {}
  } finally {
    loading.value.status = false
  }
}

const loadRegion = async () => {
  try {
    const res = await getRegionDistribution()
    const data = res.data
    regionOption.value = {
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'category',
        data: data.regions || [],
        axisLine: { lineStyle: { color: '#F2F3F5' } },
        axisLabel: { color: '#86909C' }
      },
      yAxis: {
        type: 'value',
        axisLine: { show: false },
        axisLabel: { color: '#86909C' },
        splitLine: { lineStyle: { color: '#F2F3F5' } }
      },
      series: [
        {
          name: '签约金额',
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
            borderRadius: [8, 8, 0, 0]
          },
          barWidth: '40%'
        }
      ]
    }
  } catch {
    regionOption.value = {}
  } finally {
    loading.value.region = false
  }
}

const loadOverdue = async () => {
  try {
    const res = await getContractList({ payment_status: 'overdue', page_size: 5 })
    overdueList.value = res.data?.results || res.data || []
    overdueError.value = false
  } catch {
    overdueList.value = []
    overdueError.value = true
  } finally {
    loading.value.overdue = false
  }
}

onMounted(() => {
  loadStats()
  loadTrend()
  loadStatus()
  loadRegion()
  loadOverdue()
})
</script>

<template>
  <div class="dashboard-container">
    <div class="page-header">
      <div>
        <h1>数据概览</h1>
        <p class="text-muted" style="margin-top: 4px;">实时监控销售合同核心指标</p>
      </div>
    </div>

    <el-row :gutter="16" class="stat-row">
      <el-col v-for="card in statCards" :key="card.key" :xs="24" :sm="12" :lg="6">
        <div class="stat-card" v-if="!loading.stats">
          <div class="stat-header">
            <div class="stat-icon" :style="{ backgroundColor: card.bgColor, color: card.color }">
              <el-icon :size="24"><component :is="card.icon" /></el-icon>
            </div>
          </div>
          <div class="stat-value">
            <span class="value">{{ card.value }}</span>
            <span class="unit">{{ card.unit }}</span>
          </div>
          <div class="stat-title">{{ card.title }}</div>
        </div>
        <div class="stat-card stat-card-skeleton" v-else>
          <div class="skeleton-header">
            <div class="skeleton-icon"></div>
          </div>
          <div class="skeleton-value"></div>
          <div class="skeleton-title"></div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="chart-row">
      <el-col :xs="24" :lg="12">
        <div class="card chart-card">
          <div class="card-header">
            <h3>月度合同金额趋势</h3>
            <div class="card-actions">
              <el-button size="small" type="primary" plain>近6个月</el-button>
              <el-button size="small" plain>近12个月</el-button>
            </div>
          </div>
          <div v-if="loading.trend" class="chart-skeleton">
            <div class="skeleton-line"></div>
            <div class="skeleton-line short"></div>
            <div class="skeleton-line"></div>
          </div>
          <el-empty v-else-if="!trendOption.series" description="暂无趋势数据" />
          <v-chart v-else :option="trendOption" class="chart" autoresize />
        </div>
      </el-col>
      <el-col :xs="24" :lg="12">
        <div class="card chart-card">
          <div class="card-header">
            <h3>合同类型占比</h3>
          </div>
          <div v-if="loading.status" class="chart-skeleton">
            <div class="skeleton-circle"></div>
          </div>
          <el-empty v-else-if="!statusOption.series" description="暂无状态数据" />
          <v-chart v-else :option="statusOption" class="chart" autoresize />
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="chart-row">
      <el-col :span="24">
        <div class="card chart-card">
          <div class="card-header">
            <h3>部门业绩排名</h3>
          </div>
          <div v-if="loading.region" class="chart-skeleton">
            <div class="skeleton-bar-group">
              <div class="skeleton-bar" v-for="i in 5" :key="i" :style="{ height: `${Math.random() * 60 + 30}%` }"></div>
            </div>
          </div>
          <el-empty v-else-if="!regionOption.series" description="暂无区域数据" />
          <v-chart v-else :option="regionOption" class="chart" autoresize />
        </div>
      </el-col>
    </el-row>

    <div class="card alert-card">
      <div class="card-header">
        <h3>逾期合同预警</h3>
        <router-link to="/contract" class="alert-link">查看全部 →</router-link>
      </div>
      <div v-if="loading.overdue" class="table-skeleton">
        <div class="skeleton-row" v-for="i in 3" :key="i">
          <div class="skeleton-cell long"></div>
          <div class="skeleton-cell medium"></div>
          <div class="skeleton-cell short"></div>
          <div class="skeleton-cell short"></div>
        </div>
      </div>
      <el-empty v-else-if="overdueError || overdueList.length === 0" description="暂无逾期合同" />
      <el-table v-else :data="overdueList" class="alert-table">
        <el-table-column prop="contract_number" label="合同编号" min-width="140">
          <template #default="{ row }">
            <router-link :to="`/contract/${row.id}`" class="contract-link">{{ row.contract_number }}</router-link>
          </template>
        </el-table-column>
        <el-table-column prop="client_name" label="客户名称" min-width="180" />
        <el-table-column prop="overdue_days" label="逾期天数" width="100">
          <template #default="{ row }">
            <span class="text-danger">{{ row.overdue_days }}天</span>
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" width="120">
          <template #default="{ row }">
            <span class="amount">¥{{ formatAmount(row.amount) }}万</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center">
          <template #default="{ row }">
            <router-link :to="`/contract/${row.id}`" class="action-link">
              <el-icon><View /></el-icon>
              查看
            </router-link>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.dashboard-container {
  padding: 0;
}

.page-header {
  margin-bottom: 24px;

  h1 {
    font-size: 24px;
    font-weight: 600;
    color: var(--text-primary);
  }
}

.stat-row {
  margin-bottom: 16px;
}

.stat-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: default;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  }

  .stat-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 16px;
  }

  .stat-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: transform 0.3s ease;
  }

  &:hover .stat-icon {
    transform: scale(1.08);
  }

  .stat-value {
    margin-bottom: 8px;

    .value {
      font-size: 28px;
      font-weight: 600;
      color: var(--text-primary);
    }

    .unit {
      font-size: 16px;
      color: var(--text-secondary);
      margin-left: 4px;
    }
  }

  .stat-title {
    font-size: 14px;
    color: var(--text-muted);
  }
}

.stat-card-skeleton {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;

  .skeleton-header {
    margin-bottom: 16px;
  }

  .skeleton-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    background: linear-gradient(90deg, #f2f3f5 25%, #e5e6eb 50%, #f2f3f5 75%);
    background-size: 200% 100%;
    animation: skeleton-loading 1.5s ease-in-out infinite;
  }

  .skeleton-value {
    width: 60%;
    height: 28px;
    border-radius: 6px;
    margin-bottom: 8px;
    background: linear-gradient(90deg, #f2f3f5 25%, #e5e6eb 50%, #f2f3f5 75%);
    background-size: 200% 100%;
    animation: skeleton-loading 1.5s ease-in-out infinite;
  }

  .skeleton-title {
    width: 40%;
    height: 14px;
    border-radius: 4px;
    background: linear-gradient(90deg, #f2f3f5 25%, #e5e6eb 50%, #f2f3f5 75%);
    background-size: 200% 100%;
    animation: skeleton-loading 1.5s ease-in-out infinite;
  }
}

@keyframes skeleton-loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

.chart-row {
  margin-bottom: 16px;
}

.card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
}

.chart-card {
  padding: 20px;
  margin-bottom: 16px;

  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;

    h3 {
      font-size: 16px;
      font-weight: 600;
      color: var(--text-primary);
    }

    .card-actions {
      display: flex;
      gap: 8px;

      :deep(.el-button) {
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 13px;

        &.is-primary {
          background: var(--primary-color);
          border-color: var(--primary-color);
          color: #ffffff;
        }
      }
    }
  }

  .chart {
    height: 280px;
    width: 100%;
  }
}

.chart-skeleton {
  height: 280px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;

  .skeleton-line {
    width: 80%;
    height: 12px;
    border-radius: 6px;
    background: linear-gradient(90deg, #f2f3f5 25%, #e5e6eb 50%, #f2f3f5 75%);
    background-size: 200% 100%;
    animation: skeleton-loading 1.5s ease-in-out infinite;

    &.short {
      width: 50%;
    }
  }

  .skeleton-circle {
    width: 160px;
    height: 160px;
    border-radius: 50%;
    background: linear-gradient(90deg, #f2f3f5 25%, #e5e6eb 50%, #f2f3f5 75%);
    background-size: 200% 100%;
    animation: skeleton-loading 1.5s ease-in-out infinite;
  }

  .skeleton-bar-group {
    width: 80%;
    height: 200px;
    display: flex;
    align-items: flex-end;
    justify-content: space-around;
    gap: 12px;

    .skeleton-bar {
      flex: 1;
      border-radius: 6px 6px 0 0;
      background: linear-gradient(90deg, #f2f3f5 25%, #e5e6eb 50%, #f2f3f5 75%);
      background-size: 200% 100%;
      animation: skeleton-loading 1.5s ease-in-out infinite;
    }
  }
}

.alert-card {
  padding: 20px;
  margin-bottom: 16px;

  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;

    h3 {
      font-size: 16px;
      font-weight: 600;
      color: var(--text-primary);
    }

    .alert-link {
      font-size: 14px;
      color: var(--primary-color);
      text-decoration: none;

      &:hover {
        color: var(--primary-light);
      }
    }
  }
}

.table-skeleton {
  .skeleton-row {
    display: flex;
    gap: 16px;
    padding: 14px 0;
    border-bottom: 1px solid var(--border-color);

    &:last-child {
      border-bottom: none;
    }
  }

  .skeleton-cell {
    height: 16px;
    border-radius: 4px;
    background: linear-gradient(90deg, #f2f3f5 25%, #e5e6eb 50%, #f2f3f5 75%);
    background-size: 200% 100%;
    animation: skeleton-loading 1.5s ease-in-out infinite;

    &.long {
      width: 120px;
    }

    &.medium {
      flex: 1;
    }

    &.short {
      width: 80px;
    }
  }
}

.alert-table {
  :deep(.el-table__header-wrapper) {
    th {
      background: var(--bg-color);
      color: var(--text-secondary);
      font-weight: 500;
      font-size: 14px;
      padding: 12px 0;
    }
  }

  :deep(.el-table__body-wrapper) {
    td {
      padding: 14px 0;
      border-bottom: 1px solid var(--border-color);
      font-size: 14px;
      color: var(--text-primary);
    }

    tr:last-child td {
      border-bottom: none;
    }

    tr:hover > td {
      background: rgba(242, 243, 245, 0.5);
    }
  }

  .contract-link {
    color: var(--primary-color);
    text-decoration: none;

    &:hover {
      color: var(--primary-light);
    }
  }

  .text-danger {
    color: #F53F3F;
  }

  .amount {
    font-weight: 500;
    color: var(--text-primary);
  }

  .action-link {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    color: var(--primary-color);
    text-decoration: none;
    padding: 4px 8px;
    border-radius: 4px;
    transition: all 0.2s;

    &:hover {
      background: rgba(22, 93, 255, 0.08);
    }
  }
}
</style>
