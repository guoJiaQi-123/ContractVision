import request from '@/utils/request'

export function getOperationLogs(params) {
  return request.get('/api/v1/system/logs/', { params })
}

export function getLogDetail(id) {
  return request.get(`/api/v1/system/logs/${id}/`)
}

export function getBackupList() {
  return request.get('/api/v1/system/backup/')
}

export function createBackup() {
  return request.post('/api/v1/system/backup/create/')
}

export function restoreBackup(data) {
  return request.post('/api/v1/system/backup/restore/', data)
}

export function deleteBackup(data) {
  return request.post('/api/v1/system/backup/delete/', data)
}

export function exportLogs(params) {
  return request.get('/api/v1/system/logs/export/', { params, responseType: 'blob' })
}

export function getIntegrationList() {
  return request.get('/api/v1/system/integrations/')
}

export function createIntegration(data) {
  return request.post('/api/v1/system/integrations/', data)
}

export function updateIntegration(id, data) {
  return request.put(`/api/v1/system/integrations/${id}/`, data)
}

export function deleteIntegration(id) {
  return request.delete(`/api/v1/system/integrations/${id}/`)
}

export function testIntegrationConnection(id) {
  return request.post(`/api/v1/system/integrations/${id}/test_connection/`)
}

export function toggleIntegrationStatus(id) {
  return request.post(`/api/v1/system/integrations/${id}/toggle_status/`)
}

export function getDataPermissionRules(params) {
  return request.get('/api/v1/system/data-permissions/', { params })
}

export function createDataPermissionRule(data) {
  return request.post('/api/v1/system/data-permissions/', data)
}

export function updateDataPermissionRule(id, data) {
  return request.put(`/api/v1/system/data-permissions/${id}/`, data)
}

export function deleteDataPermissionRule(id) {
  return request.delete(`/api/v1/system/data-permissions/${id}/`)
}

export function getAlertRules(params) {
  return request.get('/api/v1/system/alert-rules/', { params })
}

export function createAlertRule(data) {
  return request.post('/api/v1/system/alert-rules/', data)
}

export function updateAlertRule(id, data) {
  return request.put(`/api/v1/system/alert-rules/${id}/`, data)
}

export function getAlertRuleStrategyOptions() {
  return request.get('/api/v1/system/alert-rules/strategy_options/')
}

export function getAlertRulePreviewImpact(params) {
  return request.get('/api/v1/system/alert-rules/preview_impact/', { params })
}

export function getAlerts(params) {
  return request.get('/api/v1/system/alerts/', { params })
}

export function scanAlerts() {
  return request.post('/api/v1/system/alerts/scan/')
}

export function getAlertScanPreview(params) {
  return request.get('/api/v1/system/alerts/scan_preview/', { params })
}

export function exportAlertScanPreview(params) {
  return request.get('/api/v1/system/alerts/scan_preview_export/', { params, responseType: 'blob' })
}

export function getAlertScanSummary(params) {
  return request.get('/api/v1/system/alerts/scan_summary/', { params })
}

export function processAlert(id) {
  return request.post(`/api/v1/system/alerts/${id}/process/`)
}

export function getAlertCenter() {
  return request.get('/api/v1/system/alert-center/')
}

export function processAlertCenterItem(id) {
  return request.post(`/api/v1/system/alert-center/${id}/process/`)
}

export function getAlertWorkspace(params) {
  return request.get('/api/v1/system/alert-workspace/', { params })
}

export function getAlertWorkspaceDetail(id) {
  return request.get(`/api/v1/system/alert-workspace/${id}/`)
}

export function getAlertWorkspaceSummary() {
  return request.get('/api/v1/system/alert-workspace/summary/')
}

export function getAlertWorkspaceAssignees(params) {
  return request.get('/api/v1/system/alert-workspace/assignees/', { params })
}

export function processAlertWorkspaceItem(id) {
  return request.post(`/api/v1/system/alert-workspace/${id}/process/`)
}

export function processAlertWorkspaceBatch(data) {
  return request.post('/api/v1/system/alert-workspace/batch_process/', data)
}

export function reassignAlertWorkspaceItem(id, data) {
  return request.post(`/api/v1/system/alert-workspace/${id}/reassign/`, data)
}

export function getSalesTargets(params) {
  return request.get('/api/v1/system/sales-targets/', { params })
}

export function createSalesTarget(data) {
  return request.post('/api/v1/system/sales-targets/', data)
}

export function updateSalesTarget(id, data) {
  return request.put(`/api/v1/system/sales-targets/${id}/`, data)
}

export function getDashboardConfigs(params) {
  return request.get('/api/v1/system/dashboards/', { params })
}

export function createDashboardConfig(data) {
  return request.post('/api/v1/system/dashboards/', data)
}

export function updateDashboardConfig(id, data) {
  return request.put(`/api/v1/system/dashboards/${id}/`, data)
}

export function getDataTemplates(params) {
  return request.get('/api/v1/system/templates/', { params })
}

export function createDataTemplate(data) {
  return request.post('/api/v1/system/templates/', data)
}

export function updateDataTemplate(id, data) {
  return request.put(`/api/v1/system/templates/${id}/`, data)
}

export function getCurrencyRates(params) {
  return request.get('/api/v1/system/currency-rates/', { params })
}

export function createCurrencyRate(data) {
  return request.post('/api/v1/system/currency-rates/', data)
}

export function updateCurrencyRate(id, data) {
  return request.put(`/api/v1/system/currency-rates/${id}/`, data)
}

export function getStampTaxRules(params) {
  return request.get('/api/v1/system/stamp-tax-rules/', { params })
}

export function createStampTaxRule(data) {
  return request.post('/api/v1/system/stamp-tax-rules/', data)
}

export function updateStampTaxRule(id, data) {
  return request.put(`/api/v1/system/stamp-tax-rules/${id}/`, data)
}

export function getMobileDashboard() {
  return request.get('/api/v1/system/mobile-dashboard/')
}
