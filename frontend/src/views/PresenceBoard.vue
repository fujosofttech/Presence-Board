<template>
  <v-container class="fill-height bg-slate-50 py-6" fluid>
    <!-- ナビゲーションバー -->
    <v-app-bar class="app-bar-gradient" elevation="3">
      <v-app-bar-title class="font-weight-bold text-h6 d-flex align-center">
        <v-icon icon="mdi-view-dashboard-outline" class="mr-2" />
        社内行先・在席管理システム
      </v-app-bar-title>
      
      <v-spacer></v-spacer>
      
      <!-- リアルタイム接続状態インジケータ (操作性/切断検知改善) -->
      <v-chip
        :color="isConnected ? 'success' : 'error'"
        variant="flat"
        class="mr-4 font-weight-bold text-white shadow-sm"
        size="small"
      >
        <v-icon :icon="isConnected ? 'mdi-wifi' : 'mdi-wifi-off'" class="mr-1" />
        {{ isConnected ? 'リアルタイム接続中' : '再接続中...' }}
      </v-chip>

      <v-btn
        v-if="myProfile?.is_staff"
        color="teal-lighten-5"
        variant="flat"
        prepend-icon="mdi-cog"
        class="font-weight-bold text-teal-darken-4 mr-4"
        to="/admin"
      >
        管理画面
      </v-btn>
      <v-chip class="mr-4 text-subtitle-2" color="teal-lighten-4" variant="flat">
        <v-icon icon="mdi-account-circle" class="mr-1" />
        {{ myInfo?.name || 'ゲスト' }} (自分)
      </v-chip>
    </v-app-bar>

    <v-row class="justify-center mt-12 w-100">
      <v-col cols="12" md="10" lg="9">
        
        <!-- 自分（ログイン中の利用者）のステータス表示カード (最上部固定 & カード改善) -->
        <v-card v-if="myInfo" class="mb-6 glass-card border-s-lg" :style="{ borderLeftColor: getStatusColor(myPresence.status) + ' !important', borderLeftWidth: '6px !important' }" elevation="2">
          <v-card-text class="d-flex flex-wrap align-center justify-space-between py-4">
            <div class="d-flex align-center">
              <v-avatar :color="getAvatarColor(myInfo.name)" size="56" class="mr-4 text-white font-weight-bold text-h5 elevation-2">
                {{ myInfo.name[0] }}
              </v-avatar>
              <div>
                <div class="text-subtitle-2 text-grey-darken-1 font-weight-medium">現在の自分の状況</div>
                <div class="text-h5 font-weight-bold text-slate-800">{{ myInfo.name }}</div>
              </div>
            </div>
            
            <div class="d-flex align-center flex-wrap gap-4 mt-4 mt-md-0">
              <!-- 状態表示チップ -->
              <v-chip :color="getStatusColor(myPresence.status)" variant="flat" size="large" class="font-weight-bold text-white shadow-sm py-5 px-4">
                <v-icon :icon="getStatusIcon(myPresence.status)" class="mr-2" size="large" />
                {{ getStatusLabel(myPresence.status) }}
              </v-chip>
              
              <!-- 行先・戻り予定 -->
              <div class="text-body-1 ml-2 d-flex flex-column" v-if="myPresence.destination || myPresence.end_datetime">
                <span class="text-grey-darken-1 text-caption font-weight-bold">詳細情報</span>
                <span class="text-slate-700">
                  <span v-if="myPresence.destination" class="mr-3">
                    <v-icon icon="mdi-map-marker" size="small" class="mr-1 text-grey" />
                    <strong>{{ myPresence.destination }}</strong>
                  </span>
                  <span v-if="myPresence.end_datetime">
                    <v-icon icon="mdi-clock" size="small" class="mr-1 text-grey" />
                    戻り: <strong>{{ formatTimeOnly(myPresence.end_datetime) }}</strong>
                  </span>
                </span>
              </div>

              <!-- クイック更新エリア (操作性改善) -->
              <div class="d-flex align-center bg-teal-lighten-5 px-3 py-2 rounded-lg border border-teal-lighten-4">
                <span class="text-caption text-teal-darken-4 font-weight-bold mr-2">ワンクリック更新:</span>
                <v-btn size="small" variant="flat" color="green" class="mr-1 text-white font-weight-bold" @click="quickUpdateStatus('PRESENT')">在席</v-btn>
                <v-btn size="small" variant="flat" color="light-green" class="mr-1 text-white font-weight-bold" @click="quickUpdateStatus('REMOTE')">在宅</v-btn>
                <v-btn size="small" variant="flat" color="red" class="text-white font-weight-bold" @click="quickUpdateStatus('LEAVE')">退社</v-btn>
              </div>

              <!-- 状況更新ボタン -->
              <v-btn
                color="teal-darken-2"
                prepend-icon="mdi-pencil"
                class="font-weight-bold text-white px-5 shadow-sm"
                elevation="2"
                @click="openUpdateDialog"
              >
                状況を変更
              </v-btn>
              
              <!-- 予定管理ボタン -->
              <v-btn
                color="blue-darken-2"
                prepend-icon="mdi-calendar-clock"
                class="font-weight-bold text-white px-5 shadow-sm"
                elevation="2"
                @click="openScheduleManager"
              >
                予定管理
              </v-btn>
            </div>
          </v-card-text>
        </v-card>

        <!-- 検索・絞り込みフィルターエリア (検索UI改善) -->
        <v-card class="mb-6 py-4 px-5 glass-card" elevation="2">
          <v-row dense align="center">
            <!-- 課での絞り込み -->
            <v-col cols="12" sm="4">
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
                color="teal"
              ></v-select>
            </v-col>
            
            <!-- 氏名検索 (自然言語 & Debounce 検索対応) -->
            <v-col cols="12" sm="8">
              <v-text-field
                v-model="searchQuery"
                label="氏名、状態、行先などを自然言語で検索 (例: 営業部 在宅 / 山田 本日外出)"
                prepend-inner-icon="mdi-magnify"
                variant="outlined"
                density="comfortable"
                clearable
                hide-details
                color="teal"
                :loading="searchLoading"
              ></v-text-field>
            </v-col>
          </v-row>

          <!-- クイック検索チップス (操作性・検索UI改善) -->
          <div class="mt-3 d-flex flex-wrap align-center gap-2">
            <span class="text-caption text-grey-darken-1 mr-2 font-weight-medium">クイック検索:</span>
            <v-chip
              size="small"
              color="green-darken-1"
              class="mr-2"
              @click="searchQuery = searchQuery === '在席' ? '' : '在席'"
              :variant="searchQuery === '在席' ? 'flat' : 'outlined'"
            >
              在席
            </v-chip>
            <v-chip
              size="small"
              color="orange-darken-2"
              class="mr-2"
              @click="searchQuery = searchQuery === '外出' ? '' : '外出'"
              :variant="searchQuery === '外出' ? 'flat' : 'outlined'"
            >
              外出
            </v-chip>
            <v-chip
              size="small"
              color="light-green-darken-2"
              class="mr-2"
              @click="searchQuery = searchQuery === '在宅' ? '' : '在宅'"
              :variant="searchQuery === '在宅' ? 'flat' : 'outlined'"
            >
              在宅
            </v-chip>
            <v-chip
              size="small"
              color="blue-darken-2"
              class="mr-2"
              @click="searchQuery = searchQuery === '会議' ? '' : '会議'"
              :variant="searchQuery === '会議' ? 'flat' : 'outlined'"
            >
              会議
            </v-chip>
            <v-chip
              size="small"
              color="cyan-darken-3"
              class="mr-2"
              @click="searchQuery = searchQuery === '営業部' ? '' : '営業部'"
              :variant="searchQuery === '営業部' ? 'flat' : 'outlined'"
            >
              営業部
            </v-chip>
          </div>
        </v-card>

        <!-- 社員一覧エリア (グループごとにセクション分け) -->
        <div v-for="group in filteredGroups" :key="group.id" class="mb-8">
          <div class="text-h6 font-weight-bold text-slate-800 mb-3 d-flex align-center">
            <v-icon icon="mdi-account-group-outline" class="mr-2" color="teal-darken-1" />
            {{ group.departmentName }} - {{ group.name }}
            <v-badge
              :content="group.employees.length.toString()"
              color="teal-darken-1"
              inline
              class="ml-2 font-weight-bold"
            ></v-badge>
          </div>

          <!-- モバイル表示 (レスポンシブ対応 & カードデザイン改善) -->
          <v-row v-if="smAndDown">
            <v-col
              v-for="emp in group.employees"
              :key="emp.id"
              cols="12"
              sm="6"
            >
              <v-card
                :class="{ 'highlight-row': activeHighlights[emp.employee_no] }"
                class="glass-card mb-3 py-4 px-5 border-start-solid elevation-1 transition-all"
                :style="{ borderLeftColor: getStatusColor(emp.presence.status) + ' !important', borderLeftWidth: '6px !important' }"
              >
                <div class="d-flex justify-space-between align-start">
                  <div>
                    <div class="d-flex align-center mb-2">
                      <v-avatar :color="getAvatarColor(emp.name)" size="36" class="mr-2 text-white font-weight-bold text-subtitle-2 shadow-sm">
                        {{ emp.name[0] }}
                      </v-avatar>
                      <div>
                        <span class="font-weight-bold text-subtitle-1 text-slate-800">{{ emp.name }}</span>
                        <v-chip
                          v-if="emp.employee_no === myInfo?.employee_no"
                          size="x-small"
                          color="teal"
                          class="ml-2 text-white font-weight-bold"
                          variant="flat"
                        >
                          自分
                        </v-chip>
                      </div>
                    </div>
                    
                    <div class="text-body-2 text-slate-600 mt-3 pl-1">
                      <div v-if="emp.presence.destination" class="d-flex align-center mb-1">
                        <v-icon icon="mdi-map-marker-outline" size="small" class="mr-1 text-grey-darken-1" />
                        <span>行先: <strong>{{ emp.presence.destination }}</strong></span>
                      </div>
                      <div v-if="emp.presence.end_datetime" class="d-flex align-center mb-1">
                        <v-icon icon="mdi-clock-outline" size="small" class="mr-1 text-grey-darken-1" />
                        <span>戻り予定: <strong>{{ formatTimeOnly(emp.presence.end_datetime) }}</strong></span>
                      </div>
                    </div>
                  </div>
                  
                  <div class="text-right d-flex flex-column align-end">
                    <v-chip
                      :color="getStatusColor(emp.presence.status)"
                      size="small"
                      class="font-weight-bold text-white shadow-sm mb-2"
                      variant="flat"
                    >
                      <v-icon :icon="getStatusIcon(emp.presence.status)" class="mr-1" size="x-small" />
                      {{ getStatusLabel(emp.presence.status) }}
                    </v-chip>
                    <div class="text-caption text-grey-darken-1 mt-4">
                      {{ formatTimeOnly(emp.presence.updated_at) }} 更新
                    </div>
                  </div>
                </div>
              </v-card>
            </v-col>
          </v-row>

          <!-- デスクトップ表示 (PCテーブルデザイン改善) -->
          <v-card v-else class="glass-card overflow-hidden" elevation="2">
            <v-table class="bg-transparent">
              <thead>
                <tr class="bg-teal-lighten-5">
                  <th class="text-subtitle-2 font-weight-bold text-teal-darken-4" style="width: 15%">状態</th>
                  <th class="text-subtitle-2 font-weight-bold text-teal-darken-4" style="width: 25%">氏名</th>
                  <th class="text-subtitle-2 font-weight-bold text-teal-darken-4" style="width: 30%">行先</th>
                  <th class="text-subtitle-2 font-weight-bold text-teal-darken-4" style="width: 15%">戻り予定</th>
                  <th class="text-subtitle-2 font-weight-bold text-teal-darken-4 text-right" style="width: 15%">更新時刻</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="emp in group.employees"
                  :key="emp.id"
                  :class="{ 'highlight-row': activeHighlights[emp.employee_no] }"
                  class="transition-all hover-row"
                >
                  <!-- 状態 -->
                  <td>
                    <v-chip
                      :color="getStatusColor(emp.presence.status)"
                      size="small"
                      class="font-weight-bold text-white shadow-sm"
                      variant="flat"
                    >
                      <v-icon :icon="getStatusIcon(emp.presence.status)" class="mr-1" size="small" />
                      {{ getStatusLabel(emp.presence.status) }}
                    </v-chip>
                  </td>

                  <!-- 氏名 -->
                  <td class="font-weight-bold text-slate-800">
                    <div class="d-flex align-center">
                      <v-avatar :color="getAvatarColor(emp.name)" size="30" class="mr-2 text-white font-weight-bold text-caption shadow-sm">
                        {{ emp.name[0] }}
                      </v-avatar>
                      <span>{{ emp.name }}</span>
                      <v-chip
                        v-if="emp.employee_no === myInfo?.employee_no"
                        size="x-small"
                        color="teal"
                        class="ml-2 text-white font-weight-bold"
                        variant="flat"
                      >
                        自分
                      </v-chip>
                    </div>
                  </td>

                  <!-- 行先 -->
                  <td class="text-slate-700">
                    <span v-if="emp.presence.destination" class="d-flex align-center">
                      <v-icon icon="mdi-map-marker-outline" size="small" class="mr-1 text-grey" />
                      {{ emp.presence.destination }}
                    </span>
                    <span v-else class="text-grey-lighten-1">－</span>
                  </td>

                  <!-- 予定 -->
                  <td class="text-slate-700">
                    <span v-if="emp.presence.end_datetime" class="d-flex align-center">
                      <v-icon icon="mdi-clock-outline" size="small" class="mr-1 text-grey" />
                      {{ formatTimeOnly(emp.presence.end_datetime) }} まで
                    </span>
                    <span v-else class="text-grey-lighten-1">－</span>
                  </td>

                  <!-- 更新時刻 -->
                  <td class="text-right text-caption text-grey-darken-1">
                    {{ formatTimeOnly(emp.presence.updated_at) }}
                  </td>
                </tr>
                <tr v-if="group.employees.length === 0">
                  <td colspan="5" class="text-center text-grey py-6">該当する社員がいません</td>
                </tr>
              </tbody>
            </v-table>
          </v-card>
        </div>

        <v-alert
          v-if="filteredGroups.length === 0"
          type="info"
          variant="tonal"
          class="text-center rounded-xl"
        >
          表示する社員が見つかりません。条件を変更して再検索してください。
        </v-alert>

      </v-col>
    </v-row>

    <!-- 状況更新ダイアログ -->
    <v-dialog v-model="dialog" max-width="600px" persistent>
      <v-card class="rounded-xl elevation-24">
        <v-card-title class="bg-teal-darken-3 text-white py-4 d-flex align-center">
          <v-icon icon="mdi-pencil-box-outline" class="mr-2" />
          <span class="font-weight-bold text-h6">自分の状況を更新</span>
          <v-spacer></v-spacer>
          <v-btn icon="mdi-close" variant="text" color="white" @click="closeUpdateDialog"></v-btn>
        </v-card-title>

        <v-card-text class="py-6 px-6 bg-slate-50">
          <div class="mb-5">
            <label class="text-subtitle-2 font-weight-bold text-grey-darken-3 d-block mb-3">ステータスを選択</label>
            <v-row dense>
              <v-col
                v-for="(def, key) in STATUS_DEFINITIONS"
                :key="key"
                cols="6"
                sm="3"
              >
                <v-btn
                  block
                  :color="form.status === key ? def.color : 'white'"
                  :variant="form.status === key ? 'flat' : 'outlined'"
                  :class="{'text-white': form.status === key, 'text-grey-darken-2 border-slate-200': form.status !== key}"
                  class="font-weight-bold py-2 shadow-sm text-none transition-all"
                  @click="selectStatus(key)"
                >
                  <v-icon :icon="def.icon" class="mr-1" size="small" />
                  {{ def.label }}
                </v-btn>
              </v-col>
            </v-row>
          </div>

          <!-- 行先入力 (状態ルールに応じて表示 & お気に入り/履歴のインテグレーション) -->
          <v-row v-if="statusRule.requiresDestination !== 'disabled'">
            <v-col cols="12">
              <v-combobox
                v-model="form.destination"
                :items="destinationSuggestions"
                :label="'行先を入力、またはお気に入り・履歴から選択' + (statusRule.requiresDestination === 'required' ? ' (必須)' : ' (任意)')"
                :rules="[v => (statusRule.requiresDestination !== 'required' || !!v) || '行先を入力してください']"
                prepend-inner-icon="mdi-map-marker-outline"
                variant="outlined"
                color="teal"
                clearable
                hide-no-data
                class="bg-white rounded-lg shadow-sm"
              >
                <!-- 候補選択リスト内のアイコン表示 -->
                <template v-slot:item="{ props, item }">
                  <v-list-item v-bind="props">
                    <template v-slot:prepend>
                      <v-icon :color="isFavorite(item.title) ? 'amber-darken-2' : 'grey-darken-1'">
                        {{ isFavorite(item.title) ? 'mdi-star' : 'mdi-history' }}
                      </v-icon>
                    </template>
                  </v-list-item>
                </template>

                <!-- お気に入り追加/削除ボタン (入力欄の右側) -->
                <template v-slot:append-inner>
                  <v-btn
                    v-if="form.destination"
                    icon
                    variant="text"
                    size="small"
                    :color="isFavorite(form.destination) ? 'amber-darken-2' : 'grey'"
                    @click.stop="toggleFavorite(form.destination)"
                  >
                    <v-icon>{{ isFavorite(form.destination) ? 'mdi-star' : 'mdi-star-outline' }}</v-icon>
                  </v-btn>
                </template>
              </v-combobox>

              <!-- 行先候補表示 (チップ形式 - 表示改善) -->
              <div class="mt-3" v-if="favorites.length > 0 || recents.length > 0">
                <div v-if="favorites.length > 0" class="mb-2 d-flex flex-wrap align-center">
                  <span class="text-caption text-grey-darken-1 mr-2 font-weight-bold">★ お気に入り:</span>
                  <v-chip
                    v-for="fav in favorites"
                    :key="fav.id"
                    size="small"
                    class="mr-2 mb-1 shadow-sm font-weight-bold"
                    color="amber-darken-4"
                    variant="outlined"
                    @click="form.destination = fav.destination"
                  >
                    <v-icon icon="mdi-star" size="x-small" class="mr-1" color="amber-darken-2" />
                    {{ fav.destination }}
                  </v-chip>
                </div>
                <div v-if="recents.length > 0" class="d-flex flex-wrap align-center">
                  <span class="text-caption text-grey-darken-1 mr-2 font-weight-bold">🕒 最近の履歴:</span>
                  <v-chip
                    v-for="(rec, idx) in recents"
                    :key="'rec'+idx"
                    size="small"
                    class="mr-2 mb-1 shadow-sm"
                    color="grey-darken-2"
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
                class="bg-white rounded-lg shadow-sm"
              ></v-text-field>
            </v-col>
          </v-row>

          <v-alert
            v-if="errorMessage"
            type="error"
            variant="tonal"
            class="mt-4 rounded-xl"
            density="compact"
          >
            {{ errorMessage }}
          </v-alert>
        </v-card-text>

        <v-card-actions class="px-6 pb-6 pt-3 bg-slate-50">
          <v-spacer></v-spacer>
          <v-btn
            color="grey-darken-1"
            variant="text"
            class="font-weight-bold mr-2 px-4"
            @click="closeUpdateDialog"
          >
            キャンセル
          </v-btn>
          <v-btn
            color="teal-darken-2"
            variant="flat"
            class="font-weight-bold text-white px-6 shadow-sm"
            :loading="submitting"
            @click="submitUpdate"
          >
            保存する
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 予定管理ダイアログ -->
    <v-dialog v-model="scheduleManagerDialog" max-width="800px" scrollable>
      <v-card class="rounded-xl elevation-24">
        <v-card-title class="bg-blue-darken-3 text-white py-4 d-flex align-center">
          <v-icon icon="mdi-calendar-clock" class="mr-2" />
          <span class="font-weight-bold text-h6">予定管理</span>
          <v-spacer></v-spacer>
          <v-btn icon="mdi-close" variant="text" color="white" @click="scheduleManagerDialog = false"></v-btn>
        </v-card-title>
        
        <v-card-text class="py-4 bg-slate-50" style="height: 60vh;">
          <div v-if="!scheduleEditing">
            <div class="d-flex justify-space-between align-center mb-4">
              <span class="text-subtitle-1 font-weight-bold text-grey-darken-3">今後30日間の予定</span>
              <v-btn color="blue-darken-2" prepend-icon="mdi-plus" class="font-weight-bold shadow-sm" @click="openScheduleForm()">新規登録</v-btn>
            </div>
            
            <v-card class="glass-card" elevation="2">
              <v-table class="bg-transparent">
                <thead>
                  <tr class="bg-blue-lighten-5">
                    <th class="text-subtitle-2 font-weight-bold text-blue-darken-4">対象日</th>
                    <th class="text-subtitle-2 font-weight-bold text-blue-darken-4">状態</th>
                    <th class="text-subtitle-2 font-weight-bold text-blue-darken-4">行先</th>
                    <th class="text-subtitle-2 font-weight-bold text-blue-darken-4">時間</th>
                    <th class="text-subtitle-2 font-weight-bold text-blue-darken-4">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in scheduledStatuses" :key="item.id" class="hover-row">
                    <td class="font-weight-bold text-slate-700">{{ item.target_date }}</td>
                    <td>
                      <v-chip :color="getStatusColor(item.status)" size="small" variant="flat" class="text-white font-weight-bold shadow-sm">
                        {{ getStatusLabel(item.status) }}
                      </v-chip>
                    </td>
                    <td class="text-slate-600">{{ item.destination || '－' }}</td>
                    <td class="text-slate-600">
                      {{ formatTimeOnly(item.start_time) }} 〜 {{ formatTimeOnly(item.end_time) }}
                    </td>
                    <td>
                      <v-btn icon="mdi-pencil" variant="text" size="small" color="blue" @click="openScheduleForm(item)"></v-btn>
                      <v-btn icon="mdi-delete" variant="text" size="small" color="red" @click="deleteSchedule(item.id)"></v-btn>
                    </td>
                  </tr>
                  <tr v-if="scheduledStatuses.length === 0">
                    <td colspan="5" class="text-center text-grey py-6">登録されている予定はありません</td>
                  </tr>
                </tbody>
              </v-table>
            </v-card>
          </div>

          <div v-else class="px-2">
            <div class="d-flex align-center mb-4">
              <v-btn icon="mdi-arrow-left" variant="text" @click="scheduleEditing = false"></v-btn>
              <span class="text-subtitle-1 font-weight-bold ml-2">{{ scheduleForm.id ? '予定の編集' : '予定の新規登録' }}</span>
            </div>

            <v-row dense>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="scheduleForm.target_date"
                  label="対象日 (必須)"
                  type="date"
                  variant="outlined"
                  density="comfortable"
                  :rules="[v => !!v || '対象日を入力してください']"
                  class="bg-white rounded-lg shadow-sm"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <label class="text-subtitle-2 font-weight-bold text-grey-darken-3 d-block mb-2">ステータスを選択</label>
                <v-row dense>
                  <v-col v-for="(def, key) in STATUS_DEFINITIONS" :key="key" cols="4" sm="3">
                    <v-btn
                      block
                      size="small"
                      :color="scheduleForm.status === key ? def.color : 'white'"
                      :variant="scheduleForm.status === key ? 'flat' : 'outlined'"
                      :class="{'text-white': scheduleForm.status === key, 'text-grey-darken-2 border-slate-200': scheduleForm.status !== key}"
                      class="font-weight-bold py-1 mb-2 shadow-sm"
                      @click="scheduleForm.status = key"
                    >
                      {{ def.label }}
                    </v-btn>
                  </v-col>
                </v-row>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="scheduleForm.destination"
                  label="行先"
                  variant="outlined"
                  density="comfortable"
                  class="bg-white rounded-lg shadow-sm"
                ></v-text-field>
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model="scheduleForm.start_time"
                  label="開始時刻"
                  type="time"
                  variant="outlined"
                  density="comfortable"
                  class="bg-white rounded-lg shadow-sm"
                ></v-text-field>
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model="scheduleForm.end_time"
                  label="終了時刻"
                  type="time"
                  variant="outlined"
                  density="comfortable"
                  class="bg-white rounded-lg shadow-sm"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="scheduleForm.memo"
                  label="メモ"
                  variant="outlined"
                  density="comfortable"
                  class="bg-white rounded-lg shadow-sm"
                ></v-text-field>
              </v-col>
            </v-row>

            <v-alert v-if="scheduleErrorMessage" type="error" variant="tonal" class="mt-2 rounded-xl" density="compact">
              {{ scheduleErrorMessage }}
            </v-alert>

            <div class="d-flex justify-end mt-6">
              <v-btn color="grey" variant="text" class="mr-2 px-4" @click="scheduleEditing = false">キャンセル</v-btn>
              <v-btn color="blue-darken-2" class="font-weight-bold px-6 shadow-sm" :loading="scheduleSubmitting" @click="submitSchedule">保存する</v-btn>
            </div>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useDisplay } from 'vuetify'
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

