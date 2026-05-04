<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="5" lg="4">
        <v-card elevation="4" rounded="lg">
          <v-card-title class="text-h5 pa-6 pb-2">
            <v-icon icon="mdi-login" class="mr-2" />
            Вход
          </v-card-title>
          <v-card-text class="pa-6">
            <v-alert
              v-if="errorMessage"
              type="error"
              variant="tonal"
              class="mb-4"
              closable
              @click:close="errorMessage = ''"
            >
              {{ errorMessage }}
            </v-alert>
            <v-form ref="formRef" @submit.prevent="handleLogin">
              <v-text-field
                v-model="email"
                label="Email"
                type="email"
                prepend-inner-icon="mdi-email"
                variant="outlined"
                :rules="emailRules"
                class="mb-3"
                autofocus
              />
              <v-text-field
                v-model="password"
                label="Пароль"
                :type="showPassword ? 'text' : 'password'"
                prepend-inner-icon="mdi-lock"
                :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                variant="outlined"
                :rules="passwordRules"
                class="mb-4"
                @click:append-inner="showPassword = !showPassword"
              />
              <v-btn
                type="submit"
                color="primary"
                size="large"
                block
                :loading="loading"
              >
                Войти
              </v-btn>
            </v-form>
          </v-card-text>
          <v-card-actions class="px-6 pb-6">
            <span class="text-body-2 text-medium-emphasis">
              Нет аккаунта?
            </span>
            <v-btn variant="text" color="primary" size="small" to="/register" class="ml-1">
              Зарегистрироваться
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '../api/auth.js'

const router = useRouter()
const formRef = ref(null)
const email = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const errorMessage = ref('')

const emailRules = [
  (v) => !!v || 'Email обязателен',
  (v) => /.+@.+\..+/.test(v) || 'Введите корректный email',
]

const passwordRules = [
  (v) => !!v || 'Пароль обязателен',
]

async function handleLogin() {
  const { valid } = await formRef.value.validate()
  if (!valid) return

  loading.value = true
  errorMessage.value = ''
  try {
    const { data } = await login(email.value, password.value)
    localStorage.setItem('access_token', data.access_token)
    router.push('/profile')
  } catch (err) {
    errorMessage.value = err.response?.data?.detail || 'Неверный email или пароль.'
  } finally {
    loading.value = false
  }
}
</script>
