<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getContractList,
  getContractDetail,
  getContractFulfillment,
  getPaymentPlans,
  getPaymentPlanOverview,
  createPaymentPlan,
  markPaymentPlanPaid,
  getContractMilestones,
  createContractMilestone,
  completeContractMilestone,
  getContractChangeRequests,
  createContractChangeRequest,
  approveContractChangeRequest,
  rejectContractChangeRequest,
  getContractRenewalSummary,
  renewContract,
  terminateContract,
  getContractQualityReport,
  recalculateContractQuality,
  getDuplicateContractGroups,
  mergeDuplicateContracts
} from '@/api/contract'

const loading = ref(false)
const contractOptions = ref([])
const selectedContractId = ref(null)
const contractDetail = ref({})
const fulfillment = ref({ completion_rate: 0, risk_count: 0, milestone_count: 0, nodes: [] })
const paymentPlans = ref([])
const paymentOverview = ref({})
const changeRequests = ref([])
const renewalSummary = ref({ summary: {}, list: [] })
const qualityReport = ref({ summary: {}, list: [] })
const duplicateGroups = ref([])

const milestoneDialogVisible = ref(false)
const paymentDialogVisible = ref(false)
const changeDialogVisible = ref(false)

const milestoneForm = ref({
  contract: null,
  node_type: 'delivery',
  name: '',
  progress_weight: 25,
  planned_date: '',
  remark: ''
})

const paymentForm = ref({
  contract: null,
  phase: '',
  ratio: 0,
  amount: 0,
  due_date: '',
  invoice_status: 'pending',
  remark: ''
})

const changeForm = ref({
  contract: null,
  change_type: 'core',
  title: '',
  reason: '',
  effective_date: '',
  after_snapshot: {}
})

const selectedContract = computed(() => {
  return contractOptions.value.find(item => item.id === selectedContractId.value) || {}
})

const loadContracts = async () => {
  const res = await getContractList({ page: 1, page_size: 200 })
  const list = res.data?.results || res.data?.list || res.data || []
  contractOptions.value = list
  if (!selectedContractId.value && list.length) {
    selectedContractId.value = list[0].id
  }
}

const loadContractPanel = async () => {
  if (!selectedContractId.value) return
  loading.value = true
  try {
    const [detailRes, fulfillmentRes, paymentsRes, paymentOverviewRes, changesRes, qualityRes] = await Promise.all([
      getContractDetail(selectedContractId.value),
      getContractFulfillment(selectedContractId.value),
      getPaymentPlans({ contract: selectedContractId.value }),
      getPaymentPlanOverview({ contract: selectedContractId.value }),
      getContractChangeRequests({ contract: selectedContractId.value }),
      getContractQualityReport({ contract: selectedContractId.value })
    ])

    contractDetail.value = detailRes.data || {}
    fulfillment.value = fulfillmentRes.data || {}
    paymentPlans.value = paymentsRes.data?.results || paymentsRes.data || []
    paymentOverview.value = paymentOverviewRes.data || {}
    changeRequests.value = changesRes.data?.results || changesRes.data || []
    qualityReport.value = qualityRes.data || { summary: {}, list: [] }
  } finally {
    loading.value = false
  }
}

const loadGlobalPanels = async () => {
  const [renewRes, duplicateRes] = await Promise.all([
    getContractRenewalSummary({ days: 45 }),
    getDuplicateContractGroups()
  ])
  renewalSummary.value = renewRes.data || { summary: {}, list: [] }
  duplicateGroups.value = duplicateRes.data?.groups || []
}

const handleContractChange = async () => {
  await loadContractPanel()
}

const openMilestoneDialog = () => {
  milestoneForm.value = {
    contract: selectedContractId.value,
    node_type: 'delivery',
    name: '',
    progress_weight: 25,
    planned_date: '',
    remark: ''
  }
  milestoneDialogVisible.value = true
}

const openPaymentDialog = () => {
  paymentForm.value = {
    contract: selectedContractId.value,
    phase: '',
    ratio: 0,
    amount: 0,
    due_date: '',
    invoice_status: 'pending',
    remark: ''
  }
  paymentDialogVisible.value = true
}

const openChangeDialog = () => {
  changeForm.value = {
    contract: selectedContractId.value,
    change_type: 'core',
    title: '',
    reason: '',
    effective_date: '',
    after_snapshot: {}
  }
  changeDialogVisible.value = true
}

const submitMilestone = async () => {
  await createContractMilestone(milestoneForm.value)
  milestoneDialogVisible.value = false
  ElMessage.success('履约节点已创建')
  await loadContractPanel()
}

const submitPayment = async () => {
  await createPaymentPlan(paymentForm.value)
  paymentDialogVisible.value = false
  ElMessage.success('付款节点已创建')
  await loadContractPanel()
}

