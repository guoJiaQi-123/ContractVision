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
    <section class="page-header">
      <div class="header-main">
        <div class="header-title-row">
          <h1>预警工作台</h1>
          <div class="risk-badge">
            <span class="risk-dot" />
            <span>近7日风险密度：{{ summary.week_count || 0 }} 条</span>
          </div>
        </div>
        <p class="header-desc">付款到期、交付逾期、合同到期与目标偏差集中视图 — 支持筛选、批量处理、详情抽屉跟踪与管理员重分派。</p>
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
        <div class="metric-icon-wrap">
          <el-icon :size="18"><component :is="card.icon" /></el-icon>
        </div>
        <div class="metric-body">
          <span class="metric-title">{{ card.title }}</span>
          <span class="metric-value">{{ card.value }}</span>
        </div>
      </button>
    </section>

    <section class="workspace-panel">
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
          <span class="muted">逾期 {{ summary.overdue_count || 0 }} 条</span>
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
                <span class="level-dot" :class="row.level" />
                <span class="title-text">{{ row.title }}</span>
                <el-tag :type="getLevelType(row.level)" effect="plain" size="small">
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
              <small :class="{ overdue: getCountdownText(row).includes('逾期') }">{{ getCountdownText(row) }}</small>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" effect="plain">
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
      size="540px"
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
            effect="plain"
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
                <el-tag :type="getLevelType(detailData.level)" effect="plain" size="small">
                  {{ getLevelLabel(detailData.level) }}
                </el-tag>
                <span class="type-sep">{{ getTypeLabel(detailData.warning_type) }}</span>
                <span class="type-sep">{{ detailData.contract_no || '通用事项' }}</span>
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
              <div class="dm-icon">
                <el-icon :size="16"><component :is="item.icon" /></el-icon>
              </div>
              <div class="dm-body">
                <span class="dm-value">{{ item.value }}</span>
                <span class="dm-label">{{ item.label }}</span>
              </div>
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

          <section v-if="contractSnapshot" class="detail-panel">
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
            <div class="explain-list">
              <div class="explain-row">
                <span class="explain-key">{{ ownerStrategy?.catalog_title || '负责人分派策略' }}</span>
                <span class="explain-val">{{ ownerStrategy?.strategy_title || '系统自动匹配负责人' }}</span>
              </div>
              <div class="explain-row">
                <span class="explain-key">归属原因</span>
                <span class="explain-val">{{ ownerStrategy?.reason || '当前未生成负责人解释。' }}</span>
              </div>
              <div class="explain-row">
                <span class="explain-key">触发原因</span>
                <span class="explain-val">{{ detailData?.trigger_summary || '当前未生成命中说明。' }}</span>
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
              <div v-for="item in recentLogs" :key="item.id" class="activity-row">
                <span class="activity-detail">{{ item.detail }}</span>
                <span class="activity-meta">{{ item.username || '系统' }} · {{ formatDate(item.created_at, 'YYYY-MM-DD HH:mm:ss') }}</span>
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

<style lang="scss" scoped>
.alerts-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-bottom: 12px;
}

.page-header {
  padding: 24px 28px;
  border-radius: var(--radius-md);
  background: var(--gray-800);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.header-main {
  max-width: 960px;
}

.header-title-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 8px;

  h1 {
    margin: 0;
    font-size: var(--fs-xl);
    font-weight: 600;
    color: #fff;
    letter-spacing: -0.01em;
  }
}

.risk-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border-radius: var(--radius-xs);
  background: rgba(239, 68, 68, 0.12);
  color: var(--danger);
  font-size: var(--fs-xs);
  font-weight: 500;
}

.risk-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--danger);
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.header-desc {
  margin: 0;
  color: var(--gray-400);
  font-size: var(--fs-sm);
  line-height: 1.7;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
  border-radius: var(--radius-sm);
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  cursor: pointer;
  text-align: left;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);

  &:hover {
    border-color: var(--gray-300);
    box-shadow: var(--shadow-sm);
  }

  &.blue {
    border-left: 3px solid var(--primary-dark);

    .metric-icon-wrap {
      background: var(--primary-bg);
      color: var(--primary-dark);
    }
  }

  &.red {
    border-left: 3px solid var(--danger);

    .metric-icon-wrap {
      background: var(--danger-bg);
      color: var(--danger);
    }
  }

  &.amber {
    border-left: 3px solid var(--warning);

    .metric-icon-wrap {
      background: var(--warning-bg);
      color: var(--warning);
    }
  }

  &.green {
    border-left: 3px solid var(--success);

    .metric-icon-wrap {
      background: var(--success-bg);
      color: var(--success);
    }
  }
}

