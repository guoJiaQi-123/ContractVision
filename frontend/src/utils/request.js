import axios from 'axios'
import { ElMessage } from 'element-plus'
import { getToken, clearAuth } from '@/utils/auth'

async function tryParseBlobError(blob) {
  if (!(blob instanceof Blob)) return null
  try {
    const text = await blob.text()
    if (!text) return null
    return JSON.parse(text)
  } catch {
    return null
  }
}

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
    // For file downloads (excel/pdf/csv/etc.), backend returns raw bytes rather than {code,data}.
    // Do NOT apply the JSON envelope check, otherwise all downloads will be rejected.
    const responseType = response?.config?.responseType
    if (responseType === 'blob' || responseType === 'arraybuffer') {
      return response.data
    }

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
  async (error) => {
    const response = error.response
    const blobJson = response?.data instanceof Blob ? await tryParseBlobError(response.data) : null
    const responseData = blobJson || response?.data

    if (response && response.status === 401) {
      const message = responseData?.message || '认证失败，请重新登录'
      ElMessage.warning(message)
      clearAuth()
      if (!isRedirecting) {
        isRedirecting = true
        window.location.href = '/login'
      }
    } else if (response && response.status === 400) {
      const firstFieldError = responseData?.data ? Object.values(responseData.data)[0] : null
      const message = firstFieldError || responseData?.message || '请求参数错误'
      ElMessage.error(message)
    } else {
      ElMessage.error(responseData?.message || '网络错误，请稍后重试')
    }
    return Promise.reject(error)
  }
)

export default service