interface ScheduledStatus {
  id: number
  target_date: string
  status: string
  destination: string
  start_time: string | null
  end_time: string | null
  memo: string
}

interface MyProfile {
  id: number
  employee_no: string
  name: string
  email: string
  is_staff: boolean
  presence: Presence
}

// ストアとVuetify Display
const authStore = useAuthStore()
const { smAndDown } = useDisplay()

// リアクティブデータ
const employees = ref<Employee[]>([])
const departments = ref<Department[]>([{ id: null, name: '全課' }])
const selectedDepartment = ref<number | null>(null)
const searchQuery = ref('')
const activeHighlights = ref<Record<string, boolean>>({})
const searchLoading = ref(false)

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
const scheduledStatuses = ref<ScheduledStatus[]>([])
const myProfile = ref<MyProfile | null>(null)

// 予定管理関連
const scheduleManagerDialog = ref(false)
const scheduleEditing = ref(false)
const scheduleSubmitting = ref(false)
const scheduleErrorMessage = ref('')
const scheduleForm = ref<Partial<ScheduledStatus>>({})

// 選択中のステータスの定義ルール
const statusRule = computed<StatusInfo>(() => {
  return getStatusDefinition(form.value.status)
})

// ログイン中の「自分」の情報
const myInfo = computed(() => {
  return myProfile.value || employees.value.find(e => e.employee_no === authStore.currentUserNo) || null
})

