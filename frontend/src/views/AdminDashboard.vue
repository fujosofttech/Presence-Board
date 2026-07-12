<template>
  <v-container class="fill-height bg-grey-lighten-4 py-6" fluid>
    <!-- ナビゲーションバー -->
    <v-app-bar color="teal-darken-3" elevation="2">
      <v-app-bar-title class="font-weight-bold text-h6">
        <v-icon icon="mdi-shield-account-outline" class="mr-2" />
        Presence Board 管理画面
      </v-app-bar-title>
      <v-spacer></v-spacer>
      <v-btn
        color="teal-lighten-5"
        variant="flat"
        prepend-icon="mdi-arrow-left"
        class="font-weight-bold text-teal-darken-4 mr-4"
        to="/"
      >
        一般画面に戻る
      </v-btn>
    </v-app-bar>

    <v-row class="justify-center mt-12 w-100">
      <v-col cols="12" md="11" lg="10">
        <!-- 管理画面メインカード -->
        <v-card class="rounded-lg shadow-lg" elevation="2">
          <!-- タブヘッダー -->
          <v-tabs v-model="activeTab" bg-color="teal-darken-2" align-tabs="start" stacked>
            <v-tab value="employees" class="font-weight-bold">
              <v-icon icon="mdi-account-multiple" class="mb-1" />
              社員管理
            </v-tab>
            <v-tab value="departments" class="font-weight-bold">
              <v-icon icon="mdi-domain" class="mb-1" />
              部署管理
            </v-tab>
            <v-tab value="groups" class="font-weight-bold">
              <v-icon icon="mdi-account-group-outline" class="mb-1" />
              グループ管理
            </v-tab>
            <v-tab value="work-locations" class="font-weight-bold">
              <v-icon icon="mdi-map-marker-radius-outline" class="mb-1" />
              勤務場所管理
            </v-tab>
            <v-tab value="status-masters" class="font-weight-bold">
              <v-icon icon="mdi-list-status" class="mb-1" />
              状態マスタ管理
            </v-tab>
          </v-tabs>

          <!-- 各タブのコンテンツ -->
          <v-card-text class="py-6 px-6">
            <v-window v-model="activeTab">
              <!-- ==========================================
                   社員管理タブ
                   ========================================== -->
              <v-window-item value="employees">
                <div class="d-flex justify-space-between align-center mb-4 flex-wrap gap-4">
                  <v-text-field
                    v-model="employeeSearch"
                    label="氏名、社員番号、メールで検索"
                    prepend-inner-icon="mdi-magnify"
                    variant="outlined"
                    density="comfortable"
                    clearable
                    hide-details
                    style="max-width: 400px; min-width: 250px"
                  ></v-text-field>
                  <v-btn
                    color="teal-darken-2"
                    prepend-icon="mdi-plus"
                    class="font-weight-bold text-white"
                    @click="openEmployeeDialog()"
                  >
                    社員を新規登録
                  </v-btn>
                </div>

                <v-card elevation="1">
                  <v-table>
                    <thead>
                      <tr class="bg-teal-lighten-5">
                        <th class="text-subtitle-2 font-weight-bold text-teal-darken-4">社員番号</th>
                        <th class="text-subtitle-2 font-weight-bold text-teal-darken-4">氏名</th>
                        <th class="text-subtitle-2 font-weight-bold text-teal-darken-4">メールアドレス</th>
                        <th class="text-subtitle-2 font-weight-bold text-teal-darken-4">部署</th>
                        <th class="text-subtitle-2 font-weight-bold text-teal-darken-4">グループ</th>
                        <th class="text-subtitle-2 font-weight-bold text-teal-darken-4">勤務場所</th>
                        <th class="text-subtitle-2 font-weight-bold text-teal-darken-4">連絡先</th>
                        <th class="text-subtitle-2 font-weight-bold text-teal-darken-4">表示順</th>
                        <th class="text-subtitle-2 font-weight-bold text-teal-darken-4 text-center" style="width: 120px">操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="item in filteredEmployees" :key="item.id">
                        <td class="font-weight-bold">{{ item.employee_no }}</td>
                        <td>{{ item.name }}</td>
                        <td>{{ item.email }}</td>
                        <td>{{ item.department_name }}</td>
                        <td>{{ item.group_name }}</td>
                        <td>
                          {{ item.work_location_company ? `${item.work_location_company} ${item.work_location_office || ''}` : '－' }}
                        </td>
                        <td>{{ item.phone_number || '－' }}</td>
                        <td>{{ item.display_order }}</td>
                        <td class="text-center">
                          <v-btn
                            icon="mdi-pencil"
                            variant="text"
                            size="small"
                            color="blue"
                            @click="openEmployeeDialog(item)"
                          ></v-btn>
                          <v-btn
                            icon="mdi-delete"
                            variant="text"
                            size="small"
                            color="red"
                            @click="confirmDelete('employee', item.id)"
                          ></v-btn>
                        </td>
                      </tr>
                      <tr v-if="filteredEmployees.length === 0">
                        <td colspan="9" class="text-center text-grey py-4">該当する社員はいません</td>
                      </tr>
                    </tbody>
                  </v-table>
                </v-card>
              </v-window-item>

              <!-- ==========================================
                   部署管理タブ
                   ========================================== -->
              <v-window-item value="departments">
                <div class="d-flex justify-space-between align-center mb-4">
                  <v-text-field
                    v-model="departmentSearch"
                    label="部署名で検索"
                    prepend-inner-icon="mdi-magnify"
                    variant="outlined"
                    density="comfortable"
                    clearable
                    hide-details
                    style="max-width: 400px; min-width: 250px"
                  ></v-text-field>
                  <v-btn
                    color="teal-darken-2"
                    prepend-icon="mdi-plus"
                    class="font-weight-bold text-white"
                    @click="openDepartmentDialog()"
                  >
                    部署を新規登録
                  </v-btn>
                </div>

                <v-card elevation="1">
                  <v-table>
                    <thead>
                      <tr class="bg-teal-lighten-5">
                        <th class="text-subtitle-2 font-weight-bold text-teal-darken-4">ID</th>
                        <th class="text-subtitle-2 font-weight-bold text-teal-darken-4">部署名</th>
                        <th class="text-subtitle-2 font-weight-bold text-teal-darken-4">表示順</th>
                        <th class="text-subtitle-2 font-weight-bold text-teal-darken-4 text-center" style="width: 120px">操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="item in filteredDepartments" :key="item.id">
                        <td>{{ item.id }}</td>
                        <td class="font-weight-bold">{{ item.name }}</td>
                        <td>{{ item.display_order }}</td>
                        <td class="text-center">
                          <v-btn
                            icon="mdi-pencil"
                            variant="text"
                            size="small"
                            color="blue"
                            @click="openDepartmentDialog(item)"
                          ></v-btn>
                          <v-btn
                            icon="mdi-delete"
                            variant="text"
                            size="small"
                            color="red"
                            @click="confirmDelete('department', item.id)"
                          ></v-btn>
                        </td>
                      </tr>
                      <tr v-if="filteredDepartments.length === 0">
                        <td colspan="4" class="text-center text-grey py-4">該当する部署はありません</td>
                      </tr>
                    </tbody>
                  </v-table>
                </v-card>
              </v-window-item>

              <!-- ==========================================
                   グループ管理タブ
                   ========================================== -->
              <v-window-item value="groups">
                <div class="d-flex justify-space-between align-center mb-4">
                  <v-text-field
                    v-model="groupSearch"
                    label="グループ名で検索"
                    prepend-inner-icon="mdi-magnify"
                    variant="outlined"
                    density="comfortable"
                    clearable
                    hide-details
                    style="max-width: 400px; min-width: 250px"
                  ></v-text-field>
                  <v-btn
                    color="teal-darken-2"
                    prepend-icon="mdi-plus"
                    class="font-weight-bold text-white"
                    @click="openGroupDialog()"
                  >
                    グループを新規登録
                  </v-btn>
                </div>

                <v-card elevation="1">
                  <v-table>
                    <thead>
                      <tr class="bg-teal-lighten-5">
                        <th class="text-subtitle-2 font-weight-bold text-teal-darken-4">ID</th>
                        <th class="text-subtitle-2 font-weight-bold text-teal-darken-4">所属部署</th>
                        <th class="text-subtitle-2 font-weight-bold text-teal-darken-4">グループ名</th>
                        <th class="text-subtitle-2 font-weight-bold text-teal-darken-4">表示順</th>
                        <th class="text-subtitle-2 font-weight-bold text-teal-darken-4 text-center" style="width: 120px">操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="item in filteredGroups" :key="item.id">
                        <td>{{ item.id }}</td>
                        <td>{{ item.department_name }}</td>
                        <td class="font-weight-bold">{{ item.name }}</td>
                        <td>{{ item.display_order }}</td>
                        <td class="text-center">
                          <v-btn
                            icon="mdi-pencil"
                            variant="text"
                            size="small"
                            color="blue"
                            @click="openGroupDialog(item)"
                          ></v-btn>
                          <v-btn
                            icon="mdi-delete"
                            variant="text"
                            size="small"
                            color="red"
                            @click="confirmDelete('group', item.id)"
                          ></v-btn>
                        </td>
                      </tr>
                      <tr v-if="filteredGroups.length === 0">
                        <td colspan="5" class="text-center text-grey py-4">該当するグループはありません</td>
                      </tr>
                    </tbody>
                  </v-table>
                </v-card>
              </v-window-item>

              <!-- ==========================================
                   勤務場所管理タブ
                   ========================================== -->
              <v-window-item value="work-locations">
                <div class="d-flex justify-space-between align-center mb-4">
                  <v-text-field
                    v-model="workLocationSearch"
                    label="会社名、事業所名で検索"
                    prepend-inner-icon="mdi-magnify"
                    variant="outlined"
                    density="comfortable"
                    clearable
                    hide-details
                    style="max-width: 400px; min-width: 250px"
                  ></v-text-field>
                  <v-btn
                    color="teal-darken-2"
                    prepend-icon="mdi-plus"
                    class="font-weight-bold text-white"
                    @click="openWorkLocationDialog()"
                  >
                    勤務場所を新規登録
                  </v-btn>
                </div>

                <v-card elevation="1">
                  <v-table>
                    <thead>
                      <tr class="bg-teal-lighten-5">
                        <th class="text-subtitle-2 font-weight-bold text-teal-darken-4">会社名</th>
                        <th class="text-subtitle-2 font-weight-bold text-teal-darken-4">事業所名</th>
                        <th class="text-subtitle-2 font-weight-bold text-teal-darken-4">住所</th>
                        <th class="text-subtitle-2 font-weight-bold text-teal-darken-4">表示順</th>
                        <th class="text-subtitle-2 font-weight-bold text-teal-darken-4 text-center" style="width: 120px">操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="item in filteredWorkLocations" :key="item.id">
                        <td class="font-weight-bold">{{ item.company_name }}</td>
                        <td>{{ item.office_name }}</td>
                        <td>{{ item.address }}</td>
                        <td>{{ item.display_order }}</td>
                        <td class="text-center">
                          <v-btn
                            icon="mdi-pencil"
                            variant="text"
                            size="small"
                            color="blue"
                            @click="openWorkLocationDialog(item)"
                          ></v-btn>
                          <v-btn
                            icon="mdi-delete"
                            variant="text"
                            size="small"
                            color="red"
                            @click="confirmDelete('work-location', item.id)"
                          ></v-btn>
                        </td>
                      </tr>
                      <tr v-if="filteredWorkLocations.length === 0">
                        <td colspan="5" class="text-center text-grey py-4">該当する勤務場所はありません</td>
                      </tr>
                    </tbody>
                  </v-table>
                </v-card>
              </v-window-item>

              <!-- ==========================================
                   状態マスタ管理タブ
                   ========================================== -->
              <v-window-item value="status-masters">
                <div class="d-flex justify-space-between align-center mb-4">
                  <v-text-field
                    v-model="statusMasterSearch"
                    label="状態コードで検索"
                    prepend-inner-icon="mdi-magnify"
                    variant="outlined"
                    density="comfortable"
                    clearable
                    hide-details
                    style="max-width: 400px; min-width: 250px"
                  ></v-text-field>
                  <v-btn
                    color="teal-darken-2"
                    prepend-icon="mdi-plus"
                    class="font-weight-bold text-white"
                    @click="openStatusMasterDialog()"
                  >
                    状態を新規登録
                  </v-btn>
                </div>

                <v-card elevation="1">
                  <v-table>
                    <thead>
                      <tr class="bg-teal-lighten-5">
                        <th class="text-subtitle-2 font-weight-bold text-teal-darken-4">状態コード</th>
                        <th class="text-subtitle-2 font-weight-bold text-teal-darken-4">対応日本語名 (UI表示用)</th>
                        <th class="text-subtitle-2 font-weight-bold text-teal-darken-4">表示順</th>
                        <th class="text-subtitle-2 font-weight-bold text-teal-darken-4 text-center" style="width: 120px">操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="item in filteredStatusMasters" :key="item.id">
                        <td class="font-weight-bold">{{ item.name }}</td>
                        <td>{{ item.name_display || getStatusLabel(item.name) }}</td>
                        <td>{{ item.display_order }}</td>
                        <td class="text-center">
                          <v-btn
                            icon="mdi-pencil"
                            variant="text"
                            size="small"
                            color="blue"
                            @click="openStatusMasterDialog(item)"
                          ></v-btn>
                          <v-btn
                            icon="mdi-delete"
                            variant="text"
                            size="small"
                            color="red"
                            @click="confirmDelete('status-master', item.id)"
                          ></v-btn>
                        </td>
                      </tr>
                      <tr v-if="filteredStatusMasters.length === 0">
                        <td colspan="4" class="text-center text-grey py-4">該当する状態はありません</td>
                      </tr>
                    </tbody>
                  </v-table>
                </v-card>
              </v-window-item>
            </v-window>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- ==========================================
         社員編集/登録ダイアログ
         ========================================== -->
    <v-dialog v-model="employeeDialog" max-width="600px" persistent>
      <v-card class="rounded-lg">
        <v-card-title class="bg-teal-darken-3 text-white py-4">
          <v-icon icon="mdi-account" class="mr-2" />
          <span class="font-weight-bold text-h6">{{ employeeForm.id ? '社員の編集' : '社員の新規登録' }}</span>
        </v-card-title>
        <v-card-text class="py-6 px-6">
          <v-form ref="employeeFormRef" v-model="isEmployeeFormValid">
            <v-row dense>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="employeeForm.employee_no"
                  label="社員番号 (必須)"
                  variant="outlined"
                  density="comfortable"
                  :rules="[v => !!v || '社員番号を入力してください', v => v.length <= 10 || '10文字以内で入力してください']"
                ></v-text-field>
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="employeeForm.name"
                  label="氏名 (必須)"
                  variant="outlined"
                  density="comfortable"
                  :rules="[v => !!v || '氏名を入力してください', v => v.length <= 100 || '100文字以内で入力してください']"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="employeeForm.email"
                  label="メールアドレス (必須)"
                  variant="outlined"
                  density="comfortable"
                  :rules="[v => !!v || 'メールアドレスを入力してください', v => /.+@.+\..+/.test(v) || '正しいメールアドレスの形式で入力してください']"
                ></v-text-field>
              </v-col>
              <v-col cols="12" sm="6">
                <v-select
                  v-model="employeeForm.department"
                  :items="rawDepartments"
                  item-title="name"
                  item-value="id"
                  label="部署 (必須)"
                  variant="outlined"
                  density="comfortable"
                  :rules="[v => !!v || '部署を選択してください']"
                  @update:model-value="onDepartmentChange"
                ></v-select>
              </v-col>
              <v-col cols="12" sm="6">
                <v-select
                  v-model="employeeForm.group"
                  :items="filteredGroupsForEmployeeSelect"
                  item-title="name"
                  item-value="id"
                  label="グループ (必須)"
                  variant="outlined"
                  density="comfortable"
                  :rules="[v => !!v || 'グループを選択してください']"
                ></v-select>
              </v-col>
              <v-col cols="12">
                <v-select
                  v-model="employeeForm.work_location"
                  :items="rawWorkLocations"
                  item-title="company_name"
                  item-value="id"
                  label="勤務場所 (任意)"
                  variant="outlined"
                  density="comfortable"
                  clearable
                >
                  <template v-slot:item="{ props, item }">
                    <v-list-item v-bind="props" :subtitle="item.raw.office_name"></v-list-item>
                  </template>
                </v-select>
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="employeeForm.phone_number"
                  label="連絡先 (任意)"
                  variant="outlined"
                  density="comfortable"
                ></v-text-field>
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="employeeForm.display_order"
                  label="表示順 (必須)"
                  type="number"
                  variant="outlined"
                  density="comfortable"
                  :rules="[v => v !== null && v !== undefined || '表示順を入力してください']"
                ></v-text-field>
              </v-col>
            </v-row>
          </v-form>
          <v-alert v-if="formErrorMessage" type="error" variant="tonal" class="mt-4" density="compact">
            {{ formErrorMessage }}
          </v-alert>
        </v-card-text>
        <v-card-actions class="px-6 pb-6 pt-0">
          <v-spacer></v-spacer>
          <v-btn color="grey-darken-1" variant="text" @click="employeeDialog = false">キャンセル</v-btn>
          <v-btn color="teal-darken-2" variant="flat" class="text-white" :loading="formSubmitting" @click="saveEmployee">
            保存する
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- ==========================================
         部署編集/登録ダイアログ
         ========================================== -->
    <v-dialog v-model="departmentDialog" max-width="500px" persistent>
      <v-card class="rounded-lg">
        <v-card-title class="bg-teal-darken-3 text-white py-4">
          <v-icon icon="mdi-domain" class="mr-2" />
          <span class="font-weight-bold text-h6">{{ departmentForm.id ? '部署の編集' : '部署の新規登録' }}</span>
        </v-card-title>
        <v-card-text class="py-6 px-6">
          <v-form ref="departmentFormRef" v-model="isDepartmentFormValid">
            <v-row dense>
              <v-col cols="12">
                <v-text-field
                  v-model="departmentForm.name"
                  label="部署名 (必須)"
                  variant="outlined"
                  density="comfortable"
                  :rules="[v => !!v || '部署名を入力してください', v => v.length <= 100 || '100文字以内で入力してください']"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="departmentForm.display_order"
                  label="表示順 (必須)"
                  type="number"
                  variant="outlined"
                  density="comfortable"
                  :rules="[v => v !== null && v !== undefined || '表示順を入力してください']"
                ></v-text-field>
              </v-col>
            </v-row>
          </v-form>
          <v-alert v-if="formErrorMessage" type="error" variant="tonal" class="mt-4" density="compact">
            {{ formErrorMessage }}
          </v-alert>
        </v-card-text>
        <v-card-actions class="px-6 pb-6 pt-0">
          <v-spacer></v-spacer>
          <v-btn color="grey-darken-1" variant="text" @click="departmentDialog = false">キャンセル</v-btn>
          <v-btn color="teal-darken-2" variant="flat" class="text-white" :loading="formSubmitting" @click="saveDepartment">
            保存する
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- ==========================================
         グループ編集/登録ダイアログ
         ========================================== -->
    <v-dialog v-model="groupDialog" max-width="500px" persistent>
      <v-card class="rounded-lg">
        <v-card-title class="bg-teal-darken-3 text-white py-4">
          <v-icon icon="mdi-account-group-outline" class="mr-2" />
          <span class="font-weight-bold text-h6">{{ groupForm.id ? 'グループの編集' : 'グループの新規登録' }}</span>
        </v-card-title>
        <v-card-text class="py-6 px-6">
          <v-form ref="groupFormRef" v-model="isGroupFormValid">
            <v-row dense>
              <v-col cols="12">
                <v-select
                  v-model="groupForm.department"
                  :items="rawDepartments"
                  item-title="name"
                  item-value="id"
                  label="所属部署 (必須)"
                  variant="outlined"
                  density="comfortable"
                  :rules="[v => !!v || '部署を選択してください']"
                ></v-select>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="groupForm.name"
                  label="グループ名 (必須)"
                  variant="outlined"
                  density="comfortable"
                  :rules="[v => !!v || 'グループ名を入力してください', v => v.length <= 100 || '100文字以内で入力してください']"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="groupForm.display_order"
                  label="表示順 (必須)"
                  type="number"
                  variant="outlined"
                  density="comfortable"
                  :rules="[v => v !== null && v !== undefined || '表示順を入力してください']"
                ></v-text-field>
              </v-col>
            </v-row>
          </v-form>
          <v-alert v-if="formErrorMessage" type="error" variant="tonal" class="mt-4" density="compact">
            {{ formErrorMessage }}
          </v-alert>
        </v-card-text>
        <v-card-actions class="px-6 pb-6 pt-0">
          <v-spacer></v-spacer>
          <v-btn color="grey-darken-1" variant="text" @click="groupDialog = false">キャンセル</v-btn>
          <v-btn color="teal-darken-2" variant="flat" class="text-white" :loading="formSubmitting" @click="saveGroup">
            保存する
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- ==========================================
         勤務場所編集/登録ダイアログ
         ========================================== -->
    <v-dialog v-model="workLocationDialog" max-width="500px" persistent>
      <v-card class="rounded-lg">
        <v-card-title class="bg-teal-darken-3 text-white py-4">
          <v-icon icon="mdi-map-marker-radius-outline" class="mr-2" />
          <span class="font-weight-bold text-h6">{{ workLocationForm.id ? '勤務場所の編集' : '勤務場所の新規登録' }}</span>
        </v-card-title>
        <v-card-text class="py-6 px-6">
          <v-form ref="workLocationFormRef" v-model="isWorkLocationFormValid">
            <v-row dense>
              <v-col cols="12">
                <v-text-field
                  v-model="workLocationForm.company_name"
                  label="会社名 (必須)"
                  variant="outlined"
                  density="comfortable"
                  :rules="[v => !!v || '会社名を入力してください', v => v.length <= 200 || '200文字以内で入力してください']"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="workLocationForm.office_name"
                  label="事業所名 (必須)"
                  variant="outlined"
                  density="comfortable"
                  :rules="[v => !!v || '事業所名を入力してください', v => v.length <= 200 || '200文字以内で入力してください']"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="workLocationForm.address"
                  label="住所 (必須)"
                  variant="outlined"
                  density="comfortable"
                  :rules="[v => !!v || '住所を入力してください', v => v.length <= 500 || '500文字以内で入力してください']"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="workLocationForm.display_order"
                  label="表示順 (必須)"
                  type="number"
                  variant="outlined"
                  density="comfortable"
                  :rules="[v => v !== null && v !== undefined || '表示順を入力してください']"
                ></v-text-field>
              </v-col>
            </v-row>
          </v-form>
          <v-alert v-if="formErrorMessage" type="error" variant="tonal" class="mt-4" density="compact">
            {{ formErrorMessage }}
          </v-alert>
        </v-card-text>
        <v-card-actions class="px-6 pb-6 pt-0">
          <v-spacer></v-spacer>
          <v-btn color="grey-darken-1" variant="text" @click="workLocationDialog = false">キャンセル</v-btn>
          <v-btn color="teal-darken-2" variant="flat" class="text-white" :loading="formSubmitting" @click="saveWorkLocation">
            保存する
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- ==========================================
         状態マスタ編集/登録ダイアログ
         ========================================== -->
    <v-dialog v-model="statusMasterDialog" max-width="500px" persistent>
      <v-card class="rounded-lg">
        <v-card-title class="bg-teal-darken-3 text-white py-4">
          <v-icon icon="mdi-list-status" class="mr-2" />
          <span class="font-weight-bold text-h6">{{ statusMasterForm.id ? '状態の編集' : '状態の新規登録' }}</span>
        </v-card-title>
        <v-card-text class="py-6 px-6">
          <v-form ref="statusMasterFormRef" v-model="isStatusMasterFormValid">
            <v-row dense>
              <v-col cols="12">
                <v-select
                  v-model="statusMasterForm.name"
                  :items="STATUS_CHOICES"
                  label="状態コード (必須)"
                  variant="outlined"
                  density="comfortable"
                  :rules="[v => !!v || '状態コードを選択してください']"
                  :disabled="!!statusMasterForm.id"
                ></v-select>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="statusMasterForm.display_order"
                  label="表示順 (必須)"
                  type="number"
                  variant="outlined"
                  density="comfortable"
                  :rules="[v => v !== null && v !== undefined || '表示順を入力してください']"
                ></v-text-field>
              </v-col>
            </v-row>
          </v-form>
          <v-alert v-if="formErrorMessage" type="error" variant="tonal" class="mt-4" density="compact">
            {{ formErrorMessage }}
          </v-alert>
        </v-card-text>
        <v-card-actions class="px-6 pb-6 pt-0">
          <v-spacer></v-spacer>
          <v-btn color="grey-darken-1" variant="text" @click="statusMasterDialog = false">キャンセル</v-btn>
          <v-btn color="teal-darken-2" variant="flat" class="text-white" :loading="formSubmitting" @click="saveStatusMaster">
            保存する
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- ==========================================
         削除確認ダイアログ
         ========================================== -->
    <v-dialog v-model="deleteConfirmDialog" max-width="400px">
      <v-card class="rounded-lg">
        <v-card-title class="bg-red-darken-3 text-white py-4 d-flex align-center">
          <v-icon icon="mdi-alert" class="mr-2" />
          <span class="font-weight-bold text-h6">削除確認</span>
        </v-card-title>
        <v-card-text class="py-6 px-6 text-body-1">
          本当にこのデータを削除（論理削除）しますか？<br />
          ※この操作は取り消せません。
        </v-card-text>
        <v-card-actions class="px-6 pb-6 pt-0">
          <v-spacer></v-spacer>
          <v-btn color="grey-darken-1" variant="text" @click="deleteConfirmDialog = false">キャンセル</v-btn>
          <v-btn color="red-darken-2" variant="flat" class="text-white px-6" :loading="deleteSubmitting" @click="executeDelete">
            削除する
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'
import { getStatusLabel } from '../utils/status'