const submitChangeRequest = async () => {
  await createContractChangeRequest(changeForm.value)
  changeDialogVisible.value = false
  ElMessage.success('变更申请已提交')
  await loadContractPanel()
}

const handleCompleteMilestone = async (row) => {
  await completeContractMilestone(row.id, { actual_date: new Date().toISOString().slice(0, 10) })
  ElMessage.success('节点已完成')
  await loadContractPanel()
}

const handleMarkPaid = async (row) => {
  await markPaymentPlanPaid(row.id, {
    paid_date: new Date().toISOString().slice(0, 10),
    actual_amount: row.amount
  })
  ElMessage.success('回款状态已更新')
  await loadContractPanel()
}

const handleApproveChange = async (row) => {
  await approveContractChangeRequest(row.id, {})
  ElMessage.success('变更已处理')
  await loadContractPanel()
}

const handleRejectChange = async (row) => {
  await rejectContractChangeRequest(row.id, {})
  ElMessage.success('变更已驳回')
  await loadContractPanel()
}

const handleRenew = async () => {
  await renewContract(selectedContractId.value, {
    renewal_contract_no: `${selectedContract.value.contract_no || 'CV'}-R`,
    renewal_reminder_days: 30
  })
  ElMessage.success('续签状态已更新')
  await Promise.all([loadContractPanel(), loadGlobalPanels()])
}

const handleTerminate = async (status) => {
  await terminateContract(selectedContractId.value, {
    status,
    reason: status === 'voided' ? '业务调整作废' : '提前终止',
    effective_date: new Date().toISOString().slice(0, 10)
  })
  ElMessage.success('合同状态已更新')
  await Promise.all([loadContractPanel(), loadGlobalPanels()])
}

const handleRecalculateQuality = async () => {
  await recalculateContractQuality(selectedContractId.value)
  ElMessage.success('质量评分已刷新')
  await loadContractPanel()
}

const handleMergeDuplicates = async (group) => {
  const duplicateIds = group.contracts.map(item => item.id).filter(id => id !== group.primary_id)
  await mergeDuplicateContracts({
    primary_id: group.primary_id,
    duplicate_ids: duplicateIds
  })
  ElMessage.success('重复合同已合并')
  await Promise.all([loadContracts(), loadGlobalPanels(), loadContractPanel()])
}

onMounted(async () => {
  await loadContracts()
  await Promise.all([loadContractPanel(), loadGlobalPanels()])
})
</script>

