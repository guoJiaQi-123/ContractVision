<script setup>
import { useAppStore } from '@/store/modules/app'
import { AppSidebar, AppHeader } from './components'

const appStore = useAppStore()
</script>

<template>
  <el-container class="layout-container">
    <AppSidebar />
    <el-container
      class="main-container"
      :style="{ marginLeft: appStore.sidebar.collapsed ? '64px' : '220px' }"
    >
      <AppHeader />
      <el-main class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<style lang="scss" scoped>
.layout-container {
  height: 100%;
}

.main-container {
  flex-direction: column;
  transition: margin-left 0.3s;
  min-height: 100%;
}

.app-main {
  padding: 24px;
  background: var(--bg-color);
  min-height: calc(100vh - 60px);
}
</style>
