<script setup lang="ts">
import { format } from 'date-fns'
import type { Transaction, Payment } from '~/types/betelchain'
const isDev = process.env.NODE_ENV === 'development'

const props = defineProps<{
  transaction: Transaction
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'updated'): void
}>()

const {
  getTransactionSummary,
  startRecording,
  completeRecording,
  detectAndSaveHarvest,
  listPayments,
  createPayment,
  approvePayment
} = useBetelchain()

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

const loadPayments = async () => {
  if (!props.transaction?.id) return
  try {
    paymentsLoading.value = true
    payments.value = await listPayments(props.transaction.id)
  } catch (error: any) {
    toast.add({
      title: 'Error',
      description: error.message || 'Failed to load payments',
      color: 'red'
    })
  } finally {
    paymentsLoading.value = false
  }
}

const loadSummary = async () => {
  if (!props.transaction?.id) return
  try {
    loading.value = !summary.value
    refreshing.value = !!summary.value
    const data = await getTransactionSummary(props.transaction.id)
    summary.value = data
    await loadPayments()  // <— tambah di sini
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
const payments = ref<Payment[]>([])
const paymentsLoading = ref(false)

const addPaymentOpen = ref(false)
const addPaymentLoading = ref(false)

const paymentForm = reactive({
  payment_type: 'remaining' as 'initial' | 'remaining',
  amount: 0,
  payment_method: 'cash',
  payment_note: ''
})

const resetPaymentForm = () => {
  paymentForm.payment_type = 'remaining'
  paymentForm.amount = 0
  paymentForm.payment_method = 'cash'
  paymentForm.payment_note = ''
}

const onAddPayment = async () => {
  if (!props.transaction.id || !summary.value) return
  try {
    addPaymentLoading.value = true

    await createPayment({
      transaction_id: props.transaction.id,
      payment_type: paymentForm.payment_type,
      amount: paymentForm.amount,
      payment_method: paymentForm.payment_method,
      payment_note: paymentForm.payment_note || undefined
    })

    toast.add({
      title: 'Payment created',
      description: 'Payment has been recorded.',
      color: 'green'
    })

    addPaymentOpen.value = false
    resetPaymentForm()
    await loadSummary()
    await loadPayments()  // <— TAMBAH BARIS INI
    emit('updated')
  } catch (error: any) {
    toast.add({
      title: 'Error',
      description: error.message || 'Failed to create payment',
      color: 'red'
    })
  } finally {
    addPaymentLoading.value = false
  }
}

const videoEl = ref<HTMLVideoElement | null>(null)
const canvasEl = ref<HTMLCanvasElement | null>(null)
const cameraStream = ref<MediaStream | null>(null)
const cameraOpen = ref(false)
const cameraLoading = ref(false)
const scanning = ref(false)
const openCamera = async () => {
  try {
    cameraLoading.value = true

    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment' }
    })

    cameraStream.value = stream
    cameraOpen.value = true

    await nextTick()

    const video = videoEl.value
    if (video) {
      video.srcObject = stream
      video.autoplay = true
      video.playsInline = true
      video.muted = true

      await new Promise(resolve => {
        video.onloadedmetadata = () => {
          video.play()
          resolve(null)
        }
      })
    }
  } catch (error: any) {
    cameraOpen.value = false
    if (cameraStream.value) {
      cameraStream.value.getTracks().forEach(t => t.stop())
      cameraStream.value = null
    }
    toast.add({
      title: 'Camera error',
      description: error.message || 'Failed to access camera',
      color: 'red'
    })
  } finally {
    cameraLoading.value = false
  }
}

const closeCamera = () => {
  if (cameraStream.value) {
    cameraStream.value.getTracks().forEach(t => t.stop())
  }
  cameraStream.value = null
  cameraOpen.value = false
}

onBeforeUnmount(() => {
  closeCamera()
})

