<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Bell,
  Warning,
  CircleCheck,
  Calendar,
  Search,
  Refresh,
  List,
  Promotion,
  User,
  Switch,
  Opportunity,
  ArrowRight,
  InfoFilled,
  Document,
  Timer,
  Guide
} from '@element-plus/icons-vue'
import { useUserStore } from '@/store/modules/user'
import {
  getAlertWorkspace,
  getAlertWorkspaceDetail,
  getAlertWorkspaceSummary,
  getAlertWorkspaceAssignees,
  processAlertWorkspaceItem,
  processAlertWorkspaceBatch,
  reassignAlertWorkspaceItem
} from '@/api/system'
import { formatDate } from '@/utils'

const router = useRouter()
const userStore = useUserStore()
const isAdmin = computed(() => userStore.role === 'admin')

const loading = ref(false)
const summaryLoading = ref(false)
const detailLoading = ref(false)
const assigneeLoading = ref(false)
const reassigning = ref(false)
const tableData = ref([])
const selectedRows = ref([])
const processingIds = ref([])
const assigneeOptions = ref([])
const detailVisible = ref(false)
const detailData = ref(null)
const summary = ref({
  total_count: 0,
  pending_count: 0,
  processed_count: 0,
  high_count: 0,
  overdue_count: 0,
  today_count: 0,
  week_count: 0
})
const queryParams = ref({
  page: 1,
  page_size: 10,
  keyword: '',
  status: 'pending',
  level: '',
  warning_type: '',
  due_scope: '',
  owner: ''
})
const reassignForm = ref({
  owner: ''
})
const total = ref(0)

const roleLabelMap = {
  admin: '管理员',
  operator: '操作员',
  viewer: '查看者'
}

const statusOptions = [
  { label: '待处理', value: 'pending' },
  { label: '已处理', value: 'processed' }
]

const levelOptions = [
  { label: '高危', value: 'high' },
  { label: '中危', value: 'medium' },
  { label: '提示', value: 'low' }
]

const warningTypeOptions = [
  { label: '付款到期', value: 'payment_due' },
  { label: '交付到期', value: 'delivery_due' },
  { label: '合同到期', value: 'contract_expiry' },
  { label: '发票开具', value: 'invoice_due' },
  { label: '目标达成', value: 'target_progress' }
]

const dueScopeOptions = [
  { label: '今日到期', value: 'today' },
  { label: '7天内到期', value: '7d' },
  { label: '已逾期', value: 'overdue' }
]

const quickCards = computed(() => [
  {
    key: 'pending',
    title: '待处理预警',
    value: summary.value.pending_count || 0,
    icon: Bell,
    tone: 'blue',
    action: () => quickFilter({ status: 'pending' })
  },
  {
    key: 'high',
    title: '高危事项',
    value: summary.value.high_count || 0,
    icon: Warning,
    tone: 'red',
    action: () => quickFilter({ status: 'pending', level: 'high' })
  },
  {
    key: 'today',
    title: '今日截止',
    value: summary.value.today_count || 0,
    icon: Calendar,
    tone: 'amber',
    action: () => quickFilter({ status: 'pending', due_scope: 'today' })
  },
  {
    key: 'processed',
    title: '已处理事项',
    value: summary.value.processed_count || 0,
    icon: CircleCheck,
    tone: 'green',
    action: () => quickFilter({ status: 'processed' })
  }
])

const detailInsightCards = computed(() => {
  if (!detailData.value) return []
  return [
    {
      label: '负责人',
      value: detailData.value.owner_name || '待分派',
      icon: User,
      tone: 'slate'
    },
    {
      label: '处置状态',
      value: detailData.value.status_display || '-',
      icon: Switch,
      tone: detailData.value.status === 'processed' ? 'green' : 'amber'
    },
    {
      label: '剩余时效',
      value: getCountdownText(detailData.value),
      icon: Opportunity,
      tone: detailData.value.level === 'high' ? 'red' : 'blue'
    }
  ]
})

const contractSnapshot = computed(() => detailData.value?.contract_snapshot || null)
const recentLogs = computed(() => detailData.value?.recent_logs || [])
const ownerStrategy = computed(() => detailData.value?.owner_strategy || null)
const alertTimeline = computed(() => detailData.value?.timeline || [])

