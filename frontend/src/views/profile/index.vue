<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getProfile, updateProfile } from '@/api/user'
import { changePassword } from '@/api/auth'
import { useUserStore } from '@/store/modules/user'
import { UserFilled } from '@element-plus/icons-vue'

const userStore = useUserStore()
const activeTab = ref('info')
const loading = ref(false)

const profileData = ref({})
const profileForm = reactive({
  email: '',
  phone: '',
  company_name: ''
})
const profileFormRef = ref(null)
const profileLoading = ref(false)
const profileFieldErrors = reactive({})

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})
const passwordFormRef = ref(null)
const passwordLoading = ref(false)
const passwordFieldErrors = reactive({})

const roleMap = { admin: '管理员', operator: '操作员', viewer: '查看者' }

const profileRules = {
  email: [{ type: 'email', message: '邮箱格式不正确', trigger: 'blur' }],
  phone: [{ pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' }]
}

const passwordRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码长度不能少于8位', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (!/[A-Z]/.test(value)) callback(new Error('密码必须包含至少一个大写字母'))
        else if (!/[a-z]/.test(value)) callback(new Error('密码必须包含至少一个小写字母'))
        else if (!/\d/.test(value)) callback(new Error('密码必须包含至少一个数字'))
        else callback()
      },
      trigger: 'blur'
    }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.new_password) callback(new Error('两次输入的密码不一致'))
        else callback()
      },
      trigger: 'blur'
    }
  ]
}

const loadProfile = async () => {
  loading.value = true
  try {
    const res = await getProfile()
    profileData.value = res.data
    profileForm.email = res.data.email || ''
    profileForm.phone = res.data.phone || ''
    profileForm.company_name = res.data.company_name || ''
  } catch {
  } finally {
    loading.value = false
  }
}

const handleUpdateProfile = async () => {
  try {
    await profileFormRef.value.validate()
  } catch {
    return
  }
  profileLoading.value = true
  Object.keys(profileFieldErrors).forEach(k => profileFieldErrors[k] = '')
  try {
    const res = await updateProfile(profileForm)
    profileData.value = res.data
    ElMessage.success('个人信息更新成功')
    await userStore.getUserInfoAction()
  } catch (error) {
    const res = error.response?.data
    if (res?.data && typeof res.data === 'object') {
      Object.entries(res.data).forEach(([key, val]) => {
        profileFieldErrors[key] = Array.isArray(val) ? val[0] : val
      })
    }
  } finally {
    profileLoading.value = false
  }
}

const handleChangePassword = async () => {
  try {
    await passwordFormRef.value.validate()
  } catch {
    return
  }
  passwordLoading.value = true
  Object.keys(passwordFieldErrors).forEach(k => passwordFieldErrors[k] = '')
  try {
    await changePassword(passwordForm)
    ElMessage.success('密码修改成功')
    Object.assign(passwordForm, { old_password: '', new_password: '', confirm_password: '' })
    passwordFormRef.value.resetFields()
  } catch (error) {
    const res = error.response?.data
    if (res?.data && typeof res.data === 'object') {
      Object.entries(res.data).forEach(([key, val]) => {
        passwordFieldErrors[key] = Array.isArray(val) ? val[0] : val
      })
    }
  } finally {
    passwordLoading.value = false
  }
}

const formatDate = (val) => {
  if (!val) return '-'
  return val.replace('T', ' ').substring(0, 19)
}

onMounted(loadProfile)
</script>