const scanSack = async () => {
  if (!videoEl.value || !canvasEl.value || !props.transaction.id) return

  try {
    scanning.value = true

    const video = videoEl.value
    const canvas = canvasEl.value
    const ctx = canvas.getContext('2d')
    if (!ctx) throw new Error('Canvas not supported')

    await new Promise(resolve => {
      if (video.readyState >= 2) return resolve(null)
      video.onloadeddata = () => resolve(null)
    })

    canvas.width = video.videoWidth || 640
    canvas.height = video.videoHeight || 480
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

    const blob: Blob | null = await new Promise(resolve =>
      canvas.toBlob(b => resolve(b), 'image/jpeg', 0.9)
    )
    if (!blob) throw new Error('Failed to capture frame')

    const file = new File([blob], `harvest-${Date.now()}.jpg`, { type: 'image/jpeg' })

    const data = await detectAndSaveHarvest(props.transaction.id, file)

    toast.add({
      title: 'Sack detected',
      description: `Grade ${data.grade}, color ${data.sack_color}`,
      color: 'green'
    })

    await loadSummary()
    emit('updated')
  } catch (error: any) {
    toast.add({
      title: 'Error',
      description: error.message || 'Failed to scan sack',
      color: 'red'
    })
  } finally {
    scanning.value = false
  }
}
const approvePaymentLoading = ref<string | null>(null)
const isPaymentFinal = (status: string) => status !== 'pending'