// インターフェース定義
interface Department {
  id: number
  name: string
  display_order: number
}

interface Group {
  id: number
  department: number
  department_name: string
  name: string
  display_order: number
}

interface WorkLocation {
  id: number
  company_name: string
  office_name: string
  address: string
  display_order: number
}

interface StatusMaster {
  id: number
  name: string
  name_display?: string
  display_order: number
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
  work_location_company?: string
  work_location_office?: string
  phone_number: string
  display_order: number
}

// 状態コードの選択肢
const STATUS_CHOICES = [
  'PRESENT',
  'CUSTOMER',
  'OUT',
  'MEETING',
  'REMOTE',
  'HOLIDAY',
  'LEAVE',
  'DIRECT_HOME'
]

// アクティブタブ
const activeTab = ref('employees')

// リストデータ
const rawEmployees = ref<Employee[]>([])
const rawDepartments = ref<Department[]>([])
const rawGroups = ref<Group[]>([])
const rawWorkLocations = ref<WorkLocation[]>([])
const rawStatusMasters = ref<StatusMaster[]>([])

// 検索キーワード
const employeeSearch = ref('')
const departmentSearch = ref('')
const groupSearch = ref('')
const workLocationSearch = ref('')
const statusMasterSearch = ref('')

// ダイアログ表示管理
const employeeDialog = ref(false)
const departmentDialog = ref(false)
const groupDialog = ref(false)
const workLocationDialog = ref(false)
const statusMasterDialog = ref(false)
const deleteConfirmDialog = ref(false)

