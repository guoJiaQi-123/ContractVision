<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { generateReport, exportReport } from '@/api/analytics'
import { Download } from '@element-plus/icons-vue'

const loading = ref(false)
const exportLoading = ref(false)
const reportData = ref(null)

const form = reactive({
  report_type: 'monthly_summary',
  start_date: '',
  end_date: ''
})

const reportTypes = [
  { label: '月度销售汇总', value: 'monthly_summary' },
  { label: '客户业绩分析', value: 'client_analysis' },
  { label: '产品销售分析', value: 'product_analysis' },
  { label: '区域业绩统计', value: 'region_analysis' },
  { label: '销售人员分析', value: 'salesperson_analysis' }
]

const handleGenerate = async () => {
  loading.value = true
  reportData.value = null
  try {
    const res = await generateReport(form)
    reportData.value = res.data
  } catch {
    ElMessage.error('报表生成失败')
  } finally {
    loading.value = false
  }
}

const handleExport = async (format) => {
  if (!reportData.value) {
    ElMessage.warning('请先生成报表')
    return
  }
  exportLoading.value = true
  try {
    const res = await exportReport({
      format,
      report_data: reportData.value
    })
    const blob = new Blob([res])
    const link = document.createElement('a')
    const ext = format === 'pdf' ? 'pdf' : 'xlsx'
    link.href = URL.createObjectURL(blob)
    link.download = `${reportData.value.title || '报表'}.${ext}`
    link.click()
    URL.revokeObjectURL(link.href)
    ElMessage.success('导出成功')
  } catch {
    ElMessage.error('导出失败')
  } finally {
    exportLoading.value = false
  }
}
</script>

<template>
  <div class="report-container">
    <div class="page-header">
      <h1>报表中心</h1>
      <p class="text-muted">生成多维度数据报表并导出</p>
    </div>

    <div class="card">
      <el-form :model="form" :inline="true">
        <el-form-item label="报表类型">
          <el-select v-model="form.report_type" style="width: 200px">
            <el-option v-for="t in reportTypes" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" placeholder="选择开始日期" />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker v-model="form.end_date" type="date" value-format="YYYY-MM-DD" placeholder="选择结束日期" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleGenerate">生成报表</el-button>
        </el-form-item>
        <el-form-item v-if="reportData">
          <el-dropdown @command="handleExport" :loading="exportLoading">
            <el-button :icon="Download">
              导出报表
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="excel">导出 Excel</el-dropdown-item>
                <el-dropdown-item command="pdf">导出 PDF</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </el-form-item>
      </el-form>
    </div>

    <div v-if="reportData" class="card" style="margin-top: 16px;">
      <h3 class="report-title">{{ reportData.title }}</h3>
      <el-table :data="reportData.rows" stripe border style="width: 100%">
        <el-table-column
          v-for="(col, index) in reportData.columns"
          :key="index"
          :prop="Object.keys(reportData.rows[0] || {})[index]"
          :label="col"
          min-width="120"
        />
      </el-table>
    </div>

    <el-empty v-else-if="!loading" description="请选择报表类型并生成报表" style="margin-top: 60px;" />
  </div>
</template>

<style lang="scss" scoped>
.report-container {
  .page-header {
    margin-bottom: 24px;
    h1 { font-size: 24px; font-weight: 600; color: var(--text-primary); }
    .text-muted { margin-top: 4px; font-size: 14px; color: var(--text-muted); }
  }
  .card {
    background: var(--card-bg); border: 1px solid var(--border-color);
    border-radius: 12px; padding: 24px;
  }
  .report-title {
    font-size: 18px; font-weight: 600; color: var(--text-primary); margin-bottom: 16px;
  }
}
</style>
