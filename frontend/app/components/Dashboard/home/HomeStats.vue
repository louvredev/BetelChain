<script setup lang="ts">
import type { Period, Range } from '~/types'

const props = defineProps<{
  period: Period
  range: Range
}>()

const { getWarehouseDashboard } = useBetelchain()

const formatCurrency = (value: number): string => {
  return value.toLocaleString('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0
  })
}

// Data untuk 4 kartu
const stats = ref([
  {
    title: 'Farmers',
    icon: 'i-lucide-users',
    value: '-',
    variation: 0
  },
  {
    title: 'Major grade',
    icon: 'i-lucide-chart-pie',
    value: '-',
    variation: 0
  },
  {
    title: 'Spent',
    icon: 'i-lucide-circle-dollar-sign',
    value: '-',
    variation: 0
  },
  {
    title: 'Sacks',
    icon: 'i-lucide-shopping-cart',
    value: '-',
    variation: 0
  }
])

const loading = ref(true)
const error = ref<string | null>(null)

const loadDashboard = async () => {
  try {
    loading.value = true
    error.value = null

    const data = await getWarehouseDashboard()

    const dominantPercent = data.dominant_grade
      ? Math.round(data.dominant_grade_ratio * 100)
      : 0

    stats.value = [
      {
        title: 'Farmers',
        icon: 'i-lucide-users',
        value: data.farmers_count.toString(),
        variation: 0
      },
      {
        title: 'Major grade',
        icon: 'i-lucide-chart-pie',
        value: data.dominant_grade || '-',
        variation: 0,
        badge: data.dominant_grade
          ? {
              label: `${Math.round(data.dominant_grade_ratio * 100)}%`,
              color: 'primary'
            }
          : null
      },
      {
        title: 'Spent',
        icon: 'i-lucide-circle-dollar-sign',
        value: formatCurrency(data.total_spent),
        variation: 0
      },
      {
        title: 'Sacks',
        icon: 'i-lucide-shopping-cart',
        value: data.total_sacks.toString(),
        variation: 0
      }
    ]
  } catch (e: any) {
    error.value = e.message || 'Failed to load dashboard summary'
  } finally {
    loading.value = false
  }
}

// Load sekali saat mount (opsional: bisa juga re-load saat range/period berubah)
await loadDashboard()

watch(
  () => [props.period, props.range],
  () => {
    // Untuk sekarang bisa diabaikan (murni summary total), 
    // atau nanti di-make dynamic by period
  }
)
</script>


<template>
  <UPageGrid class="lg:grid-cols-4 gap-4 sm:gap-6 lg:gap-px">
    <UPageCard
      v-for="(stat, index) in stats"
      :key="index"
      :icon="stat.icon"
      :title="stat.title"
      variant="subtle"
      :ui="{
        container: 'gap-y-1.5',
        wrapper: 'items-start',
        leading: 'p-2.5 rounded-full bg-primary/10 ring ring-inset ring-primary/25 flex-col',
        title: 'font-normal text-muted text-xs uppercase'
      }"
      class="lg:rounded-none first:rounded-l-lg last:rounded-r-lg hover:z-1"
    >
      <div class="flex items-center gap-2">
        <span class="text-2xl font-semibold text-lg">
          {{ stat.value }}
        </span>

        <UBadge
          v-if="stat.variation !== 0"
          :color="stat.variation > 0 ? 'success' : 'error'"
          variant="subtle"
          class="text-xs"
        >
          {{ stat.variation > 0 ? '+' : '' }}{{ stat.variation }}%
        </UBadge>
        <UBadge
          v-if="stat.badge"
          :color="stat.badge.color"
          variant="subtle"
          class="text-xs"
        >
          {{ stat.badge.label }}
        </UBadge>
      </div>
    </UPageCard>
  </UPageGrid>
</template>

