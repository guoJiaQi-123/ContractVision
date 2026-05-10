<script setup>
import { onMounted, ref, computed } from 'vue'
import { getMobileDashboard } from '@/api/system'

const loading = ref(true)
const data = ref({
  summary: {},
  status_distribution: [],
  payment_distribution: [],
  delivery_distribution: [],
  trend: { months: [], amounts: [], counts: [] },
  top_clients: [],
  recent_alerts: [],
  sales_target: { period: '', target: 0, actual: 0, progress: 0 }
})

const loadData = async () => {
  try {
    const res = await getMobileDashboard()
    data.value = res.data || data.value
  } catch {
  } finally {
    loading.value = false
  }
}

const formatAmount = (val) => {
  const num = parseFloat(val) || 0
  if (num >= 10000) return (num / 10000).toFixed(1) + '万'
  return num.toLocaleString()
}

const formatWan = (val) => {
  const num = parseFloat(val) || 0
  return (num / 10000).toFixed(1)
}

const summary = computed(() => data.value.summary || {})

const kpiCards = computed(() => [
  {
    label: '合同总数',
    value: summary.value.total_contracts || 0,
    unit: '份',
    icon: '📄',
    accent: 'teal'
  },
  {
    label: '累计金额',
    value: formatWan(summary.value.total_amount || 0),
    unit: '万',
    icon: '💰',
    accent: 'amber'
  },
  {
    label: '本月新签',
    value: summary.value.month_new || 0,
    unit: '份',
    icon: '✍️',
    accent: 'teal'
  },
  {
    label: '本月金额',
    value: formatWan(summary.value.month_amount || 0),
    unit: '万',
    icon: '📈',
    accent: 'amber'
  }
])

const alertCards = computed(() => [
  {
    label: '待处理预警',
    value: summary.value.pending_alerts || 0,
    color: '#c0392b'
  },
  {
    label: '30天内到期',
    value: summary.value.expiring_contracts || 0,
    color: '#c4790a'
  },
  {
    label: '逾期付款',
    value: summary.value.overdue_payments || 0,
    color: '#c0392b'
  },
  {
    label: '待续签',
    value: summary.value.pending_renewals || 0,
    color: '#0d7377'
  }
])

const statusColors = {
  draft: '#86909c',
  active: '#0d7377',
  completed: '#27ae60',
  terminated: '#c0392b',
  voided: '#7f8c8d'
}

const severityColors = {
  high: '#c0392b',
  medium: '#c4790a',
  low: '#0d7377'
}

const severityLabels = {
  high: '高',
  medium: '中',
  low: '低'
}

const trendMax = computed(() => {
  const amounts = data.value.trend?.amounts || []
  return Math.max(...amounts, 1)
})

const targetProgress = computed(() => {
  const p = data.value.sales_target?.progress || 0
  return Math.min(p, 100)
})

