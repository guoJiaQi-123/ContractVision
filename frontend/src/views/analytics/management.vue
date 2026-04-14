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
  return (dashboardData.value.widget_data || []).find(item => item.type === 'ranking') || { list: [] }
})

const dashboardTrendOption = computed(() => {
  const trend = (dashboardData.value.widget_data || []).find(item => item.type === 'trend')
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 24, right: 16, top: 20, bottom: 24, containLabel: true },
    xAxis: { type: 'category', data: trend?.labels || [] },
    yAxis: { type: 'value' },
    series: [{ type: 'line', smooth: true, data: trend?.series || [], areaStyle: {} }]
  }
})

const drilldownOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 16, right: 16, top: 24, bottom: 24, containLabel: true },
  xAxis: { type: 'category', data: (drilldownData.value.list || []).map(item => item.name) },
  yAxis: { type: 'value' },
  series: [{ type: 'bar', data: (drilldownData.value.list || []).map(item => item.total_amount) }]
}))

const clvOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0 },
  series: [{
    type: 'pie',
    radius: ['42%', '70%'],
    data: [
      { name: '高价值', value: customerValue.value.segments?.high || 0 },
      { name: '中价值', value: customerValue.value.segments?.medium || 0 },
      { name: '低价值', value: customerValue.value.segments?.low || 0 }
    ]
  }]
}))

const taxOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 16, right: 16, top: 24, bottom: 24, containLabel: true },
  xAxis: { type: 'category', data: (taxAnalysis.value.monthly || []).map(item => item.month) },
  yAxis: { type: 'value' },
  series: [{ type: 'bar', data: (taxAnalysis.value.monthly || []).map(item => item.total_tax) }]
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
    <div class="hero">
      <div>
        <div class="eyebrow">F032 - F036 / F040</div>
        <h1>经营驾驶舱</h1>
        <p>覆盖目标达成预警、自定义看板、下钻联动、CLV、团队绩效与印花税统计。</p>
      </div>
    </div>

    <div class="warning-board">
      <div class="board-header">
        <h3>目标达成预警</h3>
        <span>{{ targetData.warnings?.length || 0 }} 个主体低于阈值</span>
      </div>
      <div class="warning-list">
        <div v-for="item in targetData.warnings" :key="item.id" class="warning-card">
          <div class="warning-title">{{ item.name }}</div>
          <div class="warning-meta">{{ item.owner_value }} / {{ item.period_label }}</div>
          <div class="warning-rate">{{ item.progress_rate }}%</div>
        </div>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :xl="14">
        <div class="panel">
          <div class="panel-header">
            <div>
              <h3>{{ dashboardData.config?.name || '默认驾驶舱' }}</h3>
              <p>自定义经营看板组件实时渲染</p>
            </div>
          </div>
          <div class="metric-grid">
            <div v-for="item in dashboardMetricCards" :key="item.id" class="metric-tile">
              <span>{{ item.title }}</span>
              <strong>{{ item.value }}</strong>
            </div>
          </div>
          <v-chart class="chart" :option="dashboardTrendOption" autoresize />
        </div>
      </el-col>
      <el-col :xs="24" :xl="10">
        <div class="panel">
          <div class="panel-header">
            <div>
              <h3>排名组件</h3>
              <p>驾驶舱内联榜单</p>
            </div>
          </div>
          <div v-for="(item, index) in dashboardRanking.list || []" :key="index" class="ranking-row">
            <span>#{{ index + 1 }} {{ item[dashboardRanking.field] }}</span>
            <strong>{{ item.amount }}</strong>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :xl="12">
        <div class="panel">
          <div class="panel-header">
            <div>
              <h3>多维下钻联动</h3>
              <p>从区域、部门、业务员到合同明细逐层下钻</p>
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
          <el-table :data="drilldownData.details || []" size="small">
            <el-table-column prop="contract_no" label="合同编号" min-width="140" />
            <el-table-column prop="client_name" label="客户" min-width="140" />
            <el-table-column prop="base_amount" label="本位币金额" width="130" />
          </el-table>
        </div>
      </el-col>
      <el-col :xs="24" :xl="12">
        <div class="panel">
          <div class="panel-header">
            <div>
              <h3>客户生命周期价值</h3>
              <p>自动划分高、中、低价值客户层级</p>
            </div>
          </div>
          <v-chart class="chart" :option="clvOption" autoresize />
          <el-table :data="customerValue.clients || []" size="small">
            <el-table-column prop="client_name" label="客户" min-width="150" />
            <el-table-column prop="level" label="层级" width="90" />
            <el-table-column prop="value_score" label="分值" width="90" />
            <el-table-column prop="total_amount" label="累计金额" width="120" />
          </el-table>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :xl="12">
        <div class="panel">
          <div class="panel-header">
            <div>
              <h3>团队 / 个人绩效分析</h3>
              <p>目标达成、回款率、客单价与签约数量综合对比</p>
            </div>
          </div>
          <el-table :data="teamPerformance">
            <el-table-column prop="salesperson" label="业务员" min-width="120" />
            <el-table-column prop="contract_count" label="合同数" width="90" />
            <el-table-column prop="total_amount" label="业绩额" width="120" />
            <el-table-column prop="recovery_rate" label="回款率" width="90" />
            <el-table-column prop="target_rate" label="目标达成" width="110" />
          </el-table>
        </div>
      </el-col>
      <el-col :xs="24" :xl="12">
        <div class="panel">
          <div class="panel-header">
            <div>
              <h3>印花税统计</h3>
              <p>按纳税周期自动汇总应缴税额</p>
            </div>
          </div>
          <div class="tax-summary">
            <div class="tax-box">
              <span>应缴税额</span>
              <strong>{{ taxAnalysis.summary.total_tax || 0 }}</strong>
            </div>
            <div class="tax-box">
              <span>合同数量</span>
              <strong>{{ taxAnalysis.summary.contract_count || 0 }}</strong>
            </div>
            <div class="tax-box">
              <span>未处理预警</span>
              <strong>{{ taxAnalysis.summary.pending_alerts || 0 }}</strong>
            </div>
          </div>
          <v-chart class="chart" :option="taxOption" autoresize />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped lang="scss">
