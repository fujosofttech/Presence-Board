import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export const useAuthStore = defineStore('auth', () => {
  const isAuthenticated = ref(false)
  const currentUserNo = ref<string | null>(null)
  const currentUserName = ref<string | null>(null)
  const currentUserEmail = ref<string | null>(null)
  const isStaff = ref(false)
  const isInitialized = ref(false)

  const setAuthData = (data: any) => {
    if (data.authenticated) {
      isAuthenticated.value = true
      currentUserNo.value = data.employee ? data.employee.employee_no : null
      currentUserName.value = data.employee ? data.employee.name : (data.user ? data.user.username : 'ゲスト')
      currentUserEmail.value = data.user ? data.user.email : null
      isStaff.value = data.user ? data.user.is_staff : false
    } else {
      clearAuthData()
    }
  }

  const clearAuthData = () => {
    isAuthenticated.value = false
    currentUserNo.value = null
    currentUserName.value = null
    currentUserEmail.value = null
    isStaff.value = false
  }

  const checkAuth = async () => {
    try {
      const res = await api.get('/auth/')
      setAuthData(res.data)
    } catch (err) {
      clearAuthData()
    } finally {
      isInitialized.value = true
    }
  }

  const login = async (username: string, password: string) => {
    try {
      const res = await api.post('/auth/', { username, password })
      setAuthData(res.data)
      return res.data
    } catch (err) {
      clearAuthData()
      throw err
    }
  }

  const logout = async () => {
    try {
      await api.post('/auth/logout/')
    } catch (err) {
      console.error('Logout API failed:', err)
    } finally {
      clearAuthData()
    }
  }

  return {
    isAuthenticated,
    currentUserNo,
    currentUserName,
    currentUserEmail,
    isStaff,
    isInitialized,
    checkAuth,
    login,
    logout
  }
})