const targetColor = computed(() => {
  const p = data.value.sales_target?.progress || 0
  if (p >= 80) return '#27ae60'
  if (p >= 50) return '#c4790a'
  return '#c0392b'
})

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="m-dash">
    <header class="m-header">
      <div class="m-header-inner">
        <div class="m-header-top">
          <h1>经营驾驶舱</h1>
          <span class="m-header-period">{{ data.sales_target?.period || '--' }}</span>
        </div>
        <p class="m-header-sub">核心经营指标一览</p>
      </div>
    </header>

    <section class="m-section" v-if="!loading">
      <div class="m-kpi-grid">
        <div
          v-for="card in kpiCards"
          :key="card.label"
          class="m-kpi-card"
          :class="card.accent"
        >
          <span class="m-kpi-icon">{{ card.icon }}</span>
          <div class="m-kpi-body">
            <span class="m-kpi-label">{{ card.label }}</span>
            <div class="m-kpi-value-row">
              <strong class="m-kpi-value">{{ card.value }}</strong>
              <span class="m-kpi-unit">{{ card.unit }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="m-section" v-if="!loading">
      <div class="m-section-head">
        <h2>风险预警</h2>
      </div>
      <div class="m-alert-grid">
        <div
          v-for="card in alertCards"
          :key="card.label"
          class="m-alert-card"
        >
          <span class="m-alert-dot" :style="{ backgroundColor: card.color }"></span>
          <div class="m-alert-body">
            <span class="m-alert-value" :style="{ color: card.color }">{{ card.value }}</span>
            <span class="m-alert-label">{{ card.label }}</span>
          </div>
        </div>
      </div>
    </section>

    <section class="m-section" v-if="!loading">
      <div class="m-section-head">
        <h2>月度趋势</h2>
      </div>
      <div class="m-card">
        <div class="m-trend-chart">
          <div
            v-for="(val, idx) in data.trend.amounts"
            :key="idx"
            class="m-trend-bar-group"
          >
            <div class="m-trend-bar-wrapper">
              <div
                class="m-trend-bar"
                :style="{ height: Math.max((val / trendMax) * 100, 2) + '%' }"
              ></div>
            </div>
            <span class="m-trend-label">{{ (data.trend.months[idx] || '').slice(5) }}</span>
          </div>
        </div>
        <div class="m-trend-legend">
          <span class="m-legend-dot teal"></span>
          <span>月度签约金额</span>
        </div>
      </div>
    </section>

    <section class="m-section" v-if="!loading">
      <div class="m-section-head">
        <h2>销售目标</h2>
      </div>
      <div class="m-card">
        <div class="m-target-header">
          <div>
            <span class="m-target-actual">{{ formatWan(data.sales_target?.actual || 0) }}</span>
            <span class="m-target-unit">万 / </span>
            <span class="m-target-goal">{{ formatWan(data.sales_target?.target || 0) }}</span>
            <span class="m-target-unit">万</span>
          </div>
          <span class="m-target-pct" :style="{ color: targetColor }">
            {{ data.sales_target?.progress || 0 }}%
          </span>
        </div>
        <div class="m-progress-track">
          <div
            class="m-progress-fill"
            :style="{ width: targetProgress + '%', backgroundColor: targetColor }"
          ></div>
        </div>
      </div>
    </section>

    <section class="m-section" v-if="!loading && data.status_distribution.length">
      <div class="m-section-head">
        <h2>合同状态</h2>
      </div>
      <div class="m-card">
        <div
          v-for="item in data.status_distribution"
          :key="item.status"
          class="m-dist-row"
        >
          <div class="m-dist-info">
            <span class="m-dist-dot" :style="{ backgroundColor: statusColors[item.status] || '#86909c' }"></span>
            <span class="m-dist-label">{{ item.label }}</span>
          </div>
          <div class="m-dist-bar-track">
            <div
              class="m-dist-bar-fill"
              :style="{
                width: Math.max((item.count / (summary.total_contracts || 1)) * 100, 2) + '%',
                backgroundColor: statusColors[item.status] || '#86909c'
              }"
            ></div>
          </div>
          <span class="m-dist-count">{{ item.count }}</span>
        </div>
      </div>
    </section>

    <section class="m-section" v-if="!loading && data.top_clients.length">
      <div class="m-section-head">
        <h2>TOP 客户</h2>
      </div>
      <div class="m-card">
        <div
          v-for="(client, idx) in data.top_clients"
          :key="client.client_name"
          class="m-client-row"
        >
          <span class="m-client-rank" :class="{ top: idx < 3 }">{{ idx + 1 }}</span>
          <div class="m-client-info">
            <span class="m-client-name">{{ client.client_name }}</span>
            <span class="m-client-cnt">{{ client.cnt }}份合同</span>
          </div>
          <span class="m-client-amount">{{ formatAmount(client.total) }}</span>
        </div>
      </div>
    </section>

    <section class="m-section" v-if="!loading && data.payment_distribution.length">
      <div class="m-section-head">
        <h2>付款状态</h2>
      </div>
      <div class="m-card">
        <div class="m-hbar-group">
          <div
            v-for="item in data.payment_distribution"
            :key="item.payment_status"
            class="m-hbar-item"
          >
            <span class="m-hbar-label">{{ item.label }}</span>
            <div class="m-hbar-track">
              <div
                class="m-hbar-fill payment"
                :style="{ width: Math.max((item.count / (summary.total_contracts || 1)) * 100, 3) + '%' }"
              ></div>
            </div>
            <span class="m-hbar-val">{{ item.count }}</span>
          </div>
        </div>
      </div>
    </section>

    <section class="m-section" v-if="!loading && data.delivery_distribution.length">
      <div class="m-section-head">
        <h2>交付状态</h2>
      </div>
      <div class="m-card">
        <div class="m-hbar-group">
          <div
            v-for="item in data.delivery_distribution"
            :key="item.delivery_status"
            class="m-hbar-item"
          >
            <span class="m-hbar-label">{{ item.label }}</span>
            <div class="m-hbar-track">
              <div
                class="m-hbar-fill delivery"
                :style="{ width: Math.max((item.count / (summary.total_contracts || 1)) * 100, 3) + '%' }"
              ></div>
            </div>
            <span class="m-hbar-val">{{ item.count }}</span>
          </div>
        </div>
      </div>
    </section>

    <section class="m-section" v-if="!loading && data.recent_alerts.length">
      <div class="m-section-head">
        <h2>最新预警</h2>
      </div>
      <div class="m-card">
        <div
          v-for="alert in data.recent_alerts"
          :key="alert.id"
          class="m-alert-row"
        >
          <span
            class="m-alert-severity"
            :style="{ backgroundColor: severityColors[alert.level] || '#86909c' }"
          >
            {{ severityLabels[alert.level] || alert.level }}
          </span>
          <div class="m-alert-content">
            <span class="m-alert-title">{{ alert.title }}</span>
          </div>
        </div>
      </div>
    </section>

    <div class="m-skeleton" v-if="loading">
      <div class="m-sk-line wide"></div>
      <div class="m-sk-grid">
        <div class="m-sk-card" v-for="i in 4" :key="i"></div>
      </div>
      <div class="m-sk-line"></div>
      <div class="m-sk-grid">
        <div class="m-sk-card" v-for="i in 4" :key="'a'+i"></div>
      </div>
      <div class="m-sk-line"></div>
      <div class="m-sk-bar-group">
        <div class="m-sk-bar" v-for="i in 6" :key="'b'+i" :style="{ height: (Math.random() * 60 + 20) + '%' }"></div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.m-dash {
  max-width: 480px;
  margin: 0 auto;
  min-height: 100vh;
  background: var(--bg-color);
}

