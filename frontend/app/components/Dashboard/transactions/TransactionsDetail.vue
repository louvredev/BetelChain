<script setup lang="ts">
import { format } from 'date-fns'
import type { Transaction, Payment } from '~/types/betelchain'

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
  getPaymentByTransaction,
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

const payment = ref<Payment | null>(null)
const paymentLoading = ref(false)

const formatDateTime = (d?: string | null) => {
  if (!d) return '-'
  const date = new Date(d)
  // Format dengan timezone GMT+7 (Jakarta)
  return date.toLocaleString('id-ID', { 
    timeZone: 'Asia/Jakarta',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
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

const loadPayment = async () => {
  if (!props.transaction?.id) return
  try {
    paymentLoading.value = true
    const paymentData = await getPaymentByTransaction(props.transaction.id)
    payment.value = paymentData
  } catch (error: any) {
    toast.add({
      title: 'Error',
      description: error.message || 'Failed to load payment',
      color: 'red'
    })
  } finally {
    paymentLoading.value = false
  }
}

const loadSummary = async () => {
  if (!props.transaction?.id) return
  try {
    loading.value = !summary.value
    refreshing.value = !!summary.value
    const data = await getTransactionSummary(props.transaction.id)
    summary.value = data
    await loadPayment()
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

watch(
  () => props.transaction.id,
  () => {
    summary.value = null
    payment.value = null
    loadSummary()
  },
  { immediate: true }
)

const onStartRecording = async () => {
  if (!props.transaction.id) return
  try {
    actionLoading.value = 'start'

    // 1) Start recording di backend
    await startRecording(props.transaction.id)

    // 2) Buka kamera setelah recording berhasil
    await openCamera()

    toast.add({
      title: 'Recording started',
      description: 'Recording has started and camera is open.',
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

    // 1) Tutup kamera dulu
    closeCamera()

    // 2) Tandai recording selesai di backend
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


const recordingStarted = computed(() => !!summary.value?.transaction?.recording_started_at)
const recordingCompleted = computed(() => !!summary.value?.transaction?.recording_completed_at)


const createPaymentModalOpen = ref(false)

const onPaymentCreated = async () => {
  createPaymentModalOpen.value = false
  await loadPayment()
  await loadSummary()
  emit('updated')
}

const approvePaymentLoading = ref(false)

const onApprovePayment = async () => {
  if (!payment.value?.id) return
  try {
    approvePaymentLoading.value = true
    await approvePayment(payment.value.id, 'approved')

    toast.add({
      title: 'Payment approved',
      description: 'Payment has been approved successfully.',
      color: 'green'
    })

    await loadPayment()
    await loadSummary()

    // Emit updated transaction dengan payment_status terbaru
    if (summary.value?.transaction) {
      emit('updated', {
        ...props.transaction,
        payment_status: summary.value.transaction.payment_status || 'unpaid'
      } as Transaction)
    }
  } catch (error: any) {
    toast.add({
      title: 'Error',
      description: error.message || 'Failed to approve payment',
      color: 'red'
    })
  } finally {
    approvePaymentLoading.value = false
  }
}




// Camera & harvest
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

const tabs = computed(() => [
  { label: 'Summary', slot: 'summary' },
  { label: 'Payment', slot: 'payment' },
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
      </template>
    </UDashboardNavbar>

    <div class="flex flex-col gap-4 p-4 sm:p-6 overflow-y-auto h-full">
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
                  <p class="text-muted text-xs">Price per sack</p>
                  <p class="font-medium">
                    {{
                      summary.harvest_summary.total_records > 0
                        ? formatCurrency(
                            summary.transaction.initial_price / summary.harvest_summary.total_records
                          )
                        : '-'
                    }}
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

        <!-- Tab 2: Payment -->
        <template #payment>
          <UCard>
            <template #header>
              <div class="flex items-center justify-between">
                <p class="font-semibold text-sm">Payment</p>
              </div>
            </template>

            <div v-if="paymentLoading" class="text-sm text-muted">
              Loading payment...
            </div>

            <!-- No payment yet -->
            <div v-else-if="!payment" class="space-y-3">
              <p class="text-sm text-muted">
                No payment created yet for this transaction.
              </p>
              <DashboardTransactionsCreatePaymentModal
                :transaction-id="transaction.id"
                :initial-amount="summary?.transaction?.total_price || summary?.transaction?.initial_price || 0"
                @created="onPaymentCreated"
              >
                <template #default="{ open }">
                  <UButton
                    color="primary"
                    size="sm"
                    @click="open"
                  >
                    Create Payment
                  </UButton>
                </template>
              </DashboardTransactionsCreatePaymentModal>
            </div>

            <!-- No payment yet -->
            <div v-else-if="!payment" class="space-y-3">
              <p class="text-sm text-muted">
                No payment created yet for this transaction.
              </p>
              <DashboardTransactionsCreatePaymentModal
                :transaction-id="transaction.id"
                :initial-amount="summary?.transaction?.total_price || summary?.transaction?.initial_price || 0"
                @created="onPaymentCreated"
              >
                <template #default="{ open }">
                  <UButton
                    color="primary"
                    size="sm"
                    @click="open"
                  >
                    Create Payment
                  </UButton>
                </template>
              </DashboardTransactionsCreatePaymentModal>
            </div>

            <!-- Payment exists -->
            <div v-else class="space-y-4">
              <div class="grid gap-3 text-sm">
                <div>
                  <p class="text-muted text-xs">Amount</p>
                  <p class="font-medium">
                    {{ formatCurrency(payment.amount) }}
                  </p>
                </div>
                <div>
                  <p class="text-muted text-xs">Method</p>
                  <p class="font-medium capitalize">
                    {{ payment.payment_method }}
                  </p>
                </div>
                <div>
                  <p class="text-muted text-xs">Status</p>
                  <div class="flex items-center gap-2">
                    <UBadge
                      size="sm"
                      :color="payment.status === 'approved' ? 'success' : 'warning'"
                      variant="subtle"
                      class="capitalize"
                    >
                      {{ payment.status }}
                    </UBadge>
                  </div>
                </div>
                <div v-if="payment.payment_note">
                  <p class="text-muted text-xs">Note</p>
                  <p class="text-sm">{{ payment.payment_note }}</p>
                </div>
                <div>
                  <p class="text-muted text-xs">Created at</p>
                  <p class="text-xs">
                    {{ formatDateTime(payment.created_at) }}
                  </p>
                </div>
              </div>

              <!-- Approve button (hanya jika pending) -->
              <div v-if="payment.status === 'pending'" class="border-t border-default pt-3">
                <UButton
                  color="success"
                  size="sm"
                  class="w-full"
                  :loading="approvePaymentLoading"
                  @click="onApprovePayment"
                >
                  Approve Payment
                </UButton>
              </div>
            </div>
          </UCard>
        </template>
       

        <!-- Tab 3: Harvest -->
        <template #harvest>
          <UCard>
            <template #header>
              <div class="flex items-center justify-between">
                <p class="font-semibold text-sm">Harvest capture</p>
                <div class="flex items-center gap-2">
                  <UButton
                    v-if="!recordingStarted"
                    size="xs"
                    color="primary"
                    variant="subtle"
                    icon="i-lucide-play-circle"
                    :loading="actionLoading === 'start'"
                    @click="onStartRecording"
                  >
                    Start recording
                  </UButton>

                  <UButton
                    v-else-if="!recordingCompleted"
                    size="xs"
                    color="primary"
                    variant="solid"
                    icon="i-lucide-check-circle"
                    :loading="actionLoading === 'complete'"
                    @click="onCompleteRecording"
                  >
                    Complete recording
                  </UButton>

                  <UButton
                    v-else
                    size="xs"
                    color="gray"
                    variant="soft"
                    icon="i-lucide-check"
                    disabled
                  >
                    Recording completed
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

            <canvas ref="canvasEl" class="hidden" />
          </UCard>
        </template>
      </UTabs>
    </div>
  </UDashboardPanel>
</template>