// フォームリファレンスとバリデーション
const employeeFormRef = ref<any>(null)
const departmentFormRef = ref<any>(null)
const groupFormRef = ref<any>(null)
const workLocationFormRef = ref<any>(null)
const statusMasterFormRef = ref<any>(null)

const isEmployeeFormValid = ref(false)
const isDepartmentFormValid = ref(false)
const isGroupFormValid = ref(false)
const isWorkLocationFormValid = ref(false)
const isStatusMasterFormValid = ref(false)

// フォーム入力データ
const employeeForm = ref<Partial<Employee>>({})
const departmentForm = ref<Partial<Department>>({})
const groupForm = ref<Partial<Group>>({})
const workLocationForm = ref<Partial<WorkLocation>>({})
const statusMasterForm = ref<Partial<StatusMaster>>({})

// 送信中・エラー管理
const formSubmitting = ref(false)
const formErrorMessage = ref('')

// 削除対象管理
const deleteTarget = ref<{ type: string; id: number } | null>(null)
const deleteSubmitting = ref(false)

// ----------------------------------------------------
// 算出プロパティ (検索・フィルタリング)
// ----------------------------------------------------
const filteredEmployees = computed(() => {
  const query = employeeSearch.value?.toLowerCase() || ''
  return rawEmployees.value.filter(item => 
    item.name.toLowerCase().includes(query) ||
    item.employee_no.toLowerCase().includes(query) ||
    item.email.toLowerCase().includes(query)
  )
})