const fetchSummary = async () => {
  summaryLoading.value = true
  try {
    const res = await getAlertWorkspaceSummary()
    summary.value = res.data || summary.value
  } finally {
    summaryLoading.value = false
  }
}

const fetchAlerts = async () => {
  loading.value = true
  try {
    const params = {
      page: queryParams.value.page,
      page_size: queryParams.value.page_size
    }
    ;['keyword', 'status', 'level', 'warning_type', 'due_scope', 'owner'].forEach((key) => {
      if (queryParams.value[key]) {
        params[key] = queryParams.value[key]
      }
    })
    const res = await getAlertWorkspace(params)
    tableData.value = res.data?.results || []
    total.value = res.data?.total || 0
  } finally {
    loading.value = false
  }
}

const fetchAssignees = async (keyword = '') => {
  if (!isAdmin.value) return
  assigneeLoading.value = true
  try {
    const res = await getAlertWorkspaceAssignees(keyword ? { keyword } : undefined)
    assigneeOptions.value = res.data || []
  } finally {
    assigneeLoading.value = false
  }
}

const loadPage = async () => {
  await Promise.all([fetchSummary(), fetchAlerts()])
}

const loadAlertDetail = async (id) => {
  if (!id) return
  detailLoading.value = true
  try {
    const res = await getAlertWorkspaceDetail(id)
    detailData.value = res.data || null
    reassignForm.value.owner = detailData.value?.owner || ''
  } finally {
    detailLoading.value = false
  }
}

const handleSearch = async () => {
  queryParams.value.page = 1
  await fetchAlerts()
}

const handleReset = async () => {
  queryParams.value = {
    page: 1,
    page_size: 10,
    keyword: '',
    status: 'pending',
    level: '',
    warning_type: '',
    due_scope: '',
    owner: ''
  }
  selectedRows.value = []
  await loadPage()
}

const handleSelectionChange = (rows) => {
  selectedRows.value = rows
}

const quickFilter = async (patch) => {
  queryParams.value = {
    ...queryParams.value,
    page: 1,
    level: '',
    due_scope: '',
    ...patch
  }
  await fetchAlerts()
}

const refreshAfterMutation = async (detailId = null) => {
  await loadPage()
  if (detailVisible.value && (detailId || detailData.value?.id)) {
    await loadAlertDetail(detailId || detailData.value?.id)
  }
}

const handleProcess = async (row) => {
  if (!row?.id || processingIds.value.includes(row.id)) return
  processingIds.value = [...processingIds.value, row.id]
  try {
    await processAlertWorkspaceItem(row.id)
    ElMessage.success('预警已处理')
    await refreshAfterMutation(row.id)
  } finally {
    processingIds.value = processingIds.value.filter((id) => id !== row.id)
  }
}

const handleBatchProcess = async () => {
  const ids = selectedRows.value.map((item) => item.id)
  if (!ids.length) {
    ElMessage.warning('请先选择要处理的预警')
    return
  }
  await processAlertWorkspaceBatch({ ids })
  ElMessage.success(`已批量处理 ${ids.length} 条预警`)
  selectedRows.value = []
  await refreshAfterMutation()
}

const openDetail = async (row) => {
  detailVisible.value = true
  detailData.value = row
  reassignForm.value.owner = row?.owner || ''
  await loadAlertDetail(row?.id)
}

const handleReassign = async () => {
  if (!detailData.value?.id) return
  if (!reassignForm.value.owner) {
    ElMessage.warning('请选择新的负责人')
    return
  }
  reassigning.value = true
  try {
    await reassignAlertWorkspaceItem(detailData.value.id, { owner: reassignForm.value.owner })
    ElMessage.success('负责人已更新')
    await refreshAfterMutation(detailData.value.id)
  } finally {
    reassigning.value = false
  }
}

const goDetail = (row) => {
  const contractId = row?.contract || detailData.value?.contract
  if (!contractId) return
  router.push(`/contract/detail/${contractId}`)
}

const closeDrawer = () => {
  detailVisible.value = false
  detailData.value = null
  reassignForm.value.owner = ''
}

