<script setup>
import { computed, onMounted, ref } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import {
  getSalesTargetProgress,
  getDashboardData,
  getDrilldownAnalysis,
  getCustomerValue,
  getTeamPerformance,
  getTaxAnalysis
} from '@/api/analytics'
import {
  Warning,
  DataAnalysis,
  TrendCharts,
  Histogram,
  User,
  Money
} from '@element-plus/icons-vue'
import DESIGN_COLORS from '@/utils/colors'
use([CanvasRenderer, BarChart, LineChart, PieChart, GridComponent, LegendComponent, TooltipComponent])

const targetData = ref({ list: [], warnings: [] })
const dashboardData = ref({ config: { widgets: [] }, widget_data: [] })
const drilldownDimension = ref('region')
const drilldownData = ref({ list: [], details: [] })
const customerValue = ref({ clients: [], segments: {} })
const teamPerformance = ref([])
const taxAnalysis = ref({ summary: {}, monthly: [], contract_types: [] })

const dashboardMetricCards = computed(() => {
  return (dashboardData.value.widget_data || []).filter(item => item.type === 'metric')
})

const dashboardRanking = computed(() => {
  return (dashboardData.value.widget_data || []).find(item => item.type === 'ranking') || { list: [], field: '' }
})

const dashboardTrendOption = computed(() => {
  const trend = (dashboardData.value.widget_data || []).find(item => item.type === 'trend')
  return {
    tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#E5E6EB', textStyle: { color: '#1D2129' } },
    grid: { left: 24, right: 16, top: 20, bottom: 24, containLabel: true },
    xAxis: {
      type: 'category',
      data: trend?.labels || [],
      axisLine: { lineStyle: { color: '#E5E6EB' } },
      axisLabel: { color: '#86909C' }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisLabel: { color: '#86909C' },
      splitLine: { lineStyle: { color: '#F2F3F5' } }
    },
    series: [{
      type: 'line',
      smooth: true,
      data: trend?.series || [],
      itemStyle: { color: DESIGN_COLORS.primary },
      lineStyle: { width: 2 },
      areaStyle: { color: 'rgba(22, 93, 255, 0.08)' },
      symbol: 'circle',
      symbolSize: 6
    }]
  }
})

const drilldownOption = computed(() => ({
  tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#E5E6EB', textStyle: { color: '#1D2129' } },
  grid: { left: 16, right: 16, top: 24, bottom: 24, containLabel: true },
  xAxis: {
    type: 'category',
    data: (drilldownData.value.list || []).map(item => item.name),
    axisLine: { lineStyle: { color: '#E5E6EB' } },
    axisLabel: { color: '#86909C' }
  },
  yAxis: {
    type: 'value',
    axisLine: { show: false },
    axisLabel: { color: '#86909C' },
    splitLine: { lineStyle: { color: '#F2F3F5' } }
  },
  series: [{
    type: 'bar',
    data: (drilldownData.value.list || []).map(item => item.total_amount),
    itemStyle: { color: DESIGN_COLORS.primary, borderRadius: [4, 4, 0, 0] },
    barWidth: '40%'
  }]
}))

const clvOption = computed(() => ({
  tooltip: { trigger: 'item', backgroundColor: '#fff', borderColor: '#E5E6EB', textStyle: { color: '#1D2129' } },
  legend: { bottom: 0, textStyle: { color: '#86909C' } },
  series: [{
    type: 'pie',
    radius: ['42%', '70%'],
    data: [
      { name: '高价值', value: customerValue.value.segments?.high || 0, itemStyle: { color: DESIGN_COLORS.primary } },
      { name: '中价值', value: customerValue.value.segments?.medium || 0, itemStyle: { color: DESIGN_COLORS.warning } },
      { name: '低价值', value: customerValue.value.segments?.low || 0, itemStyle: { color: '#86909C' } }
    ],
    itemStyle: { borderColor: '#fff', borderWidth: 2 },
    label: { color: '#4E5969' }
  }]
}))