const filteredDepartments = computed(() => {
  const query = departmentSearch.value?.toLowerCase() || ''
  return rawDepartments.value.filter(item => 
    item.name.toLowerCase().includes(query)
  )
})

const filteredGroups = computed(() => {
  const query = groupSearch.value?.toLowerCase() || ''
  return rawGroups.value.filter(item => 
    item.name.toLowerCase().includes(query) ||
    item.department_name.toLowerCase().includes(query)
  )
})

const filteredWorkLocations = computed(() => {
  const query = workLocationSearch.value?.toLowerCase() || ''
  return rawWorkLocations.value.filter(item => 
    item.company_name.toLowerCase().includes(query) ||
    item.office_name.toLowerCase().includes(query) ||
    item.address.toLowerCase().includes(query)
  )
})

const filteredStatusMasters = computed(() => {
  const query = statusMasterSearch.value?.toLowerCase() || ''
  return rawStatusMasters.value.filter(item => 
    item.name.toLowerCase().includes(query)
  )
})

// 社員登録フォームにおけるグループの選択肢（選択された部署に属するもののみ）
const filteredGroupsForEmployeeSelect = computed(() => {
  if (!employeeForm.value.department) return []
  return rawGroups.value.filter(g => g.department === employeeForm.value.department)
})

// ----------------------------------------------------
// イベントハンドラ (APIデータ取得)
// ----------------------------------------------------
const fetchData = async () => {
  try {
    const [empRes, deptRes, groupRes, locRes, statusRes] = await Promise.all([
      api.get('/employees/'),
      api.get('/departments/'),
      api.get('/groups/'),
      api.get('/work-locations/'),
      api.get('/status-masters/')
    ])
    rawEmployees.value = empRes.data
    rawDepartments.value = deptRes.data
    rawGroups.value = groupRes.data
    rawWorkLocations.value = locRes.data
    rawStatusMasters.value = statusRes.data
  } catch (error) {
    console.error('データ取得エラー:', error)
  }
}

