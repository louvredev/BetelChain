<script setup lang="ts">
import { sub } from 'date-fns'
import type { Period, Range } from '~/types'

definePageMeta({
  layout: 'dashboard'
})

const range = shallowRef<Range>({
  start: sub(new Date(), { days: 14 }),
  end: new Date()
})
const period = ref<Period>('daily')
</script>

<template>
  <UDashboardPanel id="home">
    <template #header>
      <UDashboardNavbar title="Home" :ui="{ right: 'gap-3' }">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
      </UDashboardNavbar>

      <UDashboardToolbar>
        <template #left>
          <DashboardHomeDateRangePicker v-model="range" class="-ms-1" />
          <DashboardHomePeriodSelect v-model="period" :range="range" />
        </template>
      </UDashboardToolbar>
    </template>

    <template #body>
      <DashboardHomeStats :period="period" :range="range" />
      <DashboardHomeChart :period="period" :range="range" />
    </template>
  </UDashboardPanel>
</template>
