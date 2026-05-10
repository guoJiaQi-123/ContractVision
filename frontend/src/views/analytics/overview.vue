<script setup>
import { ref, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, BarChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { getDashboardStats, getStatusDistribution, getTopClients } from '@/api/analytics'
import { TrendCharts, Document, Warning, CircleCheck, ArrowUp, ArrowDown } from '@element-plus/icons-vue'
import DESIGN_COLORS from '@/utils/colors'
use([CanvasRenderer, PieChart, BarChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const dateRange = ref([])
const loading = ref({
  stats: true,
  distribution: true,
  ranking: true
})

const stats = ref({
  totalContracts: 0,
  totalAmount: 0,
  monthlyNew: 0,
  pendingAlerts: 0
})

const distributionOption = ref({})
const rankingOption = ref({})
const distributionEmpty = ref(false)
const rankingEmpty = ref(false)

const statCards = [
  {
    key: 'totalContracts',
    title: '签约合同数',
    unit: '个',
    icon: Document,
    color: DESIGN_COLORS.primary,
    bgColor: 'rgba(22, 93, 255, 0.08)'
  },
  {
    key: 'totalAmount',
    title: '签约总金额',
    unit: '万',
    icon: TrendCharts,
    color: DESIGN_COLORS.warning,
    bgColor: 'rgba(255, 125, 0, 0.08)'
  },
  {
    key: 'monthlyNew',
    title: '本月新签合同',
    unit: '个',
    icon: CircleCheck,
    color: DESIGN_COLORS.success,
    bgColor: 'rgba(0, 180, 42, 0.08)'
  },
  {
    key: 'pendingAlerts',
    title: '待处理预警',
    unit: '个',
    icon: Warning,
    color: DESIGN_COLORS.danger,
    bgColor: 'rgba(245, 63, 63, 0.08)'
  }
]

const loadStats = async () => {
  try {
    const res = await getDashboardStats()
    stats.value = res.data
  } catch {
    stats.value = { totalContracts: 0, totalAmount: 0, monthlyNew: 0, pendingAlerts: 0 }
  } finally {
    loading.value.stats = false
  }
}

const loadDistribution = async () => {
  try {
    const res = await getStatusDistribution()
    const items = res.data?.items || []
    if (!items.length) {
      distributionEmpty.value = true
      return
    }
    distributionOption.value = {
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { orient: 'vertical', right: '5%', top: 'center' },
      series: [
        {
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['35%', '50%'],
          data: items,
          itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
          label: { show: false }
        }
      ],
      color: [DESIGN_COLORS.primary, DESIGN_COLORS.success, DESIGN_COLORS.warning, DESIGN_COLORS.danger, DESIGN_COLORS.secondary1, DESIGN_COLORS.secondary2]
    }
  } catch {
    distributionEmpty.value = true
  } finally {
    loading.value.distribution = false
  }
}

const loadRanking = async () => {
  try {
    const res = await getTopClients()
    const items = res.data?.items || []
    if (!items.length) {
      rankingEmpty.value = true
      return
    }
    const names = items.map(i => i.name).reverse()
    const amounts = items.map(i => i.amount).reverse()
    rankingOption.value = {
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
      xAxis: {
        type: 'value',
        axisLine: { show: false },
        axisLabel: { color: '#86909C' },
        splitLine: { lineStyle: { color: '#F2F3F5' } }
      },
      yAxis: {
        type: 'category',
        data: names,
        axisLine: { show: false },
        axisLabel: { color: '#4E5969' }
      },
      series: [
        {
          name: '签约金额',
          type: 'bar',
          data: amounts,
          itemStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 1, y2: 0,
              colorStops: [
                { offset: 0, color: DESIGN_COLORS.primaryLight },
                { offset: 1, color: DESIGN_COLORS.primary }
              ]
            },
            borderRadius: [0, 4, 4, 0]
          },
          barWidth: '50%'
        }
      ]
    }
  } catch {
    rankingEmpty.value = true
  } finally {
    loading.value.ranking = false
  }
}

onMounted(() => {
  loadStats()
  loadDistribution()
  loadRanking()
})
</script>

<template>
  <div class="analytics-overview-container">
    <div class="page-header">
      <div>
        <h1>数据概览</h1>
        <p class="text-muted" style="margin-top: 4px;">实时监控销售合同核心指标</p>
      </div>
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        style="width: 280px"
      />
    </div>

    <el-row :gutter="16" class="stat-row">
      <el-col v-for="card in statCards" :key="card.key" :xs="24" :sm="12" :lg="6">
        <div class="stat-card" v-loading="loading.stats">
          <div class="stat-header">
            <div class="stat-icon" :style="{ backgroundColor: card.bgColor, color: card.color }">
              <el-icon :size="24"><component :is="card.icon" /></el-icon>
            </div>
          </div>
          <div class="stat-value">
            <span class="value">{{ stats[card.key] }}</span>
            <span class="unit">{{ card.unit }}</span>
          </div>
          <div class="stat-title">{{ card.title }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="chart-row">
      <el-col :xs="24" :lg="12">
        <div class="card chart-card">
          <div class="card-header">
            <h3>合同类型分布</h3>
          </div>
          <div v-if="loading.distribution" v-loading="true" class="chart-loading"></div>
          <el-empty v-else-if="distributionEmpty" description="暂无分布数据" />
          <v-chart v-else :option="distributionOption" class="chart" autoresize />
        </div>
      </el-col>
      <el-col :xs="24" :lg="12">
        <div class="card chart-card">
          <div class="card-header">
            <h3>客户签约排名 TOP10</h3>
          </div>
          <div v-if="loading.ranking" v-loading="true" class="chart-loading"></div>
          <el-empty v-else-if="rankingEmpty" description="暂无排名数据" />
          <v-chart v-else :option="rankingOption" class="chart" autoresize />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<style lang="scss" scoped>
.analytics-overview-container {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;

  h1 {
    font-size: var(--fs-xl);
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
  border-radius: var(--radius-lg);
  padding: 20px;
  margin-bottom: 16px;
  transition: all var(--transition-normal);

  &:hover {
    box-shadow: var(--shadow-md);
    border-color: var(--border-light);
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
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .stat-value {
    margin-bottom: 8px;

    .value {
      font-size: 28px;
      font-weight: 600;
      color: var(--text-primary);
      line-height: 1.2;
    }

    .unit {
      font-size: var(--fs-md);
      color: var(--text-secondary);
      margin-left: 4px;
    }
  }

  .stat-title {
    font-size: var(--fs-base);
    color: var(--text-muted);
  }
}

.chart-row {
  margin-bottom: 16px;
}

.chart-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 20px;
  margin-bottom: 16px;
  transition: all var(--transition-normal);

  &:hover {
    box-shadow: var(--shadow-sm);
  }

  .card-header {
    margin-bottom: 16px;

    h3 {
      font-size: var(--fs-md);
      font-weight: 600;
      color: var(--text-primary);
    }
  }

  .chart {
    height: 300px;
    width: 100%;
  }

  .chart-loading {
    height: 300px;
    width: 100%;
  }
}
</style>
