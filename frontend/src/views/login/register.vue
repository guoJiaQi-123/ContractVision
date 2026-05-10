<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { register } from '@/api/auth'
import { User, Lock, DataLine, Message, Phone, Warning } from '@element-plus/icons-vue'

const router = useRouter()
const registerFormRef = ref()
const loading = ref(false)

const fieldErrors = reactive({
  username: '',
  email: '',
  phone: '',
  password: '',
  confirmPassword: ''
})

const registerForm = reactive({
  username: '',
  email: '',
  phone: '',
  password: '',
  confirmPassword: ''
})

const validateUsername = (rule, value, callback) => {
  if (!value) {
    callback(new Error('请输入用户名'))
  } else if (value.length > 150) {
    callback(new Error('用户名长度不能超过150个字符'))
  } else if (!/^[\w.@+\-]+$/.test(value)) {
    callback(new Error('用户名只能包含字母、数字和 @/./+/-/_ 字符'))
  } else {
    callback()
  }
}

const validatePhone = (rule, value, callback) => {
  if (!value) {
    callback(new Error('请输入手机号'))
  } else if (!/^1[3-9]\d{9}$/.test(value)) {
    callback(new Error('请输入正确的11位手机号码'))
  } else {
    callback()
  }
}

const validatePassword = (rule, value, callback) => {
  if (!value) {
    callback(new Error('请输入密码'))
  } else if (value.length < 8) {
    callback(new Error('密码长度不能少于8位'))
  } else if (!/[A-Z]/.test(value)) {
    callback(new Error('密码必须包含至少一个大写字母'))
  } else if (!/[a-z]/.test(value)) {
    callback(new Error('密码必须包含至少一个小写字母'))
  } else if (!/\d/.test(value)) {
    callback(new Error('密码必须包含至少一个数字'))
  } else {
    callback()
  }
}

