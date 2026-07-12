<template>
  <v-container class="fill-height bg-grey-lighten-4 py-6" fluid>
    <!-- ナビゲーションバー -->
    <v-app-bar color="teal-darken-3" elevation="2">
      <v-app-bar-title class="font-weight-bold text-h6">
        <v-icon icon="mdi-view-dashboard-outline" class="mr-2" />
        社内行先・在席管理システム
      </v-app-bar-title>
      <v-spacer></v-spacer>
      <v-chip class="mr-4 text-subtitle-1" color="teal-lighten-4" variant="flat">
        <v-icon icon="mdi-account" class="mr-1" />
        {{ myInfo?.name || 'ゲスト' }} (自分)
      </v-chip>
    </v-app-bar>

    <v-row class="justify-center mt-12 w-100">
      <v-col cols="12" md="10" lg="9">
        
        <!-- 自分（ログイン中の利用者）のステータス表示カード (最上部固定) -->
        <v-card v-if="myInfo" class="mb-6 border-s-lg border-teal shadow-lg" elevation="2">
          <v-card-text class="d-flex flex-wrap align-center justify-space-between py-4">
            <div class="d-flex align-center">
              <v-avatar color="teal-lighten-4" size="50" class="mr-4">
                <span class="text-teal-darken-3 font-weight-bold text-h6">{{ myInfo.name[0] }}</span>
              </v-avatar>
              <div>
                <div class="text-subtitle-2 text-grey">現在の自分の状況</div>
                <div class="text-h6 font-weight-bold">{{ myInfo.name }}</div>
              </div>
            </div>
            
            <div class="d-flex align-center flex-wrap gap-4 mt-2 mt-sm-0">
              <!-- 状態表示チップ -->
              <v-chip :color="getStatusColor(myPresence.status)" variant="flat" size="large" class="font-weight-bold text-white">
                <v-icon :icon="getStatusIcon(myPresence.status)" class="mr-1" />
                {{ getStatusLabel(myPresence.status) }}
              </v-chip>
              
              <!-- 行先・戻り予定 -->
              <div class="text-body-1 ml-4" v-if="myPresence.destination">
                <span class="text-grey-darken-1">行先:</span> <strong>{{ myPresence.destination }}</strong>
              </div>
              <div class="text-body-1 ml-4" v-if="myPresence.end_datetime">
                <span class="text-grey-darken-1">戻り予定:</span> <strong>{{ formatTimeOnly(myPresence.end_datetime) }}</strong>
              </div>

              <!-- 状況更新ボタン -->
              <v-btn
                color="teal-darken-2"
                prepend-icon="mdi-pencil"
                class="ml-6 font-weight-bold text-white"
                elevation="1"
                @click="openUpdateDialog"
              >
                状況を更新
              </v-btn>
            </div>
          </v-card-text>
        </v-card>

        <!-- 検索・絞り込みフィルターエリア -->
        <v-card class="mb-6 py-3 px-4" elevation="1">
          <v-row dense align="center">
            <!-- 課での絞り込み -->
            <v-col cols="12" sm="5">
              <v-select
                v-model="selectedDepartment"
                :items="departments"
                item-title="name"
                item-value="id"
                label="所属課"
                prepend-inner-icon="mdi-domain"
                variant="outlined"
                density="comfortable"
                hide-details
              ></v-select>
            </v-col>
            
            <!-- 氏名検索 -->
            <v-col cols="12" sm="7">
              <v-text-field
                v-model="searchQuery"
                label="氏名または社員番号で検索"
                prepend-inner-icon="mdi-magnify"
                variant="outlined"
                density="comfortable"
                clearable
                hide-details
              ></v-text-field>
            </v-col>
          </v-row>
        </v-card>

        <!-- 社員一覧エリア (グループごとにセクション分け) -->
        <div v-for="group in filteredGroups" :key="group.id" class="mb-6">
          <div class="text-h6 font-weight-bold text-grey-darken-3 mb-3 d-flex align-center">
            <v-icon icon="mdi-account-group-outline" class="mr-2" color="teal-darken-1" />
            {{ group.departmentName }} - {{ group.name }}
          </div>

          <v-card elevation="1">
            <v-table>
              <thead>
                <tr class="bg-teal-lighten-5">
                  <th class="text-subtitle-2 font-weight-bold text-teal-darken-4" style="width: 15%">状態</th>
                  <th class="text-subtitle-2 font-weight-bold text-teal-darken-4" style="width: 20%">氏名</th>
                  <th class="text-subtitle-2 font-weight-bold text-teal-darken-4" style="width: 30%">行先</th>
                  <th class="text-subtitle-2 font-weight-bold text-teal-darken-4" style="width: 20%">予定</th>
                  <th class="text-subtitle-2 font-weight-bold text-teal-darken-4 text-right" style="width: 15%">更新時刻</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="emp in group.employees"
                  :key="emp.id"
                  :class="{ 'highlight-row': activeHighlights[emp.employee_no] }"
                  class="transition-all"
                >
                  <!-- 状態 -->
                  <td>
                    <v-chip
                      :color="getStatusColor(emp.presence.status)"
                      size="small"
                      class="font-weight-bold text-white"
                      variant="flat"
                    >
                      <v-icon :icon="getStatusIcon(emp.presence.status)" class="mr-1" size="small" />
                      {{ getStatusLabel(emp.presence.status) }}
                    </v-chip>
                  </td>

                  <!-- 氏名 -->
                  <td class="font-weight-bold">
                    {{ emp.name }}
                    <span v-if="emp.employee_no === myInfo?.employee_no" class="text-caption text-teal ml-1">(自分)</span>
                  </td>

                  <!-- 行先 -->
                  <td class="text-grey-darken-2">
                    {{ emp.presence.destination || '－' }}
                  </td>

                  <!-- 予定 -->
                  <td class="text-grey-darken-2">
                    <span v-if="emp.presence.end_datetime">{{ formatTimeOnly(emp.presence.end_datetime) }} まで</span>
                    <span v-else>－</span>
                  </td>

                  <!-- 更新時刻 -->
                  <td class="text-right text-caption text-grey">
                    {{ formatTimeOnly(emp.presence.updated_at) }}
                  </td>
                </tr>
                <tr v-if="group.employees.length === 0">
                  <td colspan="5" class="text-center text-grey py-4">該当する社員がいません</td>
                </tr>
              </tbody>
            </v-table>
          </v-card>
        </div>

        <v-alert
          v-if="filteredGroups.length === 0"
          type="info"
          variant="tonal"
          class="text-center"
        >
          表示する社員が見つかりません。
        </v-alert>

      </v-col>
    </v-row>

    <!-- 状況更新ダイアログ -->
    <v-dialog v-model="dialog" max-width="600px" persistent>
      <v-card class="rounded-lg">
        <v-card-title class="bg-teal-darken-3 text-white py-4 d-flex align-center">
          <v-icon icon="mdi-pencil-box-outline" class="mr-2" />
          <span class="font-weight-bold text-h6">自分の状況を更新</span>
          <v-spacer></v-spacer>
          <v-btn icon="mdi-close" variant="text" color="white" @click="closeUpdateDialog"></v-btn>
        </v-card-title>

        <v-card-text class="py-6 px-6">
          <div class="mb-4">
            <label class="text-subtitle-2 font-weight-bold text-grey-darken-3 d-block mb-2">ステータス</label>
            <v-row dense>
              <v-col
                v-for="(def, key) in STATUS_DEFINITIONS"
                :key="key"
                cols="6"
                sm="3"
              >
                <v-btn
                  block
                  :color="form.status === key ? def.color : 'grey-lighten-4'"
                  :variant="form.status === key ? 'flat' : 'outlined'"
                  :class="{'text-white': form.status === key, 'text-grey-darken-2': form.status !== key}"
                  class="font-weight-bold py-2"
                  @click="selectStatus(key)"
                >
                  <v-icon :icon="def.icon" class="mr-1" size="small" />
                  {{ def.label }}
                </v-btn>
              </v-col>
            </v-row>
          </div>

          <!-- 行先入力 (状態ルールに応じて表示) -->
          <v-row v-if="statusRule.requiresDestination !== 'disabled'">
            <v-col cols="12">
              <v-text-field
                v-model="form.destination"
                :label="'行先' + (statusRule.requiresDestination === 'required' ? ' (必須)' : ' (任意)')"
                :rules="[v => (statusRule.requiresDestination !== 'required' || !!v) || '行先を入力してください']"
                prepend-inner-icon="mdi-map-marker-outline"
                variant="outlined"
                color="teal"
                clearable
              >
                <!-- お気に入り追加/削除ボタン -->
                <template v-slot:append-inner>
                  <v-btn
                    v-if="form.destination"
                    icon
                    variant="text"
                    size="small"
                    :color="isFavorite(form.destination) ? 'amber-darken-2' : 'grey'"
                    @click="toggleFavorite(form.destination)"
                  >
                    <v-icon>{{ isFavorite(form.destination) ? 'mdi-star' : 'mdi-star-outline' }}</v-icon>
                  </v-btn>
                </template>
              </v-text-field>

              <!-- 行先候補表示 -->
              <div class="mt-2" v-if="favorites.length > 0 || recents.length > 0">
                <div v-if="favorites.length > 0" class="mb-1">
                  <span class="text-caption text-grey mr-2">お気に入り:</span>
                  <v-chip
                    v-for="fav in favorites"
                    :key="fav.id"
                    size="small"
                    class="mr-2 mb-1"
                    color="amber-darken-4"
                    variant="outlined"
                    @click="form.destination = fav.destination"
                  >
                    <v-icon icon="mdi-star" size="x-small" class="mr-1" color="amber-darken-2" />
                    {{ fav.destination }}
                  </v-chip>
                </div>
                <div v-if="recents.length > 0">
                  <span class="text-caption text-grey mr-2">最近の履歴:</span>
                  <v-chip
                    v-for="(rec, idx) in recents"
                    :key="'rec'+idx"
                    size="small"
                    class="mr-2 mb-1"
                    color="grey-darken-1"
                    variant="outlined"
                    @click="form.destination = rec.destination"
                  >
                    <v-icon icon="mdi-history" size="x-small" class="mr-1" />
                    {{ rec.destination }}
                  </v-chip>
                </div>
              </div>
            </v-col>
          </v-row>

          <!-- 戻り予定時間入力 (状態ルールに応じて表示) -->
          <v-row v-if="statusRule.requiresReturnTime !== 'disabled'">
            <v-col cols="12">
              <v-text-field
                v-model="form.returnTimeRaw"
                :label="'戻り予定時間' + (statusRule.requiresReturnTime === 'required' ? ' (必須)' : ' (任意)')"
                :rules="[v => (statusRule.requiresReturnTime !== 'required' || !!v) || '戻り予定時間を入力してください']"
                prepend-inner-icon="mdi-clock-outline"
                type="time"
                variant="outlined"
                color="teal"
              ></v-text-field>
            </v-col>
          </v-row>

          <v-alert
            v-if="errorMessage"
            type="error"
            variant="tonal"
            class="mt-4"
            density="compact"
          >
            {{ errorMessage }}
          </v-alert>
        </v-card-text>

        <v-card-actions class="px-6 pb-6 pt-0">
          <v-spacer></v-spacer>
          <v-btn
            color="grey-darken-1"
            variant="text"
            class="font-weight-bold mr-2"
            @click="closeUpdateDialog"
          >
            キャンセル
          </v-btn>
          <v-btn
            color="teal-darken-2"
            variant="flat"
            class="font-weight-bold text-white px-6"
            :loading="submitting"
            @click="submitUpdate"
          >
            保存する
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { usePresenceSSE } from '../composables/usePresenceSSE'
import {
  STATUS_DEFINITIONS,
  getStatusColor,
  getStatusIcon,
  getStatusLabel,
  getStatusDefinition,
  StatusInfo
} from '../utils/status'
import api from '../services/api'

