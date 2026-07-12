import { createRouter, createWebHistory } from 'vue-router'
import PresenceBoard from '../views/PresenceBoard.vue'
import AdminDashboard from '../views/AdminDashboard.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
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

export default router
