<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Bell,
  Clock,
  DataBoard,
  MagicStick,
  Connection,
  Histogram,
  ArrowRight,
  Download,
  Guide
} from '@element-plus/icons-vue'
import { getUserList } from '@/api/user'
import {
  getApprovalProcesses,
  createApprovalProcess,
  getApprovalRequests,
  approveApprovalRequest,
  rejectApprovalRequest
} from '@/api/contract'
import {
  getDataPermissionRules,
  createDataPermissionRule,
  getAlertRules,
  createAlertRule,
  updateAlertRule,
  getAlertRuleStrategyOptions,
  getAlertRulePreviewImpact,
  getAlerts,
  scanAlerts,
  getAlertScanPreview,
  getAlertScanSummary,
  processAlert
} from '@/api/system'
import { formatDate } from '@/utils'

const router = useRouter()
const users = ref([])
const approvalProcesses = ref([])
const approvalRequests = ref([])
const permissionRules = ref([])
const alertRules = ref([])
const alerts = ref([])
const alertStrategyOptions = ref({})
const alertStrategyDefaults = ref({})
const alertStrategyCatalog = ref([])
const loading = ref(false)
const scanLoading = ref(false)
const summaryLoading = ref(false)
const previewLoading = ref(false)
const impactPreviewLoading = ref(false)
const scanPreview = ref({
  total_hits: 0,
  creatable_total: 0,
  type_counts: {},
  creatable_type_counts: {},
  preview_items: []
})
const scanSummary = ref({
  pending_total: 0,
  processed_total: 0,
  type_counts: {},
  recent_scans: [],
  recent_actions: []
})

const processDialogVisible = ref(false)
const permissionDialogVisible = ref(false)
const alertRuleDialogVisible = ref(false)
const editingAlertRuleId = ref(null)
const originalAlertRule = ref(null)
const strategyImpactPreview = ref(null)

const processForm = ref({
  name: '',
  action_type: 'update',
  min_amount: 0,
  steps: [{ name: '一级审批', approver_role: 'admin' }]
})

const permissionForm = ref({
  user: null,
  scope_type: 'self',
  scope_value: '',
  can_edit: false
})

const alertRuleForm = ref({
  name: '',
  rule_type: 'payment_due',
  remind_days: 7,
  owner_role: 'operator',
  level: 'medium',
  is_active: true
})
const previewFilters = ref({
  rule_type: '',
  only_creatable: true
})
const auditFilters = ref({
  warning_type: '',
  action: '',
  operator: '',
  date_range: []
})

const governanceCards = computed(() => [
  {
    key: 'pending',
    title: '待处理预警',
    value: scanSummary.value.pending_total || 0,
    icon: Bell,
    tone: 'blue'
  },
  {
    key: 'processed',
    title: '已处理预警',
    value: scanSummary.value.processed_total || 0,
    icon: DataBoard,
    tone: 'green'
  },
  {
    key: 'recent',
    title: '最近扫描',
    value: scanSummary.value.recent_scans?.length || 0,
    icon: MagicStick,
    tone: 'violet'
  },
  {
    key: 'handoff',
    title: '最近处置',
    value: scanSummary.value.recent_actions?.length || 0,
    icon: Connection,
    tone: 'amber'
  }
])

const typeStatCards = computed(() => {
  const typeCounts = scanSummary.value.type_counts || {}
  return [
    { label: '付款到期', value: typeCounts.payment_due || 0 },
    { label: '交付到期', value: typeCounts.delivery_due || 0 },
    { label: '合同到期', value: typeCounts.contract_expiry || 0 },
    { label: '发票开具', value: typeCounts.invoice_due || 0 },
    { label: '目标达成', value: typeCounts.target_progress || 0 }
  ]
})

const recentScanHeadline = computed(() => scanSummary.value.recent_scans?.[0] || null)

const previewTypeChips = computed(() => {
  const typeCounts = scanPreview.value.creatable_type_counts || {}
  return [
    { label: '付款到期', value: typeCounts.payment_due || 0 },
    { label: '交付到期', value: typeCounts.delivery_due || 0 },
    { label: '合同到期', value: typeCounts.contract_expiry || 0 },
    { label: '发票开具', value: typeCounts.invoice_due || 0 },
    { label: '目标达成', value: typeCounts.target_progress || 0 }
  ]
})

const strategyCatalog = computed(
  () => alertStrategyCatalog.value.length
    ? alertStrategyCatalog.value
    : (scanPreview.value.strategy_catalog || scanSummary.value.strategy_catalog || [])
)

const isEditingAlertRule = computed(() => Boolean(editingAlertRuleId.value))
const hasStrategyChanged = computed(() => {
  if (!isEditingAlertRule.value || !originalAlertRule.value) return false
  return normalizeRuleStrategyValue(alertRuleForm.value.rule_type, alertRuleForm.value.owner_role) !==
    normalizeRuleStrategyValue(originalAlertRule.value.rule_type, originalAlertRule.value.owner_role)
})

const warningTypeOptions = [
  { label: '付款到期', value: 'payment_due' },
  { label: '交付到期', value: 'delivery_due' },
  { label: '合同到期', value: 'contract_expiry' },
  { label: '发票开具', value: 'invoice_due' },
  { label: '目标达成', value: 'target_progress' }
]

