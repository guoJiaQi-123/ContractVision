const DESIGN_COLORS = {
  primary: '#4a7cc9',
  primaryLight: '#5d8fd6',
  primaryDark: '#3a5fa0',
  success: '#30a56a',
  successLight: '#45bf80',
  warning: '#e88a2d',
  warningLight: '#f0a050',
  danger: '#d44040',
  dangerLight: '#e06060',
  secondary1: '#b55d8c',
  secondary2: '#45a3a3',
  secondary3: '#c49a3d',
  gray400: '#8a8f9e',
  gray500: '#6b7280',
}

export const CHART_COLORS = [
  DESIGN_COLORS.primary,
  DESIGN_COLORS.success,
  DESIGN_COLORS.warning,
  DESIGN_COLORS.danger,
  DESIGN_COLORS.secondary1,
  DESIGN_COLORS.secondary2,
  DESIGN_COLORS.secondary3,
  DESIGN_COLORS.primaryLight,
]

export const CHART_GRADIENT = {
  primary: [
    { offset: 0, color: DESIGN_COLORS.primaryLight },
    { offset: 1, color: DESIGN_COLORS.primary },
  ],
  primaryReverse: [
    { offset: 0, color: DESIGN_COLORS.primary },
    { offset: 1, color: DESIGN_COLORS.primaryLight },
  ],
}

export default DESIGN_COLORS
