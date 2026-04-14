import request from '@/utils/request'

export function getDashboardStats() {
  return request.get('/api/v1/analytics/dashboard/')
}

export function getContractTrend(params) {
  return request.get('/api/v1/analytics/trend/', { params })
}

export function getRegionDistribution(params) {
  return request.get('/api/v1/analytics/region/', { params })
}

export function getStatusDistribution(params) {
  return request.get('/api/v1/analytics/status/', { params })
}

export function getTopClients(params) {
  return request.get('/api/v1/analytics/top-clients/', { params })
}

export function getSalespersonRanking(params) {
  return request.get('/api/v1/analytics/salesperson-ranking/', { params })
}

export function getProductDistribution(params) {
  return request.get('/api/v1/analytics/product/', { params })
}

export function getMonthlyTrend(params) {
  return request.get('/api/v1/analytics/monthly-trend/', { params })
}

export function getDepartmentRanking(params) {
  return request.get('/api/v1/analytics/department-ranking/', { params })
}

export function getOverviewSummary() {
  return request.get('/api/v1/analytics/overview-summary/')
}

export function generateReport(data) {
  return request.post('/api/v1/analytics/report/generate/', data)
}

export function exportReport(data) {
  return request.post('/api/v1/analytics/report/export/', data, {
    responseType: 'blob'
  })
}

export function getSalesPrediction(data) {
  return request.post('/api/v1/analytics/prediction/', data)
}

export function getAnomalyDetection() {
  return request.get('/api/v1/analytics/anomaly-detection/')
}

export function getCustomerValue() {
  return request.get('/api/v1/analytics/customer-value/')
}

export function getSalesTargetProgress(params) {
  return request.get('/api/v1/analytics/target-progress/', { params })
}

export function getDashboardData(params) {
  return request.get('/api/v1/analytics/dashboard-data/', { params })
}

export function getDrilldownAnalysis(params) {
  return request.get('/api/v1/analytics/drilldown/', { params })
}

export function getTeamPerformance(params) {
  return request.get('/api/v1/analytics/team-performance/', { params })
}

export function getTaxAnalysis(params) {
  return request.get('/api/v1/analytics/tax-analysis/', { params })
}
