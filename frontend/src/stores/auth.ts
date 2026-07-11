import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  // 将来の認証機能実装と結合するが、現時点では仮のログインユーザー社員番号（E0001）を返す
  const currentUserNo = ref('E0001')

  return {
    currentUserNo
  }
})
