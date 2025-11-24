// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  modules: [
    '@nuxt/image',
    '@nuxt/ui',
    '@nuxt/content',
    '@vueuse/nuxt',
    '@pinia/nuxt'
  ],

  devtools: {
    enabled: true
  },

  css: ['./app/assets/css/main.css'],

  mdc: {
    highlight: {
      noApiRoute: false
    }
  },

  routeRules: {
    '/': { prerender: true },
    '/api/**': { cors: true }
  },

  nitro: {
    prerender: {
      routes: ['/']
    }
  },

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000'
    }
  },

  compatibilityDate: '2025-01-15'
})