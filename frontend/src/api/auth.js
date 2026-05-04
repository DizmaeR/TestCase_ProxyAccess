import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8002/api/v1',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const register = (email, password) =>
  api.post('/auth/register', { email, password })

export const login = (email, password) =>
  api.post('/auth/login', { email, password })

export const getProfile = () =>
  api.get('/profile/')

export const refreshKey = () =>
  api.post('/profile/refresh-key')

export const changePassword = (oldPassword, newPassword, newPasswordConfirm) =>
  api.put('/profile/password', {
    old_password: oldPassword,
    new_password: newPassword,
    new_password_confirm: newPasswordConfirm,
  })

export const activateKey = (key) =>
  api.post(`/proxy/activate-key?key=${encodeURIComponent(key)}`)

export const disconnectProxy = () =>
  api.post('/proxy/disconnect')
