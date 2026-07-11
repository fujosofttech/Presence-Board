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
              <v-chip :color="getStatusColor(myPresence.status)" variant="flat" size="large" class="font-weight-bold">
                <v-icon :icon="getStatusIcon(myPresence.status)" class="mr-1" />
                {{ getStatusLabel(myPresence.status) }}
              </v-chip>
              
              <!-- 行先・戻り予定 -->
              <div class="text-body-1 ml-4" v-if="myPresence.destination">
                <span class="text-grey-darken-1">行先:</span> <strong>{{ myPresence.destination }}</strong>
              </div>
              <div class="text-body-1 ml-4" v-if="myPresence.return_time">
                <span class="text-grey-darken-1">戻り予定:</span> <strong>{{ myPresence.return_time }}</strong>
              </div>
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
                    <span v-if="emp.presence.return_time">{{ emp.presence.return_time }} まで</span>
                    <span v-else>－</span>
                  </td>

                  <!-- 更新時刻 -->
                  <td class="text-right text-caption text-grey">
                    {{ emp.presence.updated_at || '－' }}
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
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import api from '../services/api'

// インターフェース定義
interface Presence {
  status: string
  destination: string
  return_time: string
  updated_at: string
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
  presence: Presence // APIと結合するまで仮で格納する
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

// ストア
const authStore = useAuthStore()

// リアクティブデータ
const employees = ref<Employee[]>([])
const departments = ref<Department[]>([{ id: null, name: '全課' }])
const selectedDepartment = ref<number | null>(null)
const searchQuery = ref('')
const activeHighlights = ref<Record<string, boolean>>({})

// SSE 接続管理
let eventSource: EventSource | null = null

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
    return_time: '',
    updated_at: ''
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
    // ログイン中の「自分」は最上部に固定表示するため、グループ一覧側からは除外（または両方表示するが、仕様の「最上部固定」を満たすために一旦除外または非表示にするか、もしくは最上部にカード表示するのみでグループリスト内にも表示するか。ここではグループリスト内にも表示しつつ、最上部にカード表示する形が一般的で分かりやすいため、両方に表示します）
    
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

// 初期データの読み込み
const loadInitialData = async () => {
  try {
    // 1. 課一覧の取得
    const deptRes = await api.get('/departments/')
    departments.value = [{ id: null, name: '全課' }, ...deptRes.data]

    // 2. 社員一覧の取得
    const empRes = await api.get('/employees/')
    
    // 現在は Presence モデルが未実装のため、API から取得したデータに仮の presence 情報を付与する
    employees.value = empRes.data.map((emp: any) => {
      // テストデータ用に一部の社員にダミーの在籍状況を割り当てる
      let status = 'PRESENT'
      let destination = ''
      let return_time = ''
      
      if (emp.employee_no === 'E0002') {
        status = 'OUT'
        destination = '〇〇商事'
        return_time = '15:00'
      } else if (emp.employee_no === 'E0003') {
        status = 'REMOTE'
      }

      return {
        ...emp,
        presence: {
          status,
          destination,
          return_time,
          updated_at: '10:30'
        }
      }
    })
  } catch (error) {
    console.error('Failed to load initial data:', error)
  }
}

// 状態に応じたスタイル値のマッピング
const getStatusColor = (status: string) => {
  switch (status) {
    case 'PRESENT': return 'green'
    case 'CUSTOMER': return 'cyan'
    case 'OUT': return 'orange'
    case 'MEETING': return 'blue'
    case 'REMOTE': return 'light-green'
    case 'HOLIDAY': return 'grey'
    case 'LEAVE':
    case 'DIRECT_HOME': return 'red'
    default: return 'grey'
  }
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'PRESENT': return 'mdi-checkbox-marked-circle-outline'
    case 'CUSTOMER': return 'mdi-briefcase-outline'
    case 'OUT': return 'mdi-walk'
    case 'MEETING': return 'mdi-account-multiple'
    case 'REMOTE': return 'mdi-home-account'
    case 'HOLIDAY': return 'mdi-island'
    case 'LEAVE': return 'mdi-logout'
    case 'DIRECT_HOME': return 'mdi-arrow-right-bold-box-outline'
    default: return 'mdi-help-circle-outline'
  }
}

const getStatusLabel = (status: string) => {
  switch (status) {
    case 'PRESENT': return '在席'
    case 'CUSTOMER': return '客先'
    case 'OUT': return '外出'
    case 'MEETING': return '会議'
    case 'REMOTE': return '在宅'
    case 'HOLIDAY': return '休暇'
    case 'LEAVE': return '退社'
    case 'DIRECT_HOME': return '直帰'
    default: return status
  }
}

// SSE ストリーム接続設定
const setupSSE = () => {
  // バックエンドの SSE エンドポイントに接続
  eventSource = new EventSource('/api/v1/events/stream/')

  // 状態更新イベント受信時の処理
  eventSource.addEventListener('presence_updated', (event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data)
      const { employee_no, status, destination, return_time, updated_at } = data

      // 該当する社員の presence 情報を更新
      const emp = employees.value.find(e => e.employee_no === employee_no)
      if (emp) {
        emp.presence = { status, destination, return_time, updated_at }
        
        // 該当行をハイライト表示する
        activeHighlights.value[employee_no] = true
        setTimeout(() => {
          activeHighlights.value[employee_no] = false
        }, 1200)
      }
    } catch (e) {
      console.error('Failed to parse SSE payload:', e)
    }
  })

  eventSource.onerror = (err) => {
    console.warn('SSE connection error. Retrying...', err)
  }
}

onMounted(() => {
  loadInitialData()
  setupSSE()
})

onUnmounted(() => {
  if (eventSource) {
    eventSource.close()
  }
})
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
