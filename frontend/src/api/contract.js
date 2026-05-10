import request from '@/utils/request'

export function getContractList(params) {
  return request.get('/api/v1/contracts/', { params })
}

export function getContractDetail(id) {
  return request.get(`/api/v1/contracts/${id}/`)
}

export function createContract(data) {
  return request.post('/api/v1/contracts/', data)
}

export function updateContract(id, data) {
  return request.put(`/api/v1/contracts/${id}/`, data)
}

export function deleteContract(id) {
  return request.delete(`/api/v1/contracts/${id}/`)
}

export function importContracts(formData) {
  return request.post('/api/v1/contracts/import/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function exportContracts(params) {
  return request.get('/api/v1/contracts/export/', {
    params,
    responseType: 'blob'
  })
}

export function batchDeleteContracts(ids) {
  return request.post('/api/v1/contracts/batch_delete/', { ids })
}

export function batchImportContracts(formData) {
  return request.post('/api/v1/contracts/batch_import/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function downloadImportTemplate() {
  return request.get('/api/v1/contracts/import_template/', {
    responseType: 'blob'
  })
}

export function exportContractsPdf(params) {
  return request.get('/api/v1/contracts/export_pdf/', {
    params,
    responseType: 'blob'
  })
}

export function exportContractDetailPdf(id) {
  return request.get(`/api/v1/contracts/${id}/detail_pdf/`, {
    responseType: 'blob'
  })
}

export function getContractFulfillment(id) {
  return request.get(`/api/v1/contracts/${id}/fulfillment/`)
}

export function getContractRenewalSummary(params) {
  return request.get('/api/v1/contracts/renewal_summary/', { params })
}

export function renewContract(id, data) {
  return request.post(`/api/v1/contracts/${id}/renew/`, data)
}

export function terminateContract(id, data) {
  return request.post(`/api/v1/contracts/${id}/terminate/`, data)
}

export function recalculateContractQuality(id) {
  return request.post(`/api/v1/contracts/${id}/recalculate_quality/`)
}

export function getPaymentPlans(params) {
  return request.get('/api/v1/contracts/payment-plans/', { params })
}

export function createPaymentPlan(data) {
  return request.post('/api/v1/contracts/payment-plans/', data)
}

export function updatePaymentPlan(id, data) {
  return request.put(`/api/v1/contracts/payment-plans/${id}/`, data)
}

export function markPaymentPlanPaid(id, data) {
  return request.post(`/api/v1/contracts/payment-plans/${id}/mark_paid/`, data)
}

export function getPaymentPlanOverview(params) {
  return request.get('/api/v1/contracts/payment-plans/overview/', { params })
}

export function getContractMilestones(params) {
  return request.get('/api/v1/contracts/milestones/', { params })
}

export function createContractMilestone(data) {
  return request.post('/api/v1/contracts/milestones/', data)
}

export function updateContractMilestone(id, data) {
  return request.put(`/api/v1/contracts/milestones/${id}/`, data)
}

export function completeContractMilestone(id, data) {
  return request.post(`/api/v1/contracts/milestones/${id}/mark_complete/`, data)
}

export function getContractChangeRequests(params) {
  return request.get('/api/v1/contracts/change-requests/', { params })
}

export function createContractChangeRequest(data) {
  return request.post('/api/v1/contracts/change-requests/', data)
}

export function approveContractChangeRequest(id, data) {
  return request.post(`/api/v1/contracts/change-requests/${id}/approve/`, data)
}

export function rejectContractChangeRequest(id, data) {
  return request.post(`/api/v1/contracts/change-requests/${id}/reject/`, data)
}

export function getApprovalProcesses(params) {
  return request.get('/api/v1/contracts/approval-processes/', { params })
}

export function createApprovalProcess(data) {
  return request.post('/api/v1/contracts/approval-processes/', data)
}

export function updateApprovalProcess(id, data) {
  return request.put(`/api/v1/contracts/approval-processes/${id}/`, data)
}

export function getApprovalRequests(params) {
  return request.get('/api/v1/contracts/approval-requests/', { params })
}

export function approveApprovalRequest(id, data) {
  return request.post(`/api/v1/contracts/approval-requests/${id}/approve/`, data)
}

export function rejectApprovalRequest(id, data) {
  return request.post(`/api/v1/contracts/approval-requests/${id}/reject/`, data)
}

export function getContractQualityReport(params) {
  return request.get('/api/v1/contracts/quality-report/', { params })
}

export function getDuplicateContractGroups() {
  return request.get('/api/v1/contracts/duplicate-scan/')
}

export function mergeDuplicateContracts(data) {
  return request.post('/api/v1/contracts/duplicate-scan/', data)
}
