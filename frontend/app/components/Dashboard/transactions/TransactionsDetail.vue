<script setup lang="ts">
import { format } from 'date-fns'
import type { Transaction } from '~/types/betelchain'

const props = defineProps<{
  transaction: Transaction
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'updated'): void
}>()

const { getTransactionSummary, startRecording, completeRecording } = useBetelchain()
const toast = useToast()

const loading = ref(true)
const refreshing = ref(false)
const actionLoading = ref<'start' | 'complete' | null>(null)

const summary = ref<{
  transaction: any
  harvest_summary: any
  payment_summary: any
} | null>(null)

const formatDateTime = (d?: string | null) => {
  if (!d) return '-'
  return format(new Date(d), 'dd MMM yyyy HH:mm')
}

const formatCurrency = (v?: number | null) => {
  if (!v) return 'Rp0'
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(v)
}

const loadSummary = async () => {
  if (!props.transaction?.id) return
  try {
    loading.value = !summary.value
    refreshing.value = !!summary.value
    const data = await getTransactionSummary(props.transaction.id)
    summary.value = data
  } catch (error: any) {
    toast.add({
      title: 'Error',
      description: error.message || 'Failed to load transaction summary',
      color: 'red'
    })
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

// reload saat transaction yang dipilih berubah
watch(
  () => props.transaction.id,
  () => {
    summary.value = null
    loadSummary()
  },
  { immediate: true }
)

const onStartRecording = async () => {
  if (!props.transaction.id) return
  try {
    actionLoading.value = 'start'
    await startRecording(props.transaction.id)
    toast.add({
      title: 'Recording started',
      description: 'Recording for this transaction has started.',
      color: 'green'
    })
    await loadSummary()
    emit('updated')
  } catch (error: any) {
    toast.add({
      title: 'Error',
      description: error.message || 'Failed to start recording',
      color: 'red'
    })
  } finally {
    actionLoading.value = null
  }
}

const onCompleteRecording = async () => {
  if (!props.transaction.id) return
  try {
    actionLoading.value = 'complete'
    await completeRecording(props.transaction.id)
    toast.add({
      title: 'Recording completed',
      description: 'Recording has been completed and totals calculated.',
      color: 'green'
    })
    await loadSummary()
    emit('updated')
  } catch (error: any) {
    toast.add({
      title: 'Error',
      description: error.message || 'Failed to complete recording',
      color: 'red'
    })
  } finally {
    actionLoading.value = null
  }
}
</script>

<template>
  <UDashboardPanel id="transactions-2">
    <UDashboardNavbar :title="summary?.transaction?.transaction_code || transaction.transaction_code" :toggle="false">
      <template #leading>
        <UButton
          icon="i-lucide-x"
          color="neutral"
          variant="ghost"
          class="-ms-1.5"
          @click="emit('close')"
        />
      </template>

      <template #right>
        <UButton
          color="neutral"
          variant="ghost"
          icon="i-lucide-rotate-cw"
          :loading="refreshing"
          @click="loadSummary"
        />
      </template>
    </UDashboardNavbar>

    <div class="flex flex-col gap-4 p-4 sm:p-6 overflow-y-auto">
      <!-- Status + actions -->
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="space-y-1">
          <p class="text-sm text-muted">
            Farmer:
            <span class="font-medium text-highlighted">
              {{ summary?.transaction?.farmer_name || summary?.transaction?.farmer_code || transaction.farmer_id }}
            </span>
          </p>
          <p class="text-xs text-muted">
            Created at: {{ formatDateTime(summary?.transaction?.created_at || transaction.created_at) }}
          </p>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <UBadge
            class="capitalize"
            :color="summary?.transaction?.payment_status === 'paid'
              ? 'success'
              : summary?.transaction?.payment_status === 'partial'
                ? 'warning'
                : 'neutral'"
            variant="subtle"
          >
            {{ summary?.transaction?.payment_status || transaction.payment_status || 'unpaid' }}
          </UBadge>

          <UButton
            size="xs"
            color="primary"
            variant="subtle"
            icon="i-lucide-play-circle"
            :loading="actionLoading === 'start'"
            :disabled="!!summary?.transaction?.recording_started_at"
            @click="onStartRecording"
          >
            Start recording
          </UButton>

          <UButton
            size="xs"
            color="primary"
            variant="solid"
            icon="i-lucide-check-circle"
            :loading="actionLoading === 'complete'"
            :disabled="!summary?.transaction?.recording_started_at || !!summary?.transaction?.recording_completed_at"
            @click="onCompleteRecording"
          >
            Complete recording
          </UButton>
        </div>
      </div>

      <!-- Loading state -->
      <div v-if="loading" class="text-sm text-muted">
        Loading transaction summary...
      </div>

      <template v-else-if="summary">
        <!-- Transaction summary -->
        <UCard>
          <template #header>
            <div class="flex items-center justify-between">
              <p class="font-semibold text-sm">Transaction summary</p>
            </div>
          </template>

          <div class="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            <div>
              <p class="text-muted text-xs">Initial price</p>
              <p class="font-medium">
                {{ formatCurrency(summary.transaction.initial_price) }}
              </p>
            </div>
            <div>
              <p class="text-muted text-xs">Total weight (kg)</p>
              <p class="font-medium">
                {{ summary.transaction.total_weight_kg ?? '-' }}
              </p>
            </div>
            <div>
              <p class="text-muted text-xs">Total price</p>
              <p class="font-medium">
                {{ summary.transaction.total_price ? formatCurrency(summary.transaction.total_price) : '-' }}
              </p>
            </div>
            <div>
              <p class="text-muted text-xs">Recording started</p>
              <p class="text-xs">
                {{ formatDateTime(summary.transaction.recording_started_at) }}
              </p>
            </div>
              <div>
              <p class="text-muted text-xs">Recording completed</p>
              <p class="text-xs">
                {{ formatDateTime(summary.transaction.recording_completed_at) }}
              </p>
            </div>
          </div>
        </UCard>

        <!-- Harvest summary -->
        <UCard>
          <template #header>
            <p class="font-semibold text-sm">Harvest summary</p>
          </template>

          <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div>
              <p class="text-muted text-xs">Total records</p>
              <p class="font-medium">
                {{ summary.harvest_summary.total_records }}
              </p>
            </div>
            <div>
              <p class="text-muted text-xs">Total weight (kg)</p>
              <p class="font-medium">
                {{ summary.harvest_summary.total_weight_kg ?? '-' }}
              </p>
            </div>
            <div>
              <p class="text-muted text-xs">Grades (A / B / C)</p>
              <p class="font-medium">
                {{ summary.harvest_summary.grade_breakdown.A || 0 }} /
                {{ summary.harvest_summary.grade_breakdown.B || 0 }} /
                {{ summary.harvest_summary.grade_breakdown.C || 0 }}
              </p>
            </div>
            <div>
              <p class="text-muted text-xs">Avg confidence</p>
              <p class="font-medium">
                {{ summary.harvest_summary.average_confidence ?? 0 }}%
              </p>
            </div>
          </div>
        </UCard>

        <!-- Payment summary -->
        <UCard>
          <template #header>
            <p class="font-semibold text-sm">Payment summary</p>
          </template>

          <div class="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            <div>
              <p class="text-muted text-xs">Total approved</p>
              <p class="font-medium">
                {{ formatCurrency(summary.payment_summary.total_approved) }}
              </p>
            </div>
            <div>
              <p class="text-muted text-xs">Remaining needed</p>
              <p class="font-medium">
                {{ formatCurrency(summary.payment_summary.remaining_needed) }}
              </p>
            </div>
            <div>
              <p class="text-muted text-xs">Payments count</p>
              <p class="font-medium">
                {{ summary.payment_summary.total_payments }}
              </p>
            </div>
          </div>
        </UCard>
      </template>
    </div>
  </UDashboardPanel>
</template>
