<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getDataTemplates,
  createDataTemplate,
  getCurrencyRates,
  createCurrencyRate,
  getStampTaxRules,
  createStampTaxRule,
  getDashboardConfigs,
  createDashboardConfig
} from '@/api/system'

const templates = ref([])
const currencyRates = ref([])
const stampTaxRules = ref([])
const dashboards = ref([])

const templateDialogVisible = ref(false)
const rateDialogVisible = ref(false)
const taxDialogVisible = ref(false)
const dashboardDialogVisible = ref(false)

const templateForm = ref({
  name: '',
  template_type: 'import',
  version: 'v1.0',
  field_config: [],
  validation_rules: [],
  description: ''
})

const rateForm = ref({
  currency: 'USD',
  base_currency: 'CNY',
  rate: 7.12,
  effective_date: '',
  remark: ''
})

const taxForm = ref({
  contract_type: '',
  rate: 0.0003,
  description: ''
})

const dashboardForm = ref({
  name: '',
  role_scope: 'admin,viewer',
  is_mobile: false,
  layout: [{ x: 0, y: 0, w: 6, h: 4 }],
  widgets: [{ id: 'metric-1', type: 'metric', title: '累计合同金额', metric: 'amount' }]
})

const loadData = async () => {
  const [templateRes, rateRes, taxRes, dashboardRes] = await Promise.all([
    getDataTemplates(),
    getCurrencyRates(),
    getStampTaxRules(),
    getDashboardConfigs()
  ])
  templates.value = templateRes.data?.results || templateRes.data || []
  currencyRates.value = rateRes.data?.results || rateRes.data || []
  stampTaxRules.value = taxRes.data?.results || taxRes.data || []
  dashboards.value = dashboardRes.data?.results || dashboardRes.data || []
}

const submitTemplate = async () => {
  await createDataTemplate(templateForm.value)
  templateDialogVisible.value = false
  ElMessage.success('模板已保存')
  await loadData()
}

const submitRate = async () => {
  await createCurrencyRate(rateForm.value)
  rateDialogVisible.value = false
  ElMessage.success('汇率已保存')
  await loadData()
}

const submitTax = async () => {
  await createStampTaxRule(taxForm.value)
  taxDialogVisible.value = false
  ElMessage.success('印花税规则已保存')
  await loadData()
}

