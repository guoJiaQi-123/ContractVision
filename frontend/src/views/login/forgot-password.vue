<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { resetPassword } from '@/api/auth'
import { Key } from '@element-plus/icons-vue'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const fieldErrors = reactive({})

const form = reactive({
  username: '',
  phone: '',
  new_password: '',
  confirm_password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' }
  ],
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
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== form.new_password) callback(new Error('两次输入的密码不一致'))
        else callback()
      },
      trigger: 'blur'
    }
  ]
}

const clearFieldError = (field) => {
  fieldErrors[field] = ''
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  loading.value = true
  Object.keys(fieldErrors).forEach(k => fieldErrors[k] = '')

  try {
    await resetPassword(form)
    ElMessage.success('密码重置成功，请使用新密码登录')
    router.push('/login')
  } catch (error) {
    const res = error.response?.data
    if (res?.data && typeof res.data === 'object') {
      Object.entries(res.data).forEach(([key, val]) => {
        fieldErrors[key] = Array.isArray(val) ? val[0] : val
      })
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="forgot-password-container">
    <div class="forgot-password-card">
      <div class="card-header">
        <div class="logo-icon">
          <el-icon :size="28"><Key /></el-icon>
        </div>
        <h2>找回密码</h2>
        <p>请输入注册时的用户名和手机号验证身份</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" size="large">
        <el-form-item label="用户名" prop="username" :error="fieldErrors.username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            @input="clearFieldError('username')"
          />
        </el-form-item>

        <el-form-item label="手机号" prop="phone" :error="fieldErrors.phone">
          <el-input
            v-model="form.phone"
            placeholder="请输入注册手机号"
            @input="clearFieldError('phone')"
          />
        </el-form-item>

        <el-form-item label="新密码" prop="new_password" :error="fieldErrors.new_password">
          <el-input
            v-model="form.new_password"
            type="password"
            placeholder="请输入新密码"
            show-password
            @input="clearFieldError('new_password')"
          />
        </el-form-item>

        <el-form-item label="确认密码" prop="confirm_password" :error="fieldErrors.confirm_password">
          <el-input
            v-model="form.confirm_password"
            type="password"
            placeholder="请再次输入新密码"
            show-password
            @input="clearFieldError('confirm_password')"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="loading" style="width: 100%" @click="handleSubmit">
            重置密码
          </el-button>
        </el-form-item>

        <div class="form-footer">
          <router-link to="/login">返回登录</router-link>
        </div>
      </el-form>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.forgot-password-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-color);
  padding: 20px;
  font-family: var(--font-sans);
}

.forgot-password-card {
  width: 420px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 40px;
  box-shadow: var(--shadow-md);

  .card-header {
    text-align: center;
    margin-bottom: 32px;

    .logo-icon {
      width: 56px;
      height: 56px;
      margin: 0 auto 16px;
      background: var(--primary);
      border-radius: var(--radius-md);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #ffffff;
    }

    h2 {
      font-size: 22px;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 8px;
    }

    p {
      font-size: 14px;
      color: var(--text-muted);
    }
  }

  :deep(.el-form-item) {
    margin-bottom: 20px;
  }

  :deep(.el-input) {
    .el-input__wrapper {
      padding: 4px 12px;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-color);
      box-shadow: none;
      transition: border-color var(--transition-fast), box-shadow var(--transition-fast);

      &:hover {
        border-color: var(--primary);
      }

      &:focus-within {
        border-color: var(--primary);
        box-shadow: 0 0 0 3px var(--primary-bg);
      }
    }
  }

  :deep(.el-button--primary) {
    width: 100%;
    height: 48px;
    border-radius: var(--radius-md);
    font-size: 16px;
    font-weight: 500;
    background: var(--primary);
    border-color: var(--primary);
    transition: background var(--transition-fast), border-color var(--transition-fast);

    &:hover {
      background: var(--primary-light);
      border-color: var(--primary-light);
    }
  }

  :deep(.el-form-item__label) {
    font-size: 14px;
    font-weight: 500;
    color: var(--text-secondary);
  }

  .form-footer {
    text-align: center;
    margin-top: 16px;

    a {
      color: var(--primary);
      text-decoration: none;
      font-size: 14px;
      font-weight: 500;
      transition: color var(--transition-fast);

      &:hover {
        color: var(--primary-light);
      }
    }
  }
}
</style>