const taxOption = computed(() => ({
  tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#E5E6EB', textStyle: { color: '#1D2129' } },
  grid: { left: 16, right: 16, top: 24, bottom: 24, containLabel: true },
  xAxis: {
    type: 'category',
    data: (taxAnalysis.value.monthly || []).map(item => item.month),
    axisLine: { lineStyle: { color: '#E5E6EB' } },
    axisLabel: { color: '#86909C' }
  },
  yAxis: {
    type: 'value',
    axisLine: { show: false },
    axisLabel: { color: '#86909C' },
    splitLine: { lineStyle: { color: '#F2F3F5' } }
  },
  series: [{
    type: 'bar',
    data: (taxAnalysis.value.monthly || []).map(item => item.total_tax),
    itemStyle: { color: DESIGN_COLORS.warning, borderRadius: [4, 4, 0, 0] },
    barWidth: '40%'
  }]
}))

const loadData = async () => {
  const [targetRes, dashboardRes, drilldownRes, clvRes, teamRes, taxRes] = await Promise.all([
    getSalesTargetProgress(),
    getDashboardData(),
    getDrilldownAnalysis({ dimension: drilldownDimension.value }),
    getCustomerValue(),
    getTeamPerformance({ dimension: 'salesperson' }),
    getTaxAnalysis()
  ])
  targetData.value = targetRes.data || { list: [], warnings: [] }
  dashboardData.value = dashboardRes.data || { config: { widgets: [] }, widget_data: [] }
  drilldownData.value = drilldownRes.data || { list: [], details: [] }
  customerValue.value = clvRes.data || { clients: [], segments: {} }
  teamPerformance.value = teamRes.data || []
  taxAnalysis.value = taxRes.data || { summary: {}, monthly: [], contract_types: [] }
}

