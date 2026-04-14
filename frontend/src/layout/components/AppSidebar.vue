<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/store/modules/app'
import { useUserStore } from '@/store/modules/user'
import { TrendCharts, Document, DataLine, User, Setting, HomeFilled, DataAnalysis, Location, Notebook, Tickets, MagicStick, FolderOpened, Connection, Finished, Monitor, Operation, SetUp, Cellphone } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const userStore = useUserStore()

const isCollapsed = computed(() => appStore.sidebar.collapsed)
const activeMenu = computed(() => route.path)

const menuList = [
  { path: '/dashboard', title: '首页概览', icon: HomeFilled },
  { path: '/dashboard/mobile', title: '移动驾驶舱', icon: Cellphone },
  {
    path: '/contract',
    title: '合同管理',
    icon: Document,
    children: [
      { path: '/contract/list', title: '合同列表' },
      { path: '/contract/lifecycle', title: '履约中心', icon: Finished }
    ]
  },
  {
    path: '/analytics',
    title: '数据分析',
    icon: DataLine,
    children: [
      { path: '/analytics/overview', title: '数据概览', icon: DataAnalysis },
      { path: '/analytics/trend', title: '趋势分析', icon: TrendCharts },
      { path: '/analytics/region', title: '区域分析', icon: Location },
      { path: '/analytics/report', title: '报表中心', icon: Tickets },
      { path: '/analytics/prediction', title: '智能分析', icon: MagicStick },
      { path: '/analytics/management', title: '经营驾驶舱', icon: Monitor }
    ]
  },
  {
    path: '/system',
    title: '系统管理',
    icon: Setting,
    roles: ['admin'],
    children: [
      { path: '/system/user', title: '用户管理', icon: User },
      { path: '/system/log', title: '操作日志', icon: Notebook },
      { path: '/system/backup', title: '数据备份', icon: FolderOpened },
      { path: '/system/integration', title: '第三方集成', icon: Connection },
      { path: '/system/governance', title: '治理控制台', icon: Operation },
      { path: '/system/config-center', title: '模板与汇率', icon: SetUp }
    ]
  }
]

const filteredMenuList = computed(() => {
  const roles = userStore.roles
  if (roles.includes('admin')) return menuList
  return menuList.filter(item => !item.roles || item.roles.some(r => roles.includes(r)))
})

const defaultOpeneds = computed(() => {
  const matched = route.matched
  return matched
    .filter(item => item.path && item.children?.length)
    .map(item => item.path)
})

const handleMenuSelect = (path) => {
  if (path.startsWith('/')) {
    router.push(path)
  }
}
</script>

<template>
  <el-aside :width="isCollapsed ? '64px' : '220px'" class="sidebar-container">
    <div class="logo" @click="router.push('/dashboard')">
      <div class="logo-icon">
        <el-icon :size="22"><TrendCharts /></el-icon>
      </div>
      <transition name="fade">
        <span v-if="!isCollapsed" class="logo-text">ContractVision</span>
      </transition>
    </div>
    <el-scrollbar wrap-class="scrollbar-wrapper">
      <el-menu
        :default-active="activeMenu"
        :default-openeds="defaultOpeneds"
        :collapse="isCollapsed"
        :collapse-transition="false"
        class="sidebar-menu"
        @select="handleMenuSelect"
      >
        <template v-for="item in filteredMenuList" :key="item.path">
          <el-menu-item v-if="!item.children" :index="item.path">
            <el-icon><component :is="item.icon" /></el-icon>
            <template #title>{{ item.title }}</template>
          </el-menu-item>
          <el-sub-menu v-else :index="item.path">
            <template #title>
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.title }}</span>
            </template>
            <el-menu-item
              v-for="child in item.children"
              :key="child.path"
              :index="child.path"
            >
              <el-icon v-if="child.icon"><component :is="child.icon" /></el-icon>
              <template #title>{{ child.title }}</template>
            </el-menu-item>
          </el-sub-menu>
        </template>
      </el-menu>
    </el-scrollbar>
  </el-aside>
</template>

<style lang="scss" scoped>
.sidebar-container {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 1001;
  overflow: hidden;
  background-color: var(--card-bg);
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border-color);

  .logo {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    padding: 0 16px;
    background: var(--card-bg);
    border-bottom: 1px solid var(--border-color);
    white-space: nowrap;
    overflow: hidden;
    cursor: pointer;
    transition: background 0.2s;

    &:hover {
      background: var(--bg-color);
    }

    .logo-icon {
      width: 34px;
      height: 34px;
      background: linear-gradient(135deg, #165DFF 0%, #4080FF 100%);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #ffffff;
      flex-shrink: 0;
      transition: transform 0.3s ease;

      &:hover {
        transform: scale(1.05);
      }
    }

    .logo-text {
      font-size: 15px;
      font-weight: 700;
      color: var(--text-primary);
      letter-spacing: -0.02em;
    }
  }

  :deep(.el-scrollbar) {
    height: calc(100% - 60px);
    flex: 1;
  }

  :deep(.el-scrollbar__wrap) {
    overflow-x: hidden;
  }

  .sidebar-menu {
    border-right: none;
    background: transparent;
    padding: 8px;

    &:not(.el-menu--collapse) {
      width: 100%;
    }

    :deep(.el-menu-item) {
      height: 44px;
      line-height: 44px;
      margin-bottom: 2px;
      border-radius: 8px;
      color: var(--text-secondary);
      transition: all 0.2s ease;
      font-size: 14px;

      &:hover {
        background: var(--bg-color);
        color: var(--text-primary);
      }

      &.is-active {
        background: rgba(22, 93, 255, 0.08);
        color: var(--primary-color);
        font-weight: 500;

        .el-icon {
          color: var(--primary-color);
        }
      }

      .el-icon {
        font-size: 18px;
        margin-right: 10px;
        color: var(--text-muted);
        transition: color 0.2s;
      }
    }

    :deep(.el-sub-menu) {
      .el-sub-menu__title {
        height: 44px;
        line-height: 44px;
        border-radius: 8px;
        color: var(--text-secondary);
        transition: all 0.2s ease;
        font-size: 14px;

        &:hover {
          background: var(--bg-color);
          color: var(--text-primary);
        }

        .el-icon {
          font-size: 18px;
          margin-right: 10px;
          color: var(--text-muted);
          transition: color 0.2s;
        }
      }

      &.is-active > .el-sub-menu__title {
        color: var(--primary-color);
        font-weight: 500;

        .el-icon {
          color: var(--primary-color);
        }
      }

      .el-menu-item {
        height: 40px;
        line-height: 40px;
        padding-left: 52px !important;
        font-size: 13px;
        border-radius: 6px;

        .el-icon {
          font-size: 16px;
          margin-right: 8px;
        }
      }
    }
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
