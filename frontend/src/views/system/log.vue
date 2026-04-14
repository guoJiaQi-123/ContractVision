<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getOperationLogs } from '@/api/system'
import { Search, Refresh, Document, View } from '@element-plus/icons-vue'

const searchForm = ref({
  operator: '',
  action: '',
  dateRange: []
})

const tableData = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const fetchLogs = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (searchForm.value.operator) {
      params.operator = searchForm.value.operator
    }
    if (searchForm.value.action) {
      params.action = searchForm.value.action
    }
    if (searchForm.value.dateRange && searchForm.value.dateRange.length === 2) {
      params.start_date = searchForm.value.dateRange[0]
      params.end_date = searchForm.value.dateRange[1]
    }
    const res = await getOperationLogs(params)
    tableData.value = res.results || []
    total.value = res.count || 0
  } catch {
    ElMessage.error('获取操作日志失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchLogs()
}

const handleReset = () => {
  searchForm.value = {
    operator: '',
    action: '',
    dateRange: []
  }
  currentPage.value = 1
  fetchLogs()
}

const handlePageChange = () => {
  fetchLogs()
}

const handleSizeChange = () => {
  currentPage.value = 1
  fetchLogs()
}

const getActionBadge = (action) => {
  const actionMap = {
    login: { class: 'badge-info', label: '登录' },
    create: { class: 'badge-success', label: '新增' },
    update: { class: 'badge-warning', label: '编辑' },
    delete: { class: 'badge-danger', label: '删除' },
    export: { class: 'badge-info', label: '导出' }
  }
  return actionMap[action] || { class: 'badge-info', label: action }
}

onMounted(() => {
  fetchLogs()
})
</script>

<template>
  <div class="system-log-container">
    <div class="page-header">
      <div class="header-left">
        <div class="header-icon">
          <el-icon :size="24"><Document /></el-icon>
        </div>
        <div>
          <h1>操作日志</h1>
          <p class="text-muted">查看系统操作记录与审计追踪</p>
        </div>
      </div>
      <div class="header-actions">
        <el-button class="btn-outline" @click="fetchLogs">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <div class="card filter-card">
      <el-row :gutter="16" align="middle">
        <el-col :xs="24" :sm="12" :md="7">
          <div class="search-input">
            <el-icon class="search-icon"><Search /></el-icon>
            <el-input
              v-model="searchForm.operator"
              placeholder="搜索操作人"
              clearable
              @keyup.enter="handleSearch"
              @clear="handleSearch"
            />
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="5">
          <el-select
            v-model="searchForm.action"
            placeholder="全部类型"
            clearable
            style="width: 100%"
            @change="handleSearch"
          >
            <el-option label="登录" value="login" />
            <el-option label="新增" value="create" />
            <el-option label="编辑" value="update" />
            <el-option label="删除" value="delete" />
            <el-option label="导出" value="export" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="7">
          <el-date-picker
            v-model="searchForm.dateRange"
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
            <el-button type="primary" class="btn-primary" @click="handleSearch">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
            <el-button class="btn-outline" @click="handleReset">
              <el-icon><Refresh /></el-icon>
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
        :empty-text="' '"
      >
        <template #empty>
          <el-empty description="暂无操作日志" :image-size="120" />
        </template>
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="operator" label="操作人" min-width="120">
          <template #default="{ row }">
            <span class="operator-cell">{{ row.operator }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="action" label="操作类型" width="100" align="center">
          <template #default="{ row }">
            <span class="badge" :class="getActionBadge(row.action).class">
              {{ getActionBadge(row.action).label }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="module" label="操作模块" min-width="120" />
        <el-table-column prop="description" label="操作描述" min-width="240" show-overflow-tooltip />
        <el-table-column prop="ip" label="IP 地址" width="140">
          <template #default="{ row }">
            <span class="text-secondary">{{ row.ip || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="操作时间" width="170" align="center">
          <template #default="{ row }">
            <span class="text-secondary">{{ row.created_at || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" align="center" fixed="right">
          <template #default>
            <a href="javascript:void(0)" class="action-btn view-btn">
              <el-icon><View /></el-icon>
              详情
            </a>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <div class="table-info">共 {{ total }} 条记录</div>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          background
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.system-log-container {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;

  .header-left {
    display: flex;
    align-items: center;
    gap: 14px;
  }

  .header-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    border-radius: 12px;
    background: rgba(22, 93, 255, 0.1);
    color: var(--primary-color);
    flex-shrink: 0;
  }

  h1 {
    font-size: 22px;
    font-weight: 600;
    color: var(--text-primary);
    line-height: 1.3;
  }

  p {
    font-size: 14px;
    margin-top: 2px;
  }

  .header-actions {
    display: flex;
    gap: 12px;
    align-items: center;
  }
}

.filter-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  transition: box-shadow 0.3s ease;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
  }

  :deep(.el-row) {
    align-items: center;
  }

  :deep(.el-input) {
    .el-input__wrapper {
      border-radius: 8px;
      border: 1px solid var(--border-color);
      box-shadow: none;
      padding-left: 36px;
      transition: all 0.2s;

      &:hover {
        border-color: var(--primary-color);
      }

      &:focus-within {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 2px rgba(22, 93, 255, 0.1);
      }
    }
  }

  :deep(.el-select) {
    width: 100%;

    .el-input__wrapper {
      border-radius: 8px;
      border: 1px solid var(--border-color);
      box-shadow: none;
      transition: all 0.2s;

      &:hover {
        border-color: var(--primary-color);
      }

      &:focus-within {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 2px rgba(22, 93, 255, 0.1);
      }
    }
  }

  :deep(.el-date-editor) {
    .el-input__wrapper {
      border-radius: 8px;
      border: 1px solid var(--border-color);
      box-shadow: none;
      transition: border-color 0.2s;

      &:hover,
      &:focus-within {
        border-color: var(--primary-color);
      }
    }
  }

  .filter-actions {
    display: flex;
    gap: 8px;
  }
}

.search-input {
  position: relative;

  .search-icon {
    position: absolute;
    left: 12px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-muted);
    z-index: 1;
  }
}

.table-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;

  :deep(.el-table) {
    --el-table-border-color: var(--border-color);
    --el-table-header-bg-color: var(--bg-color);

    .el-table__header-wrapper {
      th {
        background: var(--bg-color);
        color: var(--text-secondary);
        font-weight: 500;
        font-size: 14px;
        padding: 14px 12px;
        border-bottom: 1px solid var(--border-color);
      }
    }

    .el-table__body-wrapper {
      td {
        padding: 14px 12px;
        border-bottom: 1px solid var(--border-color);
        font-size: 14px;
        color: var(--text-primary);
      }

      tr {
        transition: background-color 0.25s ease;
      }

      tr:hover > td {
        background: rgba(22, 93, 255, 0.03);
      }

      tr:last-child > td {
        border-bottom: none;
      }
    }

    .el-table__empty-block {
      min-height: 240px;
    }
  }

  .operator-cell {
    font-weight: 500;
    color: var(--text-primary);
  }

  .action-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 2px;
    padding: 5px 10px;
    border-radius: 6px;
    text-decoration: none;
    transition: all 0.2s;
    font-size: 13px;
    white-space: nowrap;

    &.view-btn {
      color: var(--primary-color);
      background: rgba(22, 93, 255, 0.06);

      &:hover {
        background: rgba(22, 93, 255, 0.14);
      }
    }
  }
}

.table-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);

  .table-info {
    font-size: 14px;
    color: var(--text-muted);
  }

  :deep(.el-pagination) {
    .el-pager li {
      border-radius: 6px;
      font-weight: 500;
      transition: all 0.2s;

      &:hover {
        color: var(--primary-color);
      }

      &.is-active {
        background: var(--primary-color);
        color: #fff;
      }
    }

    .btn-prev,
    .btn-next {
      border-radius: 6px;
      transition: all 0.2s;

      &:hover {
        color: var(--primary-color);
      }
    }

    .el-pagination__sizes {
      .el-input__wrapper {
        border-radius: 6px;
      }
    }
  }
}
</style>
