<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getUserList } from '@/api/user'
import {
  getApprovalProcesses,
  createApprovalProcess,
  getApprovalRequests,
  approveApprovalRequest,
  rejectApprovalRequest
} from '@/api/contract'
import {
  getDataPermissionRules,
  createDataPermissionRule,
  getAlertRules,
  createAlertRule,
  getAlerts,
  scanAlerts,
  processAlert
} from '@/api/system'

const users = ref([])
const approvalProcesses = ref([])
const approvalRequests = ref([])
const permissionRules = ref([])
const alertRules = ref([])
const alerts = ref([])

const processDialogVisible = ref(false)
const permissionDialogVisible = ref(false)
const alertRuleDialogVisible = ref(false)

const processForm = ref({
  name: '',
  action_type: 'update',
  min_amount: 0,
  steps: [{ name: '一级审批', approver_role: 'admin' }]
})

const permissionForm = ref({
  user: null,
  scope_type: 'self',
  scope_value: '',
  can_edit: false
})

const alertRuleForm = ref({
  name: '',
  rule_type: 'payment_due',
  remind_days: 7,
  owner_role: 'operator',
  level: 'medium',
  is_active: true
})

const loadData = async () => {
  const [userRes, processRes, requestRes, permissionRes, alertRuleRes, alertRes] = await Promise.all([
    getUserList({ page: 1, page_size: 200 }),
    getApprovalProcesses(),
    getApprovalRequests(),
    getDataPermissionRules(),
    getAlertRules(),
    getAlerts()
  ])
  users.value = userRes.data?.results || userRes.data || []
  approvalProcesses.value = processRes.data?.results || processRes.data || []
  approvalRequests.value = requestRes.data?.results || requestRes.data || []
  permissionRules.value = permissionRes.data?.results || permissionRes.data || []
  alertRules.value = alertRuleRes.data?.results || alertRuleRes.data || []
  alerts.value = alertRes.data?.results || alertRes.data || []
}

const submitProcess = async () => {
  await createApprovalProcess(processForm.value)
  processDialogVisible.value = false
  ElMessage.success('审批流程已创建')
  await loadData()
}

const submitPermission = async () => {
  await createDataPermissionRule(permissionForm.value)
  permissionDialogVisible.value = false
  ElMessage.success('数据权限已下发')
  await loadData()
}

const submitAlertRule = async () => {
  await createAlertRule(alertRuleForm.value)
  alertRuleDialogVisible.value = false
  ElMessage.success('预警规则已创建')
  await loadData()
}

const handleApproveRequest = async (row) => {
  await approveApprovalRequest(row.id, {})
  ElMessage.success('审批已通过')
  await loadData()
}

const handleRejectRequest = async (row) => {
  await rejectApprovalRequest(row.id, {})
  ElMessage.success('审批已驳回')
  await loadData()
}

const handleScanAlerts = async () => {
  const res = await scanAlerts()
  ElMessage.success(`预警扫描完成，新增 ${res.data?.created_count || 0} 条`)
  await loadData()
}

