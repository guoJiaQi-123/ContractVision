<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createContract, updateContract, getContractDetail } from '@/api/contract'
import { getSalespersonOptions, getDepartmentOptions, getProductTypeOptions, getCustomerOptions, generateContractNo, createCustomer, generateCustomerCode } from '@/api/enterprise'
import { ArrowLeft, Plus, Refresh } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const submitLoading = ref(false)
const fieldErrors = reactive({})

const salespersonList = ref([])
const departmentList = ref([])
const productTypeList = ref([])
const customerList = ref([])

const customerDialogVisible = ref(false)
const customerFormRef = ref(null)
const customerFormLoading = ref(false)
const customerForm = reactive({
  name: '',
  code: '',
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
const customerFormRules = {
  name: [{ required: true, message: '请输入客户名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入客户编码', trigger: 'blur' }]
}

const isEdit = computed(() => !!route.params.id)
const pageTitle = computed(() => isEdit.value ? '编辑合同' : '新建合同')

const form = reactive({
  contract_no: '',
  title: '',
  client_name: '',
  client_contact: '',
  product_type: '',
  amount: null,
  currency: 'CNY',
  region: '',
  sign_date: '',
  start_date: '',
  end_date: '',
  status: 'draft',
  payment_status: 'unpaid',
  delivery_status: 'pending',
  salesperson: '',
  department: '',
  description: '',
  milestones: []
})

const rules = {
  contract_no: [{ required: true, message: '请输入合同编号', trigger: 'blur' }],
  title: [{ required: true, message: '请输入合同标题', trigger: 'blur' }],
  client_name: [{ required: true, message: '请选择客户名称', trigger: 'change' }],
  amount: [
    { required: true, message: '请输入合同金额', trigger: 'blur' },
    { type: 'number', min: 0.01, message: '金额必须大于零', trigger: 'blur' }
  ]
}

const statusOptions = [
  { label: '草稿', value: 'draft' },
  { label: '生效中', value: 'active' },
  { label: '已完成', value: 'completed' },
  { label: '已终止', value: 'terminated' },
  { label: '已作废', value: 'voided' }
]

const paymentStatusOptions = [
  { label: '未付款', value: 'unpaid' },
  { label: '部分付款', value: 'partial' },
  { label: '已付清', value: 'paid' }
]

const deliveryStatusOptions = [
  { label: '待交付', value: 'pending' },
  { label: '交付中', value: 'delivering' },
  { label: '已交付', value: 'delivered' }
]

const currencyOptions = [
  { label: '人民币(CNY)', value: 'CNY' },
  { label: '美元(USD)', value: 'USD' },
  { label: '欧元(EUR)', value: 'EUR' }
]

const regionOptions = ['华东', '华南', '华北', '华中', '西南', '西北', '东北']

const milestoneNodeTypeOptions = [
  { label: '交付节点', value: 'delivery' },
  { label: '付款节点', value: 'payment' },
  { label: '验收节点', value: 'acceptance' },
  { label: '自定义节点', value: 'custom' }
]

const clearFieldError = (field) => {
  fieldErrors[field] = ''
}

const fetchSalespersonOptions = async () => {
  try {
    const res = await getSalespersonOptions()
    salespersonList.value = res.data || []
  } catch {}
}

const fetchDepartmentOptions = async () => {
  try {
    const res = await getDepartmentOptions()
    departmentList.value = res.data || []
  } catch {}
}

const fetchProductTypeOptions = async () => {
  try {
    const res = await getProductTypeOptions()
    productTypeList.value = res.data || []
  } catch {}
}

const fetchCustomerOptions = async () => {
  try {
    const res = await getCustomerOptions()
    customerList.value = res.data || []
  } catch {}
}

const handleGenerateContractNo = async () => {
  try {
    const res = await generateContractNo()
    form.contract_no = res.data.contract_no
    clearFieldError('contract_no')
  } catch {
    ElMessage.error('生成合同编号失败')
  }
}

const handleCustomerChange = (val) => {
  const customer = customerList.value.find(c => c.name === val)
  if (customer) {
    form.client_contact = customer.contact_person || ''
  }
}

const handleOpenCustomerDialog = () => {
  Object.assign(customerForm, {
    name: '', code: '', short_name: '', level: 'normal',
    contact_person: '', contact_phone: '', contact_email: '',
    address: '', region: '', industry: '', description: '', is_active: true
  })
  customerDialogVisible.value = true
  handleGenerateCustomerCode()
}

const handleGenerateCustomerCode = async () => {
  try {
    const res = await generateCustomerCode()
    customerForm.code = res.data.code
  } catch {}
}

const handleCustomerSubmit = async () => {
  try {
    await customerFormRef.value.validate()
  } catch { return }
  customerFormLoading.value = true
  try {
    await createCustomer({ ...customerForm })
    ElMessage.success('客户创建成功')
    customerDialogVisible.value = false
    await fetchCustomerOptions()
    form.client_name = customerForm.name
    form.client_contact = customerForm.contact_person || ''
  } catch {
    ElMessage.error('创建客户失败')
  } finally {
    customerFormLoading.value = false
  }
}

const handleSalespersonChange = (val) => {
  const user = salespersonList.value.find(u => u.id === val)
  if (user && user.department) {
    form.department = user.department
  }
}

const addMilestone = () => {
  form.milestones.push({
    node_type: 'delivery',
    name: '',
    progress_weight: 25,
    planned_date: '',
    remark: ''
  })
}

const removeMilestone = (index) => {
  form.milestones.splice(index, 1)
}

const loadDetail = async () => {
  if (!isEdit.value) return
  loading.value = true
  try {
    const res = await getContractDetail(route.params.id)
    const data = res.data || res
    Object.keys(form).forEach(key => {
      if (key === 'milestones') {
        form.milestones = data.milestones ? data.milestones.map(m => ({
          node_type: m.node_type || 'delivery',
          name: m.name || '',
          progress_weight: m.progress_weight || 25,
          planned_date: m.planned_date || '',
          remark: m.remark || ''
        })) : []
      } else if (data[key] !== undefined && data[key] !== null) {
        form[key] = key === 'amount' ? Number(data[key]) : data[key]
      }
    })
  } catch {
    ElMessage.error('加载合同信息失败')
    router.push('/contract/list')
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submitLoading.value = true
  Object.keys(fieldErrors).forEach(k => fieldErrors[k] = '')

  try {
    const submitData = { ...form }
    if (isEdit.value) {
      await updateContract(route.params.id, submitData)
      ElMessage.success('合同更新成功')
    } else {
      await createContract(submitData)
      ElMessage.success('合同创建成功')
    }
    router.push('/contract/list')
  } catch (error) {
    const res = error.response?.data
    if (res?.data && typeof res.data === 'object') {
      Object.entries(res.data).forEach(([key, val]) => {
        fieldErrors[key] = Array.isArray(val) ? val[0] : val
      })
    }
  } finally {
    submitLoading.value = false
  }
}

const goBack = () => {
  router.push('/contract/list')
}

onMounted(() => {
  fetchSalespersonOptions()
  fetchDepartmentOptions()
  fetchProductTypeOptions()
  fetchCustomerOptions()
  loadDetail()
})
</script>

<template>
  <div class="contract-form-container">
    <div class="page-header">
      <div class="header-left">
        <el-button class="back-btn" @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
        <div class="header-info">
          <h1>{{ pageTitle }}</h1>
          <p class="subtitle" v-if="isEdit">编辑合同信息</p>
          <p class="subtitle" v-else>填写合同基本信息</p>
        </div>
      </div>
    </div>

    <div class="card" v-loading="loading">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" label-position="top">
        <h3 class="section-title">基本信息</h3>
        <el-row :gutter="24">
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="合同编号" prop="contract_no" :error="fieldErrors.contract_no">
              <div class="input-with-btn">
                <el-input v-model="form.contract_no" placeholder="请输入合同编号" :disabled="isEdit" @input="clearFieldError('contract_no')" />
                <el-button v-if="!isEdit" type="primary" :icon="Refresh" @click="handleGenerateContractNo" class="inline-btn">生成</el-button>
              </div>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="合同标题" prop="title" :error="fieldErrors.title">
              <el-input v-model="form.title" placeholder="请输入合同标题" @input="clearFieldError('title')" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="合同状态" prop="status">
              <el-select v-model="form.status" style="width: 100%">
                <el-option v-for="opt in statusOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <h3 class="section-title">客户信息</h3>
        <el-row :gutter="24">
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="客户名称" prop="client_name" :error="fieldErrors.client_name">
              <div class="input-with-btn">
                <el-select
                  v-model="form.client_name"
                  placeholder="请选择客户"
                  filterable
                  style="flex: 1"
                  @change="handleCustomerChange"
                >
                  <el-option v-for="c in customerList" :key="c.id" :label="c.name" :value="c.name" />
                </el-select>
                <el-button type="primary" :icon="Plus" @click="handleOpenCustomerDialog" class="inline-btn">新增</el-button>
              </div>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="联系人" prop="client_contact">
              <el-input v-model="form.client_contact" placeholder="请输入联系人" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="产品类型" prop="product_type">
              <el-select v-model="form.product_type" placeholder="请选择产品类型" filterable style="width: 100%">
                <el-option v-for="pt in productTypeList" :key="pt.id" :label="pt.name" :value="pt.name" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <h3 class="section-title">金额信息</h3>
        <el-row :gutter="24">
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="合同金额" prop="amount" :error="fieldErrors.amount">
              <el-input-number
                v-model="form.amount"
                placeholder="请输入合同金额"
                :min="0"
                :precision="2"
                :controls="false"
                style="width: 100%"
                @change="clearFieldError('amount')"
              />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="货币" prop="currency">
              <el-select v-model="form.currency" style="width: 100%">
                <el-option v-for="opt in currencyOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="付款状态" prop="payment_status">
              <el-select v-model="form.payment_status" style="width: 100%">
                <el-option v-for="opt in paymentStatusOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <h3 class="section-title">日期与区域</h3>
        <el-row :gutter="24">
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="签订日期" prop="sign_date">
              <el-date-picker v-model="form.sign_date" type="date" placeholder="选择签订日期" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="开始日期" prop="start_date">
              <el-date-picker v-model="form.start_date" type="date" placeholder="选择开始日期" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="结束日期" prop="end_date">
              <el-date-picker v-model="form.end_date" type="date" placeholder="选择结束日期" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="24">
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="所属区域" prop="region">
              <el-select v-model="form.region" placeholder="选择区域" filterable allow-create style="width: 100%">
                <el-option v-for="r in regionOptions" :key="r" :label="r" :value="r" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="交付状态" prop="delivery_status">
              <el-select v-model="form.delivery_status" style="width: 100%">
                <el-option v-for="opt in deliveryStatusOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <h3 class="section-title">人员信息</h3>
        <el-row :gutter="24">
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="销售人员" prop="salesperson">
              <el-select v-model="form.salesperson" placeholder="请选择销售人员" filterable style="width: 100%" @change="handleSalespersonChange">
                <el-option v-for="u in salespersonList" :key="u.id" :label="u.username" :value="u.username">
                  <span>{{ u.username }}</span>
                  <span style="float: right; color: var(--text-muted); font-size: 12px">{{ u.role === 'admin' ? '管理员' : '操作员' }}</span>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="所属部门" prop="department">
              <el-select v-model="form.department" placeholder="请选择部门" filterable style="width: 100%">
                <el-option v-for="d in departmentList" :key="d.id" :label="d.name" :value="d.name" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <h3 class="section-title">
          <span>履约进度节点</span>
          <el-button type="primary" size="small" :icon="Plus" @click="addMilestone" style="margin-left: 12px">添加节点</el-button>
        </h3>
        <div v-if="form.milestones.length === 0" class="empty-milestones">
          <p>暂无履约进度节点，点击"添加节点"创建</p>
        </div>
        <div v-for="(milestone, index) in form.milestones" :key="index" class="milestone-item">
          <el-row :gutter="16">
            <el-col :xs="24" :sm="12" :md="6">
              <el-form-item label="节点类型" :prop="`milestones.${index}.node_type`">
                <el-select v-model="milestone.node_type" style="width: 100%">
                  <el-option v-for="opt in milestoneNodeTypeOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12" :md="6">
              <el-form-item label="节点名称" :prop="`milestones.${index}.name`">
                <el-input v-model="milestone.name" placeholder="请输入节点名称" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12" :md="4">
              <el-form-item label="权重(%)" :prop="`milestones.${index}.progress_weight`">
                <el-input-number v-model="milestone.progress_weight" :min="1" :max="100" :controls="false" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12" :md="5">
              <el-form-item label="计划完成时间" :prop="`milestones.${index}.planned_date`">
                <el-date-picker v-model="milestone.planned_date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12" :md="3" class="milestone-actions">
              <el-form-item label=" ">
                <el-button type="danger" text @click="removeMilestone(index)">删除</el-button>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="16">
            <el-col :span="24">
              <el-form-item label="备注" :prop="`milestones.${index}.remark`">
                <el-input v-model="milestone.remark" placeholder="请输入备注" />
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <h3 class="section-title">补充信息</h3>
        <el-row :gutter="24">
          <el-col :span="24">
            <el-form-item label="合同描述" prop="description">
              <el-input v-model="form.description" type="textarea" :rows="4" placeholder="请输入合同描述" />
            </el-form-item>
          </el-col>
        </el-row>

        <div class="form-actions">
          <el-button @click="goBack">取消</el-button>
          <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
            {{ isEdit ? '保存修改' : '创建合同' }}
          </el-button>
        </div>
      </el-form>
    </div>

    <el-dialog v-model="customerDialogVisible" title="新增客户" width="600px" :close-on-click-modal="false">
      <el-form ref="customerFormRef" :model="customerForm" :rules="customerFormRules" label-width="100px" label-position="top">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="客户编码" prop="code">
              <div style="display: flex; gap: 8px; width: 100%">
                <el-input v-model="customerForm.code" placeholder="请输入客户编码" style="flex: 1" />
                <el-button type="primary" @click="handleGenerateCustomerCode">生成</el-button>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="客户名称" prop="name">
              <el-input v-model="customerForm.name" placeholder="请输入客户名称" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="简称">
              <el-input v-model="customerForm.short_name" placeholder="请输入简称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="客户等级">
              <el-select v-model="customerForm.level" style="width: 100%">
                <el-option label="VIP客户" value="vip" />
                <el-option label="普通客户" value="normal" />
                <el-option label="潜在客户" value="potential" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="联系人">
              <el-input v-model="customerForm.contact_person" placeholder="请输入联系人" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系电话">
              <el-input v-model="customerForm.contact_phone" placeholder="请输入联系电话" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="联系邮箱">
              <el-input v-model="customerForm.contact_email" placeholder="请输入联系邮箱" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="行业">
              <el-input v-model="customerForm.industry" placeholder="请输入行业" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="区域">
              <el-input v-model="customerForm.region" placeholder="请输入区域" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="是否启用">
              <el-switch v-model="customerForm.is_active" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="地址">
          <el-input v-model="customerForm.address" placeholder="请输入地址" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="customerDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="customerFormLoading" @click="handleCustomerSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.contract-form-container {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 24px;

    .header-left {
      display: flex;
      align-items: flex-start;
      gap: 16px;
    }

    .back-btn {
      border-radius: var(--radius-md);
      font-size: var(--fs-base);
      padding: 8px 16px;
      border: 1px solid var(--border-color);
      background: var(--card-bg);
      color: var(--text-secondary);
      transition: all var(--transition-fast);

      &:hover {
        border-color: var(--primary);
        color: var(--primary);
      }
    }

    .header-info {
      h1 {
        font-size: var(--fs-xl);
        font-weight: 700;
        color: var(--text-primary);
        margin: 0;
      }

      .subtitle {
        margin: 4px 0 0;
        font-size: var(--fs-base);
        color: var(--text-muted);
      }
    }
  }

  .card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 32px;
    box-shadow: var(--shadow-xs);
  }

  .section-title {
    font-size: var(--fs-md);
    font-weight: 600;
    color: var(--text-primary);
    margin: 24px 0 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border-color);
    display: flex;
    align-items: center;

    &:first-child {
      margin-top: 0;
    }
  }

  .input-with-btn {
    display: flex;
    gap: 8px;
    width: 100%;

    .el-input,
    .el-select {
      flex: 1;
    }

    .inline-btn {
      flex-shrink: 0;
      border-radius: var(--radius-sm);
    }
  }

  .empty-milestones {
    text-align: center;
    padding: 32px 0;
    color: var(--text-muted);
    font-size: var(--fs-base);
    border: 1px dashed var(--border-color);
    border-radius: var(--radius-md);
    margin-bottom: 16px;
  }

  .milestone-item {
    background: var(--bg-color, #f8f9fa);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: 16px 16px 0;
    margin-bottom: 12px;

    .milestone-actions {
      :deep(.el-form-item__content) {
        justify-content: flex-end;
      }
    }
  }

  .form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    margin-top: 32px;
    padding-top: 24px;
    border-top: 1px solid var(--border-color);
  }
}
</style>
