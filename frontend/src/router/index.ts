import { createRouter, createWebHistory } from 'vue-router'
import PresenceBoard from '../views/PresenceBoard.vue'
import AdminDashboard from '../views/AdminDashboard.vue'
import Login from '../views/Login.vue'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory('/'),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: Login
    },
    {
      path: '/',
      name: 'presence-board',
      component: PresenceBoard
    },
    {
      path: '/admin',
      name: 'admin-dashboard',
      component: AdminDashboard
    }
  ]
})

router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()

  // 認証チェックが初期化されていない場合はバックエンドに問い合わせる
  if (!authStore.isInitialized) {
    await authStore.checkAuth()
  }

  // ログインしていない状態でログイン画面以外にアクセスしようとした場合
  if (!authStore.isAuthenticated && to.name !== 'login') {
    next({ name: 'login' })
  }
  // ログイン済みの状態でログイン画面にアクセスしようとした場合
  else if (authStore.isAuthenticated && to.name === 'login') {
    next({ name: 'presence-board' })
  }
  else {
    next()
  }
})

export default router
