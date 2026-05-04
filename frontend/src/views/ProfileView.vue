<template>
  <v-container class="py-8">
    <v-row justify="center">
      <v-col cols="12" sm="10" md="7" lg="6">

        <v-alert v-if="loadError" type="error" variant="tonal" class="mb-4">
          {{ loadError }}
        </v-alert>

        <!-- Profile card -->
        <v-card elevation="3" rounded="lg" class="mb-4" :loading="profileLoading">
          <v-card-title class="pa-6 pb-3">
            <v-icon icon="mdi-account-circle" class="mr-2" />
            Личный кабинет
          </v-card-title>
          <v-card-text class="pa-6 pt-2">
            <v-list lines="two" class="pa-0">
              <v-list-item prepend-icon="mdi-email" title="Email" :subtitle="profile.email || '—'" />
              <v-list-item
                prepend-icon="mdi-check-circle"
                title="Статус"
                :subtitle="profile.is_active ? 'Активен' : 'Неактивен'"
              >
                <template #append>
                  <v-chip
                    :color="profile.is_active ? 'success' : 'error'"
                    size="small"
                    variant="tonal"
                  >
                    {{ profile.is_active ? 'Активен' : 'Неактивен' }}
                  </v-chip>
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
          <v-card-actions class="pa-6 pt-0 gap-2 flex-wrap">
            <v-btn
              color="primary"
              variant="tonal"
              prepend-icon="mdi-key-variant"
              :loading="keyLoading"
              @click="handleRefreshKey"
            >
              Обновить ключ
            </v-btn>
            <v-spacer />
            <v-btn
              color="error"
              variant="text"
              prepend-icon="mdi-logout"
              @click="logout"
            >
              Выйти
            </v-btn>
          </v-card-actions>
        </v-card>

        <v-alert
          v-if="keyMessage"
          :type="keyMessageType"
          variant="tonal"
          class="mb-4"
          closable
          @click:close="keyMessage = ''"
        >
          {{ keyMessage }}
        </v-alert>

        <!-- Change password card -->
        <v-card elevation="3" rounded="lg">
          <v-card-title class="pa-6 pb-3">
            <v-icon icon="mdi-lock-reset" class="mr-2" />
            Смена пароля
          </v-card-title>
          <v-card-text class="pa-6 pt-2">
            <v-alert
              v-if="passwordMessage"
              :type="passwordMessageType"
              variant="tonal"
              class="mb-4"
              closable
              @click:close="passwordMessage = ''"
            >
              {{ passwordMessage }}
            </v-alert>
            <v-form ref="passwordFormRef" @submit.prevent="handleChangePassword">
              <v-text-field
                v-model="currentPassword"
                label="Текущий пароль"
                :type="showCurrent ? 'text' : 'password'"
                prepend-inner-icon="mdi-lock"
                :append-inner-icon="showCurrent ? 'mdi-eye-off' : 'mdi-eye'"
                variant="outlined"
                :rules="requiredRules"
                class="mb-3"
                @click:append-inner="showCurrent = !showCurrent"
              />
              <v-text-field
                v-model="newPassword"
                label="Новый пароль"
                :type="showNew ? 'text' : 'password'"
                prepend-inner-icon="mdi-lock-plus"
                :append-inner-icon="showNew ? 'mdi-eye-off' : 'mdi-eye'"
                variant="outlined"
                :rules="newPasswordRules"
                class="mb-3"
                @click:append-inner="showNew = !showNew"
              />
              <v-text-field
                v-model="newPasswordConfirm"
                label="Повторите новый пароль"
                :type="showConfirm ? 'text' : 'password'"
                prepend-inner-icon="mdi-lock-check"
                :append-inner-icon="showConfirm ? 'mdi-eye-off' : 'mdi-eye'"
                variant="outlined"
                :rules="confirmRules"
                class="mb-4"
                @click:append-inner="showConfirm = !showConfirm"
              />
              <v-btn
                type="submit"
                color="primary"
                size="large"
                block
                :loading="passwordLoading"
              >
                Сменить пароль
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>

      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getProfile, refreshKey, changePassword } from '../api/auth.js'

const router = useRouter()

const profile = ref({ email: '', is_active: false })
const profileLoading = ref(true)
const loadError = ref('')

const keyLoading = ref(false)
const keyMessage = ref('')
const keyMessageType = ref('success')

const passwordFormRef = ref(null)
const currentPassword = ref('')
const newPassword = ref('')
const newPasswordConfirm = ref('')
const showCurrent = ref(false)
const showNew = ref(false)
const showConfirm = ref(false)
const passwordLoading = ref(false)
const passwordMessage = ref('')
const passwordMessageType = ref('success')

const requiredRules = [(v) => !!v || 'Поле обязательно']
const newPasswordRules = [
  (v) => !!v || 'Поле обязательно',
  (v) => v.length >= 6 || 'Минимум 6 символов',
]
const confirmRules = [
  (v) => !!v || 'Поле обязательно',
  (v) => v === newPassword.value || 'Пароли не совпадают',
]

onMounted(async () => {
  try {
    const { data } = await getProfile()
    profile.value = data
  } catch (err) {
    if (err.response?.status === 401) {
      localStorage.removeItem('access_token')
      router.push('/login')
    } else {
      loadError.value = 'Не удалось загрузить профиль.'
    }
  } finally {
    profileLoading.value = false
  }
})

async function handleRefreshKey() {
  keyLoading.value = true
  keyMessage.value = ''
  try {
    await refreshKey()
    keyMessageType.value = 'success'
    keyMessage.value = 'Ключ успешно обновлён.'
  } catch (err) {
    keyMessageType.value = 'error'
    keyMessage.value = err.response?.data?.detail || 'Ошибка при обновлении ключа.'
  } finally {
    keyLoading.value = false
  }
}

async function handleChangePassword() {
  const { valid } = await passwordFormRef.value.validate()
  if (!valid) return

  passwordLoading.value = true
  passwordMessage.value = ''
  try {
    await changePassword(currentPassword.value, newPassword.value, newPasswordConfirm.value)
    passwordMessageType.value = 'success'
    passwordMessage.value = 'Пароль успешно изменён.'
    currentPassword.value = ''
    newPassword.value = ''
    newPasswordConfirm.value = ''
    passwordFormRef.value.reset()
  } catch (err) {
    passwordMessageType.value = 'error'
    passwordMessage.value = err.response?.data?.detail || 'Ошибка при смене пароля.'
  } finally {
    passwordLoading.value = false
  }
}

function logout() {
  localStorage.removeItem('access_token')
  router.push('/login')
}
</script>