const getLevelType = (level) => {
  if (level === 'high') return 'danger'
  if (level === 'medium') return 'warning'
  return 'info'
}

const getLevelLabel = (level) => {
  return level === 'high' ? '高危' : level === 'medium' ? '中危' : '提示'
}

const getStatusType = (status) => (status === 'processed' ? 'success' : 'warning')

const getTypeLabel = (type) => {
  return warningTypeOptions.find((item) => item.value === type)?.label || type || '-'
}

const formatDueDate = (date) => (date ? formatDate(date, 'YYYY-MM-DD') : '-')

const getCountdownText = (row) => {
  if (!row?.due_date) return '未设置截止日'
  const today = new Date()
  const dueDate = new Date(row.due_date)
  const diff = Math.ceil((dueDate.setHours(0, 0, 0, 0) - today.setHours(0, 0, 0, 0)) / 86400000)
  if (diff < 0) return `已逾期 ${Math.abs(diff)} 天`
  if (diff === 0) return '今日截止'
  return `${diff} 天后截止`
}

const getSuggestionText = (row) => {
  if (!row) return ''
  if (row.warning_type === 'payment_due') return '建议核对应付款节点、付款凭证与审批状态，优先推进账期确认。'
  if (row.warning_type === 'delivery_due') return '建议检查交付节点进度、验收材料和客户确认回执，避免履约延期。'
  if (row.warning_type === 'contract_expiry') return '建议尽快与客户确认续签意向，核对合同到期日与续签负责人安排。'
  if (row.warning_type === 'invoice_due') return '建议核对开票资料与回款节奏，避免发票状态影响后续结算。'
  return '建议复盘目标偏差来源，优先排查重点客户推进与区域资源配置。'
}

const getAssigneeLabel = (item) => {
  if (!item) return '未分派'
  const roleLabel = roleLabelMap[item.role] || item.role || '成员'
  const scope = [item.department, item.region].filter(Boolean).join(' / ')
  return scope ? `${item.username} · ${roleLabel} · ${scope}` : `${item.username} · ${roleLabel}`
}

const remoteSearchAssignees = async (keyword) => {
  await fetchAssignees(keyword)
}

onMounted(async () => {
  await Promise.all([loadPage(), isAdmin.value ? fetchAssignees() : Promise.resolve()])
})
</script>