<template>
  <div class="profile-container">
    <div class="page-header">
      <h1>个人中心</h1>
      <p class="text-muted">管理个人账号信息与密码</p>
    </div>

    <el-row :gutter="24">
      <el-col :xs="24" :lg="8">
        <div class="card user-card" v-loading="loading">
          <div class="user-avatar">
            <el-icon :size="40"><UserFilled /></el-icon>
          </div>
          <h3>{{ profileData.username }}</h3>
          <el-tag :type="{ admin: 'danger', operator: 'warning', viewer: 'info' }[profileData.role]" size="small">
            {{ roleMap[profileData.role] || profileData.role }}
          </el-tag>
          <el-descriptions :column="1" class="user-descriptions" style="margin-top: 24px;">
            <el-descriptions-item label="邮箱">{{ profileData.email || '-' }}</el-descriptions-item>
            <el-descriptions-item label="手机号">{{ profileData.phone || '-' }}</el-descriptions-item>
            <el-descriptions-item label="企业">{{ profileData.company_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="注册时间">{{ formatDate(profileData.created_at) }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </el-col>

      <el-col :xs="24" :lg="16">
        <div class="card">
          <el-tabs v-model="activeTab">
            <el-tab-pane label="基本信息" name="info">
              <el-form
                ref="profileFormRef"
                :model="profileForm"
                :rules="profileRules"
                label-width="80px"
                style="max-width: 480px; padding: 20px 0;"
              >
                <el-form-item label="邮箱" prop="email" :error="profileFieldErrors.email">
                  <el-input v-model="profileForm.email" placeholder="请输入邮箱" />
                </el-form-item>
                <el-form-item label="手机号" prop="phone" :error="profileFieldErrors.phone">
                  <el-input v-model="profileForm.phone" placeholder="请输入手机号" />
                </el-form-item>
                <el-form-item label="企业名称" prop="company_name" :error="profileFieldErrors.company_name">
                  <el-input v-model="profileForm.company_name" placeholder="请输入企业名称" />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" :loading="profileLoading" @click="handleUpdateProfile">
                    保存修改
                  </el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <el-tab-pane label="修改密码" name="password">
              <el-form
                ref="passwordFormRef"
                :model="passwordForm"
                :rules="passwordRules"
                label-width="80px"
                style="max-width: 480px; padding: 20px 0;"
              >
                <el-form-item label="原密码" prop="old_password" :error="passwordFieldErrors.old_password">
                  <el-input v-model="passwordForm.old_password" type="password" placeholder="请输入原密码" show-password />
                </el-form-item>
                <el-form-item label="新密码" prop="new_password" :error="passwordFieldErrors.new_password">
                  <el-input v-model="passwordForm.new_password" type="password" placeholder="请输入新密码" show-password />
                </el-form-item>
                <el-form-item label="确认密码" prop="confirm_password" :error="passwordFieldErrors.confirm_password">
                  <el-input v-model="passwordForm.confirm_password" type="password" placeholder="请确认新密码" show-password />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" :loading="passwordLoading" @click="handleChangePassword">
                    修改密码
                  </el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>
          </el-tabs>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<style lang="scss" scoped>
.profile-container {
  min-height: 100%;

  .page-header {
    margin-bottom: 24px;

    h1 {
      font-size: var(--fs-xl);
      font-weight: 600;
      color: var(--text-primary);
      line-height: 1.4;
    }

    .text-muted {
      margin-top: 4px;
      font-size: var(--fs-sm);
      color: var(--text-muted);
      line-height: 1.5;
    }
  }

  .card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 24px;
    margin-bottom: 16px;
    transition: box-shadow var(--transition-fast);
  }

  .user-card {
    text-align: center;

    .user-avatar {
      width: 80px;
      height: 80px;
      margin: 0 auto 16px;
      background: var(--primary);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #ffffff;
      transition: background var(--transition-fast);
    }

    h3 {
      font-size: var(--fs-md);
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 8px;
    }

    .user-descriptions {
      :deep(.el-descriptions__label) {
        color: var(--text-secondary);
        font-size: var(--fs-sm);
      }

      :deep(.el-descriptions__content) {
        color: var(--text-primary);
        font-size: var(--fs-sm);
      }
    }
  }

  :deep(.el-tabs__nav-wrap::after) {
    background-color: var(--border-color);
  }

  :deep(.el-tabs__active-bar) {
    background-color: var(--primary);
  }

  :deep(.el-tabs__item) {
    color: var(--text-secondary);
    font-size: var(--fs-base);
    transition: color var(--transition-fast);

    &.is-active {
      color: var(--primary);
    }

    &:hover {
      color: var(--primary);
    }
  }

  :deep(.el-form-item__label) {
    color: var(--text-secondary);
    font-size: var(--fs-sm);
  }

  :deep(.el-input__wrapper) {
    border-radius: var(--radius-sm);
    transition: box-shadow var(--transition-fast);
  }

  :deep(.el-button--primary) {
    background-color: var(--primary);
    border-color: var(--primary);
    border-radius: var(--radius-sm);
    transition: background-color var(--transition-fast), border-color var(--transition-fast);

    &:hover,
    &:focus {
      background-color: var(--primary-light);
      border-color: var(--primary-light);
    }

    &:active {
      background-color: var(--primary-dark);
      border-color: var(--primary-dark);
    }
  }

  :deep(.el-tag) {
    border-radius: var(--radius-xs);
  }
}
</style>
