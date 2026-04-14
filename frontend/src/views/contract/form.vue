<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createContract, updateContract, getContractDetail } from '@/api/contract'
import { ArrowLeft } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const submitLoading = ref(false)
const fieldErrors = reactive({})

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
  description: ''
})

const rules = {
  contract_no: [{ required: true, message: '请输入合同编号', trigger: 'blur' }],
  title: [{ required: true, message: '请输入合同标题', trigger: 'blur' }],
  client_name: [{ required: true, message: '请输入客户名称', trigger: 'blur' }],
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

const clearFieldError = (field) => {
  fieldErrors[field] = ''
}

const loadDetail = async () => {
  if (!isEdit.value) return
  loading.value = true
  try {
    const res = await getContractDetail(route.params.id)
    const data = res.data || res
    Object.keys(form).forEach(key => {
      if (data[key] !== undefined && data[key] !== null) {
        form[key] = data[key]
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

onMounted(loadDetail)
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
              <el-input v-model="form.contract_no" placeholder="请输入合同编号" :disabled="isEdit" @input="clearFieldError('contract_no')" />
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
              <el-input v-model="form.client_name" placeholder="请输入客户名称" @input="clearFieldError('client_name')" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="联系人" prop="client_contact">
              <el-input v-model="form.client_contact" placeholder="请输入联系人" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="产品类型" prop="product_type">
              <el-input v-model="form.product_type" placeholder="请输入产品类型" />
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
              <el-input v-model="form.salesperson" placeholder="请输入销售人员" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="所属部门" prop="department">
              <el-input v-model="form.department" placeholder="请输入部门" />
            </el-form-item>
          </el-col>
        </el-row>

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
      border-radius: 8px;
      font-size: 14px;
      padding: 8px 16px;
      border: 1px solid var(--border-color);
      background: var(--card-bg);
      color: var(--text-secondary);
      transition: all 0.2s;

      &:hover {
        border-color: var(--primary-color);
        color: var(--primary-color);
      }
    }

    .header-info {
      h1 {
        font-size: 24px;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0;
      }

      .subtitle {
        margin: 4px 0 0;
        font-size: 14px;
        color: var(--text-muted);
      }
    }
  }

  .card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 32px;
  }

  .section-title {
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 24px 0 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border-color);

    &:first-child {
      margin-top: 0;
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
