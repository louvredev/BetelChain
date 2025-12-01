<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { breakpointsTailwind } from '@vueuse/core'
import type { Transaction } from '~/types/betelchain'

definePageMeta({
  layout: 'dashboard'
})

const route = useRoute()
const breakpoints = useBreakpoints(breakpointsTailwind)

const { listTransactions } = useBetelchain()
const toast = useToast()

const statusFilter = ref<'all' | 'unpaid' | 'partial' | 'paid'>('all')
const transactions = ref<Transaction[]>([])
const status = ref<'idle' | 'pending' | 'success' | 'error'>('idle')

const selectedTransaction = ref<Transaction | null>(null)

const fetchTransactions = async () => {
  status.value = 'pending'
  try {
    const data = await listTransactions()
    transactions.value = data
    status.value = 'success'
  } catch (error: any) {
    status.value = 'error'
    toast.add({
      title: 'Error',
      description: error.message || 'Failed to fetch transactions',
      color: 'red'
    })
  }
}

await fetchTransactions()

// Filter by payment_status
const filteredTransactions = computed(() => {
  let base = transactions.value
  if (route.query.farmer_id) {
    base = base.filter(t => t.farmer_id === route.query.farmer_id)
  }
  if (statusFilter.value === 'all') return base
  return base.filter(t => (t.payment_status || 'unpaid') === statusFilter.value)
})


// Auto-select transaction from query param (e.g. ?transaction_id=...)
watch(
  () => route.query.transaction_id,
  (id) => {
    if (id) {
      const tx = transactions.value.find(t => t.id === id)
      if (tx) selectedTransaction.value = tx
    }
  },
  { immediate: true }
)

// Reset selection if not in filtered list
watch(filteredTransactions, () => {
  if (!filteredTransactions.value.find(t => t.id === selectedTransaction.value?.id)) {
    selectedTransaction.value = null
  }
})

const isTxPanelOpen = computed({
  get() {
    return !!selectedTransaction.value
  },
  set(value: boolean) {
    if (!value) selectedTransaction.value = null
  }
})

const isMobile = breakpoints.smaller('lg')
</script>

<template>
  <UDashboardPanel
    id="transactions-1"
    :default-size="25"
    :min-size="20"
    :max-size="30"
    resizable
  >
    <UDashboardNavbar title="Transactions">
      <template #leading>
        <UDashboardSidebarCollapse />
      </template>

      <template #trailing>
        <UBadge :label="filteredTransactions.length" variant="subtle" />
      </template>

      <template #right>
        <DashboardTransactionsCreateModal @created="fetchTransactions" />
        <USelect
          v-model="statusFilter"
          :items="[
            { label: 'All', value: 'all' },
            { label: 'Unpaid', value: 'unpaid' },
            { label: 'Partial', value: 'partial' },
            { label: 'Paid', value: 'paid' }
          ]"
          size="xs"
          class="min-w-28"
        />
      </template>
    </UDashboardNavbar>

    <DashboardTransactionsList
      v-model="selectedTransaction"
      :transactions="filteredTransactions"
      :loading="status === 'pending'"
    />
  </UDashboardPanel>

  <!-- Right panel (detail) - skeleton for now -->
  <DashboardTransactionsDetail
    v-if="selectedTransaction"
    :transaction="selectedTransaction"
    @close="selectedTransaction = null"
  />
  <div v-else class="hidden lg:flex flex-1 items-center justify-center">
    <UIcon name="i-lucide-receipt-text" class="size-32 text-dimmed" />
  </div>

  <!-- Mobile slide-over -->
  <ClientOnly>
    <USlideover v-if="isMobile" v-model:open="isTxPanelOpen">
      <template #content>
        <DashboardTransactionsDetail
          v-if="selectedTransaction"
          :transaction="selectedTransaction"
          @close="selectedTransaction = null"
        />
      </template>
    </USlideover>
  </ClientOnly>
</template>
