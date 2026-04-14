<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUserList, createUser, updateUser, toggleUserActive, assignUserRole } from '@/api/user'
import { Search, Refresh, Plus } from '@element-plus/icons-vue'

const tableData = ref([])
const total = ref(0)
const loading = ref(false)

const queryParams = reactive({
  page: 1,
  size: 10,
  search: '',
  role: '',
  is_active: ''
})

const roleOptions = [
  { label: '全部角色', value: '' },
  { label: '管理员', value: 'admin' },
  { label: '操作员', value: 'operator' },
  { label: '查看者', value: 'viewer' }
]

const roleMap = { admin: '管理员', operator: '操作员', viewer: '查看者' }
const roleTagType = { admin: 'danger', operator: 'warning', viewer: 'info' }

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getUserList(queryParams)
    const data = res.data
    tableData.value = data?.results || data || []
    total.value = data?.total || tableData.value.length
  } catch {
    tableData.value = []
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  queryParams.page = 1
  fetchData()
}

const handleReset = () => {
  queryParams.search = ''
  queryParams.role = ''
  queryParams.is_active = ''
  queryParams.page = 1
  fetchData()
}

const handlePageChange = (page) => {
  queryParams.page = page
  fetchData()
}

const handleSizeChange = (size) => {
  queryParams.size = size
  queryParams.page = 1
  fetchData()
}

const handleToggleActive = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要${row.is_active ? '禁用' : '启用'}用户 "${row.username}" 吗？`,
      '操作确认',
      { type: 'warning' }
    )
    await toggleUserActive(row.id)
    ElMessage.success(`用户已${row.is_active ? '禁用' : '启用'}`)
    fetchData()
  } catch {
    fetchData()
  }
}

const roleDialogVisible = ref(false)
const roleForm = reactive({ userId: null, username: '', role: '' })

const openRoleDialog = (row) => {
  roleForm.userId = row.id
  roleForm.username = row.username
  roleForm.role = row.role
  roleDialogVisible.value = true
}

const handleAssignRole = async () => {
  try {
    await assignUserRole(roleForm.userId, { role: roleForm.role })
    ElMessage.success('角色分配成功')
    roleDialogVisible.value = false
    fetchData()
  } catch {
  }
}

const createDialogVisible = ref(false)
const createFormRef = ref(null)
const createForm = reactive({
  username: '',
  email: '',
  phone: '',
  company_name: '',
  password: '',
  confirm_password: ''
})
const createLoading = ref(false)

const createRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码长度不能少于8位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== createForm.password) callback(new Error('两次密码不一致'))
        else callback()
      },
      trigger: 'blur'
    }
  ]
}

const openCreateDialog = () => {
  Object.assign(createForm, {
    username: '', email: '', phone: '', company_name: '', password: '', confirm_password: ''
  })
  createDialogVisible.value = true
}

const handleCreateUser = async () => {
  try {
    await createFormRef.value.validate()
  } catch {
    return
  }
  createLoading.value = true
  try {
    await createUser(createForm)
    ElMessage.success('用户创建成功')
    createDialogVisible.value = false
    fetchData()
  } catch {
  } finally {
    createLoading.value = false
  }
}

const detailVisible = ref(false)
const detailData = ref({})

const openDetail = (row) => {
  detailData.value = row
  detailVisible.value = true
}

const formatDate = (val) => {
  if (!val) return '-'
  return val.replace('T', ' ').substring(0, 19)
}

onMounted(fetchData)
</script>

<template>
  <div class="user-management-container">
    <div class="page-header">
      <h1>用户管理</h1>
      <p class="text-muted">管理平台用户账号、角色权限与账号状态</p>
    </div>

    <div class="search-bar card">
      <el-form :inline="true" :model="queryParams" class="search-form">
        <el-form-item>
          <el-input
            v-model="queryParams.search"
            placeholder="搜索用户名/邮箱/手机号"
            clearable
            style="width: 240px"
            :prefix-icon="Search"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-select v-model="queryParams.role" placeholder="角色筛选" style="width: 140px">
            <el-option
              v-for="item in roleOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-select v-model="queryParams.is_active" placeholder="状态筛选" style="width: 140px">
            <el-option label="全部状态" value="" />
            <el-option label="启用" value="true" />
            <el-option label="禁用" value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
      <el-button type="primary" :icon="Plus" @click="openCreateDialog">新建用户</el-button>
    </div>

    <div class="card table-card">
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column prop="phone" label="手机号" width="130" />
        <el-table-column prop="company_name" label="企业名称" min-width="150" />
        <el-table-column prop="role" label="角色" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="roleTagType[row.role]" size="small">{{ roleMap[row.role] || row.role }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="注册时间" width="170">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right" align="center">
          <template #default="{ row }">
            <el-button size="small" link type="primary" @click="openDetail(row)">详情</el-button>
            <el-button size="small" link type="warning" @click="openRoleDialog(row)">角色</el-button>
            <el-button
              size="small"
              link
              :type="row.is_active ? 'danger' : 'success'"
              @click="handleToggleActive(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.size"
          :page-sizes="[10, 20, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </div>

    <el-dialog v-model="roleDialogVisible" title="角色权限分配" width="400px">
      <p style="margin-bottom: 16px; color: #86909C;">
        为用户 <strong>{{ roleForm.username }}</strong> 分配角色
      </p>
      <el-radio-group v-model="roleForm.role" style="display: flex; flex-direction: column; gap: 12px;">
        <el-radio value="admin">
          <span>管理员</span>
          <span style="color: #86909C; font-size: 12px; margin-left: 8px;">全功能操作权限</span>
        </el-radio>
        <el-radio value="operator">
          <span>操作员</span>
          <span style="color: #86909C; font-size: 12px; margin-left: 8px;">合同数据管理与分析</span>
        </el-radio>
        <el-radio value="viewer">
          <span>查看者</span>
          <span style="color: #86909C; font-size: 12px; margin-left: 8px;">只读查看权限</span>
        </el-radio>
      </el-radio-group>
      <template #footer>
        <el-button @click="roleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAssignRole">确认</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="createDialogVisible" title="新建用户" width="500px">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="createForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="createForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="createForm.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="企业名称" prop="company_name">
          <el-input v-model="createForm.company_name" placeholder="请输入企业名称" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="createForm.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input v-model="createForm.confirm_password" type="password" placeholder="请确认密码" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreateUser">创建</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="detailVisible" title="用户详情" size="400px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="用户名">{{ detailData.username }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ detailData.email || '-' }}</el-descriptions-item>
        <el-descriptions-item label="手机号">{{ detailData.phone || '-' }}</el-descriptions-item>
        <el-descriptions-item label="企业名称">{{ detailData.company_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="角色">
          <el-tag :type="roleTagType[detailData.role]" size="small">{{ roleMap[detailData.role] }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="账号状态">
          <el-tag :type="detailData.is_active ? 'success' : 'danger'" size="small">
            {{ detailData.is_active ? '启用' : '禁用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="注册时间">{{ formatDate(detailData.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatDate(detailData.updated_at) }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>
  </div>
</template>

<style lang="scss" scoped>
.user-management-container {
  .page-header {
    margin-bottom: 24px;

    h1 {
      font-size: 24px;
      font-weight: 600;
      color: var(--text-primary);
    }

    .text-muted {
      margin-top: 4px;
      font-size: 14px;
      color: var(--text-muted);
    }
  }

  .card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
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
    :deep(.el-table) {
      --el-table-header-bg-color: var(--bg-color);
    }
  }

  .pagination-wrapper {
    display: flex;
    justify-content: flex-end;
    margin-top: 16px;
  }
}
</style>
