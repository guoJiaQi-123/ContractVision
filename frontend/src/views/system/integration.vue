<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getIntegrationList, createIntegration, updateIntegration,
  deleteIntegration, testIntegrationConnection, toggleIntegrationStatus
} from '@/api/system'
import { Plus } from '@element-plus/icons-vue'

const loading = ref(false)
const integrations = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('新建集成配置')
const formRef = ref(null)
const submitLoading = ref(false)
const editingId = ref(null)

const form = reactive({
  name: '',
  system_type: '',
  api_url: '',
  auth_type: 'bearer',
  sync_interval: 60
})

const rules = {
  name: [{ required: true, message: '请输入系统名称', trigger: 'blur' }],
  system_type: [{ required: true, message: '请选择系统类型', trigger: 'blur' }],
  api_url: [{ required: true, message: '请输入接口地址', trigger: 'blur' }]
}

const systemTypes = ['ERP', 'CRM', 'OA', 'SAP', 'WMS']
const authTypes = [
  { label: 'Bearer Token', value: 'bearer' },
  { label: 'API Key', value: 'api_key' },
  { label: '无认证', value: 'none' }
]

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getIntegrationList()
    integrations.value = res.data || []
  } catch {
    integrations.value = []
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  editingId.value = null
  dialogTitle.value = '新建集成配置'
  Object.assign(form, { name: '', system_type: '', api_url: '', auth_type: 'bearer', sync_interval: 60 })
  dialogVisible.value = true
}

const openEditDialog = (row) => {
  editingId.value = row.id
  dialogTitle.value = '编辑集成配置'
  Object.assign(form, {
    name: row.name,
    system_type: row.system_type,
    api_url: row.api_url,
    auth_type: row.auth_type,
    sync_interval: row.sync_interval
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  try { await formRef.value.validate() } catch { return }
  submitLoading.value = true
  try {
    if (editingId.value) {
      await updateIntegration(editingId.value, form)
      ElMessage.success('更新成功')
    } else {
      await createIntegration(form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchData()
  } catch {} finally { submitLoading.value = false }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除「${row.name}」吗？`, '删除确认', { type: 'warning' })
    await deleteIntegration(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch {}
}

const handleTestConnection = async (row) => {
  try {
    const res = await testConnection(row.id)
    if (res.data?.success) {
      ElMessage.success('连接测试成功')
    } else {
      ElMessage.warning(res.message || '连接测试失败')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '连接测试失败')
  }
}

const handleToggleStatus = async (row) => {
  try {
    await toggleIntegrationStatus(row.id)
    ElMessage.success(`接口已${row.status === 'active' ? '停用' : '启用'}`)
    fetchData()
  } catch {}
}

onMounted(fetchData)
</script>

<template>
  <div class="integration-container">
    <div class="page-header">
      <div>
        <h1>第三方集成</h1>
        <p class="text-muted">管理外部系统接口集成配置</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreateDialog">新建配置</el-button>
    </div>

    <div class="card">
      <el-table :data="integrations" v-loading="loading" stripe>
        <el-table-column prop="name" label="系统名称" min-width="140" />
        <el-table-column prop="system_type" label="类型" width="100" />
        <el-table-column prop="api_url" label="接口地址" min-width="240" show-overflow-tooltip />
        <el-table-column prop="auth_type" label="认证方式" width="120" />
        <el-table-column prop="sync_interval" label="同步间隔(分钟)" width="140" align="center" />
        <el-table-column prop="status" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ row.status_display }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right" align="center">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleTestConnection(row)">测试连接</el-button>
            <el-button link :type="row.status === 'active' ? 'warning' : 'success'" size="small" @click="handleToggleStatus(row)">
              {{ row.status === 'active' ? '停用' : '启用' }}
            </el-button>
            <el-button link type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无集成配置" />
        </template>
      </el-table>
    </div>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="520px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="系统名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入系统名称" />
        </el-form-item>
        <el-form-item label="系统类型" prop="system_type">
          <el-select v-model="form.system_type" filterable allow-create placeholder="选择或输入" style="width: 100%">
            <el-option v-for="t in systemTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="接口地址" prop="api_url">
          <el-input v-model="form.api_url" placeholder="https://example.com/api" />
        </el-form-item>
        <el-form-item label="认证方式" prop="auth_type">
          <el-select v-model="form.auth_type" style="width: 100%">
            <el-option v-for="a in authTypes" :key="a.value" :label="a.label" :value="a.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="同步间隔" prop="sync_interval">
          <el-input-number v-model="form.sync_interval" :min="5" :max="1440" />
          <span style="margin-left: 8px; color: var(--text-muted); font-size: 13px;">分钟</span>
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
.integration-container {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
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
    box-shadow: var(--shadow-xs);
  }
}
</style>
