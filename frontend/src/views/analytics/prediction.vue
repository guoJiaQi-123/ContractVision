<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getSalesPrediction, getCustomerValue, getAnomalyDetection } from '@/api/analytics'
import DESIGN_COLORS from '@/utils/colors'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components'

use([CanvasRenderer, LineChart, BarChart, PieChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent])

const activeTab = ref('prediction')

const predictionLoading = ref(false)
const predictionData = ref(null)
const predictionForm = reactive({ predict_months: 6, history_months: 12 })

const customerLoading = ref(false)
const customerData = ref(null)

const anomalyLoading = ref(false)
const anomalyData = ref(null)

const loadPrediction = async () => {
  predictionLoading.value = true
  try {
    const res = await getSalesPrediction(predictionForm)
    predictionData.value = res.data
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '预测分析失败')
  } finally {
    predictionLoading.value = false
  }
}

const loadCustomerValue = async () => {
  customerLoading.value = true
  try {
    const res = await getCustomerValue()
    customerData.value = res.data
  } catch {
    ElMessage.error('客户价值分析失败')
  } finally {
    customerLoading.value = false
  }
}

const loadAnomalyDetection = async () => {
  anomalyLoading.value = true
  try {
    const res = await getAnomalyDetection()
    anomalyData.value = res.data
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '异常检测失败')
  } finally {
    anomalyLoading.value = false
  }
}

const getPredictionChartOption = () => {
  if (!predictionData.value) return {}
  const { history, prediction } = predictionData.value
  return {
    title: { text: '销售额预测趋势', left: 'center' },
    tooltip: { trigger: 'axis' },
    legend: { data: ['历史金额', '预测金额'], bottom: 0 },
    grid: { left: '3%', right: '4%', bottom: '12%', containLabel: true },
    xAxis: {
      type: 'category',
      data: [...history.months, ...prediction.months],
      axisLabel: { rotate: 45 }
    },
    yAxis: { type: 'value', name: '金额' },
    series: [
      {
        name: '历史金额',
        type: 'line',
        data: [...history.amounts.map(Number), ...new Array(prediction.months.length).fill(null)],
        smooth: true,
        itemStyle: { color: DESIGN_COLORS.primary }
      },
      {
        name: '预测金额',
        type: 'line',
        data: [...new Array(history.months.length - 1).fill(null), Number(history.amounts[history.amounts.length - 1]), ...prediction.amounts.map(Number)],
        smooth: true,
        lineStyle: { type: 'dashed' },
        itemStyle: { color: '#F7BA1E' }
      }
    ]
  }
}

const getCustomerPieOption = () => {
  if (!customerData.value) return {}
  const { segments } = customerData.value
  return {
    title: { text: '客户价值分布', left: 'center' },
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      data: [
        { value: segments.high, name: '高价值', itemStyle: { color: DESIGN_COLORS.danger } },
        { value: segments.medium, name: '中价值', itemStyle: { color: '#F7BA1E' } },
        { value: segments.low, name: '低价值', itemStyle: { color: '#86909C' } }
      ]
    }]
  }
}

onMounted(() => {
  loadPrediction()
  loadCustomerValue()
  loadAnomalyDetection()
})
</script>