// 自分の在籍状態（Presence）
const myPresence = computed<Presence>(() => {
  if (myProfile.value) {
    return myProfile.value.presence
  }
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

// お気に入りと履歴を合算した候補 (Autocomplete用)
const destinationSuggestions = computed<string[]>(() => {
  const items: string[] = []
  favorites.value.forEach(f => {
    if (f.destination && !items.includes(f.destination)) {
      items.push(f.destination)
    }
  })
  recents.value.forEach(r => {
    if (r.destination && !items.includes(r.destination)) {
      items.push(r.destination)
    }
  })
  return items
})

// グループ別に社員をマッピングし、フィルター適用後のデータを取得
const filteredGroups = computed<GroupWithEmployees[]>(() => {
  const groupsMap: Record<number, GroupWithEmployees> = {}

  // 1. 各社員のフィルタリング
  const filteredEmployees = employees.value.filter(emp => {
    // 課での絞り込み (クライアント側の追加フィルタ)
    if (selectedDepartment.value !== null && emp.department !== selectedDepartment.value) {
      return false
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

// アバターの配色を生成する関数 (ビジュアル改善)
const getAvatarColor = (name: string) => {
  const colors = ['teal-darken-1', 'indigo-darken-1', 'blue-darken-1', 'cyan-darken-2', 'deep-purple-darken-1', 'purple-darken-1', 'pink-darken-1', 'orange-darken-2', 'blue-grey-darken-1']
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  const index = Math.abs(hash) % colors.length
  return colors[index]
}

// 自然言語検索APIとの連携 (検索UI & 自然言語検索の高度化)
let searchDebounceTimeout: number | null = null

const performSearch = async () => {
  searchLoading.value = true
  try {
    const params: any = {}
    if (selectedDepartment.value) {
      params.department = selectedDepartment.value
    }
    
    if (searchQuery.value && searchQuery.value.trim()) {
      params.q = searchQuery.value.trim()
      const res = await api.get('/presence/search/', { params })
      employees.value = res.data
    } else {
      // 検索クエリが空なら全件取得
      const res = await api.get('/presence/', { params })
      employees.value = res.data
    }
  } catch (e) {
    console.error('Search failed:', e)
  } finally {
    searchLoading.value = false
  }
}

// 検索入力の監視 (Debounce処理)
watch(searchQuery, () => {
  if (searchDebounceTimeout) {
    clearTimeout(searchDebounceTimeout)
  }
  searchDebounceTimeout = window.setTimeout(() => {
    performSearch()
  }, 350)
})

// 課選択の監視 (即時リロード)
watch(selectedDepartment, () => {
  performSearch()
})

// 初期データ（一覧）の読み込み
const loadInitialData = async () => {
  try {
    const [deptRes, presRes, favRes, recRes, meRes] = await Promise.all([
      api.get('/departments/'),
      api.get('/presence/'),
      api.get('/destinations/favorites/'),
      api.get('/destinations/recent/'),
      api.get('/presence/me/')
    ])
    
    departments.value = [{ id: null, name: '全課' }, ...deptRes.data]
    employees.value = presRes.data
    favorites.value = favRes.data
    recents.value = recRes.data
    myProfile.value = meRes.data
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

// ワンクリッククイック状況更新 (操作性改善)
const quickUpdateStatus = async (statusKey: string) => {
  const def = getStatusDefinition(statusKey)
  // 入力が必要な状態（外出や会議など）はダイアログを開く
  if (def.requiresDestination === 'required' || def.requiresReturnTime === 'required') {
    form.value.status = statusKey
    selectStatus(statusKey)
    openUpdateDialog()
    return
  }

  submitting.value = true
  try {
    const payload = {
      status: statusKey,
      destination: '',
      return_time: null
    }

    const res = await api.patch('/presence/me/', payload)
    
    // 成功時、ローカルのデータも更新する（APIレスポンスから反映）
    const myEmp = employees.value.find(e => e.employee_no === authStore.currentUserNo)
    if (myEmp) {
      myEmp.presence = res.data
    }
    if (myProfile.value) {
      myProfile.value.presence = res.data
    }
  } catch (error: any) {
    console.error('Failed to quick update presence:', error)
    alert('更新に失敗しました。')
  } finally {
    submitting.value = false
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
    if (myProfile.value) {
      myProfile.value.presence = res.data
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

// 予定管理機能
const loadScheduledStatuses = async () => {
  try {
    const res = await api.get('/scheduled-status/')
    scheduledStatuses.value = res.data
  } catch (error) {
    console.error('Failed to load scheduled statuses:', error)
  }
}

const openScheduleManager = async () => {
  await loadScheduledStatuses()
  scheduleEditing.value = false
  scheduleManagerDialog.value = true
}

const openScheduleForm = (item: ScheduledStatus | null = null) => {
  scheduleErrorMessage.value = ''
  if (item) {
    scheduleForm.value = { ...item }
    // TimeFieldから秒を除去 (HH:mm)
    if (scheduleForm.value.start_time && scheduleForm.value.start_time.length > 5) {
      scheduleForm.value.start_time = scheduleForm.value.start_time.substring(0, 5)
    }
    if (scheduleForm.value.end_time && scheduleForm.value.end_time.length > 5) {
      scheduleForm.value.end_time = scheduleForm.value.end_time.substring(0, 5)
    }
  } else {
    // 新規作成時は明日の日付を初期値とする
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    const yyyy = tomorrow.getFullYear()
    const mm = String(tomorrow.getMonth() + 1).padStart(2, '0')
    const dd = String(tomorrow.getDate()).padStart(2, '0')
    
    scheduleForm.value = {
      id: undefined,
      target_date: `${yyyy}-${mm}-${dd}`,
      status: 'OUT',
      destination: '',
      start_time: '',
      end_time: '',
      memo: ''
    }
  }
  scheduleEditing.value = true
}

const submitSchedule = async () => {
  scheduleErrorMessage.value = ''
  if (!scheduleForm.value.target_date) {
    scheduleErrorMessage.value = '対象日を入力してください'
    return
  }

  scheduleSubmitting.value = true
  try {
    // 空文字の時刻はnullに変換
    const payload = { ...scheduleForm.value }
    if (!payload.start_time) payload.start_time = null
    if (!payload.end_time) payload.end_time = null

    if (payload.id) {
      await api.patch(`/scheduled-status/${payload.id}/`, payload)
    } else {
      await api.post('/scheduled-status/', payload)
    }
    await loadScheduledStatuses()
    scheduleEditing.value = false
  } catch (error: any) {
    console.error('Failed to submit schedule:', error)
    if (error.response?.data?.message) {
      scheduleErrorMessage.value = error.response.data.message
      if (error.response.data.details) {
         // Object.values を使って詳細エラーを結合
         scheduleErrorMessage.value += ' ' + Object.values(error.response.data.details).join(' ')
      }
    } else {
      scheduleErrorMessage.value = '保存に失敗しました。'
    }
  } finally {
    scheduleSubmitting.value = false
  }
}

const deleteSchedule = async (id: number) => {
  if (!confirm('この予定を削除しますか？')) return
  try {
    await api.delete(`/scheduled-status/${id}/`)
    await loadScheduledStatuses()
  } catch (error: any) {
    console.error('Failed to delete schedule:', error)
    alert(error.response?.data?.message || '削除に失敗しました。')
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

// Composable の利用 (再接続時のデータリロード対応)
const { isConnected, connect } = usePresenceSSE(
  handlePresenceUpdated,
  (isReconnect) => {
    if (isReconnect) {
      console.log('SSE connection re-established. Re-fetching presence board data...')
      loadInitialData()
    }
  }
)

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
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.gap-4 {
  gap: 16px;
}

.gap-2 {
  gap: 8px;
}

/* Glassmorphism & custom styles */
.glass-card {
  background: rgba(255, 255, 255, 0.8) !important;
  backdrop-filter: blur(12px) !important;
  border: 1px solid rgba(255, 255, 255, 0.4) !important;
  border-radius: 16px !important;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.04) !important;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
}

.glass-card:hover {
  box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.08) !important;
}

.app-bar-gradient {
  background: linear-gradient(135deg, #0d9488 0%, #115e59 100%) !important;
  color: white !important;
}

.bg-slate-50 {
  background-color: #f8fafc !important;
}

.hover-row {
  transition: background-color 0.2s ease;
}

.hover-row:hover {
  background-color: rgba(15, 118, 110, 0.04) !important;
}

.border-start-solid {
  border-left-style: solid !important;
}
</style>
