<script setup lang="ts">
import { format } from 'date-fns'
import type { Transaction } from '~/types/betelchain'

const props = defineProps<{
  transactions: Transaction[]
  loading?: boolean
}>()

const transactionsRefs = ref<Element[]>([])
const selectedTransaction = defineModel<Transaction | null>()

watch(selectedTransaction, () => {
  if (!selectedTransaction.value) return
  const ref = transactionsRefs.value[props.transactions.findIndex(t => t.id === selectedTransaction.value?.id)]
  if (ref) ref.scrollIntoView({ block: 'nearest' })
})

defineShortcuts({
  arrowdown: () => {
    const index = props.transactions.findIndex(t => t.id === selectedTransaction.value?.id)

    if (index === -1) {
      selectedTransaction.value = props.transactions[0]
    } else if (index < props.transactions.length - 1) {
      selectedTransaction.value = props.transactions[index + 1]
    }
  },
  arrowup: () => {
    const index = props.transactions.findIndex(t => t.id === selectedTransaction.value?.id)

    if (index === -1) {
      selectedTransaction.value = props.transactions[props.transactions.length - 1]
    } else if (index > 0) {
      selectedTransaction.value = props.transactions[index - 1]
    }
  }
})

const formatDate = (d?: string | null) => {
  if (!d) return ''
  return format(new Date(d), 'dd MMM HH:mm')
}
</script>

<template>
  <div class="overflow-y-auto divide-y divide-default">
    <div v-if="loading" class="p-4 text-sm text-muted">
      Loading transactions...
    </div>

    <div
      v-for="(tx, index) in transactions"
      :key="tx.id || index"
      :ref="el => { transactionsRefs[index] = el as Element }"
    >
      <div
        class="p-4 sm:px-6 text-sm cursor-pointer border-l-2 transition-colors"
        :class="[
          'text-toned',
          selectedTransaction && selectedTransaction.id === tx.id
            ? 'border-primary bg-primary/10'
            : 'border-(--ui-bg) hover:border-primary hover:bg-primary/5'
        ]"
        @click="selectedTransaction = tx"
      >
        <div class="flex items-center justify-between">
          <div class="flex flex-col gap-0.5">
            <span class="font-semibold text-highlighted">
              {{ tx.transaction_code }}
            </span>
            <span class="text-xs text-muted">
            Farmer: {{ tx.farmer_id || 'Unknown farmer' }}
            </span>
            <span class="text-xs text-muted">
                {{ formatDate(tx.created_at) }}
            </span>
          </div>
        </div>

        <div class="mt-1 flex items-center justify-between text-xs">
            <span class="text-muted">
                Initial: {{ tx.initial_price?.toLocaleString('id-ID') }} IDR
            </span>
            <UBadge
                size="xs"
                :color="tx.payment_status === 'paid' ? 'success' : tx.payment_status === 'partial' ? 'warning' : 'neutral'"
                variant="subtle"
                class="capitalize"
            >
                {{ tx.payment_status || 'unpaid' }}
            </UBadge>
        </div>
      </div>
    </div>

    <div v-if="!loading && !transactions.length" class="p-4 text-sm text-muted">
      No transactions found.
    </div>
  </div>
</template>