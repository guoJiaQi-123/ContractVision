import { createRouter, createWebHistory } from 'vue-router'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'
import Layout from '@/layout/index.vue'
import { useUserStore } from '@/store/modules/user'
import { clearAuth } from '@/utils/auth'

NProgress.configure({ showSpinner: false })

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { title: '登录', noAuth: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/login/register.vue'),
    meta: { title: '注册', noAuth: true }
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('@/views/login/forgot-password.vue'),
    meta: { title: '找回密码', noAuth: true }
  },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    children: [
      {
        path: '/dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '首页概览', icon: 'Odometer' }
      },
      {
        path: '/dashboard/mobile',
        name: 'DashboardMobile',
        component: () => import('@/views/dashboard/mobile.vue'),
        meta: { title: '移动驾驶舱', icon: 'Cellphone' }
      },
      {
        path: '/contract',
        redirect: '/contract/list',
        children: [
          {
            path: '/contract/list',
            name: 'ContractList',
            component: () => import('@/views/contract/list.vue'),
            meta: { title: '合同列表', icon: 'Document' }
          },
          {
            path: '/contract/detail/:id',
            name: 'ContractDetail',
            component: () => import('@/views/contract/detail.vue'),
            meta: { title: '合同详情', hidden: true }
          },
          {
            path: '/contract/create',
            name: 'ContractCreate',
            component: () => import('@/views/contract/form.vue'),
            meta: { title: '新建合同', hidden: true }
          },
          {
            path: '/contract/edit/:id',
            name: 'ContractEdit',
            component: () => import('@/views/contract/form.vue'),
            meta: { title: '编辑合同', hidden: true }
          },
          {
            path: '/contract/lifecycle',
            name: 'ContractLifecycle',
            component: () => import('@/views/contract/lifecycle.vue'),
            meta: { title: '履约中心', icon: 'Finished' }
          }
        ]
      },
      {
        path: '/analytics',
        redirect: '/analytics/overview',
        children: [
          {
            path: '/analytics/overview',
            name: 'AnalyticsOverview',
            component: () => import('@/views/analytics/overview.vue'),
            meta: { title: '数据概览', icon: 'DataAnalysis' }
          },
          {
            path: '/analytics/trend',
            name: 'AnalyticsTrend',
            component: () => import('@/views/analytics/trend.vue'),
            meta: { title: '趋势分析', icon: 'TrendCharts' }
          },
          {
            path: '/analytics/region',
            name: 'AnalyticsRegion',
            component: () => import('@/views/analytics/region.vue'),
            meta: { title: '区域分析', icon: 'Location' }
          },
          {
            path: '/analytics/report',
            name: 'AnalyticsReport',
            component: () => import('@/views/analytics/report.vue'),
            meta: { title: '报表中心', icon: 'Tickets' }
          },
          {
            path: '/analytics/prediction',
            name: 'AnalyticsPrediction',
            component: () => import('@/views/analytics/prediction.vue'),
            meta: { title: '智能分析', icon: 'MagicStick' }
          },
          {
            path: '/analytics/management',
            name: 'AnalyticsManagement',
            component: () => import('@/views/analytics/management.vue'),
            meta: { title: '经营驾驶舱', icon: 'Monitor' }
          }
        ]
      },
      {
        path: '/system',
        redirect: '/system/user',
        meta: { roles: ['admin'] },
        children: [
          {
            path: '/system/user',
            name: 'SystemUser',
            component: () => import('@/views/system/user.vue'),
            meta: { title: '用户管理', icon: 'User' }
          },
          {
            path: '/system/log',
            name: 'SystemLog',
            component: () => import('@/views/system/log.vue'),
            meta: { title: '操作日志', icon: 'Notebook' }
          },
          {
            path: '/system/backup',
            name: 'SystemBackup',
            component: () => import('@/views/system/backup.vue'),
            meta: { title: '数据备份', icon: 'FolderOpened' }
          },
          {
            path: '/system/integration',
            name: 'SystemIntegration',
            component: () => import('@/views/system/integration.vue'),
            meta: { title: '第三方集成', icon: 'Connection' }
          },
          {
            path: '/system/governance',
            name: 'SystemGovernance',
            component: () => import('@/views/system/governance.vue'),
            meta: { title: '治理控制台', icon: 'Operation' }
          },
          {
            path: '/system/config-center',
            name: 'SystemConfigCenter',
            component: () => import('@/views/system/config-center.vue'),
            meta: { title: '模板与汇率', icon: 'SetUp' }
          }
        ]
      },
      {
        path: '/profile',
        name: 'Profile',
        component: () => import('@/views/profile/index.vue'),
        meta: { title: '个人中心', hidden: true }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, _from, next) => {
  NProgress.start()
  document.title = to.meta.title ? `${to.meta.title} - ContractVision` : 'ContractVision'

  const token = localStorage.getItem('access_token')

  if (!to.meta.noAuth && !token) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }

  if (to.path === '/login' && token) {
    next({ path: '/dashboard' })
    return
  }

  if (token) {
    const userStore = useUserStore()
    if (!userStore.roles || userStore.roles.length === 0) {
      try {
        await userStore.getUserInfoAction()
        if (!userStore.roles || userStore.roles.length === 0) {
          clearAuth()
          userStore.resetState()
          next({ path: '/login', query: { redirect: to.fullPath } })
          return
        }
        next({ ...to, replace: true })
        return
      } catch (error) {
        clearAuth()
        userStore.resetState()
        next({ path: '/login', query: { redirect: to.fullPath } })
        return
      }
    }
  }

  next()
})

router.afterEach(() => {
  NProgress.done()
})

export default router