.metric-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}

.metric-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.metric-title {
  color: var(--text-muted);
  font-size: var(--fs-xs);
  line-height: 1.4;
}

.metric-value {
  color: var(--gray-900);
  font-size: var(--fs-2xl);
  font-weight: 700;
  line-height: 1.2;
  font-variant-numeric: tabular-nums;
}

.workspace-panel {
  border-radius: var(--radius-md);
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.workspace-toolbar {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  background: var(--gray-50);
}

.toolbar-left {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  flex: 1;

  :deep(.el-select) {
    width: 110px;
    flex-shrink: 0;
  }
}

.owner-filter {
  width: 160px !important;
  min-width: 160px;
}

.toolbar-right {
  display: flex;
  gap: 8px;
  align-items: center;
}

.toolbar-search {
  position: relative;
  width: 220px;
  flex-shrink: 0;

  .el-icon {
    position: absolute;
    left: 10px;
    top: 50%;
    transform: translateY(-50%);
    z-index: 1;
    color: var(--text-muted);
  }

  :deep(.el-input__wrapper) {
    padding-left: 32px;
  }
}

.selection-bar {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 20px;
  border-bottom: 1px solid var(--border-light);
  color: var(--gray-600);
  font-size: var(--fs-xs);
}

.selection-left,
.selection-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.muted {
  color: var(--text-muted);
}

.alerts-table {
  :deep(.el-table__header-wrapper th) {
    background: var(--gray-50);
    color: var(--gray-600);
    font-weight: 600;
    font-size: var(--fs-xs);
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  :deep(.el-table__row td) {
    padding-top: 14px;
    padding-bottom: 14px;
  }
}

.level-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;

  &.high { background: var(--danger); }
  &.medium { background: var(--warning); }
  &.low { background: var(--primary); }
}

.title-cell {
  .title-line {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
  }

  .title-text {
    color: var(--text-primary);
    font-weight: 600;
    font-size: var(--fs-base);
  }

  p {
    margin: 0;
    color: var(--text-muted);
    font-size: var(--fs-xs);
    line-height: 1.6;
  }
}

.link-btn,
.drawer-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 0;
  border: none;
  background: transparent;
  color: var(--primary-dark);
  cursor: pointer;
  font-weight: 500;
  font-size: var(--fs-sm);
  transition: color var(--transition-fast);

  &:hover { color: var(--primary); }

  &:disabled {
    color: var(--text-muted);
    cursor: not-allowed;
  }
}

.owner-cell,
.due-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;

  span {
    color: var(--gray-800);
    font-size: var(--fs-sm);
  }

  small {
    color: var(--text-muted);
    font-size: var(--fs-xs);

    &.overdue {
      color: var(--danger);
      font-weight: 500;
    }
  }
}

.table-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.table-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  border-top: 1px solid var(--border-color);
}

.footer-note {
  color: var(--text-muted);
  font-size: var(--fs-xs);
}

.drawer-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  width: 100%;

  h3 {
    margin: 8px 0 0;
    color: var(--text-primary);
    font-size: var(--fs-lg);
    font-weight: 600;
    line-height: 1.3;
  }
}

.drawer-eyebrow {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-xs);
  background: var(--gray-100);
  color: var(--gray-600);
  font-size: var(--fs-xs);
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.drawer-body {
  min-height: 280px;
}

.drawer-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.drawer-hero {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  border-radius: var(--radius-sm);
  background: var(--gray-50);
  border: 1px solid var(--border-color);
}

.drawer-type-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  color: var(--gray-600);
  font-size: var(--fs-xs);
}

.type-sep {
  &::before {
    content: '·';
    margin-right: 8px;
    color: var(--gray-300);
  }
}

.drawer-hero-main p,
.suggestion-panel p {
  margin: 0;
  color: var(--gray-700);
  font-size: var(--fs-sm);
  line-height: 1.8;
}

.drawer-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.drawer-metric-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border-radius: var(--radius-sm);
  background: var(--card-bg);
  border: 1px solid var(--border-color);

  &.red { border-left: 3px solid var(--danger); }
  &.green { border-left: 3px solid var(--success); }
  &.amber { border-left: 3px solid var(--warning); }
  &.blue { border-left: 3px solid var(--primary-dark); }
  &.slate { border-left: 3px solid var(--gray-500); }
}

