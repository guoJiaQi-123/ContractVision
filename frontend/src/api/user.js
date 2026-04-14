import request from '@/utils/request'

export function getProfile() {
  return request.get('/api/v1/users/profile/')
}

export function updateProfile(data) {
  return request.put('/api/v1/users/profile/', data)
}

export function getUserList(params) {
  return request.get('/api/v1/users/manage/', { params })
}

export function getUserDetail(id) {
  return request.get(`/api/v1/users/manage/${id}/`)
}

export function createUser(data) {
  return request.post('/api/v1/users/manage/', data)
}

export function updateUser(id, data) {
  return request.put(`/api/v1/users/manage/${id}/`, data)
}

export function deleteUser(id) {
  return request.delete(`/api/v1/users/manage/${id}/`)
}

export function toggleUserActive(id) {
  return request.post(`/api/v1/users/manage/${id}/toggle_active/`)
}

export function assignUserRole(id, data) {
  return request.post(`/api/v1/users/manage/${id}/assign_role/`, data)
}
