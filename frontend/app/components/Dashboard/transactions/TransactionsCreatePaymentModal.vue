<script setup lang="ts">
import { z } from 'zod'
import type { FormSubmitEvent } from '@nuxt/ui'

const props = defineProps<{
  transactionId: string
  initialAmount: number
}>()

const emit = defineEmits<{
  (e: 'created'): void
}>()

const open = ref(false)
const isSubmitting = ref(false)

const schema = z.object({
  amount: z.number().positive('Amount must be > 0'),
  payment_method: z.string().min(1, 'Payment method is required'),
  payment_note: z.string().optional()
})

type Schema = z.output<typeof schema>

const state = reactive<Partial<Schema>>({
  amount: props.initialAmount,
  payment_method: 'cash',
  payment_note: ''
})

const { createPayment } = useBetelchain()
const toast = useToast()

const onSubmit = async (event: FormSubmitEvent<Schema>) => {
  isSubmitting.value = true
  try {
    await createPayment({
      transaction_id: props.transactionId,
      amount: event.data.amount,
      payment_method: event.data.payment_method,
      payment_note: event.data.payment_note || undefined
    })

    toast.add({
      title: 'Success',
      description: 'Payment created successfully',
      color: 'green'
    })

    open.value = false
    Object.assign(state, {
      amount: props.initialAmount,
      payment_method: 'cash',
      payment_note: ''
    })

    emit('created')
  } catch (error: any) {
    toast.add({
      title: 'Error',
      description: error.message || 'Failed to create payment',
      color: 'red'
    })
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <UModal
    v-model:open="open"
    title="Create Payment"
    description="Create a payment for this transaction"
  >
    <slot :open="() => (open = true)" />

    <template #body>
      <UForm
        :schema="schema"
        :state="state"
        class="space-y-4"
        @submit="onSubmit"
      >
        <UFormField label="Amount (IDR)" name="amount">
          <UInput
            v-model.number="state.amount"
            type="number"
            min="0"
            :disabled="isSubmitting"
          />
        </UFormField>

        <UFormField label="Payment Method" name="payment_method">
          <USelect
            v-model="state.payment_method"
            :items="[
              { label: 'Cash', value: 'cash' },
              { label: 'Bank Transfer', value: 'transfer' },
              { label: 'Check', value: 'check' }
            ]"
            :disabled="isSubmitting"
          />
        </UFormField>

        <UFormField label="Note (optional)" name="payment_note">
          <UTextarea
            v-model="state.payment_note"
            :rows="2"
            :disabled="isSubmitting"
          />
        </UFormField>

        <div class="flex justify-end gap-2 pt-2">
          <UButton
            color="gray"
            variant="subtle"
            type="button"
            :disabled="isSubmitting"
            @click="open = false"
          >
            Cancel
          </UButton>
          <UButton
            type="submit"
            :loading="isSubmitting"
          >
            Create Payment
          </UButton>
        </div>
      </UForm>
    </template>
  </UModal>
</template>
