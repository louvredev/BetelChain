<script setup lang="ts">
import { startOfDay, endOfDay } from 'date-fns'

definePageMeta({
  layout: 'dashboard'
})

const period = ref<'daily'>('daily')

// Range selalu 24 jam (hari ini, dari 00:00 hingga 23:59)
const range = computed(() => ({
  start: startOfDay(new Date()),
  end: endOfDay(new Date())
}))
</script>

<template>
  <UDashboardPanel id="home">
    <template #header>
      <UDashboardNavbar title="Home" :ui="{ right: 'gap-3' }">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <DashboardHomeStats :period="period" :range="range" />
      <DashboardHomeChart :period="period" :range="range" />
    </template>
  </UDashboardPanel>
</template>
