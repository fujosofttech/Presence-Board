<template>
  <v-container class="fill-height login-container" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="5" lg="4">
        <v-card class="elevation-12 glass-card pa-6 text-center animate-fade-in">
          <v-card-item class="mb-4">
            <div class="d-flex justify-center mb-3">
              <v-avatar color="teal-darken-2" size="64" class="elevation-4 logo-avatar">
                <v-icon icon="mdi-view-dashboard-outline" size="36" color="white" />
              </v-avatar>
            </div>
            <v-card-title class="text-h5 font-weight-bold text-slate-800">
              社内行先・在席管理システム
            </v-card-title>
            <v-card-subtitle class="text-subtitle-2 text-grey-darken-1 mt-1">
              サインインして在席ボードにアクセスします
            </v-card-subtitle>
          </v-card-item>

          <v-card-text>
            <v-form @submit.prevent="handleLogin" ref="loginForm" v-model="isFormValid">
              <v-text-field
                v-model="username"
                label="ユーザー名 (または社員番号)"
                prepend-inner-icon="mdi-account"
                variant="outlined"
                density="comfortable"
                color="teal-darken-2"
                class="mb-3"
                :rules="[v => !!v || 'ユーザー名を入力してください']"
                required
              ></v-text-field>

              <v-text-field
                v-model="password"
                label="パスワード"
                prepend-inner-icon="mdi-lock"
                :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                :type="showPassword ? 'text' : 'password'"
                variant="outlined"
                density="comfortable"
                color="teal-darken-2"
                class="mb-4"
                @click:append-inner="showPassword = !showPassword"
                :rules="[v => !!v || 'パスワードを入力してください']"
                required
              ></v-text-field>

              <v-alert
                v-if="errorMessage"
                type="error"
                variant="tonal"
                closable
                density="compact"
                class="text-left mb-4 text-caption font-weight-bold"
                @click:close="errorMessage = ''"
              >
                {{ errorMessage }}
              </v-alert>

              <v-btn
                type="submit"
                color="teal-darken-2"
                size="large"
                block
                class="font-weight-bold text-white shadow-sm py-3"
                elevation="2"
                :loading="isLoading"
                :disabled="!isFormValid"
              >
                サインイン
              </v-btn>
            </v-form>
          </v-card-text>

          <v-card-actions class="justify-center mt-4">
            <span class="text-caption text-grey-darken-1">
              管理者用ログイン: admin / admin1234
            </span>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const isLoading = ref(false)
const isFormValid = ref(false)
const errorMessage = ref('')

const handleLogin = async () => {
  if (!username.value || !password.value) return

  isLoading.value = true
  errorMessage.value = ''

  try {
    await authStore.login(username.value, password.value)
    router.push('/')
  } catch (err: any) {
    console.error('Login failed:', err)
    if (err.response && err.response.data && err.response.data.message) {
      errorMessage.value = err.response.data.message
    } else {
      errorMessage.value = '接続エラーが発生しました。ユーザー名またはパスワードが間違っているか、サーバーに接続できません。'
    }
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.login-container {
  background: linear-gradient(135deg, #1e3a8a 0%, #0d9488 100%);
  min-height: 100vh;
  width: 100%;
}

.glass-card {
  background: rgba(255, 255, 255, 0.9) !important;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px !important;
}

.logo-avatar {
  transition: transform 0.3s ease;
}

.logo-avatar:hover {
  transform: rotate(15deg) scale(1.1);
}

.animate-fade-in {
  animation: fadeIn 0.6s ease-out forwards;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