.dm-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-xs);
  flex-shrink: 0;

  .red & { background: var(--danger-bg); color: var(--danger); }
  .green & { background: var(--success-bg); color: var(--success); }
  .amber & { background: var(--warning-bg); color: var(--warning); }
  .blue & { background: var(--primary-bg); color: var(--primary-dark); }
  .slate & { background: var(--gray-100); color: var(--gray-600); }
}

.dm-body {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.dm-value {
  color: var(--text-primary);
  font-size: var(--fs-base);
  font-weight: 600;
  line-height: 1.4;
}

.dm-label {
  color: var(--text-muted);
  font-size: var(--fs-xs);
}

.detail-panel {
  padding: 14px 16px;
  border-radius: var(--radius-sm);
  background: var(--card-bg);
  border: 1px solid var(--border-color);
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
  color: var(--gray-800);
  font-size: var(--fs-sm);
  font-weight: 600;

  .el-icon {
    color: var(--text-muted);
  }
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 16px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 3px;

  label {
    color: var(--text-muted);
    font-size: var(--fs-xs);
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  span {
    color: var(--gray-800);
    font-size: var(--fs-sm);
    line-height: 1.5;
  }
}

.assignment-form {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
}

.explain-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.explain-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-light);

  &:last-child {
    border-bottom: none;
    padding-bottom: 0;
  }

  &:first-child {
    padding-top: 0;
  }
}

.explain-key {
  color: var(--gray-600);
  font-size: var(--fs-xs);
  font-weight: 500;
  white-space: nowrap;
}

.explain-val {
  color: var(--gray-800);
  font-size: var(--fs-xs);
  text-align: right;
  line-height: 1.5;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.activity-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-light);

  &:last-child {
    border-bottom: none;
    padding-bottom: 0;
  }

  &:first-child {
    padding-top: 0;
  }
}

.activity-detail {
  color: var(--gray-800);
  font-size: var(--fs-xs);
  font-weight: 500;
}

.activity-meta {
  color: var(--text-muted);
  font-size: var(--fs-xs);
  white-space: nowrap;
}

.timeline-track {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.timeline-node {
  position: relative;
  display: grid;
  grid-template-columns: 16px minmax(0, 1fr);
  gap: 10px;
  padding: 8px 0;

  &:not(:last-child)::after {
    content: '';
    position: absolute;
    left: 7px;
    top: 26px;
    bottom: -8px;
    width: 1px;
    background: var(--gray-300);
  }
}

.timeline-dot {
  width: 14px;
  height: 14px;
  margin-top: 2px;
  border-radius: 50%;
  background: var(--gray-800);
  border: 2px solid var(--gray-300);
}

.timeline-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 12px;
  border-radius: var(--radius-xs);
  background: var(--gray-50);
  border: 1px solid var(--border-light);

  strong {
    color: var(--gray-800);
    font-size: var(--fs-xs);
    font-weight: 600;
  }

  span {
    color: var(--gray-600);
    font-size: var(--fs-xs);
    line-height: 1.6;
  }

  small {
    color: var(--text-muted);
    font-size: var(--fs-xs);
  }
}

.drawer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 4px;
}

:deep(.el-input__wrapper),
:deep(.el-select__wrapper) {
  border-radius: var(--radius-xs);
  box-shadow: none;
  min-height: 36px;
  border: 1px solid var(--border-color);
  transition: border-color var(--transition-fast);
}

:deep(.el-button) {
  border-radius: var(--radius-xs);
  transition: all var(--transition-fast);
}

:deep(.alert-drawer .el-drawer__header) {
  margin-bottom: 0;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color);
}

:deep(.el-tag) {
  border-radius: var(--radius-xs);
}

:deep(.el-button--primary) {
  --el-button-bg-color: var(--gray-800);
  --el-button-border-color: var(--gray-800);
  --el-button-hover-bg-color: var(--gray-700);
  --el-button-hover-border-color: var(--gray-700);
  --el-button-active-bg-color: var(--gray-900);
  --el-button-active-border-color: var(--gray-900);
}

@media (max-width: 1380px) {
  .toolbar-left {
    flex-wrap: wrap;
  }
}

@media (max-width: 1280px) {
  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .workspace-toolbar {
    flex-direction: column;
  }

  .drawer-metrics,
  .detail-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 960px) {
  .page-header {
    padding: 18px 20px;
  }

  .header-title-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .metric-grid,
  .drawer-metrics,
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .toolbar-left,
  .assignment-form {
    flex-direction: column;
  }

  .toolbar-search {
    min-width: 100%;
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