const router = useRouter()

onMounted(async () => {
  try {
    const meRes = await api.get('/presence/me/')
    if (!meRes.data.is_staff) {
      alert('管理者権限がありません。')
      router.push('/')
      return
    }
  } catch (error) {
    console.error('管理者チェックエラー:', error)
    router.push('/')
    return
  }
  fetchData()
})

// ----------------------------------------------------
// ダイヤログ開閉と初期化
// ----------------------------------------------------
const openEmployeeDialog = (item?: Employee) => {
  formErrorMessage.value = ''
  if (item) {
    employeeForm.value = { ...item }
  } else {
    employeeForm.value = {
      employee_no: '',
      name: '',
      email: '',
      department: undefined,
      group: undefined,
      work_location: null,
      phone_number: '',
      display_order: 0
    }
  }
  employeeDialog.value = true
}

const onDepartmentChange = () => {
  // 部署が切り替わったら、グループの選択をリセットする
  employeeForm.value.group = undefined
}

const openDepartmentDialog = (item?: Department) => {
  formErrorMessage.value = ''
  if (item) {
    departmentForm.value = { ...item }
  } else {
    departmentForm.value = {
      name: '',
      display_order: 0
    }
  }
  departmentDialog.value = true
}

const openGroupDialog = (item?: Group) => {
  formErrorMessage.value = ''
  if (item) {
    groupForm.value = { ...item }
  } else {
    groupForm.value = {
      department: undefined,
      name: '',
      display_order: 0
    }
  }
  groupDialog.value = true
}