<template>
  <div class="lifecycle-page">
    <div class="hero-card">
      <div>
        <div class="eyebrow">F021 - F025 / F029 - F030</div>
        <h1>合同履约中心</h1>
        <p>集中管理履约节点、分期回款、续签到期、变更审批、终止归档与数据质量治理。</p>
      </div>
      <div class="hero-actions">
        <el-select v-model="selectedContractId" placeholder="选择合同" style="width: 320px" @change="handleContractChange">
          <el-option
            v-for="item in contractOptions"
            :key="item.id"
            :label="`${item.contract_no} · ${item.title}`"
            :value="item.id"
          />
        </el-select>
      </div>
    </div>

    <el-row :gutter="16" class="metric-row">
      <el-col :xs="24" :md="6">
        <div class="metric-card">
          <span class="metric-label">履约完成率</span>
          <strong>{{ fulfillment.completion_rate || 0 }}%</strong>
        </div>
      </el-col>
      <el-col :xs="24" :md="6">
        <div class="metric-card">
          <span class="metric-label">履约风险节点</span>
          <strong>{{ fulfillment.risk_count || 0 }}</strong>
        </div>
      </el-col>
      <el-col :xs="24" :md="6">
        <div class="metric-card">
          <span class="metric-label">待付款节点</span>
          <strong>{{ paymentOverview.pending_count || 0 }}</strong>
        </div>
      </el-col>
      <el-col :xs="24" :md="6">
        <div class="metric-card">
          <span class="metric-label">数据质量评分</span>
          <strong>{{ contractDetail.quality_score || 0 }}</strong>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :xl="14">
        <div class="panel">
          <div class="panel-header">
            <div>
              <h3>履约进度节点</h3>
              <p>交付、付款、验收节点可视化追踪</p>
            </div>
            <el-button type="primary" @click="openMilestoneDialog">新增节点</el-button>
          </div>
          <el-table v-loading="loading" :data="fulfillment.nodes || []">
            <el-table-column prop="name" label="节点名称" min-width="180" />
            <el-table-column prop="node_type" label="类型" width="110" />
            <el-table-column prop="planned_date" label="计划时间" width="120" />
            <el-table-column prop="actual_date" label="完成时间" width="120" />
            <el-table-column label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="row.is_risk ? 'danger' : row.status === 'completed' ? 'success' : 'info'">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button link type="primary" @click="handleCompleteMilestone(row)">完成</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
      <el-col :xs="24" :xl="10">
        <div class="panel">
          <div class="panel-header">
            <div>
              <h3>续签与归档</h3>
              <p>临近到期、续签关联、终止作废控制</p>
            </div>
            <div class="inline-actions">
              <el-button plain @click="handleRenew">登记续签</el-button>
              <el-button plain type="warning" @click="handleTerminate('terminated')">终止</el-button>
              <el-button plain type="danger" @click="handleTerminate('voided')">作废</el-button>
            </div>
          </div>
          <div class="summary-grid">
            <div class="summary-item">
              <span>临近到期</span>
              <strong>{{ renewalSummary.summary.expiring_soon || 0 }}</strong>
            </div>
            <div class="summary-item">
              <span>已到期</span>
              <strong>{{ renewalSummary.summary.expired || 0 }}</strong>
            </div>
            <div class="summary-item">
              <span>已续签</span>
              <strong>{{ renewalSummary.summary.renewed || 0 }}</strong>
            </div>
            <div class="summary-item">
              <span>未续签</span>
              <strong>{{ renewalSummary.summary.not_renewed || 0 }}</strong>
            </div>
          </div>
          <el-table :data="renewalSummary.list || []" size="small">
            <el-table-column prop="contract_no" label="合同编号" min-width="140" />
            <el-table-column prop="end_date" label="到期日" width="120" />
            <el-table-column prop="renewal_status_display" label="续签状态" width="110" />
          </el-table>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :xl="12">
        <div class="panel">
          <div class="panel-header">
            <div>
              <h3>付款逾期管理</h3>
              <p>分期计划、开票状态、逾期等级与凭证</p>
            </div>
            <el-button type="primary" @click="openPaymentDialog">新增付款节点</el-button>
          </div>
          <el-table v-loading="loading" :data="paymentPlans">
            <el-table-column prop="phase" label="阶段" min-width="130" />
            <el-table-column prop="amount" label="金额" width="120" />
            <el-table-column prop="due_date" label="应付日期" width="120" />
            <el-table-column prop="invoice_status_display" label="开票状态" width="110" />
            <el-table-column prop="overdue_level" label="逾期等级" width="110" />
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button link type="success" @click="handleMarkPaid(row)">到账</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
      <el-col :xs="24" :xl="12">
        <div class="panel">
          <div class="panel-header">
            <div>
              <h3>变更与补充协议</h3>
              <p>留存前后快照，支持发起变更审批</p>
            </div>
            <el-button type="primary" @click="openChangeDialog">发起变更</el-button>
          </div>
          <el-table v-loading="loading" :data="changeRequests">
            <el-table-column prop="title" label="申请标题" min-width="180" />
            <el-table-column prop="change_type_display" label="类型" width="110" />
            <el-table-column prop="effective_date" label="生效日" width="120" />
            <el-table-column prop="status_display" label="状态" width="110" />
            <el-table-column label="操作" width="140">
              <template #default="{ row }">
                <el-button link type="primary" @click="handleApproveChange(row)">通过</el-button>
                <el-button link type="danger" @click="handleRejectChange(row)">驳回</el-button>
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
              <h3>数据质量评分</h3>
              <p>自动识别关键字段缺陷与整改建议</p>
            </div>
            <el-button plain @click="handleRecalculateQuality">重新校验</el-button>
          </div>
          <el-table :data="qualityReport.list || []">
            <el-table-column prop="contract_no" label="合同编号" min-width="140" />
            <el-table-column prop="quality_score" label="评分" width="90" />
            <el-table-column label="问题数" width="90">
              <template #default="{ row }">{{ row.quality_issues?.length || 0 }}</template>
            </el-table-column>
            <el-table-column label="整改建议" min-width="260">
              <template #default="{ row }">
                <span>{{ row.quality_issues?.[0]?.suggestion || '无' }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
      <el-col :xs="24" :xl="12">
        <div class="panel">
          <div class="panel-header">
            <div>
              <h3>重复合同识别</h3>
              <p>按编号、客户、金额相似度自动分组</p>
            </div>
          </div>
          <div v-if="duplicateGroups.length === 0" class="empty-state">当前未识别到重复合同组</div>
          <div v-for="group in duplicateGroups" :key="group.primary_id" class="duplicate-group">
            <div class="duplicate-header">
              <div>
                <strong>主合同 #{{ group.primary_id }}</strong>
                <span>共 {{ group.contracts.length }} 条疑似重复记录</span>
              </div>
              <el-button size="small" type="primary" @click="handleMergeDuplicates(group)">一键合并</el-button>
            </div>
            <div class="duplicate-list">
              <span v-for="item in group.contracts" :key="item.id" class="duplicate-chip">
                {{ item.contract_no || '无编号' }} / 相似度 {{ item.similarity }}
              </span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-dialog v-model="milestoneDialogVisible" title="新增履约节点" width="520px">
      <el-form :model="milestoneForm" label-width="96px">
        <el-form-item label="节点类型"><el-select v-model="milestoneForm.node_type"><el-option label="交付" value="delivery" /><el-option label="付款" value="payment" /><el-option label="验收" value="acceptance" /></el-select></el-form-item>
        <el-form-item label="节点名称"><el-input v-model="milestoneForm.name" /></el-form-item>
        <el-form-item label="计划时间"><el-date-picker v-model="milestoneForm.planned_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" /></el-form-item>
        <el-form-item label="权重"><el-input-number v-model="milestoneForm.progress_weight" :min="1" :max="100" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="milestoneForm.remark" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="milestoneDialogVisible = false">取消</el-button><el-button type="primary" @click="submitMilestone">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="paymentDialogVisible" title="新增付款节点" width="520px">
      <el-form :model="paymentForm" label-width="96px">
        <el-form-item label="付款阶段"><el-input v-model="paymentForm.phase" /></el-form-item>
        <el-form-item label="付款比例"><el-input-number v-model="paymentForm.ratio" :min="0" :max="100" /></el-form-item>
        <el-form-item label="金额"><el-input-number v-model="paymentForm.amount" :min="0" :precision="2" /></el-form-item>
        <el-form-item label="应付日期"><el-date-picker v-model="paymentForm.due_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="paymentForm.remark" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="paymentDialogVisible = false">取消</el-button><el-button type="primary" @click="submitPayment">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="changeDialogVisible" title="发起合同变更" width="640px">
      <el-form :model="changeForm" label-width="96px">
        <el-form-item label="申请标题"><el-input v-model="changeForm.title" /></el-form-item>
        <el-form-item label="变更类型"><el-select v-model="changeForm.change_type"><el-option label="核心变更" value="core" /><el-option label="补充协议" value="supplement" /></el-select></el-form-item>
        <el-form-item label="生效日期"><el-date-picker v-model="changeForm.effective_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" /></el-form-item>
        <el-form-item label="变更原因"><el-input v-model="changeForm.reason" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="变更内容">
          <el-input
            :model-value="JSON.stringify(changeForm.after_snapshot, null, 2)"
            type="textarea"
            :rows="6"
            @update:model-value="val => { try { changeForm.after_snapshot = JSON.parse(val || '{}') } catch (error) {} }"
          />
        </el-form-item>
      </el-form>
      <template #footer><el-button @click="changeDialogVisible = false">取消</el-button><el-button type="primary" @click="submitChangeRequest">提交</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped lang="scss">
.lifecycle-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero-card,
.metric-card,
.panel {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(247, 249, 252, 0.98));
  border: 1px solid rgba(17, 24, 39, 0.08);
  border-radius: 18px;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
}