<template>
  <div class="alerts-page">
    <section class="hero-section">
      <div class="hero-copy">
        <div class="eyebrow">F031 关键节点智能预警</div>
        <h1>预警工作台</h1>
        <p>把付款到期、交付逾期、合同到期与目标偏差集中到一个视图里，支持筛选、批量处理、详情抽屉跟踪与管理员重分派。</p>
      </div>
      <div class="hero-side">
        <div class="radar-card">
          <div class="radar-label">7天内风险密度</div>
          <div class="radar-value">{{ summary.week_count || 0 }}</div>
          <div class="radar-subtitle">条事项待在本周内完成处理</div>
        </div>
      </div>
    </section>

    <section v-loading="summaryLoading" class="metric-grid">
      <button
        v-for="card in quickCards"
        :key="card.key"
        class="metric-card"
        :class="card.tone"
        @click="card.action"
      >
        <div class="metric-icon">
          <el-icon><component :is="card.icon" /></el-icon>
        </div>
        <div class="metric-title">{{ card.title }}</div>
        <div class="metric-value">{{ card.value }}</div>
      </button>
    </section>

    <section class="workspace-shell">
      <div class="workspace-toolbar">
        <div class="toolbar-left">
          <div class="toolbar-search">
            <el-icon><Search /></el-icon>
            <el-input
              v-model="queryParams.keyword"
              placeholder="搜索标题、合同编号、负责人"
              clearable
              @keyup.enter="handleSearch"
              @clear="handleSearch"
            />
          </div>
          <el-select v-model="queryParams.status" placeholder="状态" clearable @change="handleSearch">
            <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
          <el-select v-model="queryParams.level" placeholder="等级" clearable @change="handleSearch">
            <el-option v-for="item in levelOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
          <el-select v-model="queryParams.warning_type" placeholder="类型" clearable @change="handleSearch">
            <el-option v-for="item in warningTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
          <el-select v-model="queryParams.due_scope" placeholder="时效" clearable @change="handleSearch">
            <el-option v-for="item in dueScopeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
          <el-tooltip
            v-if="isAdmin"
            content="管理员可按当前负责人筛选预警，定位需要重分派的事项。"
            placement="top"
          >
            <el-select
              v-model="queryParams.owner"
              class="owner-filter"
              placeholder="负责人"
              clearable
              filterable
              remote
              reserve-keyword
              :remote-method="remoteSearchAssignees"
              :loading="assigneeLoading"
              @change="handleSearch"
            >
              <el-option
                v-for="item in assigneeOptions"
                :key="item.id"
                :label="getAssigneeLabel(item)"
                :value="item.id"
              />
            </el-select>
          </el-tooltip>
        </div>
        <div class="toolbar-right">
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
          <el-button type="primary" @click="handleBatchProcess">
            <el-icon><Promotion /></el-icon>
            批量处理
          </el-button>
        </div>
      </div>

      <div class="selection-bar">
        <div class="selection-left">
          <el-icon><List /></el-icon>
          <span>共 {{ total }} 条预警，已选 {{ selectedRows.length }} 条</span>
        </div>
        <div class="selection-right">
          <span class="muted">逾期事项 {{ summary.overdue_count || 0 }} 条</span>
          <span class="muted">总量 {{ summary.total_count || 0 }} 条</span>
        </div>
      </div>

      <el-table
        v-loading="loading"
        :data="tableData"
        class="alerts-table"
        @selection-change="handleSelectionChange"
      >
        <template #empty>
          <el-empty description="暂无匹配的预警事项" :image-size="100" />
        </template>
        <el-table-column type="selection" width="48" />
        <el-table-column label="预警事项" min-width="280">
          <template #default="{ row }">
            <div class="title-cell">
              <div class="title-line">
                <span class="title-text">{{ row.title }}</span>
                <el-tag :type="getLevelType(row.level)" effect="light" round size="small">
                  {{ getLevelLabel(row.level) }}
                </el-tag>
              </div>
              <p>{{ row.content || '请尽快处理该预警事项。' }}</p>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="120">
          <template #default="{ row }">{{ getTypeLabel(row.warning_type) }}</template>
        </el-table-column>
        <el-table-column label="合同" min-width="150">
          <template #default="{ row }">
            <button class="link-btn" :disabled="!row.contract" @click="goDetail(row)">
              {{ row.contract_no || '通用事项' }}
            </button>
          </template>
        </el-table-column>
        <el-table-column label="负责人" min-width="180">
          <template #default="{ row }">
            <div class="owner-cell">
              <span>{{ row.owner_name || '待分派' }}</span>
              <small>{{ row.processed_by_name ? `处理人：${row.processed_by_name}` : '等待跟进' }}</small>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="截止时间" width="150">
          <template #default="{ row }">
            <div class="due-cell">
              <span>{{ formatDueDate(row.due_date) }}</span>
              <small>{{ getCountdownText(row) }}</small>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" effect="light" round>
              {{ row.status_display }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="170">
          <template #default="{ row }">{{ formatDate(row.created_at, 'YYYY-MM-DD HH:mm:ss') }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <div class="table-actions">
              <el-button link type="primary" @click="openDetail(row)">详情</el-button>
              <el-button
                link
                type="success"
                :disabled="row.status === 'processed'"
                :loading="processingIds.includes(row.id)"
                @click="handleProcess(row)"
              >
                处理
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <div class="footer-note">点击指标卡可快速筛选；管理员可通过详情抽屉完成负责人重分派。</div>
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.page_size"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          background
          @current-change="fetchAlerts"
          @size-change="handleSearch"
        />
      </div>
    </section>

    <el-drawer
      v-model="detailVisible"
      class="alert-drawer"
      size="520px"
      destroy-on-close
      @closed="closeDrawer"
    >
      <template #header>
        <div class="drawer-header">
          <div>
            <div class="drawer-eyebrow">预警详情</div>
            <h3>{{ detailData?.title || '预警详情' }}</h3>
          </div>
          <el-tag
            v-if="detailData"
            :type="getStatusType(detailData.status)"
            effect="light"
            round
          >
            {{ detailData.status_display }}
          </el-tag>
        </div>
      </template>

      <div v-loading="detailLoading" class="drawer-body">
        <div v-if="detailData" class="drawer-content">
          <section class="drawer-hero">
            <div class="drawer-hero-main">
              <div class="drawer-type-row">
                <el-tag :type="getLevelType(detailData.level)" effect="light" round>
                  {{ getLevelLabel(detailData.level) }}
                </el-tag>
                <span>{{ getTypeLabel(detailData.warning_type) }}</span>
                <span>{{ detailData.contract_no || '通用事项' }}</span>
              </div>
              <p>{{ detailData.content || '请尽快处理该预警事项。' }}</p>
            </div>
            <button class="drawer-link" :disabled="!detailData.contract" @click="goDetail(detailData)">
              查看合同
              <el-icon><ArrowRight /></el-icon>
            </button>
          </section>

          <section class="drawer-metrics">
            <div
              v-for="item in detailInsightCards"
              :key="item.label"
              class="drawer-metric-card"
              :class="item.tone"
            >
              <el-icon><component :is="item.icon" /></el-icon>
              <strong>{{ item.value }}</strong>
              <span>{{ item.label }}</span>
            </div>
          </section>

          <section class="detail-panel">
            <div class="panel-title">
              <el-icon><InfoFilled /></el-icon>
              基础信息
            </div>
            <div class="detail-grid">
              <div class="detail-item">
                <label>截止时间</label>
                <span>{{ formatDueDate(detailData.due_date) }}</span>
              </div>
              <div class="detail-item">
                <label>时效提示</label>
                <span>{{ getCountdownText(detailData) }}</span>
              </div>
              <div class="detail-item">
                <label>负责人</label>
                <span>{{ detailData.owner_name || '待分派' }}</span>
              </div>
              <div class="detail-item">
                <label>处理时间</label>
                <span>{{ detailData.processed_at ? formatDate(detailData.processed_at, 'YYYY-MM-DD HH:mm:ss') : '-' }}</span>
              </div>
              <div class="detail-item">
                <label>处理人</label>
                <span>{{ detailData.processed_by_name || '-' }}</span>
              </div>
              <div class="detail-item">
                <label>创建时间</label>
                <span>{{ formatDate(detailData.created_at, 'YYYY-MM-DD HH:mm:ss') }}</span>
              </div>
            </div>
          </section>

          <section v-if="contractSnapshot" class="detail-panel snapshot-panel">
            <div class="panel-title">
              <el-icon><Document /></el-icon>
              合同快照
            </div>
            <div class="detail-grid">
              <div class="detail-item">
                <label>客户名称</label>
                <span>{{ contractSnapshot.client_name || '-' }}</span>
              </div>
              <div class="detail-item">
                <label>合同金额</label>
                <span>{{ contractSnapshot.amount }} {{ contractSnapshot.currency }}</span>
              </div>
              <div class="detail-item">
                <label>合同状态</label>
                <span>{{ contractSnapshot.status_display || '-' }}</span>
              </div>
              <div class="detail-item">
                <label>付款状态</label>
                <span>{{ contractSnapshot.payment_status_display || '-' }}</span>
              </div>
              <div class="detail-item">
                <label>交付状态</label>
                <span>{{ contractSnapshot.delivery_status_display || '-' }}</span>
              </div>
              <div class="detail-item">
                <label>续签状态</label>
                <span>{{ contractSnapshot.renewal_status_display || '-' }}</span>
              </div>
              <div class="detail-item">
                <label>销售/部门</label>
                <span>{{ [contractSnapshot.salesperson, contractSnapshot.department].filter(Boolean).join(' / ') || '-' }}</span>
              </div>
              <div class="detail-item">
                <label>创建/续签负责人</label>
                <span>{{ [contractSnapshot.created_by_name, contractSnapshot.renewal_owner_name].filter(Boolean).join(' / ') || '-' }}</span>
              </div>
            </div>
          </section>

          <section class="detail-panel suggestion-panel">
            <div class="panel-title">
              <el-icon><Opportunity /></el-icon>
              处置建议
            </div>
            <p>{{ getSuggestionText(detailData) }}</p>
          </section>

          <section v-if="ownerStrategy || detailData?.trigger_summary" class="detail-panel">
            <div class="panel-title">
              <el-icon><Guide /></el-icon>
              来源解释
            </div>
            <div class="activity-list explain-list">
              <div class="activity-item">
                <strong>{{ ownerStrategy?.catalog_title || '负责人分派策略' }}</strong>
                <span>{{ ownerStrategy?.strategy_title || '系统自动匹配负责人' }}</span>
              </div>
              <div class="activity-item">
                <strong>归属原因</strong>
                <span>{{ ownerStrategy?.reason || '当前未生成负责人解释。' }}</span>
              </div>
              <div class="activity-item">
                <strong>触发原因</strong>
                <span>{{ detailData?.trigger_summary || '当前未生成命中说明。' }}</span>
              </div>
            </div>
          </section>

          <section v-if="isAdmin" class="detail-panel assignment-panel">
            <div class="panel-title">
              <el-icon><User /></el-icon>
              管理员重分派
            </div>
            <div class="assignment-form">
              <el-select
                v-model="reassignForm.owner"
                placeholder="选择新的负责人"
                filterable
                remote
                reserve-keyword
                :remote-method="remoteSearchAssignees"
                :loading="assigneeLoading"
              >
                <el-option
                  v-for="item in assigneeOptions"
                  :key="item.id"
                  :label="getAssigneeLabel(item)"
                  :value="item.id"
                />
              </el-select>
              <el-button type="primary" :loading="reassigning" @click="handleReassign">
                立即重分派
              </el-button>
            </div>
          </section>

          <section class="detail-panel activity-panel">
            <div class="panel-title">
              <el-icon><Timer /></el-icon>
              最近操作
            </div>
            <div v-if="recentLogs.length" class="activity-list">
              <div v-for="item in recentLogs" :key="item.id" class="activity-item">
                <strong>{{ item.detail }}</strong>
                <span>{{ item.username || '系统' }} · {{ formatDate(item.created_at, 'YYYY-MM-DD HH:mm:ss') }}</span>
              </div>
            </div>
            <el-empty v-else description="暂无针对该预警的追踪记录" :image-size="72" />
          </section>

          <section class="detail-panel timeline-panel">
            <div class="panel-title">
              <el-icon><Timer /></el-icon>
              命中链路时间轴
            </div>
            <div v-if="alertTimeline.length" class="timeline-track">
              <div v-for="(item, index) in alertTimeline" :key="`${item.stage}-${index}`" class="timeline-node">
                <div class="timeline-dot" />
                <div class="timeline-content">
                  <strong>{{ item.title }}</strong>
                  <span>{{ item.description }}</span>
                  <small>{{ formatDate(item.time, typeof item.time === 'string' && item.time.length <= 10 ? 'YYYY-MM-DD' : 'YYYY-MM-DD HH:mm:ss') }}</small>
                </div>
              </div>
            </div>
            <el-empty v-else description="暂无命中链路记录" :image-size="72" />
          </section>

          <section class="drawer-actions">
            <el-button :disabled="!detailData.contract" @click="goDetail(detailData)">
              跳转合同详情
            </el-button>
            <el-button
              type="success"
              :disabled="detailData.status === 'processed'"
              :loading="processingIds.includes(detailData.id)"
              @click="handleProcess(detailData)"
            >
              标记为已处理
            </el-button>
          </section>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<style scoped lang="scss">
.alerts-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding-bottom: 12px;
}

