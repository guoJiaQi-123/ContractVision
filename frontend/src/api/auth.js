import request from '@/utils/request'

export function login(data) {
  return request.post('/api/v1/auth/login/', data)
}

export function register(data) {
  return request.post('/api/v1/auth/register/', data)
}

export function refreshToken(data) {
  return request.post('/api/v1/auth/token/refresh/', data)
}

export function changePassword(data) {
  return request.post('/api/v1/auth/change-password/', data)
}

export function resetPassword(data) {
  return request.post('/api/v1/auth/password-reset/', data)
}
