import { defineStore } from 'pinia'
import { login } from '@/api/auth'
import { getProfile } from '@/api/user'
import { setToken, setRefreshToken, clearAuth } from '@/utils/auth'
import router from '@/router'

export const useUserStore = defineStore('user', {
  state: () => ({
    avatar: '',
    username: '',
    nickname: '',
    roles: [],
    email: '',
    phone: '',
    company_name: '',
    role: ''
  }),

  actions: {
    async loginAction(loginForm) {
      const res = await login(loginForm)
      const data = res.data
      setToken(data.access)
      setRefreshToken(data.refresh)
      await this.getUserInfoAction()
    },

    async getUserInfoAction() {
      const res = await getProfile()
      const data = res.data
      this.avatar = data.avatar || data.avatar_url || data.profile_avatar || ''
      this.username = data.username || ''
      this.nickname = data.nickname || data.username || ''
      this.email = data.email || ''
      this.phone = data.phone || ''
      this.company_name = data.company_name || ''
      this.role = data.role || ''
      this.roles = data.role ? [data.role] : []
    },

    logoutAction() {
      clearAuth()
      this.resetState()
      router.push('/login')
    },

    resetState() {
      this.avatar = ''
      this.username = ''
      this.nickname = ''
      this.roles = []
      this.email = ''
      this.phone = ''
      this.company_name = ''
      this.role = ''
    }
  }
})
