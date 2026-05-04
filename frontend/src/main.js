import { createApp } from 'vue'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

import App from './App.vue'
import router from './router/index.js'

const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'light',
  },
})

createApp(App)
  .use(router)
  .use(vuetify)
  .mount('#app')