<template>
  <div class="prediction-container">
    <div class="page-header">
      <h1>智能分析</h1>
      <p class="text-muted">基于机器学习的销售预测与客户价值分析</p>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="销售预测" name="prediction">
        <div class="card">
          <el-form :inline="true" :model="predictionForm">
            <el-form-item label="预测月数">
              <el-input-number v-model="predictionForm.predict_months" :min="1" :max="24" />
            </el-form-item>
            <el-form-item label="历史月数">
              <el-input-number v-model="predictionForm.history_months" :min="3" :max="36" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="predictionLoading" @click="loadPrediction">
                执行预测
              </el-button>
            </el-form-item>
          </el-form>

          <div v-if="predictionData" style="margin-top: 16px;">
            <el-row :gutter="16" style="margin-bottom: 16px;">
              <el-col :span="8">
                <div class="stat-card">
                  <span class="stat-label">模型类型</span>
                  <span class="stat-value">{{ predictionData.model_info.type }}</span>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="stat-card">
                  <span class="stat-label">金额拟合度 R²</span>
                  <span class="stat-value">{{ predictionData.model_info.r2_amount }}</span>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="stat-card">
                  <span class="stat-label">数量拟合度 R²</span>
                  <span class="stat-value">{{ predictionData.model_info.r2_count }}</span>
                </div>
              </el-col>
            </el-row>
            <v-chart :option="getPredictionChartOption()" style="height: 400px;" autoresize />
          </div>
          <el-empty v-else-if="!predictionLoading" description="点击「执行预测」开始分析" />
        </div>
      </el-tab-pane>

      <el-tab-pane label="客户价值" name="customer">
        <div class="card" v-loading="customerLoading">
          <el-row :gutter="24" v-if="customerData">
            <el-col :xs="24" :lg="10">
              <v-chart :option="getCustomerPieOption()" style="height: 350px;" autoresize />
            </el-col>
            <el-col :xs="24" :lg="14">
              <el-table :data="customerData.clients" stripe size="small" max-height="400">
                <el-table-column prop="client_name" label="客户名称" min-width="140" show-overflow-tooltip />
                <el-table-column prop="contract_count" label="合同数" width="80" align="center" />
                <el-table-column prop="total_amount" label="合同总金额" width="130" align="right" />
                <el-table-column prop="value_score" label="价值评分" width="100" align="center" />
                <el-table-column prop="level" label="等级" width="90" align="center">
                  <template #default="{ row }">
                    <el-tag
                      :type="row.level === '高价值' ? 'danger' : row.level === '中价值' ? 'warning' : 'info'"
                      size="small"
                    >
                      {{ row.level }}
                    </el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </el-col>
          </el-row>
        </div>
      </el-tab-pane>

      <el-tab-pane label="异常检测" name="anomaly">
        <div class="card" v-loading="anomalyLoading">
          <div v-if="anomalyData">
            <el-row :gutter="16" style="margin-bottom: 16px;">
              <el-col :span="6">
                <div class="stat-card"><span class="stat-label">平均金额</span><span class="stat-value">¥{{ anomalyData.stats.mean_amount }}</span></div>
              </el-col>
              <el-col :span="6">
                <div class="stat-card"><span class="stat-label">标准差</span><span class="stat-value">¥{{ anomalyData.stats.std_amount }}</span></div>
              </el-col>
              <el-col :span="6">
                <div class="stat-card"><span class="stat-label">异常阈值(上)</span><span class="stat-value">¥{{ anomalyData.stats.upper_threshold }}</span></div>
              </el-col>
              <el-col :span="6">
                <div class="stat-card"><span class="stat-label">异常合同数</span><span class="stat-value danger">{{ anomalyData.stats.anomaly_count }}</span></div>
              </el-col>
            </el-row>
            <el-table :data="anomalyData.anomalies" stripe>
              <el-table-column prop="contract_no" label="合同编号" width="140" />
              <el-table-column prop="title" label="标题" min-width="160" show-overflow-tooltip />
              <el-table-column prop="client_name" label="客户" width="140" />
              <el-table-column prop="amount" label="金额" width="140" align="right" />
              <el-table-column prop="status_display" label="状态" width="100" />
            </el-table>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style lang="scss" scoped>
.prediction-container {
  min-height: 100%;

  .page-header {
    margin-bottom: 24px;

    h1 {
      font-size: var(--fs-xl);
      font-weight: 600;
      color: var(--text-primary);
      line-height: 1.4;
    }

    .text-muted {
      margin-top: 4px;
      font-size: var(--fs-base);
      color: var(--text-muted);
    }
  }

  .card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 24px;
    margin-bottom: 16px;
    box-shadow: var(--shadow-sm);
    transition: box-shadow var(--transition-fast);
  }

  .stat-card {
    background: var(--bg-color);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-md);
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    transition: box-shadow var(--transition-fast), border-color var(--transition-fast);

    &:hover {
      box-shadow: var(--shadow-md);
      border-color: var(--border-color);
    }

    .stat-label {
      font-size: var(--fs-sm);
      color: var(--text-muted);
      line-height: 1.5;
    }

    .stat-value {
      font-size: var(--fs-lg);
      font-weight: 600;
      color: var(--text-primary);
      line-height: 1.4;

      &.danger {
        color: var(--danger);
      }
    }
  }

  :deep(.el-tabs__nav-wrap::after) {
    background-color: var(--border-light);
  }

  :deep(.el-tabs__item) {
    font-size: var(--fs-base);
    color: var(--text-secondary);
    transition: color var(--transition-fast);

    &.is-active {
      color: var(--primary);
    }

    &:hover {
      color: var(--primary-light);
    }
  }

  :deep(.el-tabs__active-bar) {
    background-color: var(--primary);
  }

  :deep(.el-form-item__label) {
    font-size: var(--fs-sm);
    color: var(--text-secondary);
  }

  :deep(.el-table) {
    --el-table-border-color: var(--border-light);
    --el-table-header-bg-color: var(--bg-color);

    th.el-table__cell {
      font-size: var(--fs-sm);
      color: var(--text-secondary);
      font-weight: 500;
    }

    td.el-table__cell {
      font-size: var(--fs-sm);
      color: var(--text-primary);
    }
  }

  :deep(.el-empty__description p) {
    font-size: var(--fs-base);
    color: var(--text-muted);
  }
}
</style>
