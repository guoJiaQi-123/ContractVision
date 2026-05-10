<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getBackupList, createBackup, restoreBackup, deleteBackup } from '@/api/system'

const loading = ref(false)
const backupLoading = ref(false)
const backups = ref([])

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getBackupList()
    backups.value = res.data || []
  } catch {
    backups.value = []
  } finally {
    loading.value = false
  }
}

const handleCreateBackup = async () => {
  backupLoading.value = true
  try {
    await createBackup()
    ElMessage.success('数据备份成功')
    fetchData()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '备份失败')
  } finally {
    backupLoading.value = false
  }
}

const handleRestore = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要从备份「${row.filename}」恢复数据吗？当前数据将被覆盖！`,
      '恢复确认',
      { type: 'warning', confirmButtonText: '确定恢复', cancelButtonText: '取消' }
    )
    await restoreBackup({ filename: row.filename })
    ElMessage.success('数据恢复成功')
  } catch {}
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除备份「${row.filename}」吗？`, '删除确认', { type: 'warning' })
    await deleteBackup({ filename: row.filename })
    ElMessage.success('备份文件已删除')
    fetchData()
  } catch {}
}

const formatSize = (bytes) => {
  if (!bytes) return '0 B'
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`
}

onMounted(fetchData)
</script>

<template>
  <div class="backup-container">
    <div class="page-header">
      <div>
        <h1>数据备份管理</h1>
        <p class="text-muted">管理数据库备份与恢复操作</p>
      </div>
      <el-button type="primary" :loading="backupLoading" @click="handleCreateBackup">创建备份</el-button>
    </div>

    <div class="card">
      <el-table :data="backups" v-loading="loading" stripe>
        <el-table-column prop="filename" label="备份文件名" min-width="280" />
        <el-table-column prop="size" label="文件大小" width="120">
          <template #default="{ row }">{{ formatSize(row.size) }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="200" />
        <el-table-column label="操作" width="200" align="center">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleRestore(row)">恢复</el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无备份文件" />
        </template>
      </el-table>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.backup-container {
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
