<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getDepartmentList, createDepartment, updateDepartment, deleteDepartment, getDepartmentOptions, getDepartmentTree, getDepartmentAdminUsers, generateDepartmentCode } from '@/api/enterprise'
import { Search, Refresh, Plus } from '@element-plus/icons-vue'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const searchKeyword = ref('')
const dialogVisible = ref(false)
const dialogTitle = ref('新增部门')
const formRef = ref(null)
const departmentOptions = ref([])
const adminUsers = ref([])
const viewMode = ref('tree')

const form = reactive({
  id: null,
  code: '',
  name: '',
  parent: null,
  manager: '',
  sort_order: 0,
  description: '',
  is_active: true
})

const rules = {
  code: [{ required: true, message: '请输入部门编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入部门名称', trigger: 'blur' }]
}

const departmentTreeData = computed(() => {
  const buildTree = (items, parentId = null) => {
    return items
      .filter(item => item.parent === parentId)
      .map(item => ({
        ...item,
        children: buildTree(items, item.id)
      }))
  }
  return buildTree(departmentOptions.value)
})

const fetchData = async () => {
  loading.value = true
  try {
    if (viewMode.value === 'tree') {
      const res = await getDepartmentTree()
      const data = res.data || res
      tableData.value = data || []
      total.value = countTreeNodes(tableData.value)
    } else {
      const res = await getDepartmentList({ page: page.value, page_size: pageSize.value, search: searchKeyword.value })
      const data = res.data || res
      tableData.value = data.results || data || []
      total.value = data.count || 0
    }
  } catch {
    ElMessage.error('获取部门列表失败')
  } finally {
    loading.value = false
  }
}

const countTreeNodes = (nodes) => {
  let count = 0
  for (const node of nodes) {
    count += 1
    if (node.children && node.children.length > 0) {
      count += countTreeNodes(node.children)
    }
  }
  return count
}

const fetchOptions = async () => {
  try {
    const res = await getDepartmentOptions()
    departmentOptions.value = res.data || []
  } catch {}
}

const fetchAdminUsers = async () => {
  try {
    const res = await getDepartmentAdminUsers()
    adminUsers.value = res.data || []
  } catch {}
}

const handleSearch = () => {
  if (viewMode.value === 'tree') {
    viewMode.value = 'list'
  }
  page.value = 1
  fetchData()
}

const handleReset = () => {
  searchKeyword.value = ''
  page.value = 1
  if (viewMode.value === 'list') {
    viewMode.value = 'tree'
  }
  fetchData()
}

const handleViewModeChange = (mode) => {
  viewMode.value = mode
  if (mode === 'tree') {
    searchKeyword.value = ''
  }
  fetchData()
}

const handleAdd = () => {
  dialogTitle.value = '新增部门'
  Object.assign(form, { id: null, code: '', name: '', parent: null, manager: '', sort_order: 0, description: '', is_active: true })
  dialogVisible.value = true
  handleGenerateCode()
}

