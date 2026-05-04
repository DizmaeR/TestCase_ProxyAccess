import { createRouter, createWebHistory } from 'vue-router'
import RegisterView from '../views/RegisterView.vue'
import LoginView from '../views/LoginView.vue'
import ProfileView from '../views/ProfileView.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/register', component: RegisterView },
  { path: '/login', component: LoginView },
  {
    path: '/profile',
    component: ProfileView,
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const token = localStorage.getItem('access_token')
  if (to.meta.requiresAuth && !token) {
    return '/login'
  }
})

export default router