// インターフェース定義
interface Presence {
  status: string
  destination: string
  start_datetime: string | null
  end_datetime: string | null
  updated_at: string | null
}

interface Employee {
  id: number
  employee_no: string
  name: string
  email: string
  department: number
  department_name: string
  group: number
  group_name: string
  work_location: number | null
  phone_number: string
  display_order: number
  presence: Presence
}

interface Department {
  id: number | null
  name: string
}

interface GroupWithEmployees {
  id: number
  name: string
  departmentId: number
  departmentName: string
  employees: Employee[]
}

interface FavoriteDestination {
  id: number
  destination: string
  display_order: number
}

interface RecentDestination {
  destination: string
}

// ストア
const authStore = useAuthStore()

// リアクティブデータ
const employees = ref<Employee[]>([])
const departments = ref<Department[]>([{ id: null, name: '全課' }])
const selectedDepartment = ref<number | null>(null)
const searchQuery = ref('')
const activeHighlights = ref<Record<string, boolean>>({})

// ダイアログ・フォーム状態
const dialog = ref(false)
const submitting = ref(false)
const errorMessage = ref('')
const form = ref({
  status: 'PRESENT',
  destination: '',
  returnTimeRaw: ''
})

const favorites = ref<FavoriteDestination[]>([])
const recents = ref<RecentDestination[]>([])