const auditActionOptions = [
  { label: '预警处理', value: 'ALERT_PROCESS' },
  { label: '预警改派', value: 'ALERT_REASSIGN' }
]

const getRuleStrategyOptions = (ruleType) => alertStrategyOptions.value[ruleType] || []

const getDefaultStrategyValue = (ruleType) =>
  alertStrategyDefaults.value[ruleType] || getRuleStrategyOptions(ruleType)[0]?.value || ''

const normalizeRuleStrategyValue = (ruleType, ownerRole) => {
  const options = getRuleStrategyOptions(ruleType)
  if (options.some((item) => item.value === ownerRole)) {
    return ownerRole
  }
  return getDefaultStrategyValue(ruleType)
}

const getRuleStrategyMeta = (ruleType, ownerRole) => {
  const normalizedValue = normalizeRuleStrategyValue(ruleType, ownerRole)
  return getRuleStrategyOptions(ruleType).find((item) => item.value === normalizedValue) || {}
}

const clearStrategyImpactPreview = () => {
  strategyImpactPreview.value = null
}

const syncAlertRuleStrategy = () => {
  alertRuleForm.value.owner_role = normalizeRuleStrategyValue(
    alertRuleForm.value.rule_type,
    alertRuleForm.value.owner_role
  )
  clearStrategyImpactPreview()
}

const resetAlertRuleForm = () => {
  editingAlertRuleId.value = null
  originalAlertRule.value = null
  strategyImpactPreview.value = null
  alertRuleForm.value = {
    name: '',
    rule_type: 'payment_due',
    remind_days: 7,
    owner_role: getDefaultStrategyValue('payment_due'),
    level: 'medium',
    is_active: true
  }
  syncAlertRuleStrategy()
}

const openCreateAlertRuleDialog = () => {
  resetAlertRuleForm()
  alertRuleDialogVisible.value = true
}

const openEditAlertRuleDialog = (row) => {
  editingAlertRuleId.value = row.id
  originalAlertRule.value = { ...row }
  strategyImpactPreview.value = null
  alertRuleForm.value = {
    name: row.name || '',
    rule_type: row.rule_type || 'payment_due',
    remind_days: row.remind_days || 7,
    owner_role: normalizeRuleStrategyValue(row.rule_type, row.owner_role),
    level: row.level || 'medium',
    is_active: row.is_active !== false
  }
  alertRuleDialogVisible.value = true
}

const closeAlertRuleDialog = () => {
  alertRuleDialogVisible.value = false
  resetAlertRuleForm()
}

const loadStrategyImpactPreview = async () => {
  if (!isEditingAlertRule.value) return
  impactPreviewLoading.value = true
  try {
    const res = await getAlertRulePreviewImpact({
      rule_type: alertRuleForm.value.rule_type,
      owner_role: normalizeRuleStrategyValue(alertRuleForm.value.rule_type, alertRuleForm.value.owner_role),
      only_creatable: String(previewFilters.value.only_creatable)
    })
    strategyImpactPreview.value = res.data || null
  } finally {
    impactPreviewLoading.value = false
  }
}

const loadBaseData = async () => {
  loading.value = true
  try {
    const [userRes, processRes, requestRes, permissionRes, alertRuleRes, alertRes, strategyRes] = await Promise.all([
      getUserList({ page: 1, page_size: 200 }),
      getApprovalProcesses(),
      getApprovalRequests(),
      getDataPermissionRules(),
      getAlertRules(),
      getAlerts({ page: 1, page_size: 12 }),
      getAlertRuleStrategyOptions()
    ])
    users.value = userRes.data?.results || userRes.data || []
    approvalProcesses.value = processRes.data?.results || processRes.data || []
    approvalRequests.value = requestRes.data?.results || requestRes.data || []
    permissionRules.value = permissionRes.data?.results || permissionRes.data || []
    alertRules.value = alertRuleRes.data?.results || alertRuleRes.data || []
    alerts.value = alertRes.data?.results || alertRes.data || []
    alertStrategyOptions.value = strategyRes.data?.options || {}
    alertStrategyDefaults.value = strategyRes.data?.defaults || {}
    alertStrategyCatalog.value = strategyRes.data?.catalog || []
  } finally {
    loading.value = false
  }
}

const loadScanPreview = async () => {
  previewLoading.value = true
  try {
    const params = {}
    if (previewFilters.value.rule_type) params.rule_type = previewFilters.value.rule_type
    params.only_creatable = String(previewFilters.value.only_creatable)
    const res = await getAlertScanPreview(params)
    scanPreview.value = res.data || scanPreview.value
  } finally {
    previewLoading.value = false
  }
}

const loadScanSummary = async () => {
  summaryLoading.value = true
  try {
    const params = {}
    ;['warning_type', 'action', 'operator'].forEach((key) => {
      if (auditFilters.value[key]) params[key] = auditFilters.value[key]
    })
    if (auditFilters.value.date_range?.length === 2) {
      params.date_from = auditFilters.value.date_range[0]
      params.date_to = auditFilters.value.date_range[1]
    }
    const res = await getAlertScanSummary(params)
    scanSummary.value = res.data || scanSummary.value
  } finally {
    summaryLoading.value = false
  }
}

const loadData = async () => {
  await Promise.all([loadBaseData(), loadScanSummary(), loadScanPreview()])
}