const openWorkLocationDialog = (item?: WorkLocation) => {
  formErrorMessage.value = ''
  if (item) {
    workLocationForm.value = { ...item }
  } else {
    workLocationForm.value = {
      company_name: '',
      office_name: '',
      address: '',
      display_order: 0
    }
  }
  workLocationDialog.value = true
}

const openStatusMasterDialog = (item?: StatusMaster) => {
  formErrorMessage.value = ''
  if (item) {
    statusMasterForm.value = { ...item }
  } else {
    statusMasterForm.value = {
      name: '',
      display_order: 0
    }
  }
  statusMasterDialog.value = true
}

// ----------------------------------------------------
// 保存処理
// ----------------------------------------------------
const saveEmployee = async () => {
  const { valid } = await employeeFormRef.value.validate()
  if (!valid) return

  formSubmitting.value = true
  formErrorMessage.value = ''

  try {
    if (employeeForm.value.id) {
      await api.patch(`/employees/${employeeForm.value.id}/`, employeeForm.value)
    } else {
      await api.post('/employees/', employeeForm.value)
    }
    employeeDialog.value = false
    fetchData()
  } catch (error: any) {
    console.error(error)
    formErrorMessage.value = error.response?.data?.message || '保存中にエラーが発生しました。'
    if (error.response?.data?.details) {
      const details = error.response.data.details
      formErrorMessage.value += ' ' + Object.keys(details).map(k => `${k}: ${details[k]}`).join(', ')
    }
  } finally {
    formSubmitting.value = false
  }
}

