<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/store/modules/app'
import { useUserStore } from '@/store/modules/user'
import { Fold, Expand, UserFilled, Setting, SwitchButton, Bell } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAlertCenter, processAlertCenterItem } from '@/api/system'
import { formatDate } from '@/utils'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const userStore = useUserStore()
const roleMap = { admin: '管理员', operator: '操作员', viewer: '查看者' }
const roleTagType = { admin: 'danger', operator: 'warning', viewer: 'info' }

const isCollapsed = computed(() => appStore.sidebar.collapsed)
const displayName = computed(() => userStore.nickname || userStore.username || '未命名用户')
const roleLabel = computed(() => roleMap[userStore.role] || userStore.role || '未分配角色')
const roleType = computed(() => roleTagType[userStore.role] || 'info')
const avatarUrl = computed(() => userStore.avatar || '')
const avatarText = computed(() => {
  const source = displayName.value.trim()
  return source ? source.slice(0, 1).toUpperCase() : 'U'
})
const alertCenter = ref({
  pending_count: 0,
  processed_count: 0,
  level_counts: { high: 0, medium: 0, low: 0 },
  recent_alerts: []
})
const alertLoading = ref(false)
const processingIds = ref([])

const breadcrumbs = computed(() => {
  return route.matched
    .filter((item) => item.meta?.title)
    .map((item) => ({
      title: item.meta.title,
      path: item.path
    }))
})

const pendingAlertCount = computed(() => alertCenter.value.pending_count || 0)
const recentAlerts = computed(() => alertCenter.value.recent_alerts || [])
const alertShortcutLabel = computed(() => '进入预警台')

const getLevelTagType = (level) => {
  if (level === 'high') return 'danger'
  if (level === 'medium') return 'warning'
  return 'info'
}

const formatAlertTime = (date) => {
  return date ? formatDate(date, 'YYYY-MM-DD') : '未设置'
}

const loadAlertCenter = async () => {
  alertLoading.value = true
  try {
    const res = await getAlertCenter()
    alertCenter.value = {
      pending_count: res.data?.pending_count || 0,
      processed_count: res.data?.processed_count || 0,
      level_counts: res.data?.level_counts || { high: 0, medium: 0, low: 0 },
      recent_alerts: res.data?.recent_alerts || []
    }
  } finally {
    alertLoading.value = false
  }
}

const handleAlertAction = async (id) => {
  if (!id || processingIds.value.includes(id)) return
  processingIds.value = [...processingIds.value, id]
  try {
    await processAlertCenterItem(id)
    ElMessage.success('预警已处理')
    await loadAlertCenter()
  } finally {
    processingIds.value = processingIds.value.filter((item) => item !== id)
  }
}

const navigateAlertTarget = () => {
  router.push('/contract/alerts')
}

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

onMounted(() => {
  loadAlertCenter()
})