.hero-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 24px 28px;

  h1 {
    margin: 6px 0;
    font-size: 28px;
  }

  p {
    margin: 0;
    color: #526072;
  }
}

.eyebrow {
  color: #165dff;
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.metric-row {
  margin-bottom: 0;
}

.metric-card {
  padding: 18px 20px;
  min-height: 110px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  margin-bottom: 16px;

  strong {
    font-size: 30px;
    color: #0f172a;
  }
}

.metric-label {
  color: #64748b;
  font-size: 13px;
}

.panel {
  padding: 20px;
  margin-bottom: 16px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;

  h3 {
    margin: 0 0 4px;
    font-size: 18px;
  }

  p {
    margin: 0;
    color: #6b7280;
    font-size: 13px;
  }
}

.inline-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.summary-item {
  background: rgba(22, 93, 255, 0.06);
  border-radius: 14px;
  padding: 14px 16px;

  span {
    display: block;
    color: #64748b;
    margin-bottom: 8px;
    font-size: 13px;
  }

  strong {
    font-size: 24px;
  }
}

.empty-state {
  padding: 28px;
  text-align: center;
  color: #64748b;
}

.duplicate-group {
  border: 1px dashed rgba(22, 93, 255, 0.25);
  border-radius: 14px;
  padding: 14px;
  margin-bottom: 12px;
}

.duplicate-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;

  span {
    margin-left: 8px;
    color: #64748b;
    font-size: 13px;
  }
}

.duplicate-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.duplicate-chip {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.06);
  color: #334155;
  font-size: 12px;
}

@media (max-width: 960px) {
  .hero-card,
  .panel-header,
  .duplicate-header {
    flex-direction: column;
    align-items: stretch;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>