.hero-section {
  position: relative;
  overflow: hidden;
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(280px, 0.8fr);
  gap: 16px;
  padding: 30px;
  border-radius: 28px;
  background:
    radial-gradient(circle at top left, rgba(72, 121, 255, 0.26), transparent 34%),
    radial-gradient(circle at bottom right, rgba(255, 167, 38, 0.18), transparent 32%),
    linear-gradient(135deg, #0f172a 0%, #131f38 48%, #1d3158 100%);
  box-shadow: 0 30px 60px rgba(15, 23, 42, 0.16);
  color: #f8fafc;
}

.hero-copy {
  max-width: 760px;

  h1 {
    margin: 8px 0 10px;
    font-size: 34px;
    line-height: 1.08;
    letter-spacing: -0.03em;
  }

  p {
    margin: 0;
    max-width: 640px;
    color: rgba(226, 232, 240, 0.8);
    font-size: 15px;
    line-height: 1.7;
  }
}

.eyebrow,
.drawer-eyebrow {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: #a5d8ff;
  font-size: 12px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.hero-side {
  display: flex;
  align-items: stretch;
  justify-content: flex-end;
}

.radar-card {
  min-height: 180px;
  width: 100%;
  border-radius: 24px;
  padding: 22px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.06)),
    rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(16px);
}

