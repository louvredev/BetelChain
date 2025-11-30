<script setup lang="ts">
import type { Farmer } from '~/types/betelchain'

definePageMeta({
  layout: 'dashboard'
})

const { listFarmers } = useBetelchain()
const toast = useToast()

const farmers = ref<Farmer[]>([])
const isLoading = ref(false)

const fetchFarmers = async () => {
  isLoading.value = true
  try {
    const data = await listFarmers()
    farmers.value = data
  } catch (error: any) {
    toast.add({
      title: 'Error',
      description: error.message || 'Failed to fetch farmers',
      color: 'red'
    })
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchFarmers()
})
</script>

<template>
  <div class="space-y-6">
    <div>
      <h3 class="text-lg font-semibold mb-2">Registered Farmers</h3>
      <p class="text-sm text-gray-500">Manage your farmer list and their information.</p>
    </div>

    <!-- Farmers List -->
    <UCard :ui="{ divide: 'divide-y divide-gray-200 dark:divide-gray-800' }">
      <template #header>
        <div class="flex items-center justify-between">
          <p class="text-sm font-medium">{{ farmers.length }} farmers</p>
          <UButton
            size="sm"
            color="gray"
            variant="ghost"
            icon="i-lucide-rotate-cw"
            :loading="isLoading"
            @click="fetchFarmers"
          >
            Refresh
          </UButton>
        </div>
      </template>

      <div v-if="farmers.length" class="space-y-3">
        <div
          v-for="farmer in farmers"
          :key="farmer.id"
          class="flex items-center justify-between p-4 rounded-lg border border-default hover:bg-elevated/50 transition-colors"
        >
          <div class="flex-1">
            <p class="font-semibold">{{ farmer.full_name }}</p>
            <p class="text-sm text-gray-500">{{ farmer.farmer_code }} • {{ farmer.phone }}</p>
            <p class="text-xs text-gray-400 mt-1">{{ farmer.address }}</p>
          </div>
          <UBadge :color="farmer.is_active ? 'green' : 'red'" variant="soft">
            {{ farmer.is_active ? 'Active' : 'Inactive' }}
          </UBadge>
        </div>
      </div>

      <div v-else class="py-8 text-center">
        <UIcon name="i-lucide-users" class="mx-auto mb-2 size-8 text-gray-400" />
        <p class="text-sm text-gray-500">No farmers registered</p>
      </div>
    </UCard>
  </div>
</template>
