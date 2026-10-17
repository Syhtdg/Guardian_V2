// plugins/vuetify.js

// Styles
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

// Composables
import { createVuetify } from 'vuetify'
import { ko } from 'vuetify/locale'

// 관제실 느낌의 어두운 테마 (로그인 화면의 빨강·짙은 회색과 맞춤)
const guardian = {
  dark: true,
  colors: {
    background: '#0f1115',
    surface: '#181b21',
    'surface-bright': '#20242c',
    'surface-variant': '#2a2f38',
    primary: '#e53935',
    secondary: '#5cffd1',
    fire: '#ff5a36',
    smoke: '#9aa4b2',
    success: '#2ecc71',
    warning: '#f5a524',
    error: '#ff4d4f',
    info: '#4ea8ff',
  },
}

export default createVuetify({
  theme: {
    defaultTheme: 'guardian',
    themes: { guardian },
  },
  icons: {
    defaultSet: 'mdi',
  },
  locale: {
    locale: 'ko',
    messages: { ko },
  },
  defaults: {
    VCard: { rounded: 'lg' },
    VBtn: { rounded: 'lg' },
    VTextField: { variant: 'outlined', density: 'comfortable', color: 'primary' },
    VSelect: { variant: 'outlined', density: 'comfortable', color: 'primary' },
  },
})