// 選択中のステータスの定義ルール
const statusRule = computed<StatusInfo>(() => {
  return getStatusDefinition(form.value.status)
})

// ログイン中の「自分」の情報
const myInfo = computed(() => {
  return employees.value.find(e => e.employee_no === authStore.currentUserNo) || null
})

// 自分の在籍状態（Presence）
const myPresence = computed<Presence>(() => {
  if (myInfo.value) {
    return myInfo.value.presence
  }
  return {
    status: 'PRESENT',
    destination: '',
    start_datetime: null,
    end_datetime: null,
    updated_at: null
  }
})

// グループ別に社員をマッピングし、フィルター適用後のデータを取得
const filteredGroups = computed<GroupWithEmployees[]>(() => {
  const groupsMap: Record<number, GroupWithEmployees> = {}

  // 1. 各社員のフィルタリング
  const filteredEmployees = employees.value.filter(emp => {
    // 課での絞り込み
    if (selectedDepartment.value !== null && emp.department !== selectedDepartment.value) {
      return false
    }
    // 検索ワードでの絞り込み
    if (searchQuery.value) {
      const q = searchQuery.value.toLowerCase()
      return emp.name.toLowerCase().includes(q) || emp.employee_no.toLowerCase().includes(q)
    }
    return true
  })

  // 2. 所属グループごとに分類
  filteredEmployees.forEach(emp => {
    if (!groupsMap[emp.group]) {
      groupsMap[emp.group] = {
        id: emp.group,
        name: emp.group_name,
        departmentId: emp.department,
        departmentName: emp.department_name,
        employees: []
      }
    }
    groupsMap[emp.group].employees.push(emp)
  })

  // 3. 各グループ内の社員のソート（表示順: 1. display_order, 2. 氏名）
  Object.values(groupsMap).forEach(g => {
    g.employees.sort((a, b) => {
      // ログイン中の「自分」を一番上に置く
      if (a.employee_no === authStore.currentUserNo) return -1
      if (b.employee_no === authStore.currentUserNo) return 1
      
      if (a.display_order !== b.display_order) {
        return a.display_order - b.display_order
      }
      return a.name.localeCompare(b.name, 'ja')
    })
  })

  // 4. グループ自体のソート
  return Object.values(groupsMap).sort((a, b) => {
    return a.departmentId - b.departmentId || a.id - b.id
  })
})