const validateConfirmPassword = (rule, value, callback) => {
  if (!value) {
    callback(new Error('请再次输入密码'))
  } else if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const registerRules = reactive({
  username: [{ validator: validateUsername, trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  phone: [{ validator: validatePhone, trigger: 'blur' }],
  password: [{ validator: validatePassword, trigger: 'blur' }],
  confirmPassword: [{ validator: validateConfirmPassword, trigger: 'blur' }]
})

const backendFieldMap = {
  username: 'username',
  email: 'email',
  phone: 'phone',
  password: 'password',
  confirm_password: 'confirmPassword'
}

const clearFieldError = (field) => {
  fieldErrors[field] = ''
}

const handleRegister = async () => {
  Object.keys(fieldErrors).forEach(key => { fieldErrors[key] = '' })
  const valid = await registerFormRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await register({
      username: registerForm.username,
      email: registerForm.email,
      phone: registerForm.phone,
      password: registerForm.password,
      confirm_password: registerForm.confirmPassword
    })
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch (error) {
    const resp = error.response?.data
    if (resp?.code === 400 && resp?.data && typeof resp.data === 'object') {
      Object.entries(resp.data).forEach(([backendField, message]) => {
        const frontendField = backendFieldMap[backendField]
        if (frontendField) {
          fieldErrors[frontendField] = message
        }
      })
      const firstMessage = Object.values(resp.data)[0]
      ElMessage.warning(firstMessage)
    } else {
      ElMessage.error(resp?.message || '注册失败，请稍后重试')
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="register-container">
    <div class="register-left">
      <div class="brand-content">
        <div class="brand-icon">
          <el-icon :size="48"><DataLine /></el-icon>
        </div>
        <h1 class="brand-title">销售合同数据可视化平台</h1>
        <p class="brand-subtitle">数据驱动合同管理</p>
        <div class="brand-features">
          <p>实时监控 · 多维分析 · 智能预警</p>
        </div>
      </div>
    </div>

    <div class="register-right">
      <div class="register-form-wrapper">
        <div class="register-header">
          <h2>用户注册</h2>
          <p class="text-muted">创建账号，开始使用平台</p>
        </div>

        <el-form
          ref="registerFormRef"
          :model="registerForm"
          :rules="registerRules"
          size="large"
          class="register-form"
        >
          <el-form-item prop="username" :error="fieldErrors.username">
            <label class="form-label">
              用户名
              <el-tooltip content="用户名为1-150个字符，仅支持字母、数字和 @/./+/-/_ 字符" placement="top">
                <el-icon class="form-tip-icon"><Warning /></el-icon>
              </el-tooltip>
            </label>
            <el-input
              v-model="registerForm.username"
              placeholder="请输入用户名"
              :prefix-icon="User"
              @input="clearFieldError('username')"
            />
          </el-form-item>
          <el-form-item prop="email" :error="fieldErrors.email">
            <label class="form-label">
              邮箱
              <el-tooltip content="请输入有效的邮箱地址，如 example@domain.com" placement="top">
                <el-icon class="form-tip-icon"><Warning /></el-icon>
              </el-tooltip>
            </label>
            <el-input
              v-model="registerForm.email"
              placeholder="请输入邮箱"
              :prefix-icon="Message"
              @input="clearFieldError('email')"
            />
          </el-form-item>
          <el-form-item prop="phone" :error="fieldErrors.phone">
            <label class="form-label">
              手机号
              <el-tooltip content="请输入11位手机号码，以1开头，第二位为3-9，如 13800138000" placement="top">
                <el-icon class="form-tip-icon"><Warning /></el-icon>
              </el-tooltip>
            </label>
            <el-input
              v-model="registerForm.phone"
              placeholder="请输入手机号"
              :prefix-icon="Phone"
              @input="clearFieldError('phone')"
            />
          </el-form-item>
          <el-form-item prop="password" :error="fieldErrors.password">
            <label class="form-label">
              登录密码
              <el-tooltip placement="top">
                <el-icon class="form-tip-icon"><Warning /></el-icon>
                <template #content>
                  <div>密码长度至少8位，且必须包含：</div>
                  <div>· 至少一个大写字母</div>
                  <div>· 至少一个小写字母</div>
                  <div>· 至少一个数字</div>
                </template>
              </el-tooltip>
            </label>
            <el-input
              v-model="registerForm.password"
              type="password"
              placeholder="请输入密码"
              show-password
              :prefix-icon="Lock"
              @input="clearFieldError('password')"
            />
          </el-form-item>
          <el-form-item prop="confirmPassword" :error="fieldErrors.confirmPassword">
            <label class="form-label">
              确认密码
              <el-tooltip content="请再次输入与上方相同的密码" placement="top">
                <el-icon class="form-tip-icon"><Warning /></el-icon>
              </el-tooltip>
            </label>
            <el-input
              v-model="registerForm.confirmPassword"
              type="password"
              placeholder="请再次输入密码"
              show-password
              :prefix-icon="Lock"
              @keyup.enter="handleRegister"
              @input="clearFieldError('confirmPassword')"
            />
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              :loading="loading"
              class="register-btn"
              @click="handleRegister"
            >
              {{ loading ? '注册中...' : '注册' }}
            </el-button>
          </el-form-item>
          <div class="login-tip">
            已有账号？<router-link to="/login" class="login-link">返回登录</router-link>
          </div>
        </el-form>

        <div class="register-footer">
          © 2026 企业销售合同数据可视化平台. All rights reserved.
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.register-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
  font-family: var(--font-sans);
}

.register-left {
  display: none;
  width: 800px;
  background: var(--primary);
  flex-shrink: 0;

  @media (min-width: 1024px) {
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

.brand-content {
  text-align: center;
  color: #ffffff;
  padding: 48px;

  .brand-icon {
    width: 80px;
    height: 80px;
    background: rgba(255, 255, 255, 0.15);
    backdrop-filter: blur(10px);
    border-radius: var(--radius-lg);
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 24px;
  }

  .brand-title {
    font-size: 32px;
    font-weight: 600;
    margin-bottom: 16px;
    color: #ffffff;
  }

  .brand-subtitle {
    font-size: 18px;
    color: rgba(255, 255, 255, 0.9);
    margin-bottom: 48px;
  }

  .brand-features {
    color: rgba(255, 255, 255, 0.8);
    font-size: 14px;
  }
}

.register-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-color);
  padding: 24px;
  overflow-y: auto;
}

.register-form-wrapper {
  width: 100%;
  max-width: 400px;
}

.register-header {
  margin-bottom: 32px;

  h2 {
    font-size: 24px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 8px;
  }

  .text-muted {
    color: var(--text-muted);
    font-size: 14px;
  }
}

.register-form {
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
}

.form-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.form-tip-icon {
  font-size: 14px;
  color: var(--warning);
  cursor: pointer;
  vertical-align: middle;
  transition: color var(--transition-fast);

  &:hover {
    color: var(--warning);
  }
}

.register-btn {
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

.login-tip {
  text-align: center;
  margin-top: 4px;
  font-size: 14px;
  color: var(--text-secondary);

  .login-link {
    color: var(--primary);
    text-decoration: none;
    font-weight: 500;
    transition: color var(--transition-fast);

    &:hover {
      color: var(--primary-light);
      text-decoration: underline;
    }
  }
}

.register-footer {
  margin-top: 32px;
  text-align: center;
  font-size: 12px;
  color: var(--text-muted);
}
</style>
