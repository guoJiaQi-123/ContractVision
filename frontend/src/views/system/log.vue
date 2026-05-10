<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { getOperationLogs, getLogDetail, getLogSummary, getLogFilterOptions, exportLogs } from '@/api/system'
import {
  Search, Refresh, Document, View, Download, Calendar, Location,
  InfoFilled, Timer, Monitor, TrendCharts, WarningFilled,
  CircleCheckFilled, CircleCloseFilled, DataLine
} from '@element-plus/icons-vue'

const searchForm = ref({
  search: '',
  action: '',
  category: '',
  level: '',
  method: '',
  module: '',
  dateRange: []
})

const tableData = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const detailVisible = ref(false)
const detailLoading = ref(false)
const currentLog = ref({})

const summary = ref({
  total: 0,
  today_count: 0,
  error_count: 0,
  category_counts: {},
  level_counts: {},
  action_counts: {},
  module_counts: {},
  recent_errors: []
})

const filterOptions = ref({
  categories: [],
  levels: [],
  actions: [],
  modules: [],
  methods: []
})

const exportFormat = ref('xlsx')
const activeCard = ref('')

const fetchSummary = async () => {
  try {
    const params = {}
    if (searchForm.value.dateRange && searchForm.value.dateRange.length === 2) {
      params.start_date = searchForm.value.dateRange[0]
      params.end_date = searchForm.value.dateRange[1]
    }
    const res = await getLogSummary(params)
    summary.value = res.data?.data || res.data || res
  } catch {
    // silent
  }
}

const fetchFilterOptions = async () => {
  try {
    const res = await getLogFilterOptions()
    filterOptions.value = res.data?.data || res.data || res
  } catch {
    // silent
  }
}