const handleProcessAlert = async (row) => {
  await processAlert(row.id)
  ElMessage.success('预警已处理')
  await loadData()
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="governance-page">
    <div class="hero-card">
      <div>
        <div class="eyebrow">F026 - F031</div>
        <h1>治理控制台</h1>
        <p>统一配置审批流程、行级权限、关键节点预警，并集中处理待审与待办消息。</p>
      </div>
      <div class="hero-actions">
        <el-button @click="processDialogVisible = true">新建审批流程</el-button>
        <el-button @click="permissionDialogVisible = true">配置数据权限</el-button>
        <el-button type="primary" @click="handleScanAlerts">立即扫描预警</el-button>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :xl="12">
        <div class="panel">
          <div class="panel-header">
            <div>
              <h3>审批流程配置</h3>
              <p>控制合同新增、修改、删除、变更生效路径</p>
            </div>
            <el-button type="primary" @click="processDialogVisible = true">新增流程</el-button>
          </div>
          <el-table :data="approvalProcesses">
            <el-table-column prop="name" label="流程名称" min-width="180" />
            <el-table-column prop="action_type" label="动作类型" width="110" />
            <el-table-column prop="min_amount" label="触发金额" width="120" />
            <el-table-column label="步骤数" width="100">
              <template #default="{ row }">{{ row.steps?.length || 0 }}</template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
      <el-col :xs="24" :xl="12">
        <div class="panel">
          <div class="panel-header">
            <div>
              <h3>待处理审批</h3>
              <p>合同操作需审批后才能正式生效</p>
            </div>
          </div>
          <el-table :data="approvalRequests">
            <el-table-column prop="title" label="审批标题" min-width="220" />
            <el-table-column prop="action_type" label="动作" width="90" />
            <el-table-column prop="status_display" label="状态" width="100" />
            <el-table-column label="操作" width="140">
              <template #default="{ row }">
                <el-button link type="primary" @click="handleApproveRequest(row)">通过</el-button>
                <el-button link type="danger" @click="handleRejectRequest(row)">驳回</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :xl="12">
        <div class="panel">
          <div class="panel-header">
            <div>
              <h3>行级权限策略</h3>
              <p>按人员、部门、区域和客户范围过滤合同</p>
            </div>
            <el-button type="primary" @click="permissionDialogVisible = true">新增规则</el-button>
          </div>
          <el-table :data="permissionRules">
            <el-table-column prop="username" label="用户" min-width="120" />
            <el-table-column prop="scope_type" label="范围类型" width="110" />
            <el-table-column prop="scope_value" label="范围值" min-width="120" />
            <el-table-column label="编辑权限" width="100">
              <template #default="{ row }">
                <el-tag :type="row.can_edit ? 'success' : 'info'">{{ row.can_edit ? '可编辑' : '只读' }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
      <el-col :xs="24" :xl="12">
        <div class="panel">
          <div class="panel-header">
            <div>
              <h3>预警规则</h3>
              <p>覆盖付款、交付、到期、发票与目标达成风险</p>
            </div>
            <el-button type="primary" @click="alertRuleDialogVisible = true">新增规则</el-button>
          </div>
          <el-table :data="alertRules">
            <el-table-column prop="name" label="规则名称" min-width="160" />
            <el-table-column prop="rule_type_display" label="类型" width="120" />
            <el-table-column prop="remind_days" label="提前天数" width="100" />
            <el-table-column prop="level" label="等级" width="90" />
          </el-table>
        </div>
      </el-col>
    </el-row>

    <div class="panel">
      <div class="panel-header">
        <div>
          <h3>预警消息中心</h3>
          <p>自动生成并流转处理付款到期、交付逾期、合同到期等风险提醒</p>
        </div>
      </div>
      <el-table :data="alerts">
        <el-table-column prop="title" label="消息标题" min-width="220" />
        <el-table-column prop="contract_no" label="合同编号" width="140" />
        <el-table-column prop="level" label="等级" width="90" />
        <el-table-column prop="status_display" label="状态" width="100" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleProcessAlert(row)">处理</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="processDialogVisible" title="新增审批流程" width="560px">
      <el-form :model="processForm" label-width="100px">
        <el-form-item label="流程名称"><el-input v-model="processForm.name" /></el-form-item>
        <el-form-item label="动作类型">
          <el-select v-model="processForm.action_type">
            <el-option label="新增" value="create" />
            <el-option label="修改" value="update" />
            <el-option label="删除" value="delete" />
            <el-option label="变更" value="change" />
          </el-select>
        </el-form-item>
        <el-form-item label="触发金额"><el-input-number v-model="processForm.min_amount" :min="0" :precision="2" /></el-form-item>
        <el-form-item label="审批步骤">
          <el-input
            :model-value="JSON.stringify(processForm.steps, null, 2)"
            type="textarea"
            :rows="6"
            @update:model-value="val => { try { processForm.steps = JSON.parse(val || '[]') } catch (error) {} }"
          />
        </el-form-item>
      </el-form>
      <template #footer><el-button @click="processDialogVisible = false">取消</el-button><el-button type="primary" @click="submitProcess">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="permissionDialogVisible" title="新增数据权限" width="520px">
      <el-form :model="permissionForm" label-width="100px">
        <el-form-item label="目标用户">
          <el-select v-model="permissionForm.user" filterable style="width: 100%">
            <el-option v-for="user in users" :key="user.id" :label="user.username" :value="user.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="范围类型">
          <el-select v-model="permissionForm.scope_type">
            <el-option label="本人" value="self" />
            <el-option label="部门" value="department" />
            <el-option label="区域" value="region" />
            <el-option label="客户" value="customer" />
            <el-option label="全部" value="all" />
          </el-select>
        </el-form-item>
        <el-form-item label="范围值"><el-input v-model="permissionForm.scope_value" /></el-form-item>
        <el-form-item label="可编辑"><el-switch v-model="permissionForm.can_edit" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="permissionDialogVisible = false">取消</el-button><el-button type="primary" @click="submitPermission">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="alertRuleDialogVisible" title="新增预警规则" width="520px">
      <el-form :model="alertRuleForm" label-width="100px">
        <el-form-item label="规则名称"><el-input v-model="alertRuleForm.name" /></el-form-item>
        <el-form-item label="规则类型">
          <el-select v-model="alertRuleForm.rule_type">
            <el-option label="付款到期" value="payment_due" />
            <el-option label="交付到期" value="delivery_due" />
            <el-option label="合同到期" value="contract_expiry" />
            <el-option label="发票开具" value="invoice_due" />
            <el-option label="目标达成" value="target_progress" />
          </el-select>
        </el-form-item>
        <el-form-item label="提前天数"><el-input-number v-model="alertRuleForm.remind_days" :min="1" :max="90" /></el-form-item>
        <el-form-item label="推送角色"><el-input v-model="alertRuleForm.owner_role" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="alertRuleDialogVisible = false">取消</el-button><el-button type="primary" @click="submitAlertRule">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped lang="scss">
.governance-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero-card,
.panel {
  background: linear-gradient(180deg, rgba(12, 18, 34, 0.98), rgba(24, 32, 56, 0.96));
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 18px;
  color: #f8fafc;
  box-shadow: 0 20px 45px rgba(15, 23, 42, 0.22);
}

.hero-card {
  padding: 24px 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;

  h1 {
    margin: 8px 0;
    font-size: 28px;
  }

  p {
    margin: 0;
    color: rgba(226, 232, 240, 0.72);
  }
}

.eyebrow {
  color: #7dd3fc;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.14em;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.panel {
  padding: 20px;
  margin-bottom: 16px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;

  h3 {
    margin: 0 0 4px;
  }

  p {
    margin: 0;
    color: rgba(226, 232, 240, 0.65);
    font-size: 13px;
  }
}

:deep(.el-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(148, 163, 184, 0.08);
  --el-table-border-color: rgba(148, 163, 184, 0.12);
  --el-table-text-color: #e2e8f0;
  --el-table-header-text-color: #cbd5e1;
}

@media (max-width: 960px) {
  .hero-card,
  .panel-header {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
