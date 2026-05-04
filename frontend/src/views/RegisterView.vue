<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="5" lg="4">
        <v-card elevation="4" rounded="lg">
          <v-card-title class="text-h5 pa-6 pb-2">
            <v-icon icon="mdi-account-plus" class="mr-2" />
            Регистрация
          </v-card-title>
          <v-card-text class="pa-6">
            <v-alert
              v-if="successMessage"
              type="success"
              variant="tonal"
              class="mb-4"
              icon="mdi-email-check"
            >
              {{ successMessage }}
            </v-alert>
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
            <v-form v-if="!successMessage" ref="formRef" @submit.prevent="handleRegister">
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
                Зарегистрироваться
              </v-btn>
            </v-form>
          </v-card-text>
          <v-card-actions class="px-6 pb-6">
            <span class="text-body-2 text-medium-emphasis">
              Уже есть аккаунт?
            </span>
            <v-btn variant="text" color="primary" size="small" to="/login" class="ml-1">
              Войти
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import { register } from '../api/auth.js'

const formRef = ref(null)
const email = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

const emailRules = [
  (v) => !!v || 'Email обязателен',
  (v) => /.+@.+\..+/.test(v) || 'Введите корректный email',
]

const passwordRules = [
  (v) => !!v || 'Пароль обязателен',
  (v) => v.length >= 6 || 'Минимум 6 символов',
]

async function handleRegister() {
  const { valid } = await formRef.value.validate()
  if (!valid) return

  loading.value = true
  errorMessage.value = ''
  try {
    await register(email.value, password.value)
    successMessage.value = 'Письмо с ключом отправлено на почту'
  } catch (err) {
    errorMessage.value = err.response?.data?.detail || 'Ошибка регистрации. Попробуйте ещё раз.'
  } finally {
    loading.value = false
  }
}
</script>