.radar-label {
  color: rgba(226, 232, 240, 0.76);
  font-size: 13px;
}

.radar-value {
  margin-top: 18px;
  font-size: 56px;
  font-weight: 700;
  line-height: 1;
}

.radar-subtitle {
  margin-top: 14px;
  color: rgba(226, 232, 240, 0.7);
  font-size: 13px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.metric-card {
  position: relative;
  overflow: hidden;
  text-align: left;
  border: none;
  cursor: pointer;
  padding: 18px;
  border-radius: 22px;
  background: #ffffff;
  box-shadow: 0 18px 36px rgba(15, 23, 42, 0.06);
  transition: transform 0.2s ease, box-shadow 0.2s ease;

  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 22px 40px rgba(15, 23, 42, 0.1);
  }

  &.blue {
    background: linear-gradient(180deg, #f5f9ff 0%, #edf4ff 100%);
  }

  &.red {
    background: linear-gradient(180deg, #fff6f5 0%, #fff0ef 100%);
  }

  &.amber {
    background: linear-gradient(180deg, #fffaf1 0%, #fff4df 100%);
  }

  &.green {
    background: linear-gradient(180deg, #f4fff8 0%, #eafbf0 100%);
  }
}

.metric-icon,
.drawer-metric-card .el-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.06);
  color: #0f172a;
  font-size: 18px;
}

.metric-title {
  margin-top: 16px;
  color: #64748b;
  font-size: 13px;
}

.metric-value {
  margin-top: 10px;
  font-size: 30px;
  font-weight: 700;
  color: #0f172a;
}

.workspace-shell {
  border-radius: 28px;
  background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
  box-shadow: 0 22px 44px rgba(15, 23, 42, 0.06);
  border: 1px solid rgba(15, 23, 42, 0.06);
  overflow: hidden;
}

.workspace-toolbar {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  padding: 22px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.14);
}

.toolbar-left {
  display: grid;
  grid-template-columns: minmax(260px, 1.5fr) repeat(4, minmax(120px, 0.7fr));
  gap: 10px;
  flex: 1;
}

.owner-filter {
  min-width: 220px;
}

.toolbar-right {
  display: flex;
  gap: 10px;
  align-items: center;
}

.toolbar-search {
  position: relative;

  .el-icon {
    position: absolute;
    left: 12px;
    top: 50%;
    transform: translateY(-50%);
    z-index: 1;
    color: #94a3b8;
  }

  :deep(.el-input__wrapper) {
    padding-left: 34px;
  }
}

.selection-bar {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 0 22px 18px;
  color: #475569;
  font-size: 13px;
}

.selection-left,
.selection-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.muted {
  color: #94a3b8;
}

.alerts-table {
  :deep(.el-table__header-wrapper th) {
    background: rgba(248, 250, 252, 0.92);
    color: #64748b;
    font-weight: 600;
  }

  :deep(.el-table__row td) {
    padding-top: 16px;
    padding-bottom: 16px;
  }
}

.title-cell {
  .title-line {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 6px;
  }

  .title-text {
    color: #0f172a;
    font-weight: 600;
  }

  p {
    margin: 0;
    color: #64748b;
    font-size: 13px;
    line-height: 1.6;
  }
}

.link-btn,
.drawer-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0;
  border: none;
  background: transparent;
  color: #165dff;
  cursor: pointer;
  font-weight: 600;

  &:disabled {
    color: #94a3b8;
    cursor: not-allowed;
  }
}

