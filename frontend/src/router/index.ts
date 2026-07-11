import { createRouter, createWebHistory } from 'vue-router'
import PresenceBoard from '../views/PresenceBoard.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'presence-board',
      component: PresenceBoard
    }
  ]
})

export default router