const onChangePaymentStatus = async (paymentId: string, status: 'approved' | 'rejected') => {
  try {
    approvePaymentLoading.value = paymentId + status
    await approvePayment(paymentId, status)
    toast.add({
      title: 'Payment updated',
      description: `Payment has been ${status}.`,
      color: 'green'
    })
    await loadSummary()
    await loadPayments()  // <— TAMBAH BARIS INI
    emit('updated')
  } catch (error: any) {
    toast.add({
      title: 'Error',
      description: error.message || 'Failed to update payment',
      color: 'red'
    })
  } finally {
    approvePaymentLoading.value = null
  }
}
const tabs = computed(() => [
  { label: 'Summary', slot: 'summary' },
  { label: 'Payments', slot: 'payments' },
  { label: 'Harvest', slot: 'harvest' }
])
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

    <div class="flex flex-col gap-4 p-4 sm:p-6 overflow-y-auto h-full">
      <!-- Status + actions (tetap di atas tabs) -->
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

      <!-- Tabs -->
      <UTabs v-else-if="summary" :items="tabs" :ui="{ list: { background: 'bg-transparent' } }">
        <!-- Tab 1: Summary -->
        <template #summary>
          <div class="space-y-4">
            <!-- Transaction summary -->
            <UCard>
              <template #header>
                <p class="font-semibold text-sm">Transaction summary</p>
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
          </div>
        </template>

        <!-- Tab 2: Payments -->
        <template #payments>
          <UCard>
            <template #header>
              <div class="flex items-center justify-between">
                <p class="font-semibold text-sm">Payment summary</p>
                <UButton
                  size="xs"
                  color="primary"
                  variant="subtle"
                  icon="i-lucide-plus"
                  @click="addPaymentOpen = !addPaymentOpen"
                >
                  {{ addPaymentOpen ? 'Close' : 'Add payment' }}
                </UButton>
              </div>
            </template>

            <div class="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm mb-4">
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

            <div class="border-t border-default pt-3">
              <p class="text-xs text-muted mb-2">Payments</p>

              <div v-if="paymentsLoading" class="text-xs text-muted">
                Loading payments...
              </div>

              <div v-else-if="!payments.length" class="text-xs text-muted">
                No payments recorded yet.
              </div>

              <div v-else class="space-y-2 text-xs">
                <div
                  v-for="p in payments"
                  :key="p.id"
                  class="flex items-center justify-between gap-3"
                >
                  <div>
                    <p class="font-medium">
                      {{ formatCurrency(p.amount) }}
                    </p>
                    <p class="text-muted">
                      {{ p.payment_type }} • {{ p.payment_method }}
                    </p>
                  </div>

                  <div class="flex flex-col items-end gap-1">
                    <div class="flex items-center gap-2">
                      <UBadge
                        size="xs"
                        :color="p.status === 'approved' ? 'success' : p.status === 'pending' ? 'warning' : 'neutral'"
                        variant="subtle"
                        class="capitalize"
                      >
                        {{ p.status }}
                      </UBadge>
                      <p class="text-muted text-xs">
                        {{ formatDateTime(p.created_at) }}
                      </p>
                    </div>

                    <div class="flex items-center gap-2">
                      <UButton
                        size="2xs"
                        color="success"
                        variant="soft"
                        :disabled="isPaymentFinal(p.status) || approvePaymentLoading === p.id + 'approved'"
                        :loading="approvePaymentLoading === p.id + 'approved'"
                        @click="onChangePaymentStatus(p.id, 'approved')"
                      >
                        Approve
                      </UButton>
                      <UButton
                        size="2xs"
                        color="red"
                        variant="soft"
                        :disabled="isPaymentFinal(p.status) || approvePaymentLoading === p.id + 'rejected'"
                        :loading="approvePaymentLoading === p.id + 'rejected'"
                        @click="onChangePaymentStatus(p.id, 'rejected')"
                      >
                        Reject
                      </UButton>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- inline Add payment form -->
            <div v-if="addPaymentOpen" class="mt-4 border-t border-default pt-3 space-y-4">
              <p class="text-xs text-muted">Add payment</p>

              <UFormField label="Payment type">
                <USelect
                  v-model="paymentForm.payment_type"
                  :items="[
                    { label: 'Initial', value: 'initial' },
                    { label: 'Remaining', value: 'remaining' }
                  ]"
                />
              </UFormField>

              <UFormField label="Amount (IDR)">
                <UInput
                  v-model.number="paymentForm.amount"
                  type="number"
                  min="0"
                  placeholder="e.g. 1000000"
                />
              </UFormField>

              <UFormField label="Method">
                <UInput
                  v-model="paymentForm.payment_method"
                  placeholder="e.g. cash, transfer"
                />
              </UFormField>

              <UFormField label="Note (optional)">
                <UTextarea
                  v-model="paymentForm.payment_note"
                  :rows="2"
                />
              </UFormField>

              <div class="flex justify-end gap-2 pt-2">
                <UButton
                  color="gray"
                  variant="subtle"
                  type="button"
                  :disabled="addPaymentLoading"
                  @click="addPaymentOpen = false"
                >
                  Cancel
                </UButton>
                <UButton
                  color="primary"
                  :loading="addPaymentLoading"
                  @click="onAddPayment"
                >
                  Save payment
                </UButton>
              </div>
            </div>
          </UCard>
        </template>

        <!-- Tab 3: Harvest capture (test) -->
        <template #harvest>
          <UCard>
            <template #header>
              <div class="flex items-center justify-between">
                <p class="font-semibold text-sm">Harvest capture</p>
                <div class="flex items-center gap-2">
                  <UButton
                    size="xs"
                    color="neutral"
                    variant="outline"
                    :loading="cameraLoading"
                    @click="cameraOpen ? closeCamera() : openCamera()"
                  >
                    {{ cameraOpen ? 'Close camera' : 'Open camera' }}
                  </UButton>
                  <UButton
                    size="xs"
                    color="primary"
                    variant="solid"
                    icon="i-lucide-scan-line"
                    :disabled="!cameraOpen || scanning"
                    :loading="scanning"
                    @click="scanSack"
                  >
                    Scan sack
                  </UButton>
                </div>
              </div>
            </template>

            <div class="space-y-2">
              <div
                v-if="cameraOpen"
                class="relative w-full max-w-md aspect-video bg-black rounded-lg overflow-hidden"
              >
                <video
                  ref="videoEl"
                  autoplay
                  playsinline
                  muted
                  class="w-full h-full object-cover"
                />
                <div class="absolute inset-0 border-2 border-dashed border-primary/70 pointer-events-none" />
              </div>
              <p class="text-xs text-muted">
                Arahkan kamera ke karung, lalu tekan Scan sack untuk mencatat karung ke transaksi ini.
              </p>
            </div>

            <!-- Canvas hidden untuk capture frame -->
            <canvas ref="canvasEl" class="hidden" />
          </UCard>
        </template>

      </UTabs>
    </div>
  </UDashboardPanel>
</template>