.owner-cell,
.due-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;

  span {
    color: #0f172a;
  }

  small {
    color: #64748b;
    font-size: 12px;
  }
}

.table-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.table-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 20px 22px 22px;
  border-top: 1px solid rgba(148, 163, 184, 0.14);
}

.footer-note {
  color: #94a3b8;
  font-size: 13px;
}

.drawer-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  width: 100%;

  h3 {
    margin: 10px 0 0;
    color: #0f172a;
    font-size: 24px;
    line-height: 1.2;
  }
}

.drawer-body {
  min-height: 280px;
}

.drawer-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.drawer-hero {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 20px;
  border-radius: 24px;
  background:
    radial-gradient(circle at top right, rgba(59, 130, 246, 0.14), transparent 30%),
    linear-gradient(180deg, #f8fbff 0%, #f6f9fe 100%);
  border: 1px solid rgba(59, 130, 246, 0.1);
}

.drawer-type-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  color: #475569;
  font-size: 13px;
}

.drawer-hero-main p,
.suggestion-panel p {
  margin: 0;
  color: #334155;
  line-height: 1.8;
}

.drawer-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.drawer-metric-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
  border-radius: 20px;
  background: #fff;
  border: 1px solid rgba(15, 23, 42, 0.06);
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.05);

  strong {
    color: #0f172a;
    font-size: 15px;
    line-height: 1.5;
  }

  span {
    color: #64748b;
    font-size: 12px;
  }

  &.red {
    background: linear-gradient(180deg, #fff7f7 0%, #fff1f1 100%);
  }

  &.green {
    background: linear-gradient(180deg, #f4fff8 0%, #eefcf2 100%);
  }

  &.amber {
    background: linear-gradient(180deg, #fffaf1 0%, #fff6e6 100%);
  }

  &.blue {
    background: linear-gradient(180deg, #f5f9ff 0%, #eef5ff 100%);
  }

  &.slate {
    background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  }
}

.detail-panel {
  padding: 18px 20px;
  border-radius: 22px;
  background: #fff;
  border: 1px solid rgba(15, 23, 42, 0.06);
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.04);
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
  color: #0f172a;
  font-weight: 600;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px 12px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 6px;

  label {
    color: #94a3b8;
    font-size: 12px;
  }

  span {
    color: #0f172a;
    font-size: 14px;
    line-height: 1.5;
  }
}

.assignment-form {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.activity-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px 16px;
  border-radius: 16px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);

  strong {
    color: #0f172a;
    font-size: 14px;
    line-height: 1.5;
  }

  span {
    color: #64748b;
    font-size: 12px;
  }
}

.timeline-track {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.timeline-node {
  position: relative;
  display: grid;
  grid-template-columns: 18px minmax(0, 1fr);
  gap: 12px;

  &:not(:last-child)::after {
    content: '';
    position: absolute;
    left: 8px;
    top: 22px;
    bottom: -12px;
    width: 2px;
    background: linear-gradient(180deg, rgba(59, 130, 246, 0.28), rgba(148, 163, 184, 0.18));
  }
}

.timeline-dot {
  width: 18px;
  height: 18px;
  margin-top: 2px;
  border-radius: 999px;
  background: linear-gradient(180deg, #3b82f6 0%, #2563eb 100%);
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.12);
}

.timeline-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 14px;
  border-radius: 16px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);

  strong {
    color: #0f172a;
    font-size: 14px;
  }

  span {
    color: #475569;
    font-size: 13px;
    line-height: 1.6;
  }

  small {
    color: #94a3b8;
    font-size: 12px;
  }
}

.drawer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-bottom: 8px;
}

:deep(.el-input__wrapper),
:deep(.el-select__wrapper) {
  border-radius: 14px;
  box-shadow: none;
  min-height: 42px;
}

:deep(.el-button) {
  border-radius: 14px;
}

:deep(.alert-drawer .el-drawer__header) {
  margin-bottom: 0;
  padding-bottom: 8px;
}

@media (max-width: 1380px) {
  .toolbar-left {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 1280px) {
  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .workspace-toolbar {
    flex-direction: column;
  }

  .toolbar-left {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .drawer-metrics,
  .detail-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 960px) {
  .hero-section {
    grid-template-columns: 1fr;
    padding: 22px;
  }

  .metric-grid,
  .drawer-metrics,
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .toolbar-left,
  .assignment-form {
    grid-template-columns: 1fr;
  }

  .toolbar-right,
  .selection-bar,
  .table-footer,
  .drawer-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
