<script setup>
import { ref, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getContractList, deleteContract, batchDeleteContracts,
  batchImportContracts, exportContracts, exportContractsPdf,
  downloadImportTemplate
} from '@/api/contract'
import {
  Search, Download, Plus, Edit, Delete, View, Refresh,
  Upload, DocumentChecked
} from '@element-plus/icons-vue'

const router = useRouter()
const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const selectedIds = ref([])

const queryParams = reactive({
  keyword: '',
  status: '',
  page: 1,
  page_size: 10,
  start_date: '',
  end_date: ''
})

const dateRange = ref(null)

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

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: queryParams.page,
      page_size: queryParams.page_size
    }
    if (queryParams.keyword) params.keyword = queryParams.keyword
    if (queryParams.status) params.status = queryParams.status
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    const res = await getContractList(params)
    tableData.value = res.results || res.data?.results || []
    total.value = res.count || res.data?.count || 0
  } catch {
    tableData.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  queryParams.page = 1
  fetchData()
}

const handleReset = () => {
  queryParams.keyword = ''
  queryParams.status = ''
  queryParams.page = 1
  dateRange.value = null
  fetchData()
}

const handlePageChange = (page) => {
  queryParams.page = page
  fetchData()
}

const handleSizeChange = (size) => {
  queryParams.page_size = size
  queryParams.page = 1
  fetchData()
}

const handleView = (row) => {
  router.push(`/contract/detail/${row.id}`)
}

const handleEdit = (row) => {
  router.push(`/contract/edit/${row.id}`)
}

