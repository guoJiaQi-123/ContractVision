<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getCustomerList, createCustomer, updateCustomer, deleteCustomer, generateCustomerCode } from '@/api/enterprise'
import { Search, Refresh, Plus } from '@element-plus/icons-vue'

const tableData = ref([])
const total = ref(0)
const loading = ref(false)

const queryParams = reactive({
  page: 1,
  size: 10,
  search: ''
})

const levelOptions = [
  { label: 'VIP客户', value: 'vip' },
  { label: '普通客户', value: 'normal' },
  { label: '潜在客户', value: 'potential' }
]

const levelMap = { vip: 'VIP客户', normal: '普通客户', potential: '潜在客户' }
const levelTagType = { vip: 'danger', normal: '', potential: 'info' }

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getCustomerList(queryParams)
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

const dialogVisible = ref(false)
const dialogTitle = ref('新增客户')
const formRef = ref(null)
const formLoading = ref(false)
const editingId = ref(null)

const form = reactive({
  code: '',
  name: '',
  short_name: '',
  level: 'normal',
  contact_person: '',
  contact_phone: '',
  contact_email: '',
  address: '',
  region: '',
  industry: '',
  description: '',
  is_active: true
})

const rules = {
  code: [{ required: true, message: '请输入客户编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入客户名称', trigger: 'blur' }],
  level: [{ required: true, message: '请选择客户等级', trigger: 'change' }]
}

const resetForm = () => {
  Object.assign(form, {
    code: '',
    name: '',
    short_name: '',
    level: 'normal',
    contact_person: '',
    contact_phone: '',
    contact_email: '',
    address: '',
    region: '',
    industry: '',
    description: '',
    is_active: true
  })
  editingId.value = null
}

const openCreateDialog = () => {
  resetForm()
  dialogTitle.value = '新增客户'
  dialogVisible.value = true
  handleGenerateCode()
}

const handleGenerateCode = async () => {
  try {
    const res = await generateCustomerCode()
    form.code = res.data.code
  } catch {}
}

const openEditDialog = (row) => {
  resetForm()
  dialogTitle.value = '编辑客户'
  editingId.value = row.id
  Object.assign(form, {
    code: row.code || '',
    name: row.name || '',
    short_name: row.short_name || '',
    level: row.level || 'normal',
    contact_person: row.contact_person || '',
    contact_phone: row.contact_phone || '',
    contact_email: row.contact_email || '',
    address: row.address || '',
    region: row.region || '',
    industry: row.industry || '',
    description: row.description || '',
    is_active: row.is_active !== false
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  formLoading.value = true
  try {
    if (editingId.value) {
      await updateCustomer(editingId.value, form)
      ElMessage.success('客户更新成功')
    } else {
      await createCustomer(form)
      ElMessage.success('客户创建成功')
    }
    dialogVisible.value = false
    fetchData()
  } catch {
  } finally {
    formLoading.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除客户 "${row.name}" 吗？删除后不可恢复。`,
      '删除确认',
      { type: 'warning' }
    )
    await deleteCustomer(row.id)
    ElMessage.success('客户删除成功')
    fetchData()
  } catch {
  }
}

onMounted(fetchData)
</script>

<template>
  <div class="customer-management-container">
    <div class="page-header">
      <h1>客户管理</h1>
      <p class="text-muted">管理企业客户信息、等级分类与联系方式</p>
    </div>

    <div class="search-bar card">
      <el-form :inline="true" :model="queryParams" class="search-form">
        <el-form-item>
          <el-input
            v-model="queryParams.search"
            placeholder="搜索客户名称/编码"
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
      </el-form>
      <el-button type="primary" :icon="Plus" @click="openCreateDialog">新增客户</el-button>
    </div>

    <div class="card table-card">
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="code" label="客户编码" min-width="120" />
        <el-table-column prop="name" label="客户名称" min-width="160" />
        <el-table-column prop="short_name" label="简称" min-width="100" />
        <el-table-column prop="level" label="客户等级" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="levelTagType[row.level]" size="small">{{ levelMap[row.level] || row.level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="contact_person" label="联系人" min-width="100" />
        <el-table-column prop="contact_phone" label="联系电话" min-width="130" />
        <el-table-column prop="region" label="区域" min-width="80" />
        <el-table-column prop="industry" label="行业" min-width="80" />
        <el-table-column prop="is_active" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active !== false ? 'success' : 'danger'" size="small">
              {{ row.is_active !== false ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right" align="center">
          <template #default="{ row }">
            <el-button size="small" link type="primary" @click="openEditDialog(row)">编辑</el-button>
            <el-button size="small" link type="danger" @click="handleDelete(row)">删除</el-button>
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px" @close="resetForm">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="客户编码" prop="code">
              <div style="display: flex; gap: 8px; width: 100%">
                <el-input v-model="form.code" placeholder="请输入客户编码" :disabled="!!editingId" style="flex: 1" />
                <el-button type="primary" @click="handleGenerateCode" :disabled="!!editingId">生成</el-button>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="客户名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入客户名称" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="简称">
              <el-input v-model="form.short_name" placeholder="请输入简称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="客户等级" prop="level">
              <el-select v-model="form.level" placeholder="请选择客户等级" style="width: 100%">
                <el-option
                  v-for="item in levelOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="联系人">
              <el-input v-model="form.contact_person" placeholder="请输入联系人" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系电话">
              <el-input v-model="form.contact_phone" placeholder="请输入联系电话" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="联系邮箱">
              <el-input v-model="form.contact_email" placeholder="请输入联系邮箱" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="区域">
              <el-input v-model="form.region" placeholder="请输入区域" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="行业">
              <el-input v-model="form.industry" placeholder="请输入行业" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="是否启用">
              <el-switch v-model="form.is_active" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="地址">
          <el-input v-model="form.address" placeholder="请输入地址" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="formLoading" @click="handleSubmit">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.customer-management-container {
  .page-header {
    margin-bottom: var(--space-6, 24px);

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
    margin-bottom: var(--space-4, 16px);
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
    margin-top: var(--space-4, 16px);
    padding-top: var(--space-4, 16px);
    border-top: 1px solid var(--border-light);
  }
}
</style>
