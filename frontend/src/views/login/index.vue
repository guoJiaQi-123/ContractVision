<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/modules/user'
import { User, Lock, DataLine } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const loginFormRef = ref()
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = reactive({
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ]
})

const handleLogin = async () => {
  const valid = await loginFormRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await userStore.loginAction(loginForm)
    const redirect = route.query.redirect || '/dashboard'
    router.push(redirect)
    ElMessage.success('登录成功')
  } catch (error) {
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-container">
    <div class="login-left">
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

    <div class="login-right">
      <div class="login-form-wrapper">
        <div class="login-header">
          <h2>系统登录</h2>
          <p class="text-muted">欢迎使用销售合同数据可视化平台</p>
        </div>

        <el-form
          ref="loginFormRef"
          :model="loginForm"
          :rules="loginRules"
          size="large"
          class="login-form"
        >
          <el-form-item prop="username">
            <label class="form-label">用户名</label>
            <el-input
              v-model="loginForm.username"
              placeholder="请输入用户名"
              :prefix-icon="User"
            />
          </el-form-item>
          <el-form-item prop="password">
            <label class="form-label">登录密码</label>
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              show-password
              :prefix-icon="Lock"
              @keyup.enter="handleLogin"
            />
          </el-form-item>
          <div class="form-options">
            <el-checkbox label="记住密码" />
            <button type="button" class="forgot-link">忘记密码？</button>
          </div>
          <el-form-item>
            <el-button
              type="primary"
              :loading="loading"
              class="login-btn"
              @click="handleLogin"
            >
              {{ loading ? '登录中...' : '登录' }}
            </el-button>
          </el-form-item>
          <div class="register-tip">
            还没有账号？<router-link to="/register" class="register-link">立即注册</router-link>
          </div>
        </el-form>

        <div class="login-footer">
          © 2026 企业销售合同数据可视化平台. All rights reserved.
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.login-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
  font-family: var(--font-sans);
}

.login-left {
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

.login-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-color);
  padding: 24px;
}

.login-form-wrapper {
  width: 100%;
  max-width: 400px;
}

.login-header {
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

.login-form {
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
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.form-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  font-size: 14px;

  :deep(.el-checkbox) {
    color: var(--text-secondary);
  }

  .forgot-link {
    background: none;
    border: none;
    color: var(--primary);
    font-size: 14px;
    cursor: pointer;
    transition: color var(--transition-fast);

    &:hover {
      color: var(--primary-light);
    }
  }
}

.login-btn {
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

.register-tip {
  text-align: center;
  margin-top: 4px;
  font-size: 14px;
  color: var(--text-secondary);

  .register-link {
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

.login-footer {
  margin-top: 32px;
  text-align: center;
  font-size: 12px;
  color: var(--text-muted);
}
</style>
