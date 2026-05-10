<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getProductTypeList, createProductType, updateProductType, deleteProductType, generateProductTypeCode } from '@/api/enterprise'
import { Search, Refresh, Plus } from '@element-plus/icons-vue'

const tableData = ref([])
const total = ref(0)
const loading = ref(false)

const queryParams = reactive({
  page: 1,
  size: 10,
  search: ''
})

const categoryMap = {
  physical: '实物产品',
  service: '服务产品',
  digital: '数字产品',
  financial: '金融产品',
  other: '其他'
}

const categoryOptions = [
  { label: '实物产品', value: 'physical' },
  { label: '服务产品', value: 'service' },
  { label: '数字产品', value: 'digital' },
  { label: '金融产品', value: 'financial' },
  { label: '其他', value: 'other' }
]

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getProductTypeList(queryParams)
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
const dialogTitle = ref('新增产品类型')
const formRef = ref(null)
const submitLoading = ref(false)

const form = reactive({
  id: null,
  code: '',
  name: '',
  category: '',
  sort_order: 0,
  description: '',
  is_active: true
})

const rules = {
  code: [{ required: true, message: '请输入编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }]
}

const resetForm = () => {
  Object.assign(form, {
    id: null,
    code: '',
    name: '',
    category: '',
    sort_order: 0,
    description: '',
    is_active: true
  })
}

const openCreateDialog = () => {
  resetForm()
  dialogTitle.value = '新增产品类型'
  dialogVisible.value = true
  handleGenerateCode()
}

const handleGenerateCode = async () => {
  try {
    const res = await generateProductTypeCode()
    form.code = res.data.code
  } catch {}
}

const openEditDialog = (row) => {
  Object.assign(form, {
    id: row.id,
    code: row.code,
    name: row.name,
    category: row.category,
    sort_order: row.sort_order,
    description: row.description || '',
    is_active: row.is_active
  })
  dialogTitle.value = '编辑产品类型'
  dialogVisible.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  submitLoading.value = true
  try {
    const payload = { ...form }
    delete payload.id
    if (form.id) {
      await updateProductType(form.id, payload)
      ElMessage.success('更新成功')
    } else {
      await createProductType(payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchData()
  } catch {
  } finally {
    submitLoading.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除产品类型 "${row.name}" 吗？删除后不可恢复。`,
      '删除确认',
      { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' }
    )
    await deleteProductType(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch {
  }
}

onMounted(fetchData)
</script>

<template>
  <div class="product-type-container">
    <div class="page-header">
      <h1>产品类型管理</h1>
      <p class="text-muted">管理产品类型编码、分类与状态</p>
    </div>

    <div class="search-bar card">
      <el-form :inline="true" :model="queryParams" class="search-form">
        <el-form-item>
          <el-input
            v-model="queryParams.search"
            placeholder="搜索名称/编码"
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
      <el-button type="primary" :icon="Plus" @click="openCreateDialog">新增产品类型</el-button>
    </div>

    <div class="card table-card">
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="code" label="编码" min-width="120" />
        <el-table-column prop="name" label="名称" min-width="150" />
        <el-table-column prop="category" label="分类" width="120" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ categoryMap[row.category] || row.category }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="80" align="center" />
        <el-table-column prop="is_active" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right" align="center">
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="520px" @close="resetForm">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="编码" prop="code">
          <div style="display: flex; gap: 8px; width: 100%">
            <el-input v-model="form.code" placeholder="请输入编码" :disabled="!!form.id" style="flex: 1" />
            <el-button type="primary" @click="handleGenerateCode" :disabled="!!form.id">生成</el-button>
          </div>
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入名称" />
        </el-form-item>
        <el-form-item label="分类" prop="category">
          <el-select v-model="form.category" placeholder="请选择分类" style="width: 100%">
            <el-option
              v-for="item in categoryOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="排序" prop="sort_order">
          <el-input-number v-model="form.sort_order" :min="0" :max="9999" controls-position="right" style="width: 100%" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="是否启用" prop="is_active">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.product-type-container {
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