const submitProcess = async () => {
  await createApprovalProcess(processForm.value)
  processDialogVisible.value = false
  ElMessage.success('审批流程已创建')
  await loadData()
}

const submitPermission = async () => {
  await createDataPermissionRule(permissionForm.value)
  permissionDialogVisible.value = false
  ElMessage.success('数据权限已下发')
  await loadData()
}

const submitAlertRule = async () => {
  const payload = {
    ...alertRuleForm.value,
    owner_role: normalizeRuleStrategyValue(alertRuleForm.value.rule_type, alertRuleForm.value.owner_role)
  }
  if (editingAlertRuleId.value) {
    await updateAlertRule(editingAlertRuleId.value, payload)
    ElMessage.success('预警规则已更新')
  } else {
    await createAlertRule(payload)
    ElMessage.success('预警规则已创建')
  }
  closeAlertRuleDialog()
  await loadData()
}

const handleApproveRequest = async (row) => {
  await approveApprovalRequest(row.id, {})
  ElMessage.success('审批已通过')
  await loadData()
}

const handleRejectRequest = async (row) => {
  await rejectApprovalRequest(row.id, {})
  ElMessage.success('审批已驳回')
  await loadData()
}

const handleScanAlerts = async () => {
  scanLoading.value = true
  try {
    const res = await scanAlerts()
    const createdCount = res.data?.created_count || 0
    const typeCounts = res.data?.created_type_counts || {}
    const summaryText = Object.entries(typeCounts)
      .filter(([, value]) => value)
      .map(([key, value]) => `${key}:${value}`)
      .join(' / ')
    ElMessage.success(summaryText ? `预警扫描完成，新增 ${createdCount} 条，${summaryText}` : `预警扫描完成，新增 ${createdCount} 条`)
    await loadData()
  } finally {
    scanLoading.value = false
  }
}

const handleProcessAlert = async (row) => {
  await processAlert(row.id)
  ElMessage.success('预警已处理')
  await loadData()
}