const refreshDrilldown = async () => {
  const res = await getDrilldownAnalysis({ dimension: drilldownDimension.value })
  drilldownData.value = res.data || { list: [], details: [] }
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="management-page">
    <div class="page-header">
      <div>
        <h1>经营驾驶舱</h1>
        <p class="text-muted">目标达成预警、自定义看板、下钻联动、CLV、团队绩效与印花税统计</p>
      </div>
    </div>

    <div class="card warning-section">
      <div class="card-header">
        <div class="card-title-group">
          <div class="card-icon warning-icon">
            <el-icon :size="20"><Warning /></el-icon>
          </div>
          <div>
            <h3>目标达成预警</h3>
            <p class="card-desc">{{ targetData.warnings?.length || 0 }} 个主体低于阈值</p>
          </div>
        </div>
      </div>
      <div class="warning-grid">
        <div v-for="item in targetData.warnings" :key="item.id" class="warning-card">
          <div class="warning-card-top">
            <span class="warning-name">{{ item.name }}</span>
            <span class="warning-rate">{{ item.progress_rate }}%</span>
          </div>
          <div class="warning-card-bottom">
            <span>{{ item.owner_value }}</span>
            <span class="warning-period">{{ item.period_label }}</span>
          </div>
          <div class="warning-bar">
            <div class="warning-bar-fill" :style="{ width: Math.min(item.progress_rate, 100) + '%' }" />
          </div>
        </div>
        <div v-if="!targetData.warnings?.length" class="empty-hint">暂无预警数据</div>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :xl="14">
        <div class="card">
          <div class="card-header">
            <div class="card-title-group">
              <div class="card-icon primary-icon">
                <el-icon :size="20"><DataAnalysis /></el-icon>
              </div>
              <div>
                <h3>{{ dashboardData.config?.name || '默认驾驶舱' }}</h3>
                <p class="card-desc">自定义经营看板组件实时渲染</p>
              </div>
            </div>
          </div>
          <div class="metric-grid">
            <div v-for="item in dashboardMetricCards" :key="item.id" class="metric-card">
              <span class="metric-label">{{ item.title }}</span>
              <strong class="metric-value">{{ item.value }}</strong>
            </div>
          </div>
          <v-chart class="chart" :option="dashboardTrendOption" autoresize />
        </div>
      </el-col>
      <el-col :xs="24" :xl="10">
        <div class="card ranking-card">
          <div class="card-header">
            <div class="card-title-group">
              <div class="card-icon orange-icon">
                <el-icon :size="20"><Histogram /></el-icon>
              </div>
              <div>
                <h3>排名组件</h3>
                <p class="card-desc">驾驶舱内联榜单</p>
              </div>
            </div>
          </div>
          <div class="ranking-list">
            <div v-for="(item, index) in dashboardRanking.list || []" :key="index" class="ranking-row">
              <div class="ranking-left">
                <span class="ranking-index" :class="{ 'top3': index < 3 }">{{ index + 1 }}</span>
                <span class="ranking-name">{{ item[dashboardRanking.field] }}</span>
              </div>
              <span class="ranking-value">{{ item.amount }}</span>
            </div>
            <div v-if="!dashboardRanking.list?.length" class="empty-hint">暂无排名数据</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :xl="12">
        <div class="card">
          <div class="card-header">
            <div class="card-title-group">
              <div class="card-icon primary-icon">
                <el-icon :size="20"><TrendCharts /></el-icon>
              </div>
              <div>
                <h3>多维下钻联动</h3>
                <p class="card-desc">从区域、部门、业务员到合同明细逐层下钻</p>
              </div>
            </div>
            <el-select v-model="drilldownDimension" style="width: 140px" @change="refreshDrilldown">
              <el-option label="区域" value="region" />
              <el-option label="部门" value="department" />
              <el-option label="业务员" value="salesperson" />
              <el-option label="客户" value="client" />
              <el-option label="产品" value="product" />
            </el-select>
          </div>
          <v-chart class="chart" :option="drilldownOption" autoresize />
          <el-table :data="drilldownData.details || []" size="small" class="inner-table">
            <el-table-column prop="contract_no" label="合同编号" min-width="140" />
            <el-table-column prop="client_name" label="客户" min-width="140" />
            <el-table-column prop="base_amount" label="本位币金额" width="130" />
          </el-table>
        </div>
      </el-col>
      <el-col :xs="24" :xl="12">
        <div class="card">
          <div class="card-header">
            <div class="card-title-group">
              <div class="card-icon orange-icon">
                <el-icon :size="20"><User /></el-icon>
              </div>
              <div>
                <h3>客户生命周期价值</h3>
                <p class="card-desc">自动划分高、中、低价值客户层级</p>
              </div>
            </div>
          </div>
          <v-chart class="chart" :option="clvOption" autoresize />
          <el-table :data="customerValue.clients || []" size="small" class="inner-table">
            <el-table-column prop="client_name" label="客户" min-width="150" />
            <el-table-column prop="level" label="层级" width="90">
              <template #default="{ row }">
                <el-tag
                  :type="row.level === '高价值' ? 'primary' : row.level === '中价值' ? 'warning' : 'info'"
                  size="small"
                  effect="plain"
                >{{ row.level }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="value_score" label="分值" width="90" />
            <el-table-column prop="total_amount" label="累计金额" width="120" />
          </el-table>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :xl="12">
        <div class="card">
          <div class="card-header">
            <div class="card-title-group">
              <div class="card-icon primary-icon">
                <el-icon :size="20"><User /></el-icon>
              </div>
              <div>
                <h3>团队 / 个人绩效分析</h3>
                <p class="card-desc">目标达成、回款率、客单价与签约数量综合对比</p>
              </div>
            </div>
          </div>
          <el-table :data="teamPerformance" class="inner-table">
            <el-table-column prop="salesperson" label="业务员" min-width="120" />
            <el-table-column prop="contract_count" label="合同数" width="90" align="center" />
            <el-table-column prop="total_amount" label="业绩额" width="120" align="right" />
            <el-table-column prop="recovery_rate" label="回款率" width="90" align="center">
              <template #default="{ row }">
                <span :class="{ 'text-success': Number(row.recovery_rate) >= 80, 'text-danger': Number(row.recovery_rate) < 60 }">
                  {{ row.recovery_rate }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="target_rate" label="目标达成" width="110" align="center">
              <template #default="{ row }">
                <span :class="{ 'text-success': Number(row.target_rate) >= 100, 'text-danger': Number(row.target_rate) < 80 }">
                  {{ row.target_rate }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
      <el-col :xs="24" :xl="12">
        <div class="card">
          <div class="card-header">
            <div class="card-title-group">
              <div class="card-icon orange-icon">
                <el-icon :size="20"><Money /></el-icon>
              </div>
              <div>
                <h3>印花税统计</h3>
                <p class="card-desc">按纳税周期自动汇总应缴税额</p>
              </div>
            </div>
          </div>
          <div class="tax-summary">
            <div class="tax-stat">
              <span class="tax-stat-label">应缴税额</span>
              <strong class="tax-stat-value">{{ taxAnalysis.summary.total_tax || 0 }}</strong>
            </div>
            <div class="tax-stat">
              <span class="tax-stat-label">合同数量</span>
              <strong class="tax-stat-value">{{ taxAnalysis.summary.contract_count || 0 }}</strong>
            </div>
            <div class="tax-stat">
              <span class="tax-stat-label">未处理预警</span>
              <strong class="tax-stat-value text-danger">{{ taxAnalysis.summary.pending_alerts || 0 }}</strong>
            </div>
          </div>
          <v-chart class="chart" :option="taxOption" autoresize />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<style lang="scss" scoped>
.management-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  margin-bottom: 4px;

  h1 {
    font-size: var(--fs-xl);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 4px;
  }
}

.card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.card-title-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.card-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.primary-icon {
  background: var(--primary-bg);
  color: var(--primary);
}

.warning-icon {
  background: var(--danger-bg);
  color: var(--danger);
}

.orange-icon {
  background: var(--warning-bg);
  color: var(--warning);
}

.card-header h3 {
  margin: 0;
  font-size: var(--fs-md);
  font-weight: 600;
  color: var(--text-primary);
}

.card-desc {
  margin: 2px 0 0;
  font-size: var(--fs-sm);
  color: var(--text-muted);
}

.warning-section {
  border-left: 3px solid var(--danger);
}

.warning-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.warning-card {
  background: var(--bg-color);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 14px 16px;
  transition: box-shadow var(--transition-fast);

  &:hover {
    box-shadow: var(--shadow-sm);
  }
}

.warning-card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.warning-name {
  font-weight: 600;
  font-size: var(--fs-base);
  color: var(--text-primary);
}

.warning-rate {
  font-size: var(--fs-lg);
  font-weight: 700;
  color: var(--danger);
}

.warning-card-bottom {
  display: flex;
  justify-content: space-between;
  font-size: var(--fs-xs);
  color: var(--text-muted);
  margin-bottom: 10px;
}

.warning-period {
  color: var(--text-secondary);
}

.warning-bar {
  height: 4px;
  background: var(--gray-100);
  border-radius: 2px;
  overflow: hidden;
}

.warning-bar-fill {
  height: 100%;
  background: var(--danger);
  border-radius: 2px;
  transition: width 0.6s ease;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.metric-card {
  background: var(--bg-color);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 14px 16px;
  transition: box-shadow var(--transition-fast);

  &:hover {
    box-shadow: var(--shadow-sm);
  }
}

.metric-label {
  display: block;
  color: var(--text-muted);
  font-size: var(--fs-sm);
  margin-bottom: 8px;
}

.metric-value {
  display: block;
  font-size: var(--fs-xl);
  color: var(--text-primary);
}

.chart {
  height: 280px;
  width: 100%;
}

.ranking-card {
  display: flex;
  flex-direction: column;
}

.ranking-list {
  flex: 1;
}

.ranking-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-light);
  transition: background var(--transition-fast);

  &:hover {
    background: var(--gray-50);
  }

  &:last-child {
    border-bottom: none;
  }
}

.ranking-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ranking-index {
  width: 24px;
  height: 24px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--fs-xs);
  font-weight: 600;
  color: var(--text-muted);
  background: var(--bg-color);
}

.ranking-index.top3 {
  background: var(--primary-bg);
  color: var(--primary);
}

.ranking-name {
  font-size: var(--fs-base);
  color: var(--text-primary);
}

.ranking-value {
  font-size: var(--fs-base);
  font-weight: 600;
  color: var(--text-primary);
}

.inner-table {
  :deep(.el-table__header-wrapper th) {
    background: var(--bg-color);
    color: var(--text-secondary);
    font-weight: 500;
    font-size: var(--fs-sm);
  }

  :deep(.el-table__body-wrapper td) {
    font-size: var(--fs-sm);
    color: var(--text-primary);
  }
}

.tax-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.tax-stat {
  background: var(--bg-color);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 14px 16px;
}

.tax-stat-label {
  display: block;
  color: var(--text-muted);
  font-size: var(--fs-sm);
  margin-bottom: 8px;
}

.tax-stat-value {
  display: block;
  font-size: var(--fs-xl);
  color: var(--text-primary);
}

.text-success {
  color: var(--success);
}

.text-danger {
  color: var(--danger);
}

.empty-hint {
  color: var(--text-muted);
  font-size: var(--fs-sm);
  padding: 24px 0;
  text-align: center;
}

@media (max-width: 960px) {
  .metric-grid,
  .tax-summary {
    grid-template-columns: 1fr;
  }
}
</style>