const fetchLogs = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (searchForm.value.search) params.search = searchForm.value.search
    if (searchForm.value.action) params.action = searchForm.value.action
    if (searchForm.value.category) params.category = searchForm.value.category
    if (searchForm.value.level) params.level = searchForm.value.level
    if (searchForm.value.method) params.method = searchForm.value.method
    if (searchForm.value.module) params.module = searchForm.value.module
    if (searchForm.value.dateRange && searchForm.value.dateRange.length === 2) {
      params.start_date = searchForm.value.dateRange[0]
      params.end_date = searchForm.value.dateRange[1]
    }
    const res = await getOperationLogs(params)
    tableData.value = res.data?.results || res.results || []
    total.value = res.data?.total ?? res.total ?? 0
  } catch {
    ElMessage.error('获取操作日志失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  activeCard.value = ''
  currentPage.value = 1
  fetchLogs()
  fetchSummary()
}

const handleReset = () => {
  searchForm.value = {
    search: '',
    action: '',
    category: '',
    level: '',
    method: '',
    module: '',
    dateRange: []
  }
  activeCard.value = ''
  currentPage.value = 1
  fetchLogs()
  fetchSummary()
}

const handleCardClick = (card) => {
  if (activeCard.value === card.key) {
    activeCard.value = ''
    searchForm.value.category = ''
    searchForm.value.level = ''
    searchForm.value.dateRange = []
  } else {
    activeCard.value = card.key
    searchForm.value.category = ''
    searchForm.value.level = ''
    searchForm.value.dateRange = []
    if (card.key === 'today') {
      const today = new Date()
      const todayStr = today.toISOString().slice(0, 10)
      searchForm.value.dateRange = [todayStr, todayStr]
    } else if (card.key === 'errors') {
      searchForm.value.level = 'error'
    } else if (card.key === 'operations') {
      searchForm.value.category = 'operation'
    } else if (card.key === 'contract') {
      searchForm.value.category = 'contract'
    }
  }
  currentPage.value = 1
  fetchLogs()
}

const handlePageChange = () => fetchLogs()
const handleSizeChange = () => { currentPage.value = 1; fetchLogs() }

const handleExport = async (format) => {
  try {
    const params = { format }
    if (searchForm.value.search) params.search = searchForm.value.search
    if (searchForm.value.action) params.action = searchForm.value.action
    if (searchForm.value.category) params.category = searchForm.value.category
    if (searchForm.value.level) params.level = searchForm.value.level
    if (searchForm.value.method) params.method = searchForm.value.method
    if (searchForm.value.module) params.module = searchForm.value.module
    if (searchForm.value.dateRange && searchForm.value.dateRange.length === 2) {
      params.start_date = searchForm.value.dateRange[0]
      params.end_date = searchForm.value.dateRange[1]
    }
    const res = await exportLogs(params)
    const ext = format === 'csv' ? 'csv' : 'xlsx'
    const mime = format === 'csv'
      ? 'text/csv'
      : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    const blob = new Blob([res], { type: mime })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `操作日志_${new Date().getTime()}.${ext}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(link.href)
    ElMessage.success('导出成功')
  } catch {
    ElMessage.error('导出失败')
  }
}

const handleView = async (row) => {
  detailVisible.value = true
  detailLoading.value = true
  currentLog.value = {}
  try {
    const res = await getLogDetail(row.id)
    currentLog.value = res.data?.data || res.data || res
  } catch {
    ElMessage.error('获取日志详情失败')
    detailVisible.value = false
  } finally {
    detailLoading.value = false
  }
}

const getActionBadge = (action) => {
  const map = {
    LOGIN: { class: 'badge-info', label: '登录' },
    LOGIN_FAILED: { class: 'badge-danger', label: '登录失败' },
    LOGOUT: { class: 'badge-info', label: '登出' },
    CREATE: { class: 'badge-success', label: '新增' },
    UPDATE: { class: 'badge-warning', label: '编辑' },
    DELETE: { class: 'badge-danger', label: '删除' },
    VIEW: { class: 'badge-info', label: '查看' },
    EXPORT: { class: 'badge-info', label: '导出' },
    ALERT_SCAN: { class: 'badge-system', label: '预警扫描' },
    ALERT_PROCESS: { class: 'badge-system', label: '预警处理' },
    ALERT_REASSIGN: { class: 'badge-system', label: '预警改派' },
  }
  return map[action] || { class: 'badge-default', label: action || '未知' }
}

const getCategoryBadge = (category) => {
  const map = {
    operation: { class: 'badge-info', label: '操作' },
    error: { class: 'badge-danger', label: '错误' },
    system: { class: 'badge-system', label: '系统' },
    security: { class: 'badge-warning', label: '安全' },
    contract: { class: 'badge-contract', label: '合同' },
  }
  return map[category] || { class: 'badge-default', label: category || '-' }
}

const getLevelBadge = (level) => {
  const map = {
    debug: { class: 'badge-default', label: 'DEBUG' },
    info: { class: 'badge-info', label: 'INFO' },
    warning: { class: 'badge-warning', label: 'WARN' },
    error: { class: 'badge-danger', label: 'ERROR' },
    critical: { class: 'badge-critical', label: 'CRIT' },
  }
  return map[level] || { class: 'badge-default', label: level || '-' }
}

const formatJson = (data) => {
  if (!data) return ''
  try {
    return JSON.stringify(data, null, 2)
  } catch {
    return String(data)
  }
}

const formatDuration = (ms) => {
  if (!ms && ms !== 0) return '-'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(2)}s`
}

const getModuleLabel = (mod) => {
  const map = { contracts: '合同', users: '用户', auth: '认证', system: '系统' }
  return map[mod] || mod || '-'
}

const summaryCards = computed(() => [
  { key: 'total', label: '日志总量', value: summary.value.total, icon: Document, color: '#374151' },
  { key: 'today', label: '今日新增', value: summary.value.today_count, icon: TrendCharts, color: '#2563eb' },
  { key: 'errors', label: '异常日志', value: summary.value.error_count, icon: WarningFilled, color: '#dc2626' },
  { key: 'operations', label: '操作日志', value: summary.value.category_counts?.operation || 0, icon: CircleCheckFilled, color: '#16a34a' },
  { key: 'contract', label: '合同日志', value: summary.value.category_counts?.contract || 0, icon: DataLine, color: '#7c3aed' },
])

onMounted(() => {
  fetchFilterOptions()
  fetchSummary()
  fetchLogs()
})
</script>

<template>
  <div class="system-log-container">
    <div class="page-header">
      <div class="header-left">
        <div class="header-icon">
          <el-icon :size="20"><Document /></el-icon>
        </div>
        <div class="header-text">
          <h1>操作日志</h1>
          <p class="text-muted">监控系统全局操作行为，保障业务合规与数据安全可追溯</p>
        </div>
      </div>
      <div class="header-actions">
        <el-dropdown trigger="click" @command="handleExport">
          <el-button class="btn-square">
            <el-icon><Download /></el-icon>
            导出日志
            <el-icon class="el-icon--right"><arrow-down /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="xlsx">导出 Excel (.xlsx)</el-dropdown-item>
              <el-dropdown-item command="csv">导出 CSV (.csv)</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button class="btn-square" @click="fetchLogs(); fetchSummary()">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <div class="summary-row">
      <div
        v-for="card in summaryCards"
        :key="card.key"
        class="summary-card"
        :class="{ active: activeCard === card.key }"
        :style="activeCard === card.key ? { borderColor: card.color, background: card.color + '08' } : {}"
        @click="handleCardClick(card)"
      >
        <div class="summary-icon" :style="{ color: card.color, background: card.color + '0d' }">
          <el-icon :size="20"><component :is="card.icon" /></el-icon>
        </div>
        <div class="summary-info">
          <span class="summary-value" :style="activeCard === card.key ? { color: card.color } : {}">{{ card.value }}</span>
          <span class="summary-label">{{ card.label }}</span>
        </div>
        <div v-if="activeCard === card.key" class="card-active-indicator" :style="{ background: card.color }"></div>
      </div>
    </div>

    <div class="card filter-card">
      <el-row :gutter="16" align="middle" class="filter-row">
        <el-col :xs="24" :sm="12" :md="5">
          <el-input
            v-model="searchForm.search"
            placeholder="搜索操作人、对象、IP、路径"
            clearable
            class="flat-input"
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :xs="24" :sm="12" :md="3">
          <el-select
            v-model="searchForm.category"
            placeholder="日志分类"
            clearable
            class="flat-select"
            @change="handleSearch"
          >
            <el-option
              v-for="c in filterOptions.categories"
              :key="c.value"
              :label="c.label"
              :value="c.value"
            />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="3">
          <el-select
            v-model="searchForm.level"
            placeholder="日志级别"
            clearable
            class="flat-select"
            @change="handleSearch"
          >
            <el-option
              v-for="l in filterOptions.levels"
              :key="l.value"
              :label="l.label"
              :value="l.value"
            />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="3">
          <el-select
            v-model="searchForm.action"
            placeholder="操作类型"
            clearable
            class="flat-select"
            @change="handleSearch"
          >
            <el-option
              v-for="a in filterOptions.actions"
              :key="a"
              :label="getActionBadge(a).label"
              :value="a"
            />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="5">
          <el-date-picker
            v-model="searchForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            class="flat-date-picker"
            @change="handleSearch"
          />
        </el-col>
        <el-col :xs="24" :sm="12" :md="5">
          <div class="filter-actions">
            <el-button type="primary" class="btn-primary-flat" @click="handleSearch">
              <el-icon><Search /></el-icon>
              查询
            </el-button>
            <el-button class="btn-outline-flat" @click="handleReset">
              重置
            </el-button>
          </div>
        </el-col>
      </el-row>
    </div>

    <div class="card table-card">
      <el-table
        v-loading="loading"
        :data="tableData"
        style="width: 100%"
        class="enterprise-table"
        :empty-text="'暂无操作记录'"
        row-key="id"
      >
        <template #empty>
          <div class="empty-state">
            <el-icon class="empty-icon"><Document /></el-icon>
            <p>暂无符合条件的审计日志</p>
          </div>
        </template>
        <el-table-column prop="username" label="操作人" min-width="110">
          <template #default="{ row }">
            <div class="user-cell">
              <div class="avatar-placeholder">{{ (row.username || 'U').charAt(0).toUpperCase() }}</div>
              <span class="operator-name">{{ row.username || 'System' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="action" label="操作类型" width="110">
          <template #default="{ row }">
            <span class="flat-badge" :class="getActionBadge(row.action).class">
              {{ getActionBadge(row.action).label }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="80">
          <template #default="{ row }">
            <span class="flat-badge small" :class="getCategoryBadge(row.category).class">
              {{ getCategoryBadge(row.category).label }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="level" label="级别" width="80">
          <template #default="{ row }">
            <span class="flat-badge small" :class="getLevelBadge(row.level).class">
              {{ getLevelBadge(row.level).label }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="target" label="操作对象" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="target-text">{{ row.target || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="detail" label="操作详情" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="detail-text">{{ row.detail || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP 地址" width="130">
          <template #default="{ row }">
            <div class="ip-cell">
              <el-icon><Location /></el-icon>
              <span>{{ row.ip_address || '-' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="status_code" label="状态" width="80">
          <template #default="{ row }">
            <span v-if="row.status_code >= 200 && row.status_code < 300" class="status-dot success">成功</span>
            <span v-else-if="row.status_code >= 400" class="status-dot danger">失败</span>
            <span v-else class="status-dot info">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="duration_ms" label="耗时" width="80">
          <template #default="{ row }">
            <span :class="['duration-text', row.duration_ms > 3000 ? 'slow' : '']">
              {{ formatDuration(row.duration_ms) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="操作时间" width="170">
          <template #default="{ row }">
            <div class="time-cell">
              <el-icon><Calendar /></el-icon>
              <span>{{ row.created_at || '-' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" class="action-btn-flat" @click="handleView(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <div class="table-info">共 <span class="highlight-total">{{ total }}</span> 条记录</div>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          class="flat-pagination"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </div>

    <el-drawer
      v-model="detailVisible"
      title="操作日志详情"
      size="640px"
      destroy-on-close
      class="enterprise-drawer"
    >
      <div v-loading="detailLoading" class="drawer-content">
        <template v-if="currentLog.id">
          <div class="detail-section">
            <h3 class="section-title">基础信息</h3>
            <div class="info-grid">
              <div class="info-item">
                <span class="info-label">操作人</span>
                <span class="info-value">{{ currentLog.username || 'System' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">操作类型</span>
                <span class="flat-badge" :class="getActionBadge(currentLog.action).class">
                  {{ getActionBadge(currentLog.action).label }}
                </span>
              </div>
              <div class="info-item">
                <span class="info-label">日志分类</span>
                <span class="flat-badge" :class="getCategoryBadge(currentLog.category).class">
                  {{ getCategoryBadge(currentLog.category).label }}
                </span>
              </div>
              <div class="info-item">
                <span class="info-label">日志级别</span>
                <span class="flat-badge" :class="getLevelBadge(currentLog.level).class">
                  {{ getLevelBadge(currentLog.level).label }}
                </span>
              </div>
              <div class="info-item">
                <span class="info-label">操作对象</span>
                <span class="info-value">{{ currentLog.target || '-' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">操作时间</span>
                <span class="info-value">{{ currentLog.created_at }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">IP 地址</span>
                <span class="info-value">{{ currentLog.ip_address || '-' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">状态码</span>
                <span class="info-value">
                  <span v-if="currentLog.status_code >= 200 && currentLog.status_code < 300" class="status-text success">{{ currentLog.status_code }} (成功)</span>
                  <span v-else-if="currentLog.status_code >= 400" class="status-text danger">{{ currentLog.status_code }} (失败)</span>
                  <span v-else>{{ currentLog.status_code || '-' }}</span>
                </span>
              </div>
              <div class="info-item">
                <span class="info-label">请求耗时</span>
                <span class="info-value" :class="{ 'text-danger': currentLog.duration_ms > 3000 }">
                  {{ formatDuration(currentLog.duration_ms) }}
                </span>
              </div>
              <div class="info-item">
                <span class="info-label">功能模块</span>
                <span class="info-value">{{ getModuleLabel(currentLog.module) }}</span>
              </div>
            </div>
          </div>

          <div class="detail-section">
            <h3 class="section-title">网络信息</h3>
            <div class="info-grid single-col">
              <div class="info-item">
                <span class="info-label">请求路径</span>
                <span class="info-value code-font">{{ currentLog.path || '-' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">请求方法</span>
                <span class="info-value code-font tag-method">{{ currentLog.method || '-' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">User-Agent</span>
                <span class="info-value code-font ua-text">{{ currentLog.user_agent || '-' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">操作描述</span>
                <span class="info-value">{{ currentLog.detail || '-' }}</span>
              </div>
            </div>
          </div>

          <div class="detail-section" v-if="currentLog.before_data && Object.keys(currentLog.before_data).length > 0">
            <h3 class="section-title">操作前数据</h3>
            <div class="json-viewer">
              <pre>{{ formatJson(currentLog.before_data) }}</pre>
            </div>
          </div>

          <div class="detail-section" v-if="currentLog.after_data && Object.keys(currentLog.after_data).length > 0">
            <h3 class="section-title">操作后数据</h3>
            <div class="json-viewer">
              <pre>{{ formatJson(currentLog.after_data) }}</pre>
            </div>
          </div>
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<style lang="scss" scoped>
.system-log-container {
  padding: 24px;
  background-color: var(--bg-color);
  min-height: calc(100vh - 60px);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .header-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 48px;
    height: 48px;
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    color: var(--text-primary);
    box-shadow: var(--shadow-xs);
  }

  .header-text {
    h1 {
      font-size: var(--fs-lg);
      font-weight: 600;
      color: var(--text-primary);
      margin: 0 0 4px 0;
      letter-spacing: -0.01em;
    }
    p {
      font-size: var(--fs-sm);
      color: var(--text-secondary);
      margin: 0;
    }
  }

  .header-actions {
    display: flex;
    gap: 12px;
  }
}

.summary-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.summary-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 20px;
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
  position: relative;
  overflow: hidden;

  &:hover {
    border-color: var(--gray-300);
    box-shadow: var(--shadow-md);
    transform: translateY(-1px);
  }

  &:active {
    transform: translateY(0);
    box-shadow: var(--shadow-xs);
  }

  &.active {
    box-shadow: var(--shadow-md);
  }

  .summary-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    border-radius: var(--radius-md);
    flex-shrink: 0;
  }

  .summary-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .summary-value {
    font-size: var(--fs-xl);
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.2;
    transition: color var(--transition-fast);
  }

  .summary-label {
    font-size: var(--fs-sm);
    color: var(--text-muted);
    font-weight: 500;
  }

  .card-active-indicator {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 3px;
    border-radius: 0 0 var(--radius-md) var(--radius-md);
  }
}

.btn-square {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 36px;
  padding: 0 16px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: var(--fs-base);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);

  &:hover {
    border-color: var(--gray-400);
    background: var(--gray-50);
  }

  &:active {
    background: var(--gray-100);
  }
}

.btn-primary-flat {
  background: var(--text-primary) !important;
  border: 1px solid var(--text-primary) !important;
  color: var(--text-inverse) !important;
  border-radius: var(--radius-sm);
  font-weight: 500;
  height: 36px;
  padding: 0 20px;
  transition: all var(--transition-fast);

  &:hover {
    background: var(--gray-800) !important;
    border-color: var(--gray-800) !important;
  }
}

.btn-outline-flat {
  background: var(--card-bg) !important;
  border: 1px solid var(--border-color) !important;
  color: var(--text-primary) !important;
  border-radius: var(--radius-sm);
  font-weight: 500;
  height: 36px;
  padding: 0 20px;
  transition: all var(--transition-fast);

  &:hover {
    border-color: var(--gray-400) !important;
    background: var(--gray-50) !important;
  }
}

.action-btn-flat {
  font-weight: 500;
  color: var(--primary) !important;

  &:hover {
    color: var(--primary-dark) !important;
  }
}

.card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  margin-bottom: 20px;
}

.filter-card {
  padding: 16px 20px;

  .filter-row {
    margin-bottom: 0;
  }

  .filter-actions {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
  }
}

:deep(.flat-input),
:deep(.flat-select),
:deep(.flat-date-picker) {
  width: 100%;

  .el-input__wrapper {
    box-shadow: 0 0 0 1px var(--border-color) inset;
    border-radius: var(--radius-sm);
    background: var(--card-bg);
    padding: 0 12px;

    &:hover {
      box-shadow: 0 0 0 1px var(--gray-400) inset;
    }

    &.is-focus {
      box-shadow: 0 0 0 2px var(--text-primary) inset !important;
    }
  }

  .el-input__inner {
    color: var(--text-primary);
    font-size: var(--fs-base);
    &::placeholder {
      color: var(--gray-400);
    }
  }
}

.table-card {
  padding: 0;
  overflow: hidden;
}

:deep(.enterprise-table) {
  --el-table-border-color: var(--border-color);
  --el-table-header-bg-color: var(--gray-50);
  --el-table-header-text-color: var(--text-secondary);
  --el-table-text-color: var(--text-primary);
  --el-table-row-hover-bg-color: var(--gray-100);

  .el-table__header th {
    font-weight: 600;
    font-size: var(--fs-sm);
    padding: 12px 16px;
    border-bottom: 1px solid var(--border-color);
    text-transform: uppercase;
    letter-spacing: 0.02em;
  }

  .el-table__body td {
    padding: 14px 16px;
    font-size: var(--fs-base);
    border-bottom: 1px solid var(--border-light);
  }

  .el-table__inner-wrapper::before {
    display: none;
  }
}

.empty-state {
  padding: 60px 0;
  text-align: center;
  color: var(--gray-400);

  .empty-icon {
    font-size: 48px;
    margin-bottom: 16px;
    opacity: 0.5;
  }

  p {
    margin: 0;
    font-size: var(--fs-base);
  }
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 10px;

  .avatar-placeholder {
    width: 28px;
    height: 28px;
    border-radius: var(--radius-xs);
    background: var(--gray-100);
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: var(--fs-xs);
    border: 1px solid var(--border-light);
  }

  .operator-name {
    font-weight: 500;
  }
}

.ip-cell, .time-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: var(--fs-sm);

  .el-icon {
    color: var(--gray-400);
  }
}

.target-text {
  font-weight: 500;
  color: var(--text-primary);
}

.detail-text {
  color: var(--text-secondary);
}

.duration-text {
  font-family: var(--font-mono);
  font-size: var(--fs-sm);
  color: var(--text-secondary);

  &.slow {
    color: var(--warning);
    font-weight: 600;
  }
}

.flat-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: var(--radius-xs);
  font-size: var(--fs-xs);
  font-weight: 600;
  letter-spacing: 0.01em;

  &.small {
    padding: 2px 8px;
    font-size: var(--fs-xs);
  }

  &.badge-info {
    background: var(--primary-bg);
    color: var(--primary-dark);
    border: 1px solid var(--border-light);
  }

  &.badge-success {
    background: var(--success-bg);
    color: var(--success);
    border: 1px solid var(--border-light);
  }

  &.badge-warning {
    background: var(--warning-bg);
    color: var(--warning);
    border: 1px solid var(--border-light);
  }

  &.badge-danger {
    background: var(--danger-bg);
    color: var(--danger);
    border: 1px solid var(--border-light);
  }

  &.badge-system {
    background: var(--primary-bg);
    color: var(--primary-dark);
    border: 1px solid var(--border-light);
  }

  &.badge-contract {
    background: var(--primary-bg);
    color: var(--primary-dark);
    border: 1px solid var(--border-light);
  }

  &.badge-critical {
    background: var(--danger);
    color: var(--text-inverse);
    border: 1px solid var(--danger);
  }

  &.badge-default {
    background: var(--gray-100);
    color: var(--text-secondary);
    border: 1px solid var(--border-light);
  }
}

.status-dot {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
  font-size: var(--fs-sm);

  &::before {
    content: '';
    display: block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
  }

  &.success {
    color: var(--success);
    &::before { background: var(--success); }
  }

  &.danger {
    color: var(--danger);
    &::before { background: var(--danger); }
  }

  &.info {
    color: var(--gray-400);
    &::before { background: var(--gray-300); }
  }
}

.table-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--card-bg);
  border-top: 1px solid var(--border-color);

  .table-info {
    font-size: var(--fs-base);
    color: var(--text-secondary);

    .highlight-total {
      font-weight: 600;
      color: var(--text-primary);
    }
  }
}

:deep(.flat-pagination) {
  .btn-prev, .btn-next, .el-pager li {
    background: var(--card-bg) !important;
    border: 1px solid var(--border-light);
    border-radius: var(--radius-xs);
    color: var(--text-secondary);
    font-weight: 500;
    margin: 0 4px;
    min-width: 32px;
    height: 32px;

    &:hover {
      border-color: var(--gray-400);
      color: var(--text-primary);
    }

    &.is-active {
      background: var(--text-primary) !important;
      border-color: var(--text-primary);
      color: var(--text-inverse);
    }
  }
}

:deep(.enterprise-drawer) {
  .el-drawer__header {
    margin-bottom: 0;
    padding: 20px 24px;
    border-bottom: 1px solid var(--border-color);
    color: var(--text-primary);
    font-weight: 600;
    font-size: var(--fs-md);
  }

  .el-drawer__body {
    padding: 0;
    background: var(--bg-color);
  }
}

.drawer-content {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.detail-section {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  overflow: hidden;

  .section-title {
    margin: 0;
    padding: 16px 20px;
    font-size: var(--fs-base);
    font-weight: 600;
    color: var(--text-primary);
    border-bottom: 1px solid var(--border-color);
    background: var(--gray-50);
  }
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  padding: 20px;

  &.single-col {
    grid-template-columns: 1fr;
  }

  .info-item {
    display: flex;
    flex-direction: column;
    gap: 6px;

    .info-label {
      font-size: var(--fs-sm);
      color: var(--text-muted);
      font-weight: 500;
    }

    .info-value {
      font-size: var(--fs-base);
      color: var(--text-primary);
      word-break: break-all;
    }
  }
}

.code-font {
  font-family: var(--font-mono);
  font-size: var(--fs-sm) !important;
}

.tag-method {
  display: inline-block;
  padding: 2px 8px;
  background: var(--gray-100);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-xs);
  color: var(--text-primary);
  font-weight: 600;
  width: fit-content;
}

.ua-text {
  font-size: var(--fs-xs) !important;
  line-height: 1.4;
  color: var(--text-secondary) !important;
}

.status-text {
  font-weight: 600;
  &.success { color: var(--success); }
  &.danger { color: var(--danger); }
}

.text-danger {
  color: var(--danger) !important;
  font-weight: 600;
}

.json-viewer {
  padding: 20px;
  background: var(--gray-900);
  margin: 0;

  pre {
    margin: 0;
    font-family: var(--font-mono);
    font-size: var(--fs-sm);
    line-height: 1.5;
    color: var(--gray-200);
    white-space: pre-wrap;
    word-break: break-all;
  }
}

@media (max-width: 768px) {
  .summary-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 769px) and (max-width: 1200px) {
  .summary-row {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
