<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/store/modules/app'
import { useUserStore } from '@/store/modules/user'
import { Fold, Expand, UserFilled, Setting, SwitchButton, Bell } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const userStore = useUserStore()

const isCollapsed = computed(() => appStore.sidebar.collapsed)

const breadcrumbs = computed(() => {
  return route.matched
    .filter((item) => item.meta?.title)
    .map((item) => ({
      title: item.meta.title,
      path: item.path
    }))
})

const toggleSidebar = () => {
  appStore.toggleSidebar()
}

const handleCommand = (command) => {
  if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      userStore.logoutAction()
    }).catch(() => {})
  }
}
</script>

<template>
  <div class="app-header">
    <div class="header-left">
      <button class="hamburger-btn" @click="toggleSidebar">
        <el-icon :size="18">
          <Fold v-if="!isCollapsed" />
          <Expand v-else />
        </el-icon>
      </button>
      <el-breadcrumb separator="/" class="header-breadcrumb">
        <el-breadcrumb-item v-for="item in breadcrumbs" :key="item.path">
          {{ item.title }}
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    <div class="header-right">
      <button class="header-icon-btn">
        <el-badge :value="0" :hidden="true" type="danger">
          <el-icon :size="18"><Bell /></el-icon>
        </el-badge>
      </button>
      <el-dropdown trigger="click" @command="handleCommand">
        <div class="user-info">
          <div class="user-avatar">
            <el-icon :size="16"><UserFilled /></el-icon>
          </div>
          <span class="nickname">{{ userStore.nickname }}</span>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">
              <el-icon><Setting /></el-icon>
              个人中心
            </el-dropdown-item>
            <el-dropdown-item command="logout" divided>
              <el-icon><SwitchButton /></el-icon>
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.app-header {
  height: 60px;
  background: var(--card-bg);
  border-bottom: 1px solid var(--border-color);
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;

  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .hamburger-btn {
    width: 36px;
    height: 36px;
    border: none;
    background: transparent;
    border-radius: 8px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-secondary);
    transition: all 0.2s ease;

    &:hover {
      background: var(--bg-color);
      color: var(--primary-color);
    }

    &:active {
      transform: scale(0.95);
    }
  }

  .header-breadcrumb {
    :deep(.el-breadcrumb__item) {
      .el-breadcrumb__inner {
        font-size: 14px;
        color: var(--text-muted);
        font-weight: 400;
      }

      &:last-child .el-breadcrumb__inner {
        color: var(--text-primary);
        font-weight: 500;
      }
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .header-icon-btn {
    width: 36px;
    height: 36px;
    border: none;
    background: transparent;
    border-radius: 8px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-secondary);
    transition: all 0.2s ease;

    &:hover {
      background: var(--bg-color);
      color: var(--primary-color);
    }
  }

  .user-info {
    display: flex;
    align-items: center;
    cursor: pointer;
    padding: 6px 12px;
    border-radius: 8px;
    transition: all 0.2s ease;

    .user-avatar {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: linear-gradient(135deg, #165DFF, #4080FF);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #ffffff;
      flex-shrink: 0;
    }

    .nickname {
      margin-left: 8px;
      font-size: 14px;
      font-weight: 500;
      color: var(--text-primary);
    }

    &:hover {
      background: var(--bg-color);
    }
  }
}

:deep(.el-dropdown-menu__item) {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  padding: 8px 16px;

  &:hover {
    background: var(--primary-bg);
    color: var(--primary-color);
  }
}
</style>