// 初期データ（一覧）の読み込み
const loadInitialData = async () => {
  try {
    const [deptRes, presRes, favRes, recRes] = await Promise.all([
      api.get('/departments/'),
      api.get('/presence/'),
      api.get('/destinations/favorites/'),
      api.get('/destinations/recent/')
    ])
    
    departments.value = [{ id: null, name: '全課' }, ...deptRes.data]
    employees.value = presRes.data
    favorites.value = favRes.data
    recents.value = recRes.data
  } catch (error) {
    console.error('Failed to load initial data:', error)
  }
}

// お気に入り関連の処理
const isFavorite = (dest: string) => {
  return favorites.value.some(f => f.destination === dest)
}

const toggleFavorite = async (dest: string) => {
  if (!dest) return
  const existing = favorites.value.find(f => f.destination === dest)
  try {
    if (existing) {
      await api.delete(`/destinations/favorites/${existing.id}/`)
      favorites.value = favorites.value.filter(f => f.id !== existing.id)
    } else {
      const res = await api.post('/destinations/favorites/', { destination: dest, display_order: 0 })
      favorites.value.push(res.data)
    }
  } catch (e) {
    console.error('Failed to toggle favorite', e)
  }
}

// 時刻表示のみのフォーマット（HH:mm）
const formatTimeOnly = (isoString: string | null) => {
  if (!isoString) return '－'
  try {
    const d = new Date(isoString)
    if (isNaN(d.getTime())) {
      // 既に "10:30" などの文字列の場合はそのまま返す
      return isoString
    }
    const hh = String(d.getHours()).padStart(2, '0')
    const mm = String(d.getMinutes()).padStart(2, '0')
    return `${hh}:${mm}`
  } catch (e) {
    return isoString
  }
}