.m-header {
  background: var(--primary);
  padding: 28px 20px 24px;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: -40px;
    right: -30px;
    width: 140px;
    height: 140px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.06);
  }

  &::after {
    content: '';
    position: absolute;
    bottom: -20px;
    left: 40%;
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.04);
  }
}

.m-header-inner {
  position: relative;
  z-index: 1;
}

.m-header-top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}

.m-header h1 {
  color: #fff;
  font-size: var(--fs-xl);
  font-weight: 700;
  margin: 0;
  letter-spacing: -0.02em;
}

.m-header-period {
  color: rgba(255, 255, 255, 0.7);
  font-size: var(--fs-sm);
  font-weight: 500;
  letter-spacing: 0.04em;
}

.m-header-sub {
  margin: 6px 0 0;
  color: rgba(255, 255, 255, 0.65);
  font-size: var(--fs-sm);
}

.m-section {
  padding: 0 16px;
  margin-top: 16px;
}

.m-section-head {
  margin-bottom: 10px;

  h2 {
    font-size: var(--fs-md);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
}

.m-kpi-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.m-kpi-card {
  background: var(--card-bg);
  border-radius: var(--radius-lg);
  padding: 16px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-xs);
  transition: transform var(--transition-fast), box-shadow var(--transition-fast);

  &:active {
    transform: scale(0.98);
  }

  &.teal {
    .m-kpi-value {
      color: var(--primary);
    }
  }

  &.amber {
    .m-kpi-value {
      color: var(--warning);
    }
  }
}

.m-kpi-icon {
  font-size: var(--fs-xl);
  line-height: 1;
  flex-shrink: 0;
  margin-top: 2px;
}

.m-kpi-body {
  flex: 1;
  min-width: 0;
}

.m-kpi-label {
  display: block;
  font-size: var(--fs-xs);
  color: var(--text-muted);
  margin-bottom: 6px;
}

.m-kpi-value-row {
  display: flex;
  align-items: baseline;
  gap: 3px;
}

.m-kpi-value {
  font-size: var(--fs-xl);
  font-weight: 700;
  line-height: 1.1;
}

.m-kpi-unit {
  font-size: var(--fs-xs);
  color: var(--text-muted);
}

.m-alert-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.m-alert-card {
  background: var(--card-bg);
  border-radius: var(--radius-lg);
  padding: 14px 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-xs);
}

.m-alert-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.m-alert-body {
  display: flex;
  flex-direction: column;
}

.m-alert-value {
  font-size: var(--fs-lg);
  font-weight: 700;
  line-height: 1.2;
}

.m-alert-label {
  font-size: var(--fs-xs);
  color: var(--text-muted);
  margin-top: 2px;
}

.m-card {
  background: var(--card-bg);
  border-radius: var(--radius-lg);
  padding: 16px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-xs);
}

.m-trend-chart {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  height: 120px;
  padding-bottom: 24px;
  position: relative;
}

.m-trend-bar-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
}

.m-trend-bar-wrapper {
  flex: 1;
  width: 100%;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.m-trend-bar {
  width: 70%;
  max-width: 32px;
  min-height: 3px;
  border-radius: var(--radius-xs) var(--radius-xs) 0 0;
  background: var(--primary);
  transition: height 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.m-trend-label {
  font-size: var(--fs-xs);
  color: var(--text-muted);
  margin-top: 6px;
  white-space: nowrap;
}

.m-trend-legend {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 10px;
  font-size: var(--fs-xs);
  color: var(--text-muted);
}

.m-legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;

  &.teal {
    background: var(--primary);
  }
}

.m-target-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 10px;
}