watch(() => route.fullPath, () => {
  loadAlertCenter()
})
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
      <el-popover
        placement="bottom-end"
        :width="360"
        trigger="click"
        popper-class="alert-popover"
        @show="loadAlertCenter"
      >
        <template #reference>
          <button class="header-icon-btn" :class="{ 'has-alert': pendingAlertCount > 0 }">
            <el-badge :value="pendingAlertCount" :hidden="pendingAlertCount === 0" type="danger">
              <el-icon :size="18"><Bell /></el-icon>
            </el-badge>
          </button>
        </template>
        <div class="alert-panel">
          <div class="alert-panel-header">
            <div>
              <strong>预警中心</strong>
              <p>实时汇总当前账号待处理事项</p>
            </div>
            <el-tag type="danger" effect="light" round>{{ pendingAlertCount }} 条待处理</el-tag>
          </div>
          <div class="alert-summary">
            <div class="summary-item high">
              <span>高危</span>
              <strong>{{ alertCenter.level_counts?.high || 0 }}</strong>
            </div>
            <div class="summary-item medium">
              <span>中危</span>
              <strong>{{ alertCenter.level_counts?.medium || 0 }}</strong>
            </div>
            <div class="summary-item low">
              <span>提示</span>
              <strong>{{ alertCenter.level_counts?.low || 0 }}</strong>
            </div>
          </div>
          <div v-loading="alertLoading" class="alert-list">
            <div v-if="recentAlerts.length" class="alert-items">
              <div v-for="item in recentAlerts" :key="item.id" class="alert-item">
                <div class="alert-item-main">
                  <div class="alert-item-title">
                    <span>{{ item.title }}</span>
                    <el-tag :type="getLevelTagType(item.level)" effect="light" round size="small">
                      {{ item.level === 'high' ? '高危' : item.level === 'medium' ? '中危' : '提示' }}
                    </el-tag>
                  </div>
                  <p>{{ item.content || '请尽快跟进该预警事项。' }}</p>
                  <div class="alert-item-meta">
                    <span>合同：{{ item.contract_no || '通用事项' }}</span>
                    <span>截止：{{ formatAlertTime(item.due_date) }}</span>
                  </div>
                </div>
                <el-button
                  type="primary"
                  link
                  :loading="processingIds.includes(item.id)"
                  @click="handleAlertAction(item.id)"
                >
                  处理
                </el-button>
              </div>
            </div>
            <el-empty v-else description="暂无待处理预警" :image-size="72" />
          </div>
          <div class="alert-panel-footer">
            <span>已处理 {{ alertCenter.processed_count || 0 }} 条历史预警</span>
            <el-button type="primary" link @click="navigateAlertTarget">{{ alertShortcutLabel }}</el-button>
          </div>
        </div>
      </el-popover>
      <el-dropdown trigger="click" @command="handleCommand">
        <div class="user-info">
          <div class="user-avatar">
            <img v-if="avatarUrl" :src="avatarUrl" :alt="`${displayName}头像`" class="avatar-image" />
            <template v-else>
              <span class="avatar-text">{{ avatarText }}</span>
              <el-icon :size="16" class="avatar-icon"><UserFilled /></el-icon>
            </template>
          </div>
          <div class="user-meta">
            <span class="nickname">{{ displayName }}</span>
            <el-tag :type="roleType" size="small" effect="light" round>
              {{ roleLabel }}
            </el-tag>
          </div>
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

    &.has-alert {
      color: var(--primary-color);
      background: rgba(22, 93, 255, 0.08);
    }
  }

  .user-info {
    display: flex;
    align-items: center;
    cursor: pointer;
    gap: 10px;
    padding: 6px 12px;
    border-radius: 12px;
    transition: all 0.2s ease;

    .user-avatar {
      position: relative;
      width: 38px;
      height: 38px;
      border-radius: 50%;
      background: linear-gradient(135deg, #165DFF, #4080FF);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #ffffff;
      flex-shrink: 0;
      overflow: hidden;
      box-shadow: 0 8px 18px rgba(22, 93, 255, 0.2);

      .avatar-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }

      .avatar-text {
        position: absolute;
        z-index: 1;
        font-size: 14px;
        font-weight: 700;
        letter-spacing: 0.02em;
      }

      .avatar-icon {
        position: absolute;
        right: -2px;
        bottom: -1px;
        width: 18px;
        height: 18px;
        border-radius: 50%;
        background: rgba(12, 22, 44, 0.22);
        backdrop-filter: blur(6px);
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid rgba(255, 255, 255, 0.4);
      }
    }

    .user-meta {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 4px;
      min-width: 0;

      .nickname {
        max-width: 140px;
        font-size: 14px;
        font-weight: 600;
        line-height: 1;
        color: var(--text-primary);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      :deep(.el-tag) {
        margin: 0;
        border: none;
        font-weight: 500;
      }
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

:deep(.alert-popover) {
  padding: 0 !important;
  border-radius: 18px !important;
  overflow: hidden;
}

.alert-panel {
  padding: 16px;
}

.alert-panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;

  strong {
    display: block;
    color: var(--text-primary);
    font-size: 15px;
  }

  p {
    margin: 4px 0 0;
    color: var(--text-muted);
    font-size: 12px;
  }
}

.alert-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.summary-item {
  padding: 10px 12px;
  border-radius: 14px;
  background: var(--bg-color);
  display: flex;
  flex-direction: column;
  gap: 4px;

  span {
    color: var(--text-muted);
    font-size: 12px;
  }

  strong {
    color: var(--text-primary);
    font-size: 18px;
    line-height: 1;
  }

  &.high {
    background: rgba(245, 108, 108, 0.08);
  }

  &.medium {
    background: rgba(230, 162, 60, 0.08);
  }

  &.low {
    background: rgba(64, 158, 255, 0.08);
  }
}

.alert-list {
  min-height: 120px;
}

.alert-items {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.alert-item {
  display: flex;
  gap: 8px;
  justify-content: space-between;
  padding: 12px;
  border-radius: 14px;
  background: var(--bg-color);
  border: 1px solid rgba(148, 163, 184, 0.14);
}

.alert-item-main {
  min-width: 0;
  flex: 1;

  p {
    margin: 6px 0;
    color: var(--text-secondary);
    font-size: 12px;
    line-height: 1.5;
  }
}

.alert-item-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 600;
}

.alert-item-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  color: var(--text-muted);
  font-size: 12px;
}

.alert-panel-footer {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: var(--text-muted);
  font-size: 12px;
}
</style>
