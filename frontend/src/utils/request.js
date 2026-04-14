import axios from 'axios'
import { ElMessage } from 'element-plus'
import { getToken, clearAuth } from '@/utils/auth'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 15000
})

service.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

let isRedirecting = false

service.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res.code !== 200) {
      ElMessage.error(res.message || '请求失败')
      if (res.code === 401) {
        clearAuth()
        if (!isRedirecting) {
          isRedirecting = true
          window.location.href = '/login'
        }
      }
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res
  },
  (error) => {
    const response = error.response
    if (response && response.status === 401) {
      const message = response.data?.message || '认证失败，请重新登录'
      ElMessage.warning(message)
      clearAuth()
      if (!isRedirecting) {
        isRedirecting = true
        window.location.href = '/login'
      }
    } else if (response && response.status === 400) {
      const resData = response.data
      const firstFieldError = resData?.data ? Object.values(resData.data)[0] : null
      const message = firstFieldError || resData?.message || '请求参数错误'
      ElMessage.error(message)
    } else {
      ElMessage.error(response?.data?.message || '网络错误，请稍后重试')
    }
    return Promise.reject(error)
  }
)

export default service