// 戻り予定時間（HH:mm）の抽出
const extractTime = (isoString: string | null) => {
  if (!isoString) return ''
  try {
    const d = new Date(isoString)
    if (isNaN(d.getTime())) return ''
    const hh = String(d.getHours()).padStart(2, '0')
    const mm = String(d.getMinutes()).padStart(2, '0')
    return `${hh}:${mm}`
  } catch (e) {
    return ''
  }
}

// 送信用に現在日付と入力時間を結合したISO8601文字列を生成
const generateISODatetime = (timeStr: string) => {
  if (!timeStr) return null
  const today = new Date()
  const yyyy = today.getFullYear()
  const mm = String(today.getMonth() + 1).padStart(2, '0')
  const dd = String(today.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}T${timeStr}:00+09:00` // JSTタイムゾーン
}

// 状況更新ダイアログを開く
const openUpdateDialog = () => {
  if (myPresence.value) {
    form.value.status = myPresence.value.status
    form.value.destination = myPresence.value.destination || ''
    form.value.returnTimeRaw = extractTime(myPresence.value.end_datetime)
  }
  errorMessage.value = ''
  dialog.value = true
}

const closeUpdateDialog = () => {
  dialog.value = false
  errorMessage.value = ''
}

const selectStatus = (statusKey: string) => {
  form.value.status = statusKey
  
  // 状態が切り替わったら、不要な項目のフォーム入力をクリアする
  const def = getStatusDefinition(statusKey)
  if (def.requiresDestination === 'disabled') {
    form.value.destination = ''
  }
  if (def.requiresReturnTime === 'disabled') {
    form.value.returnTimeRaw = ''
  }
}

// 状況更新の送信
const submitUpdate = async () => {
  errorMessage.value = ''
  
  // フロントエンド簡易チェック
  if (statusRule.value.requiresDestination === 'required' && !form.value.destination) {
    errorMessage.value = '行先を入力してください。'
    return
  }
  if (statusRule.value.requiresReturnTime === 'required' && !form.value.returnTimeRaw) {
    errorMessage.value = '戻り予定時間を入力してください。'
    return
  }

  submitting.value = true
  try {
    const payload = {
      status: form.value.status,
      destination: form.value.destination,
      return_time: generateISODatetime(form.value.returnTimeRaw)
    }

    const res = await api.patch('/presence/me/', payload)
    
    // 成功時、ローカルのデータも更新する（APIレスポンスから反映）
    const myEmp = employees.value.find(e => e.employee_no === authStore.currentUserNo)
    if (myEmp) {
      myEmp.presence = res.data
    }

    closeUpdateDialog()
  } catch (error: any) {
    console.error('Failed to update presence:', error)
    if (error.response && error.response.data && error.response.data.message) {
      errorMessage.value = error.response.data.message
    } else {
      errorMessage.value = '更新に失敗しました。時間や入力内容を確認してください。'
    }
  } finally {
    submitting.value = false
  }
}

// SSE イベント受信時のコールバック
const handlePresenceUpdated = (data: any) => {
  const { employee_no, status: empStatus, destination, return_time, updated_at } = data
  
  const emp = employees.value.find(e => e.employee_no === employee_no)
  if (emp) {
    emp.presence = {
      status: empStatus,
      destination,
      start_datetime: updated_at,
      end_datetime: return_time,
      updated_at
    }
    
    // 該当行をハイライト表示する
    activeHighlights.value[employee_no] = true
    setTimeout(() => {
      activeHighlights.value[employee_no] = false
    }, 1200)
  }
}

// Composable の利用
const { connect } = usePresenceSSE(handlePresenceUpdated)

onMounted(() => {
  loadInitialData()
  connect() // SSEの接続開始
})
</script>

<script lang="ts">
// Vueコンポーネントオプション（必要に応じて）
export default {
  name: 'PresenceBoard'
}
</script>

<style scoped>
/* フェードアウトする更新ハイライトアニメーション */
.highlight-row {
  animation: flash-highlight 1.2s ease-out;
}

@keyframes flash-highlight {
  0% {
    background-color: rgba(255, 235, 59, 0.6); /* 黄色の半透明 */
  }
  100% {
    background-color: transparent;
  }
}

.transition-all {
  transition: all 0.3s ease;
}

.gap-4 {
  gap: 16px;
}
</style>