.management-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero,
.warning-board,
.panel {
  background: #ffffff;
  border-radius: 20px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
}

.hero {
  padding: 28px;
  background:
    radial-gradient(circle at top right, rgba(34, 197, 94, 0.18), transparent 26%),
    radial-gradient(circle at left bottom, rgba(59, 130, 246, 0.16), transparent 24%),
    linear-gradient(140deg, #0f172a, #132238 52%, #1d4ed8);
  color: #f8fafc;

  h1 {
    margin: 8px 0;
    font-size: 30px;
  }

  p {
    margin: 0;
    color: rgba(226, 232, 240, 0.8);
  }
}

.eyebrow {
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #93c5fd;
}

.warning-board {
  padding: 20px;
}

.board-header,
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.board-header h3,
.panel-header h3 {
  margin: 0 0 4px;
}

.panel-header p {
  margin: 0;
  color: #64748b;
  font-size: 13px;
}

.warning-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.warning-card,
.metric-tile,
.tax-box {
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(248, 250, 252, 1), rgba(241, 245, 249, 1));
  border: 1px solid rgba(148, 163, 184, 0.16);
  padding: 16px;
}

.warning-title {
  font-weight: 600;
}

.warning-meta {
  margin-top: 6px;
  color: #64748b;
  font-size: 12px;
}

.warning-rate {
  margin-top: 14px;
  font-size: 28px;
  color: #dc2626;
}

.panel {
  padding: 20px;
  margin-bottom: 16px;
}

.metric-grid,
.tax-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.metric-tile,
.tax-box {
  span {
    display: block;
    color: #64748b;
    font-size: 13px;
  }

  strong {
    display: block;
    margin-top: 10px;
    font-size: 22px;
    color: #0f172a;
  }
}

.chart {
  height: 280px;
  width: 100%;
}

.ranking-row {
  display: flex;
  justify-content: space-between;
  padding: 12px 14px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.8);
}

@media (max-width: 960px) {
  .metric-grid,
  .tax-summary {
    grid-template-columns: 1fr;
  }
}
</style>
