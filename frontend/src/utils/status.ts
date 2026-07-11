export interface StatusInfo {
  code: string
  label: string
  color: string
  icon: string
  requiresDestination: 'required' | 'optional' | 'disabled'
  requiresReturnTime: 'required' | 'optional' | 'disabled'
}

export const STATUS_DEFINITIONS: Record<string, Omit<StatusInfo, 'code'>> = {
  PRESENT: {
    label: '在席',
    color: 'green',
    icon: 'mdi-checkbox-marked-circle-outline',
    requiresDestination: 'disabled',
    requiresReturnTime: 'disabled',
  },
  CUSTOMER: {
    label: '客先',
    color: 'cyan',
    icon: 'mdi-briefcase-outline',
    requiresDestination: 'required',
    requiresReturnTime: 'optional',
  },
  OUT: {
    label: '外出',
    color: 'orange',
    icon: 'mdi-walk',
    requiresDestination: 'required',
    requiresReturnTime: 'required',
  },
  MEETING: {
    label: '会議',
    color: 'blue',
    icon: 'mdi-account-multiple',
    requiresDestination: 'required',
    requiresReturnTime: 'optional',
  },
  REMOTE: {
    label: '在宅',
    color: 'light-green',
    icon: 'mdi-home-account',
    requiresDestination: 'disabled',
    requiresReturnTime: 'disabled',
  },
  HOLIDAY: {
    label: '休暇',
    color: 'grey',
    icon: 'mdi-island',
    requiresDestination: 'disabled',
    requiresReturnTime: 'disabled',
  },
  LEAVE: {
    label: '退社',
    color: 'red',
    icon: 'mdi-logout',
    requiresDestination: 'disabled',
    requiresReturnTime: 'disabled',
  },
  DIRECT_HOME: {
    label: '直帰',
    color: 'red',
    icon: 'mdi-arrow-right-bold-box-outline',
    requiresDestination: 'required',
    requiresReturnTime: 'disabled',
  },
}

export const getStatusColor = (status: string): string => {
  return STATUS_DEFINITIONS[status]?.color || 'grey'
}

export const getStatusIcon = (status: string): string => {
  return STATUS_DEFINITIONS[status]?.icon || 'mdi-help-circle-outline'
}

export const getStatusLabel = (status: string): string => {
  return STATUS_DEFINITIONS[status]?.label || status
}

export const getStatusDefinition = (status: string): StatusInfo => {
  const def = STATUS_DEFINITIONS[status]
  return {
    code: status,
    label: def?.label || status,
    color: def?.color || 'grey',
    icon: def?.icon || 'mdi-help-circle-outline',
    requiresDestination: def?.requiresDestination || 'disabled',
    requiresReturnTime: def?.requiresReturnTime || 'disabled',
  }
}