const saveDepartment = async () => {
  const { valid } = await departmentFormRef.value.validate()
  if (!valid) return

  formSubmitting.value = true
  formErrorMessage.value = ''

  try {
    if (departmentForm.value.id) {
      await api.patch(`/departments/${departmentForm.value.id}/`, departmentForm.value)
    } else {
      await api.post('/departments/', departmentForm.value)
    }
    departmentDialog.value = false
    fetchData()
  } catch (error: any) {
    formErrorMessage.value = error.response?.data?.message || '保存中にエラーが発生しました。'
  } finally {
    formSubmitting.value = false
  }
}

const saveGroup = async () => {
  const { valid } = await groupFormRef.value.validate()
  if (!valid) return

  formSubmitting.value = true
  formErrorMessage.value = ''

  try {
    if (groupForm.value.id) {
      await api.patch(`/groups/${groupForm.value.id}/`, groupForm.value)
    } else {
      await api.post('/groups/', groupForm.value)
    }
    groupDialog.value = false
    fetchData()
  } catch (error: any) {
    formErrorMessage.value = error.response?.data?.message || '保存中にエラーが発生しました。'
  } finally {
    formSubmitting.value = false
  }
}

const saveWorkLocation = async () => {
  const { valid } = await workLocationFormRef.value.validate()
  if (!valid) return

  formSubmitting.value = true
  formErrorMessage.value = ''

  try {
    if (workLocationForm.value.id) {
      await api.patch(`/work-locations/${workLocationForm.value.id}/`, workLocationForm.value)
    } else {
      await api.post('/work-locations/', workLocationForm.value)
    }
    workLocationDialog.value = false
    fetchData()
  } catch (error: any) {
    formErrorMessage.value = error.response?.data?.message || '保存中にエラーが発生しました。'
  } finally {
    formSubmitting.value = false
  }
}

