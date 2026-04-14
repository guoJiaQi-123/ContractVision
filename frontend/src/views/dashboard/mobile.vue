<script setup>
import { onMounted, ref } from 'vue'
import { getMobileDashboard } from '@/api/system'

const data = ref({ config: null, summary: {} })

const loadData = async () => {
  const res = await getMobileDashboard()
  data.value = res.data || { config: null, summary: {} }
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="mobile-dashboard">
    <div class="mobile-hero">
      <div class="badge">F039 移动端驾驶舱</div>
      <h1>随时掌握经营动态</h1>
      <p>面向手机与平板轻量化展示核心经营指标、预警数量与临期合同。</p>
    </div>

    <div class="mobile-grid">
      <div class="mobile-card">
        <span>合同总数</span>
        <strong>{{ data.summary.total_contracts || 0 }}</strong>
      </div>
      <div class="mobile-card">
        <span>累计金额</span>
        <strong>{{ data.summary.total_amount || 0 }}</strong>
      </div>
      <div class="mobile-card danger">
        <span>待处理预警</span>
        <strong>{{ data.summary.pending_alerts || 0 }}</strong>
      </div>
      <div class="mobile-card warning">
        <span>30 天内到期</span>
        <strong>{{ data.summary.expiring_contracts || 0 }}</strong>
      </div>
    </div>

    <div class="widget-panel">
      <div class="panel-title">移动端模板</div>
      <pre>{{ JSON.stringify(data.config?.widgets || [], null, 2) }}</pre>
    </div>
  </div>
</template>

<style scoped lang="scss">
.mobile-dashboard {
  max-width: 560px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.mobile-hero,
.mobile-card,
.widget-panel {
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  box-shadow: 0 18px 36px rgba(15, 23, 42, 0.2);
}

.mobile-hero {
  padding: 24px;
  color: #f8fafc;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.2), transparent 26%),
    linear-gradient(145deg, #0f172a, #1d4ed8 52%, #14b8a6);

  h1 {
    margin: 12px 0 8px;
    font-size: 30px;
    line-height: 1.1;
  }

  p {
    margin: 0;
    color: rgba(226, 232, 240, 0.82);
  }
}

.badge {
  display: inline-flex;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  font-size: 12px;
  letter-spacing: 0.08em;
}

.mobile-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.mobile-card {
  padding: 18px;
  background: #fff;

  span {
    display: block;
    color: #64748b;
    font-size: 13px;
  }

  strong {
    display: block;
    margin-top: 12px;
    font-size: 28px;
    color: #0f172a;
  }

  &.danger strong {
    color: #dc2626;
  }

  &.warning strong {
    color: #d97706;
  }
}

.widget-panel {
  background: #ffffff;
  padding: 18px;

  .panel-title {
    font-weight: 600;
    margin-bottom: 12px;
  }

  pre {
    margin: 0;
    white-space: pre-wrap;
    word-break: break-word;
    font-size: 12px;
    color: #475569;
  }
}

@media (max-width: 640px) {
  .mobile-grid {
    grid-template-columns: 1fr;
  }
}
</style>