const handleCreate = () => {
  router.push('/contract/create')
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除合同「${row.title}」吗？`, '删除确认', { type: 'warning' })
    await deleteContract(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch {}
}

const handleSelectionChange = (rows) => {
  selectedIds.value = rows.map(r => r.id)
}

const handleBatchDelete = async () => {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请先选择要删除的合同')
    return
  }
  try {
    await ElMessageBox.confirm(`确定要批量删除 ${selectedIds.value.length} 条合同吗？`, '批量删除确认', { type: 'warning' })
    await batchDeleteContracts(selectedIds.value)
    ElMessage.success('批量删除成功')
    selectedIds.value = []
    fetchData()
  } catch {}
}

const importDialogVisible = ref(false)
const importLoading = ref(false)
const importResult = ref(null)
const uploadRef = ref(null)

const openImportDialog = () => {
  importResult.value = null
  importDialogVisible.value = true
}

const handleImportUpload = async (params) => {
  importLoading.value = true
  importResult.value = null
  const formData = new FormData()
  formData.append('file', params.file)
  try {
    const res = await batchImportContracts(formData)
    importResult.value = res.data
    ElMessage.success(res.message || '导入完成')
    fetchData()
  } catch (error) {
    const msg = error.response?.data?.message || '导入失败'
    ElMessage.error(msg)
  } finally {
    importLoading.value = false
  }
}

const handleDownloadTemplate = async () => {
  try {
    const res = await downloadImportTemplate()
    const blob = res instanceof Blob
      ? res
      : new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = 'contract_import_template.xlsx'
    link.click()
    URL.revokeObjectURL(link.href)
  } catch {
    ElMessage.error('下载模板失败')
  }
}

const handleExport = async (format) => {
  try {
    const params = {}
    if (queryParams.keyword) params.keyword = queryParams.keyword
    if (queryParams.status) params.status = queryParams.status
    
    let res
    let filename
    if (format === 'pdf') {
      res = await exportContractsPdf(params)
      filename = 'contracts.pdf'
    } else {
      res = await exportContracts(params)
      filename = 'contracts.xlsx'
    }
    
    const blob = res instanceof Blob ? res : new Blob([res])
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = filename
    link.click()
    URL.revokeObjectURL(link.href)
    ElMessage.success('导出成功')
  } catch {
    ElMessage.error('导出失败')
  }
}

const formatAmount = (val) => {
  if (!val && val !== 0) return '¥0.00'
  return `¥${parseFloat(val).toLocaleString('zh-CN', { minimumFractionDigits: 2 })}`
}

onMounted(fetchData)
</script>

<template>
  <div class="contract-list-container">
    <div class="page-header">
      <div class="header-info">
        <h1>合同管理</h1>
        <p class="subtitle">管理和跟踪所有销售合同</p>
      </div>
      <div class="header-actions">
        <el-button @click="openImportDialog">
          <el-icon><Upload /></el-icon>
          批量导入
        </el-button>
        <el-dropdown @command="handleExport">
          <el-button>
            <el-icon><Download /></el-icon>
            导出
            <el-icon class="el-icon--right"><arrow-down /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="excel">导出 Excel</el-dropdown-item>
              <el-dropdown-item command="pdf">导出 PDF</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新增合同
        </el-button>
      </div>
    </div>

    <div class="filter-card">
      <el-row :gutter="16" align="middle">
        <el-col :xs="24" :sm="12" :md="7">
          <div class="search-input">
            <el-icon class="search-icon"><Search /></el-icon>
            <el-input
              v-model="queryParams.keyword"
              placeholder="搜索合同编号/客户名称"
              clearable
              @keyup.enter="handleSearch"
              @clear="handleSearch"
            />
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="5">
          <el-select v-model="queryParams.status" placeholder="全部状态" clearable style="width: 100%" @change="handleSearch">
            <el-option v-for="opt in statusOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="7">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
            @change="handleSearch"
          />
        </el-col>
        <el-col :xs="24" :sm="12" :md="5">
          <div class="filter-actions">
            <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
            <el-button :icon="Refresh" @click="handleReset">重置</el-button>
          </div>
        </el-col>
      </el-row>
    </div>

    <div class="table-card">
      <div class="table-toolbar" v-if="selectedIds.length > 0">
        <span class="selected-info">已选择 {{ selectedIds.length }} 项</span>
        <el-button type="danger" size="small" :icon="Delete" @click="handleBatchDelete">批量删除</el-button>
      </div>

      <el-table v-loading="loading" :data="tableData" style="width: 100%" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="contract_no" label="合同编号" min-width="140">
          <template #default="{ row }">
            <a href="javascript:void(0)" class="contract-link" @click="handleView(row)">{{ row.contract_no }}</a>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="合同标题" min-width="160" show-overflow-tooltip />
        <el-table-column prop="client_name" label="客户名称" min-width="140" show-overflow-tooltip />
        <el-table-column prop="product_type" label="产品类型" width="120" />
        <el-table-column prop="amount" label="合同金额" width="140" align="right">
          <template #default="{ row }">
            <span class="amount">{{ formatAmount(row.amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="sign_date" label="签订日期" width="120" />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusTag(row.status).type" size="small">
              {{ getStatusTag(row.status).label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="salesperson" label="销售人员" width="100" />
        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleView(row)">
              <el-icon><View /></el-icon> 查看
            </el-button>
            <el-button link type="primary" size="small" @click="handleEdit(row)">
              <el-icon><Edit /></el-icon> 编辑
            </el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row)">
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无合同数据" />
        </template>
      </el-table>

      <div class="table-footer">
        <div class="table-info">共 {{ total }} 条记录</div>
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.page_size"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          background
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </div>

    <el-dialog v-model="importDialogVisible" title="批量导入合同" width="560px">
      <div class="import-dialog-content">
        <div class="import-tips">
          <p>请先下载导入模板，按照模板格式填写数据后上传文件。</p>
          <el-button type="primary" link @click="handleDownloadTemplate">
            <el-icon><DocumentChecked /></el-icon> 下载导入模板
          </el-button>
        </div>

        <el-upload
          ref="uploadRef"
          drag
          :auto-upload="true"
          :show-file-list="false"
          :http-request="handleImportUpload"
          accept=".xlsx,.xls,.csv"
        >
          <el-icon class="el-icon--upload" :size="40"><Upload /></el-icon>
          <div class="el-upload__text">将文件拖拽至此处，或 <em>点击上传</em></div>
          <template #tip>
            <div class="el-upload__tip">支持 .xlsx / .xls / .csv 格式</div>
          </template>
        </el-upload>

        <div v-if="importLoading" class="import-progress">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>正在导入中...</span>
        </div>

        <div v-if="importResult" class="import-result">
          <el-alert
            :title="`导入完成：成功 ${importResult.success_count} 条，失败 ${importResult.error_count} 条`"
            :type="importResult.error_count > 0 ? 'warning' : 'success'"
            :closable="false"
          />
          <div v-if="importResult.errors && importResult.errors.length > 0" class="error-list">
            <p class="error-title">失败详情：</p>
            <div v-for="err in importResult.errors" :key="err.row" class="error-item">
              第 {{ err.row }} 行：{{ err.error }}
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="importDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.contract-list-container {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;

  .header-info {
    h1 { font-size: 24px; font-weight: 700; color: var(--text-primary); margin: 0; }
    .subtitle { margin: 6px 0 0; font-size: 14px; color: var(--text-muted); }
  }

  .header-actions { display: flex; gap: 12px; }
}

.filter-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;

  .filter-actions { display: flex; gap: 8px; }
}

.search-input {
  position: relative;
  .search-icon {
    position: absolute; left: 12px; top: 50%; transform: translateY(-50%);
    color: var(--text-muted); z-index: 1;
  }
  :deep(.el-input .el-input__wrapper) { padding-left: 36px; }
}

.table-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;

  .table-toolbar {
    display: flex; align-items: center; gap: 12px;
    padding: 12px 20px; background: #e6f7ff; border-bottom: 1px solid #91d5ff;
    .selected-info { font-size: 14px; color: #1890ff; }
  }

  .contract-link {
    color: var(--primary-color); text-decoration: none; font-weight: 500;
    &:hover { color: var(--primary-light, #4080FF); }
  }

  .amount { font-weight: 500; color: var(--text-primary); }
}

.table-footer {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px; border-top: 1px solid var(--border-color);
  .table-info { font-size: 14px; color: var(--text-muted); }
}

.import-dialog-content {
  .import-tips {
    margin-bottom: 16px; padding: 12px 16px;
    background: #f6f7fa; border-radius: 8px;
    display: flex; justify-content: space-between; align-items: center;
    p { margin: 0; font-size: 14px; color: var(--text-secondary); }
  }
  .import-progress {
    display: flex; align-items: center; gap: 8px; margin-top: 16px;
    color: var(--primary-color); font-size: 14px;
  }
  .import-result {
    margin-top: 16px;
    .error-list {
      margin-top: 12px; max-height: 200px; overflow-y: auto;
      .error-title { font-size: 13px; font-weight: 600; color: var(--text-secondary); margin-bottom: 8px; }
      .error-item { font-size: 13px; color: #F53F3F; padding: 4px 0; }
    }
  }
}
</style>