const saveStatusMaster = async () => {
  const { valid } = await statusMasterFormRef.value.validate()
  if (!valid) return

  formSubmitting.value = true
  formErrorMessage.value = ''

  try {
    if (statusMasterForm.value.id) {
      await api.patch(`/status-masters/${statusMasterForm.value.id}/`, statusMasterForm.value)
    } else {
      await api.post('/status-masters/', statusMasterForm.value)
    }
    statusMasterDialog.value = false
    fetchData()
  } catch (error: any) {
    formErrorMessage.value = error.response?.data?.message || '保存中にエラーが発生しました。'
  } finally {
    formSubmitting.value = false
  }
}

// ----------------------------------------------------
// 削除処理
// ----------------------------------------------------
const confirmDelete = (type: string, id: number) => {
  deleteTarget.value = { type, id }
  deleteConfirmDialog.value = true
}

const executeDelete = async () => {
  if (!deleteTarget.value) return

  deleteSubmitting.value = true
  const { type, id } = deleteTarget.value

  try {
    let endpoint = ''
    if (type === 'employee') endpoint = `/employees/${id}/`
    else if (type === 'department') endpoint = `/departments/${id}/`
    else if (type === 'group') endpoint = `/groups/${id}/`
    else if (type === 'work-location') endpoint = `/work-locations/${id}/`
    else if (type === 'status-master') endpoint = `/status-masters/${id}/`

    await api.delete(endpoint)
    deleteConfirmDialog.value = false
    fetchData()
  } catch (error: any) {
    console.error('削除エラー:', error)
    alert(error.response?.data?.message || '削除中にエラーが発生しました。子データが紐づいている可能性があります。')
  } finally {
    deleteSubmitting.value = false
    deleteTarget.value = null
  }
}
</script>

<style scoped>
.v-table th {
  font-size: 0.875rem !important;
}
.v-table td {
  font-size: 0.875rem !important;
}
</style>
