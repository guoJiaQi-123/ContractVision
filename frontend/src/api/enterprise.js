import request from '@/utils/request'

export function getDepartmentList(params) {
  return request.get('/api/v1/system/departments/', { params })
}

export function getDepartmentDetail(id) {
  return request.get(`/api/v1/system/departments/${id}/`)
}

export function createDepartment(data) {
  return request.post('/api/v1/system/departments/', data)
}

export function updateDepartment(id, data) {
  return request.put(`/api/v1/system/departments/${id}/`, data)
}

export function deleteDepartment(id) {
  return request.delete(`/api/v1/system/departments/${id}/`)
}

export function getDepartmentOptions() {
  return request.get('/api/v1/system/departments/options/')
}

export function getDepartmentTree() {
  return request.get('/api/v1/system/departments/tree/')
}

export function getDepartmentAdminUsers() {
  return request.get('/api/v1/system/departments/admin_users/')
}

export function generateDepartmentCode() {
  return request.get('/api/v1/system/departments/generate_code/')
}

export function getProductTypeList(params) {
  return request.get('/api/v1/system/product-types/', { params })
}

export function getProductTypeDetail(id) {
  return request.get(`/api/v1/system/product-types/${id}/`)
}

export function createProductType(data) {
  return request.post('/api/v1/system/product-types/', data)
}

export function updateProductType(id, data) {
  return request.put(`/api/v1/system/product-types/${id}/`, data)
}

export function deleteProductType(id) {
  return request.delete(`/api/v1/system/product-types/${id}/`)
}

export function getProductTypeOptions() {
  return request.get('/api/v1/system/product-types/options/')
}

export function generateProductTypeCode() {
  return request.get('/api/v1/system/product-types/generate_code/')
}

export function getCustomerList(params) {
  return request.get('/api/v1/system/customers/', { params })
}

export function getCustomerDetail(id) {
  return request.get(`/api/v1/system/customers/${id}/`)
}

export function createCustomer(data) {
  return request.post('/api/v1/system/customers/', data)
}

export function updateCustomer(id, data) {
  return request.put(`/api/v1/system/customers/${id}/`, data)
}

export function deleteCustomer(id) {
  return request.delete(`/api/v1/system/customers/${id}/`)
}

export function getCustomerOptions() {
  return request.get('/api/v1/system/customers/options/')
}

export function generateCustomerCode() {
  return request.get('/api/v1/system/customers/generate_code/')
}

export function generateContractNo() {
  return request.get('/api/v1/contracts/generate_contract_no/')
}

export function getSalespersonOptions() {
  return request.get('/api/v1/contracts/salesperson_options/')
}
