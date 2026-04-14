<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getContractDetail } from '@/api/contract'
import { ArrowLeft, Document, Download } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const loadError = ref(false)

const contractInfo = ref({})

const statusOptions = [
  { label: '草稿', value: 'draft', type: 'info' },
  { label: '生效中', value: 'active', type: 'success' },
  { label: '已完成', value: 'completed', type: '' },
  { label: '已终止', value: 'terminated', type: 'warning' },
  { label: '已作废', value: 'voided', type: 'danger' }
]

const getStatusTag = (status) => {
  const item = statusOptions.find(o => o.value === status)
  return item || { label: status, type: 'info' }
}

const formatAmount = (val) => {
  if (!val && val !== 0) return '¥0.00'
  return `¥${parseFloat(val).toLocaleString('zh-CN', { minimumFractionDigits: 2 })}`
}

const goBack = () => {
  router.push('/contract/list')
}

const loadDetail = async () => {
  loading.value = true
  loadError.value = false
  try {
    const res = await getContractDetail(route.params.id)
    contractInfo.value = res.data || res
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadDetail()
})
</script>

<template>
  <div class="contract-detail-container">
    <div class="page-header">
      <div class="header-left">
        <el-button class="back-btn" @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
        <div class="header-info">
          <h1>合同详情</h1>
          <p class="subtitle" v-if="contractInfo.contract_no">{{ contractInfo.contract_no }}</p>
        </div>
      </div>
      <div class="header-actions" v-if="!loading && !loadError">
        <el-button class="btn-outline">
          <el-icon><Download /></el-icon>
          导出PDF
        </el-button>
        <el-button type="primary" class="btn-primary">
          <el-icon><Document /></el-icon>
          编辑合同
        </el-button>
      </div>
    </div>

    <div v-if="loading" v-loading="true" class="loading-container"></div>

    <el-empty v-else-if="loadError" description="加载合同详情失败">
      <el-button type="primary" @click="loadDetail">重新加载</el-button>
    </el-empty>

    <template v-else>
      <div class="detail-grid">
        <div class="card info-card">
          <div class="card-header">
            <h3>基本信息</h3>
            <el-tag :type="getStatusTag(contractInfo.status).type" size="small">
              {{ getStatusTag(contractInfo.status).label }}
            </el-tag>
          </div>
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">合同编号</span>
              <span class="info-value">{{ contractInfo.contract_no || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">合同名称</span>
              <span class="info-value">{{ contractInfo.title || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">客户名称</span>
              <span class="info-value">{{ contractInfo.client_name || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">合同金额</span>
              <span class="info-value amount">{{ formatAmount(contractInfo.amount) }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">签订日期</span>
              <span class="info-value">{{ contractInfo.sign_date || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">产品类型</span>
              <span class="info-value">{{ contractInfo.product_type || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">开始日期</span>
              <span class="info-value">{{ contractInfo.start_date || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">结束日期</span>
              <span class="info-value">{{ contractInfo.end_date || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">销售人员</span>
              <span class="info-value">{{ contractInfo.salesperson || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">所属区域</span>
              <span class="info-value">{{ contractInfo.region || '-' }}</span>
            </div>
          </div>
          <div class="info-full" v-if="contractInfo.description">
            <span class="info-label">合同描述</span>
            <span class="info-value">{{ contractInfo.description }}</span>
          </div>
        </div>

        <div class="card section-card">
          <div class="card-header">
            <h3>合同附件</h3>
          </div>
          <el-empty description="暂无附件" :image-size="80" />
        </div>

        <div class="card section-card">
          <div class="card-header">
            <h3>操作记录</h3>
          </div>
          <el-empty description="暂无操作记录" :image-size="80" />
        </div>
      </div>
    </template>
  </div>
</template>

<style lang="scss" scoped>
.contract-detail-container {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;

  .header-left {
    display: flex;
    align-items: flex-start;
    gap: 16px;
  }

  .back-btn {
    border-radius: 8px;
    font-size: 14px;
    padding: 8px 16px;
    border: 1px solid var(--border-color);
    background: var(--card-bg);
    color: var(--text-secondary);
    transition: all 0.2s;

    &:hover {
      border-color: var(--primary-color);
      color: var(--primary-color);
    }
  }

  .header-info {
    h1 {
      font-size: 24px;
      font-weight: 700;
      color: var(--text-primary);
      margin: 0;
      letter-spacing: -0.02em;
    }

    .subtitle {
      margin: 4px 0 0;
      font-size: 14px;
      color: var(--text-muted);
    }
  }

  .header-actions {
    display: flex;
    gap: 12px;
  }
}

.loading-container {
  min-height: 400px;
}

.detail-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 24px;
  transition: box-shadow 0.3s ease;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
  }
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;

  h3 {
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
  }
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 6px;

  .info-label {
    font-size: 13px;
    color: var(--text-muted);
    font-weight: 400;
  }

  .info-value {
    font-size: 15px;
    color: var(--text-primary);
    font-weight: 500;

    &.amount {
      color: #165DFF;
      font-size: 18px;
      font-weight: 600;
    }
  }
}

.info-full {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 6px;

  .info-label {
    font-size: 13px;
    color: var(--text-muted);
  }

  .info-value {
    font-size: 14px;
    color: var(--text-primary);
    line-height: 1.6;
  }
}

.section-card {
  :deep(.el-empty) {
    padding: 24px 0;
  }
}
</style>
