<template>
  <v-app-bar color="primary" elevation="2">
    <v-app-bar-title>
      <v-icon icon="mdi-shield-lock" class="mr-2" />
      Proxy Access
    </v-app-bar-title>
    <template #append>
      <template v-if="isLoggedIn">
        <v-btn variant="text" to="/profile" prepend-icon="mdi-account">Профиль</v-btn>
        <v-btn variant="text" prepend-icon="mdi-logout" @click="logout">Выйти</v-btn>
      </template>
      <template v-else>
        <v-btn variant="text" to="/login" prepend-icon="mdi-login">Войти</v-btn>
        <v-btn variant="text" to="/register" prepend-icon="mdi-account-plus">Регистрация</v-btn>
      </template>
    </template>
  </v-app-bar>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

// route.path as dependency forces recompute on every navigation
const isLoggedIn = computed(() => {
  void route.path
  return !!localStorage.getItem('access_token')
})

function logout() {
  localStorage.removeItem('access_token')
  router.push('/login')
}
</script>