const handleGenerateCode = async () => {
  try {
    const res = await generateDepartmentCode()
    form.code = res.data.code
  } catch {}
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑部门'
  Object.assign(form, { ...row })
  dialogVisible.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除部门"${row.name}"吗？`, '提示', { type: 'warning' })
    await deleteDepartment(row.id)
    ElMessage.success('删除成功')
    fetchData()
    fetchOptions()
  } catch {}
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
  } catch { return }
  try {
    const data = { ...form }
    delete data.id
    if (form.id) {
      await updateDepartment(form.id, data)
      ElMessage.success('更新成功')
    } else {
      await createDepartment(data)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchData()
    fetchOptions()
  } catch {}
}

const handlePageChange = (val) => {
  page.value = val
  fetchData()
}

const handleSizeChange = (val) => {
  pageSize.value = val
  page.value = 1
  fetchData()
}

const getParentName = (parentId) => {
  if (!parentId) return '-'
  const found = departmentOptions.value.find(item => item.id === parentId)
  return found ? found.name : '-'
}

const roleTagType = (role) => {
  return role === 'admin' ? 'danger' : ''
}

onMounted(() => {
  fetchData()
  fetchOptions()
  fetchAdminUsers()
})
</script>

<template>
  <div class="department-management-container">
    <div class="page-header">
      <h1>部门管理</h1>
      <p class="text-muted">管理企业部门架构、人员分配与部门状态</p>
    </div>

    <div class="search-bar card">
      <el-form :inline="true" class="search-form">
        <el-form-item>
          <el-input
            v-model="searchKeyword"
            placeholder="搜索部门名称"
            clearable
            style="width: 240px"
            :prefix-icon="Search"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
        <el-form-item>
          <el-radio-group v-model="viewMode" @change="handleViewModeChange">
            <el-radio-button value="tree">树形</el-radio-button>
            <el-radio-button value="list">列表</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <el-button type="primary" :icon="Plus" @click="handleAdd">新增部门</el-button>
    </div>

    <div class="card table-card">
      <el-table
        v-if="viewMode === 'tree'"
        :data="tableData"
        v-loading="loading"
        row-key="id"
        :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
        stripe
        default-expand-all
      >
        <el-table-column prop="code" label="部门编码" min-width="120" />
        <el-table-column prop="name" label="部门名称" min-width="150" />
        <el-table-column prop="manager" label="负责人" min-width="120">
          <template #default="{ row }">
            <template v-if="row.manager">
              <el-tag size="small" :type="roleTagType(adminUsers.find(u => u.username === row.manager)?.role)">
                {{ row.manager }}
              </el-tag>
            </template>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="80" align="center" />
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right" align="center">
          <template #default="{ row }">
            <el-button size="small" link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-table
        v-else
        :data="tableData"
        v-loading="loading"
        stripe
      >
        <el-table-column prop="code" label="部门编码" min-width="120" />
        <el-table-column prop="name" label="部门名称" min-width="150" />
        <el-table-column label="上级部门" min-width="140">
          <template #default="{ row }">{{ getParentName(row.parent) }}</template>
        </el-table-column>
        <el-table-column prop="manager" label="负责人" min-width="120">
          <template #default="{ row }">
            <template v-if="row.manager">
              <el-tag size="small" :type="roleTagType(adminUsers.find(u => u.username === row.manager)?.role)">
                {{ row.manager }}
              </el-tag>
            </template>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="80" align="center" />
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right" align="center">
          <template #default="{ row }">
            <el-button size="small" link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="viewMode === 'list'" class="pagination-wrapper">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="520px" @closed="formRef?.resetFields()">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="部门编码" prop="code">
          <div style="display: flex; gap: 8px; width: 100%">
            <el-input v-model="form.code" placeholder="请输入部门编码" style="flex: 1" />
            <el-button type="primary" @click="handleGenerateCode" :disabled="!!form.id">生成</el-button>
          </div>
        </el-form-item>
        <el-form-item label="部门名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入部门名称" />
        </el-form-item>
        <el-form-item label="上级部门" prop="parent">
          <el-tree-select
            v-model="form.parent"
            :data="departmentTreeData"
            :props="{ label: 'name', value: 'id', children: 'children' }"
            placeholder="请选择上级部门"
            clearable
            check-strictly
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="负责人" prop="manager">
          <el-select v-model="form.manager" placeholder="请选择负责人" clearable filterable style="width: 100%">
            <el-option
              v-for="user in adminUsers"
              :key="user.id"
              :label="`${user.username}（${user.role === 'admin' ? '管理员' : '操作员'}）`"
              :value="user.username"
            >
              <span>{{ user.username }}</span>
              <el-tag size="small" :type="user.role === 'admin' ? 'danger' : ''" style="margin-left: 8px">
                {{ user.role === 'admin' ? '管理员' : '操作员' }}
              </el-tag>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="排序" prop="sort_order">
          <el-input-number v-model="form.sort_order" :min="0" :max="9999" controls-position="right" style="width: 100%" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入部门描述" />
        </el-form-item>
        <el-form-item label="是否启用" prop="is_active">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.department-management-container {
  .page-header {
    margin-bottom: 24px;

    h1 {
      font-size: var(--fs-xl);
      font-weight: 600;
      color: var(--text-primary);
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
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: var(--shadow-xs);
  }

  .search-bar {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;

    .search-form {
      display: flex;
      flex-wrap: wrap;
      gap: 0;
    }
  }

  .table-card {
    border-radius: var(--radius-lg);
    border: 1px solid var(--border-color);

    :deep(.el-table) {
      --el-table-header-bg-color: var(--gray-50);
      --el-table-border-color: var(--border-light);
      --el-table-row-hover-bg-color: var(--primary-bg);
      border-radius: var(--radius-lg);
    }
  }

  .pagination-wrapper {
    display: flex;
    justify-content: flex-end;
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid var(--border-light);
  }
}
</style>