.m-target-actual {
  font-size: var(--fs-lg);
  font-weight: 700;
  color: var(--text-primary);
}

.m-target-goal {
  font-size: var(--fs-base);
  font-weight: 600;
  color: var(--text-secondary);
}

.m-target-unit {
  font-size: var(--fs-xs);
  color: var(--text-muted);
}

.m-target-pct {
  font-size: var(--fs-lg);
  font-weight: 700;
}

.m-progress-track {
  height: 8px;
  background: var(--border-color);
  border-radius: var(--radius-xs);
  overflow: hidden;
}

.m-progress-fill {
  height: 100%;
  border-radius: var(--radius-xs);
  transition: width 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.m-dist-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;

  & + & {
    border-top: 1px solid var(--border-color);
  }
}

.m-dist-info {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 72px;
}

.m-dist-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.m-dist-label {
  font-size: var(--fs-sm);
  color: var(--text-secondary);
  white-space: nowrap;
}

.m-dist-bar-track {
  flex: 1;
  height: 6px;
  background: var(--border-color);
  border-radius: var(--radius-xs);
  overflow: hidden;
}

.m-dist-bar-fill {
  height: 100%;
  border-radius: var(--radius-xs);
  transition: width var(--transition-normal);
}

.m-dist-count {
  font-size: var(--fs-sm);
  font-weight: 600;
  color: var(--text-primary);
  min-width: 28px;
  text-align: right;
}

.m-client-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;

  & + & {
    border-top: 1px solid var(--border-color);
  }
}

.m-client-rank {
  width: 22px;
  height: 22px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--fs-xs);
  font-weight: 700;
  color: var(--text-muted);
  background: var(--border-color);
  flex-shrink: 0;

  &.top {
    background: var(--warning);
    color: #fff;
  }
}

.m-client-info {
  flex: 1;
  min-width: 0;
}

.m-client-name {
  display: block;
  font-size: var(--fs-base);
  font-weight: 500;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.m-client-cnt {
  font-size: var(--fs-xs);
  color: var(--text-muted);
}

.m-client-amount {
  font-size: var(--fs-base);
  font-weight: 600;
  color: var(--primary);
  flex-shrink: 0;
}

.m-hbar-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.m-hbar-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.m-hbar-label {
  font-size: var(--fs-sm);
  color: var(--text-secondary);
  min-width: 56px;
  white-space: nowrap;
}

.m-hbar-track {
  flex: 1;
  height: 6px;
  background: var(--border-color);
  border-radius: var(--radius-xs);
  overflow: hidden;
}

.m-hbar-fill {
  height: 100%;
  border-radius: var(--radius-xs);
  transition: width var(--transition-normal);

  &.payment {
    background: var(--primary);
  }

  &.delivery {
    background: var(--warning);
  }
}

.m-hbar-val {
  font-size: var(--fs-sm);
  font-weight: 600;
  color: var(--text-primary);
  min-width: 28px;
  text-align: right;
}

.m-alert-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;

  & + & {
    border-top: 1px solid var(--border-color);
  }
}

.m-alert-severity {
  padding: 2px 8px;
  border-radius: var(--radius-xs);
  font-size: var(--fs-xs);
  font-weight: 600;
  color: #fff;
  flex-shrink: 0;
}

.m-alert-content {
  flex: 1;
  min-width: 0;
}

.m-alert-title {
  font-size: var(--fs-sm);
  color: var(--text-primary);
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.m-skeleton {
  padding: 16px;
}

.m-sk-line {
  height: 18px;
  border-radius: var(--radius-xs);
  background: var(--gray-200);
  animation: sk-pulse 1.5s ease-in-out infinite;
  margin-bottom: 16px;

  &.wide {
    width: 60%;
  }
}

.m-sk-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 16px;
}

.m-sk-card {
  height: 72px;
  border-radius: var(--radius-lg);
  background: var(--gray-200);
  animation: sk-pulse 1.5s ease-in-out infinite;
}

.m-sk-bar-group {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  height: 100px;
  padding: 16px;
  border-radius: var(--radius-lg);
  background: var(--gray-200);
}

.m-sk-bar {
  flex: 1;
  border-radius: var(--radius-xs) var(--radius-xs) 0 0;
  background: var(--gray-300);
}

@keyframes sk-pulse {
  0% { opacity: 1; }
  50% { opacity: 0.4; }
  100% { opacity: 1; }
}

@media (max-width: 360px) {
  .m-kpi-value {
    font-size: var(--fs-lg);
  }

  .m-alert-value {
    font-size: var(--fs-md);
  }
}
</style>