const submitDashboard = async () => {
  await createDashboardConfig(dashboardForm.value)
  dashboardDialogVisible.value = false
  ElMessage.success('驾驶舱模板已保存')
  await loadData()
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="config-page">
    <section class="hero-card">
      <div class="hero-main">
        <h1>模板与汇率中心</h1>
        <p>统一管理导入导出模板、多币种汇率、印花税规则与 PC / 移动驾驶舱模板。</p>
      </div>
      <div class="hero-side">
        <div class="hero-status-card">
          <span>当前模板</span>
          <strong>{{ templates.length }} 份</strong>
          <small>汇率 {{ currencyRates.length }} 条 · 税率 {{ stampTaxRules.length }} 条</small>
        </div>
        <div class="hero-actions">
          <el-button @click="templateDialogVisible = true">新建模板</el-button>
          <el-button @click="rateDialogVisible = true">维护汇率</el-button>
          <el-button type="primary" @click="dashboardDialogVisible = true">新增驾驶舱</el-button>
        </div>
      </div>
    </section>

    <el-row :gutter="24">
      <el-col :xs="24" :lg="12">
        <div class="panel">
          <div class="panel-header">
            <div>
              <h3>数据模板库</h3>
              <p>导入、导出、报表模板支持版本化管理</p>
            </div>
            <el-button type="primary" @click="templateDialogVisible = true">新增模板</el-button>
          </div>
          <el-table :data="templates">
            <el-table-column prop="name" label="模板名称" min-width="160" />
            <el-table-column prop="template_type_display" label="类型" width="110" />
            <el-table-column prop="version" label="版本" width="90" />
            <el-table-column label="字段数" width="90">
              <template #default="{ row }">{{ row.field_config?.length || 0 }}</template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
      <el-col :xs="24" :lg="12">
        <div class="panel">
          <div class="panel-header">
            <div>
              <h3>多币种汇率管理</h3>
              <p>支持签约日 / 结算日汇率换算</p>
            </div>
            <el-button type="primary" @click="rateDialogVisible = true">新增汇率</el-button>
          </div>
          <el-table :data="currencyRates">
            <el-table-column prop="currency" label="币种" width="90" />
            <el-table-column prop="base_currency" label="本位币" width="90" />
            <el-table-column prop="rate" label="汇率" width="120" />
            <el-table-column prop="effective_date" label="生效日期" width="120" />
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="row.is_latest ? 'success' : 'info'">{{ row.is_latest ? '最新' : '历史' }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="24">
      <el-col :xs="24" :lg="12">
        <div class="panel">
          <div class="panel-header">
            <div>
              <h3>印花税规则</h3>
              <p>按合同类型自动匹配税率并汇总应缴税额</p>
            </div>
            <el-button type="primary" @click="taxDialogVisible = true">新增税率</el-button>
          </div>
          <el-table :data="stampTaxRules">
            <el-table-column prop="contract_type" label="合同类型" min-width="140" />
            <el-table-column prop="rate" label="税率" width="120" />
            <el-table-column prop="description" label="说明" min-width="160" />
          </el-table>
        </div>
      </el-col>
      <el-col :xs="24" :lg="12">
        <div class="panel">
          <div class="panel-header">
            <div>
              <h3>驾驶舱模板</h3>
              <p>支持保存 PC / 移动端组件布局模板</p>
            </div>
            <el-button type="primary" @click="dashboardDialogVisible = true">新增模板</el-button>
          </div>
          <el-table :data="dashboards">
            <el-table-column prop="name" label="模板名称" min-width="150" />
            <el-table-column prop="role_scope" label="适用角色" min-width="120" />
            <el-table-column label="终端" width="100">
              <template #default="{ row }">
                <el-tag :type="row.is_mobile ? 'warning' : 'success'">{{ row.is_mobile ? '移动端' : 'PC端' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="组件数" width="90">
              <template #default="{ row }">{{ row.widgets?.length || 0 }}</template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
    </el-row>

    <el-dialog v-model="templateDialogVisible" title="新增模板" width="620px">
      <el-form :model="templateForm" label-width="100px">
        <el-form-item label="模板名称"><el-input v-model="templateForm.name" /></el-form-item>
        <el-form-item label="模板类型">
          <el-select v-model="templateForm.template_type">
            <el-option label="导入模板" value="import" />
            <el-option label="导出模板" value="export" />
            <el-option label="报表模板" value="report" />
          </el-select>
        </el-form-item>
        <el-form-item label="字段配置">
          <el-input
            :model-value="JSON.stringify(templateForm.field_config, null, 2)"
            type="textarea"
            :rows="6"
            @update:model-value="val => { try { templateForm.field_config = JSON.parse(val || '[]') } catch (error) {} }"
          />
        </el-form-item>
      </el-form>
      <template #footer><el-button @click="templateDialogVisible = false">取消</el-button><el-button type="primary" @click="submitTemplate">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="rateDialogVisible" title="新增汇率" width="520px">
      <el-form :model="rateForm" label-width="100px">
        <el-form-item label="币种"><el-input v-model="rateForm.currency" /></el-form-item>
        <el-form-item label="本位币"><el-input v-model="rateForm.base_currency" /></el-form-item>
        <el-form-item label="汇率"><el-input-number v-model="rateForm.rate" :min="0.000001" :precision="6" /></el-form-item>
        <el-form-item label="生效日期"><el-date-picker v-model="rateForm.effective_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="rateDialogVisible = false">取消</el-button><el-button type="primary" @click="submitRate">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="taxDialogVisible" title="新增印花税规则" width="520px">
      <el-form :model="taxForm" label-width="100px">
        <el-form-item label="合同类型"><el-input v-model="taxForm.contract_type" /></el-form-item>
        <el-form-item label="税率"><el-input-number v-model="taxForm.rate" :min="0.000001" :precision="6" /></el-form-item>
        <el-form-item label="说明"><el-input v-model="taxForm.description" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="taxDialogVisible = false">取消</el-button><el-button type="primary" @click="submitTax">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="dashboardDialogVisible" title="新增驾驶舱模板" width="680px">
      <el-form :model="dashboardForm" label-width="100px">
        <el-form-item label="模板名称"><el-input v-model="dashboardForm.name" /></el-form-item>
        <el-form-item label="适用角色"><el-input v-model="dashboardForm.role_scope" /></el-form-item>
        <el-form-item label="移动端"><el-switch v-model="dashboardForm.is_mobile" /></el-form-item>
        <el-form-item label="布局配置">
          <el-input
            :model-value="JSON.stringify(dashboardForm.layout, null, 2)"
            type="textarea"
            :rows="4"
            @update:model-value="val => { try { dashboardForm.layout = JSON.parse(val || '[]') } catch (error) {} }"
          />
        </el-form-item>
        <el-form-item label="组件配置">
          <el-input
            :model-value="JSON.stringify(dashboardForm.widgets, null, 2)"
            type="textarea"
            :rows="6"
            @update:model-value="val => { try { dashboardForm.widgets = JSON.parse(val || '[]') } catch (error) {} }"
          />
        </el-form-item>
      </el-form>
      <template #footer><el-button @click="dashboardDialogVisible = false">取消</el-button><el-button type="primary" @click="submitDashboard">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped lang="scss">
.config-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

.hero-card {
  background: var(--gray-800);
  border: 1px solid var(--gray-700);
  border-radius: var(--radius-lg);
  color: var(--gray-50);
  box-shadow: var(--shadow-sm);
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(360px, 0.9fr);
  gap: 24px;
  padding: 24px;

  h1 {
    margin: 8px 0 12px;
    font-size: var(--fs-xl);
    font-weight: 600;
    line-height: 1.2;
    color: var(--gray-50);
  }

  p {
    margin: 0;
    color: var(--gray-300);
    line-height: 1.6;
    font-size: var(--fs-base);
  }
}

.hero-side {
  display: flex;
  flex-direction: column;
  gap: 16px;
  justify-content: center;
}

.hero-status-card {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 16px;
  border-radius: var(--radius-md);
  background: var(--gray-900);
  border: 1px solid var(--gray-700);

  span,
  small {
    color: var(--gray-300);
    font-size: var(--fs-xs);
  }

  strong {
    font-size: var(--fs-md);
    font-weight: 600;
    color: var(--gray-50);
  }
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.panel {
  border-radius: var(--radius-lg);
  padding: 20px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-xs);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 20px;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 12px;

  h3 {
    margin: 0 0 4px;
    font-size: var(--fs-md);
    font-weight: 600;
    color: var(--text-primary);
  }

  p {
    margin: 0;
    color: var(--text-secondary);
    font-size: var(--fs-sm);
  }
}

:deep(.el-button) {
  border-radius: var(--radius-sm);
  font-weight: 500;
}

:deep(.el-select__wrapper),
:deep(.el-input__wrapper) {
  border-radius: var(--radius-sm);
  min-height: 32px;
  box-shadow: 0 0 0 1px var(--border-color) inset;
}

@media (max-width: 960px) {
  .hero-card {
    grid-template-columns: 1fr;
  }

  .hero-actions,
  .panel-header {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