const handleExportPreview = async () => {
  const rows = [
    ['预警类型', '规则名称', '预警标题', '合同编号', '负责人', '负责人策略', '触发说明', '截止时间', '状态'],
    ...((scanPreview.value.preview_items || []).map((item) => [
      warningTypeOptions.find((option) => option.value === item.warning_type)?.label || item.warning_type || '',
      item.rule_name || '',
      item.title || '',
      item.contract_no || '',
      item.owner?.username || '',
      item.owner_strategy?.strategy_title || '',
      item.trigger_summary || '',
      item.due_date || '',
      item.existing_pending ? '已存在待处理' : '将新建'
    ]))
  ]
  const csvContent = '\uFEFF' + rows.map((row) => row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(',')).join('\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'alert-scan-preview.csv'
  link.click()
  window.URL.revokeObjectURL(url)
  ElMessage.success('预览结果已导出')
}

const handleExportAudit = async () => {
  const rows = [
    ['预警类型', '动作类型', '操作说明', '操作人', '时间'],
    ...((scanSummary.value.recent_actions || []).map((item) => [
      warningTypeOptions.find((option) => option.value === item.warning_type)?.label || item.warning_type || '',
      auditActionOptions.find((option) => option.value === item.action)?.label || item.action || '',
      item.detail || '',
      item.username || '',
      item.created_at ? formatDate(item.created_at, 'YYYY-MM-DD HH:mm:ss') : ''
    ]))
  ]
  const csvContent = '\uFEFF' + rows.map((row) => row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(',')).join('\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'alert-audit-export.csv'
  link.click()
  window.URL.revokeObjectURL(url)
  ElMessage.success('处置审计已导出')
}

const handlePreviewFilterChange = async () => {
  await loadScanPreview()
}

const handleAuditFilterChange = async () => {
  await loadScanSummary()
}

const resetPreviewFilters = async () => {
  previewFilters.value = {
    rule_type: '',
    only_creatable: true
  }
  await loadScanPreview()
}

const resetAuditFilters = async () => {
  auditFilters.value = {
    warning_type: '',
    action: '',
    operator: '',
    date_range: []
  }
  await loadScanSummary()
}

const goAlertWorkspace = () => {
  router.push('/contract/alerts')
}

onMounted(() => {
  resetAlertRuleForm()
  loadData()
})
</script>

<template>
  <div class="governance-page">
    <section class="hero-card">
      <div class="hero-main">
        <div class="eyebrow">F026 - F031</div>
        <h1>治理控制台</h1>
        <p>统一配置审批流程、行级权限与预警规则，并把扫描结果、最近处置与高风险分布集中在一个管理员视图里。</p>
      </div>
      <div class="hero-side">
        <div class="hero-status-card">
          <span>最近扫描</span>
          <strong>{{ recentScanHeadline?.username || '暂无记录' }}</strong>
          <small>{{ recentScanHeadline?.created_at ? formatDate(recentScanHeadline.created_at, 'YYYY-MM-DD HH:mm:ss') : '等待首次执行' }}</small>
        </div>
        <div class="hero-actions">
          <el-button @click="processDialogVisible = true">新建审批流程</el-button>
          <el-button @click="permissionDialogVisible = true">配置数据权限</el-button>
          <el-button type="primary" :loading="scanLoading" @click="handleScanAlerts">立即扫描预警</el-button>
          <el-button type="success" plain @click="goAlertWorkspace">进入预警工作台</el-button>
        </div>
      </div>
    </section>

    <section v-loading="summaryLoading" class="metric-grid">
      <div v-for="card in governanceCards" :key="card.key" class="metric-card" :class="card.tone">
        <div class="metric-icon">
          <el-icon><component :is="card.icon" /></el-icon>
        </div>
        <div class="metric-title">{{ card.title }}</div>
        <div class="metric-value">{{ card.value }}</div>
      </div>
    </section>

    <section v-loading="previewLoading" class="panel preview-panel">
      <div class="panel-header compact light">
        <div>
          <h3>扫描试运行预览</h3>
          <p>正式落库前，先查看本次将命中的预警、负责人归属与重复拦截结果</p>
        </div>
        <div class="filter-actions">
          <el-button @click="resetPreviewFilters">重置</el-button>
          <el-button @click="handleExportPreview">
            <el-icon><Download /></el-icon>
            导出预览
          </el-button>
          <el-button type="primary" plain @click="loadScanPreview">刷新预览</el-button>
        </div>
      </div>
      <div class="filter-bar">
        <el-select v-model="previewFilters.rule_type" placeholder="规则类型" clearable @change="handlePreviewFilterChange">
          <el-option v-for="item in warningTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-switch
          v-model="previewFilters.only_creatable"
          inline-prompt
          active-text="仅看将新建"
          inactive-text="全部命中"
          @change="handlePreviewFilterChange"
        />
      </div>
      <div class="preview-summary-row">
        <div class="preview-summary-card">
          <span>命中总数</span>
          <strong>{{ scanPreview.total_hits || 0 }}</strong>
        </div>
        <div class="preview-summary-card">
          <span>可新建预警</span>
          <strong>{{ scanPreview.creatable_total || 0 }}</strong>
        </div>
        <div class="preview-chip-list">
          <el-tag v-for="item in previewTypeChips" :key="item.label" round effect="light" class="preview-chip">
            {{ item.label }} {{ item.value }}
          </el-tag>
        </div>
      </div>
      <el-table :data="scanPreview.preview_items" class="preview-table">
        <template #empty>
          <el-empty description="暂无命中的试运行预警" :image-size="88" />
        </template>
        <el-table-column prop="title" label="预警标题" min-width="240" />
        <el-table-column prop="contract_no" label="合同编号" width="140">
          <template #default="{ row }">{{ row.contract_no || '通用事项' }}</template>
        </el-table-column>
        <el-table-column label="负责人" min-width="180">
          <template #default="{ row }">
            <div class="preview-owner">
              <span>{{ row.owner?.username || '待分派' }}</span>
              <small>{{ [row.owner?.department, row.owner?.region].filter(Boolean).join(' / ') || '未匹配范围' }}</small>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="策略说明" min-width="220">
          <template #default="{ row }">
            <div class="preview-owner">
              <span>{{ row.owner_strategy?.configured_label || row.owner_strategy?.strategy_title || '系统匹配' }}</span>
              <small>{{ row.owner_strategy?.reason || '-' }}</small>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="命中说明" min-width="240">
          <template #default="{ row }">
            <div class="preview-owner">
              <span>{{ row.trigger_summary || '-' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="时效/结果" width="180">
          <template #default="{ row }">
            <div class="preview-status">
              <el-tag :type="row.existing_pending ? 'info' : 'success'" round effect="light">
                {{ row.existing_pending ? '已存在待处理' : '将新建' }}
              </el-tag>
              <small>{{ row.due_date || '-' }}</small>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="panel strategy-panel">
      <div class="panel-header compact light">
        <div>
          <h3>负责人策略面板</h3>
          <p>展示不同预警类型的默认归属逻辑，便于管理员理解扫描归属口径。</p>
        </div>
      </div>
      <div class="strategy-grid">
        <div v-for="item in strategyCatalog" :key="item.warning_type" class="strategy-card">
          <div class="strategy-badge">
            <el-icon><Guide /></el-icon>
            <span>{{ warningTypeOptions.find(option => option.value === item.warning_type)?.label || item.warning_type }}</span>
          </div>
          <strong>{{ item.configured_label || item.title }}</strong>
          <p>{{ item.description }}</p>
          <small class="strategy-meta">{{ item.rule_name || '系统默认规则' }}</small>
          <small class="strategy-meta">
            当前：{{ item.configured_label || '未配置' }} · 推荐：{{ item.recommended_label || '-' }}
          </small>
        </div>
      </div>
    </section>

    <section class="scan-overview-grid">
      <div class="panel focus-panel">
        <div class="panel-header compact light">
          <div>
            <h3>扫描结果摘要</h3>
            <p>最近一轮扫描产出与当前待处理结构</p>
          </div>
          <el-button link type="primary" @click="handleScanAlerts">
            重新扫描
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
        <div class="type-stat-grid">
          <div v-for="item in typeStatCards" :key="item.label" class="type-stat-item">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </div>
        </div>
        <div class="latest-scan-card">
          <div class="latest-scan-top">
            <div>
              <span class="card-label">最近扫描说明</span>
              <strong>{{ recentScanHeadline?.detail || '尚未执行预警扫描' }}</strong>
            </div>
            <el-icon class="headline-icon"><Histogram /></el-icon>
          </div>
          <small>
            {{ recentScanHeadline?.username || '系统' }}
            {{ recentScanHeadline?.created_at ? ` · ${formatDate(recentScanHeadline.created_at, 'YYYY-MM-DD HH:mm:ss')}` : '' }}
          </small>
        </div>
      </div>

      <div class="panel timeline-panel">
        <div class="panel-header compact light">
          <div>
            <h3>最近扫描历史</h3>
            <p>保留最近几次扫描的执行摘要</p>
          </div>
        </div>
        <div v-if="scanSummary.recent_scans?.length" class="timeline-list">
          <div v-for="item in scanSummary.recent_scans" :key="item.id" class="timeline-item">
            <strong>{{ item.detail }}</strong>
            <span>{{ item.username || '系统' }} · {{ formatDate(item.created_at, 'YYYY-MM-DD HH:mm:ss') }}</span>
          </div>
        </div>
        <el-empty v-else description="暂无扫描历史" :image-size="88" />
      </div>
    </section>

    <el-row :gutter="16">
      <el-col :xs="24" :xl="12">
        <div class="panel dark-panel">
          <div class="panel-header">
            <div>
              <h3>审批流程配置</h3>
              <p>控制合同新增、修改、删除、变更生效路径</p>
            </div>
            <el-button type="primary" @click="processDialogVisible = true">新增流程</el-button>
          </div>
          <el-table v-loading="loading" :data="approvalProcesses">
            <el-table-column prop="name" label="流程名称" min-width="180" />
            <el-table-column prop="action_type" label="动作类型" width="110" />
            <el-table-column prop="min_amount" label="触发金额" width="120" />
            <el-table-column label="步骤数" width="100">
              <template #default="{ row }">{{ row.steps?.length || 0 }}</template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
      <el-col :xs="24" :xl="12">
        <div class="panel dark-panel">
          <div class="panel-header">
            <div>
              <h3>待处理审批</h3>
              <p>合同操作需审批后才能正式生效</p>
            </div>
          </div>
          <el-table v-loading="loading" :data="approvalRequests">
            <el-table-column prop="title" label="审批标题" min-width="220" />
            <el-table-column prop="action_type" label="动作" width="90" />
            <el-table-column prop="status_display" label="状态" width="100" />
            <el-table-column label="操作" width="140">
              <template #default="{ row }">
                <el-button link type="primary" @click="handleApproveRequest(row)">通过</el-button>
                <el-button link type="danger" @click="handleRejectRequest(row)">驳回</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :xl="12">
        <div class="panel dark-panel">
          <div class="panel-header">
            <div>
              <h3>行级权限策略</h3>
              <p>按人员、部门、区域和客户范围过滤合同</p>
            </div>
            <el-button type="primary" @click="permissionDialogVisible = true">新增规则</el-button>
          </div>
          <el-table v-loading="loading" :data="permissionRules">
            <el-table-column prop="username" label="用户" min-width="120" />
            <el-table-column prop="scope_type" label="范围类型" width="110" />
            <el-table-column prop="scope_value" label="范围值" min-width="120" />
            <el-table-column label="编辑权限" width="100">
              <template #default="{ row }">
                <el-tag :type="row.can_edit ? 'success' : 'info'">{{ row.can_edit ? '可编辑' : '只读' }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
      <el-col :xs="24" :xl="12">
        <div class="panel dark-panel">
          <div class="panel-header">
            <div>
              <h3>预警规则</h3>
              <p>覆盖付款、交付、到期、发票与目标达成风险</p>
            </div>
            <el-button type="primary" @click="openCreateAlertRuleDialog">新增规则</el-button>
          </div>
          <el-table v-loading="loading" :data="alertRules">
            <el-table-column prop="name" label="规则名称" min-width="160" />
            <el-table-column prop="rule_type_display" label="类型" width="120" />
            <el-table-column prop="remind_days" label="提前天数" width="100" />
            <el-table-column label="负责人策略" min-width="180">
              <template #default="{ row }">
                {{ getRuleStrategyMeta(row.rule_type, row.owner_role).label || '默认策略' }}
              </template>
            </el-table-column>
            <el-table-column prop="level" label="等级" width="90" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'" effect="light">
                  {{ row.is_active ? '启用' : '停用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button link type="primary" @click="openEditAlertRuleDialog(row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
    </el-row>

    <section class="scan-overview-grid bottom-grid">
      <div class="panel action-panel dark-panel">
        <div class="panel-header">
          <div>
            <h3>最近处置审计</h3>
            <p>记录最近的预警处理与重分派动作</p>
          </div>
          <div class="filter-actions">
            <el-button @click="resetAuditFilters">重置</el-button>
            <el-button @click="handleExportAudit">
              <el-icon><Download /></el-icon>
              导出处置
            </el-button>
          </div>
        </div>
        <div class="audit-filter-bar">
          <el-select v-model="auditFilters.warning_type" placeholder="预警类型" clearable @change="handleAuditFilterChange">
            <el-option v-for="item in warningTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
          <el-select v-model="auditFilters.action" placeholder="动作类型" clearable @change="handleAuditFilterChange">
            <el-option v-for="item in auditActionOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
          <el-select v-model="auditFilters.operator" placeholder="操作人" clearable filterable @change="handleAuditFilterChange">
            <el-option v-for="user in users" :key="user.id" :label="user.username" :value="user.id" />
          </el-select>
          <el-date-picker
            v-model="auditFilters.date_range"
            type="daterange"
            value-format="YYYY-MM-DD"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            @change="handleAuditFilterChange"
          />
        </div>
        <div v-if="scanSummary.recent_actions?.length" class="audit-list">
          <div v-for="item in scanSummary.recent_actions" :key="item.id" class="audit-item">
            <div class="audit-icon" :class="item.action === 'ALERT_REASSIGN' ? 'violet' : 'green'">
              <el-icon><component :is="item.action === 'ALERT_REASSIGN' ? Connection : Clock" /></el-icon>
            </div>
            <div class="audit-main">
              <strong>{{ item.detail }}</strong>
              <span>{{ item.username || '系统' }} · {{ formatDate(item.created_at, 'YYYY-MM-DD HH:mm:ss') }}</span>
            </div>
          </div>
        </div>
        <el-empty v-else description="暂无处置记录" :image-size="88" />
      </div>

      <div class="panel dark-panel">
        <div class="panel-header">
          <div>
            <h3>预警消息中心</h3>
            <p>集中处理付款到期、交付逾期、合同到期等风险提醒</p>
          </div>
        </div>
        <el-table v-loading="loading" :data="alerts">
          <el-table-column prop="title" label="消息标题" min-width="220" />
          <el-table-column prop="contract_no" label="合同编号" width="140" />
          <el-table-column prop="owner_name" label="负责人" width="110" />
          <el-table-column prop="status_display" label="状态" width="100" />
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button link type="primary" @click="handleProcessAlert(row)">处理</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </section>

    <el-dialog v-model="processDialogVisible" title="新增审批流程" width="560px">
      <el-form :model="processForm" label-width="100px">
        <el-form-item label="流程名称"><el-input v-model="processForm.name" /></el-form-item>
        <el-form-item label="动作类型">
          <el-select v-model="processForm.action_type">
            <el-option label="新增" value="create" />
            <el-option label="修改" value="update" />
            <el-option label="删除" value="delete" />
            <el-option label="变更" value="change" />
          </el-select>
        </el-form-item>
        <el-form-item label="触发金额"><el-input-number v-model="processForm.min_amount" :min="0" :precision="2" /></el-form-item>
        <el-form-item label="审批步骤">
          <el-input
            :model-value="JSON.stringify(processForm.steps, null, 2)"
            type="textarea"
            :rows="6"
            @update:model-value="val => { try { processForm.steps = JSON.parse(val || '[]') } catch (error) {} }"
          />
        </el-form-item>
      </el-form>
      <template #footer><el-button @click="processDialogVisible = false">取消</el-button><el-button type="primary" @click="submitProcess">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="permissionDialogVisible" title="新增数据权限" width="520px">
      <el-form :model="permissionForm" label-width="100px">
        <el-form-item label="目标用户">
          <el-select v-model="permissionForm.user" filterable style="width: 100%">
            <el-option v-for="user in users" :key="user.id" :label="user.username" :value="user.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="范围类型">
          <el-select v-model="permissionForm.scope_type">
            <el-option label="本人" value="self" />
            <el-option label="部门" value="department" />
            <el-option label="区域" value="region" />
            <el-option label="客户" value="customer" />
            <el-option label="全部" value="all" />
          </el-select>
        </el-form-item>
        <el-form-item label="范围值"><el-input v-model="permissionForm.scope_value" /></el-form-item>
        <el-form-item label="可编辑"><el-switch v-model="permissionForm.can_edit" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="permissionDialogVisible = false">取消</el-button><el-button type="primary" @click="submitPermission">保存</el-button></template>
    </el-dialog>

    <el-dialog
      v-model="alertRuleDialogVisible"
      :title="isEditingAlertRule ? '编辑预警规则' : '新增预警规则'"
      width="560px"
      @closed="closeAlertRuleDialog"
    >
      <el-form :model="alertRuleForm" label-width="100px">
        <el-form-item label="规则名称"><el-input v-model="alertRuleForm.name" /></el-form-item>
        <el-form-item label="规则类型">
          <el-select v-model="alertRuleForm.rule_type" @change="syncAlertRuleStrategy">
            <el-option label="付款到期" value="payment_due" />
            <el-option label="交付到期" value="delivery_due" />
            <el-option label="合同到期" value="contract_expiry" />
            <el-option label="发票开具" value="invoice_due" />
            <el-option label="目标达成" value="target_progress" />
          </el-select>
        </el-form-item>
        <el-form-item label="提前天数"><el-input-number v-model="alertRuleForm.remind_days" :min="1" :max="90" /></el-form-item>
        <el-form-item label="负责人策略">
          <el-select v-model="alertRuleForm.owner_role" @change="clearStrategyImpactPreview">
            <el-option
              v-for="item in getRuleStrategyOptions(alertRuleForm.rule_type)"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
          <div class="form-helper">{{ getRuleStrategyMeta(alertRuleForm.rule_type, alertRuleForm.owner_role).description || '系统将按当前策略自动匹配负责人。' }}</div>
        </el-form-item>
        <el-form-item v-if="isEditingAlertRule" label="策略影响">
          <div class="impact-toolbar">
            <el-tag :type="hasStrategyChanged ? 'warning' : 'info'" effect="light">
              {{ hasStrategyChanged ? '策略已变更，建议先预览影响' : '当前策略与已保存配置一致' }}
            </el-tag>
            <el-button
              type="primary"
              plain
              size="small"
              :loading="impactPreviewLoading"
              @click="loadStrategyImpactPreview"
            >
              预览改派影响
            </el-button>
          </div>
          <div v-if="strategyImpactPreview" class="impact-preview">
            <div class="impact-summary">
              <div class="impact-card">
                <span>命中条数</span>
                <strong>{{ strategyImpactPreview.total_hits || 0 }}</strong>
              </div>
              <div class="impact-card accent">
                <span>负责人变更</span>
                <strong>{{ strategyImpactPreview.changed_count || 0 }}</strong>
              </div>
              <div class="impact-card">
                <span>保持不变</span>
                <strong>{{ strategyImpactPreview.unchanged_count || 0 }}</strong>
              </div>
            </div>
            <div class="impact-strategy-line">
              <span>当前策略：{{ strategyImpactPreview.current_strategy?.label || '-' }}</span>
              <span>拟改策略：{{ strategyImpactPreview.proposed_strategy?.label || '-' }}</span>
            </div>
            <div v-if="strategyImpactPreview.compare_items?.length" class="impact-list">
              <div
                v-for="(item, index) in strategyImpactPreview.compare_items"
                :key="`${item.title}-${index}`"
                class="impact-item"
                :class="{ changed: item.changed }"
              >
                <div class="impact-main">
                  <strong>{{ item.title }}</strong>
                  <small>{{ item.contract_no || '通用事项' }} · {{ item.due_date || '-' }}</small>
                  <span>{{ item.trigger_summary || '-' }}</span>
                </div>
                <div class="impact-owners">
                  <span>{{ item.current_owner?.username || '待分派' }}</span>
                  <ArrowRight class="impact-arrow" />
                  <span>{{ item.proposed_owner?.username || '待分派' }}</span>
                </div>
              </div>
            </div>
            <el-empty v-else description="当前策略下暂无可比对的命中项" :image-size="72" />
          </div>
        </el-form-item>
        <el-form-item label="预警等级">
          <el-select v-model="alertRuleForm.level">
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="启用状态"><el-switch v-model="alertRuleForm.is_active" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="closeAlertRuleDialog">取消</el-button><el-button type="primary" @click="submitAlertRule">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped lang="scss">
.governance-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero-card,
.dark-panel {
  background: linear-gradient(180deg, rgba(12, 18, 34, 0.98), rgba(24, 32, 56, 0.96));
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 24px;
  color: #f8fafc;
  box-shadow: 0 20px 45px rgba(15, 23, 42, 0.22);
}

.panel {
  border-radius: 24px;
  padding: 20px;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.08);
}

.hero-card {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(360px, 0.9fr);
  gap: 20px;
  padding: 28px;

  h1 {
    margin: 10px 0;
    font-size: 30px;
    line-height: 1.1;
  }

  p {
    margin: 0;
    color: rgba(226, 232, 240, 0.74);
    line-height: 1.7;
  }
}

.eyebrow {
  color: #7dd3fc;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.14em;
}

.hero-side {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.hero-status-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 18px 20px;
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.06));
  border: 1px solid rgba(255, 255, 255, 0.08);

  span,
  small {
    color: rgba(226, 232, 240, 0.72);
  }

  strong {
    font-size: 18px;
    color: #fff;
  }
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.filter-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.metric-card {
  padding: 18px;
  border-radius: 22px;
  background: #fff;
  border: 1px solid rgba(15, 23, 42, 0.06);

  &.blue {
    background: linear-gradient(180deg, #f4f8ff 0%, #ecf3ff 100%);
  }

  &.green {
    background: linear-gradient(180deg, #f3fff8 0%, #e9fbf1 100%);
  }

  &.violet {
    background: linear-gradient(180deg, #f7f4ff 0%, #f0ebff 100%);
  }

  &.amber {
    background: linear-gradient(180deg, #fffaf1 0%, #fff3de 100%);
  }
}

.metric-icon,
.audit-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.06);
  color: #0f172a;
}

.metric-title {
  margin-top: 16px;
  color: #64748b;
  font-size: 13px;
}

.metric-value {
  margin-top: 8px;
  font-size: 30px;
  font-weight: 700;
  color: #0f172a;
}

.preview-panel {
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.preview-summary-row {
  display: grid;
  grid-template-columns: 160px 160px minmax(0, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.filter-bar,
.audit-filter-bar {
  display: grid;
  gap: 10px;
  margin-bottom: 16px;
}

.filter-bar {
  grid-template-columns: minmax(220px, 280px) auto;
  align-items: center;
}

.audit-filter-bar {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.preview-summary-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px 16px;
  border-radius: 18px;
  background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);

  span {
    color: rgba(226, 232, 240, 0.72);
    font-size: 12px;
  }

  strong {
    color: #fff;
    font-size: 26px;
  }
}

.preview-chip-list {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  padding: 8px 4px;
}

.preview-chip {
  border-radius: 999px;
}

.preview-owner,
.preview-status {
  display: flex;
  flex-direction: column;
  gap: 6px;

  span {
    color: #0f172a;
    font-weight: 600;
  }

  small {
    color: #64748b;
    font-size: 12px;
  }
}

.preview-table :deep(.el-table__header-wrapper th) {
  background: rgba(248, 250, 252, 0.92);
  color: #64748b;
}

.strategy-panel {
  background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.strategy-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

.strategy-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 18px;
  border-radius: 20px;
  background: linear-gradient(180deg, #f8fbff 0%, #f1f5f9 100%);
  border: 1px solid rgba(59, 130, 246, 0.08);

  strong {
    color: #0f172a;
    font-size: 15px;
    line-height: 1.5;
  }

  p {
    margin: 0;
    color: #475569;
    font-size: 13px;
    line-height: 1.7;
  }
}

.strategy-meta {
  color: #64748b;
  font-size: 12px;
  line-height: 1.6;
}

.strategy-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #2563eb;
  font-size: 12px;
  font-weight: 600;
}

.scan-overview-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr);
  gap: 16px;
}

.bottom-grid {
  align-items: start;
}

.focus-panel,
.timeline-panel {
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;

  h3 {
    margin: 0 0 4px;
  }

  p {
    margin: 0;
    color: rgba(226, 232, 240, 0.65);
    font-size: 13px;
  }

  &.light p {
    color: #64748b;
  }

  &.compact {
    margin-bottom: 14px;
  }
}

.type-stat-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}

.type-stat-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px;
  border-radius: 18px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);

  span {
    color: #64748b;
    font-size: 12px;
  }

  strong {
    color: #0f172a;
    font-size: 22px;
  }
}

.latest-scan-card {
  margin-top: 16px;
  padding: 18px 20px;
  border-radius: 22px;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  color: #f8fafc;

  small {
    color: rgba(226, 232, 240, 0.72);
  }
}

.latest-scan-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;

  strong {
    display: block;
    margin-top: 8px;
    font-size: 18px;
    line-height: 1.5;
  }
}

.card-label {
  color: rgba(226, 232, 240, 0.7);
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.headline-icon {
  font-size: 22px;
  color: #7dd3fc;
}

.timeline-list,
.audit-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.timeline-item,
.audit-item {
  display: flex;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(148, 163, 184, 0.08);

  strong {
    color: inherit;
    line-height: 1.5;
  }

  span {
    color: inherit;
    opacity: 0.72;
    font-size: 12px;
  }
}

.timeline-item {
  flex-direction: column;
  background: linear-gradient(180deg, #f8fafc 0%, #eff6ff 100%);
  color: #0f172a;
}

.audit-item {
  align-items: flex-start;
}

.audit-icon.violet {
  background: rgba(124, 58, 237, 0.12);
  color: #7c3aed;
}

.audit-icon.green {
  background: rgba(22, 163, 74, 0.12);
  color: #15803d;
}

.audit-main {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: #f8fafc;
}

:deep(.el-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(148, 163, 184, 0.08);
  --el-table-border-color: rgba(148, 163, 184, 0.12);
  --el-table-text-color: #e2e8f0;
  --el-table-header-text-color: #cbd5e1;
}

:deep(.el-button) {
  border-radius: 14px;
}

:deep(.el-select__wrapper),
:deep(.el-input__wrapper) {
  border-radius: 14px;
  min-height: 40px;
}

.form-helper {
  margin-top: 8px;
  color: #64748b;
  font-size: 12px;
  line-height: 1.6;
}

.impact-toolbar,
.impact-summary,
.impact-list,
.impact-main {
  display: flex;
}

.impact-toolbar,
.impact-main {
  flex-direction: column;
}

.impact-toolbar {
  width: 100%;
  gap: 10px;
}

.impact-preview {
  width: 100%;
  margin-top: 12px;
  padding: 14px;
  border-radius: 16px;
  background: linear-gradient(180deg, #f8fbff 0%, #f1f5f9 100%);
  border: 1px solid rgba(59, 130, 246, 0.08);
}

.impact-summary {
  gap: 10px;
  margin-bottom: 12px;
}

.impact-card {
  flex: 1;
  padding: 12px;
  border-radius: 14px;
  background: #fff;

  span {
    display: block;
    color: #64748b;
    font-size: 12px;
  }

  strong {
    color: #0f172a;
    font-size: 22px;
  }
}

.impact-card.accent {
  background: linear-gradient(180deg, #fff7ed 0%, #ffedd5 100%);
}

.impact-strategy-line {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  color: #475569;
  font-size: 12px;
}

.impact-list {
  flex-direction: column;
  gap: 10px;
  max-height: 280px;
  overflow: auto;
}

.impact-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(148, 163, 184, 0.16);
}

.impact-item.changed {
  border-color: rgba(245, 158, 11, 0.28);
  background: linear-gradient(180deg, #fffaf0 0%, #fff7ed 100%);
}

.impact-main {
  gap: 4px;

  strong {
    color: #0f172a;
  }

  small,
  span {
    color: #64748b;
    line-height: 1.6;
  }
}

.impact-owners {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 180px;
  color: #0f172a;
  font-weight: 600;
}

.impact-arrow {
  width: 14px;
  height: 14px;
  color: #94a3b8;
}

@media (max-width: 1280px) {
  .hero-card,
  .scan-overview-grid,
  .metric-grid,
  .type-stat-grid,
  .preview-summary-row,
  .audit-filter-bar,
  .strategy-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 960px) {
  .hero-card,
  .metric-grid,
  .scan-overview-grid,
  .type-stat-grid,
  .preview-summary-row,
  .filter-bar,
  .audit-filter-bar,
  .strategy-grid {
    grid-template-columns: 1fr;
  }

  .hero-actions,
  .panel-header,
  .filter-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
