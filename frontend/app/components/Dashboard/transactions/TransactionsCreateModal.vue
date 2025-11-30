<script setup lang="ts">
import { z } from 'zod'
import type { FormSubmitEvent } from '@nuxt/ui'
import type { Farmer } from '~/types/betelchain'

const open = ref(false)
const isSubmitting = ref(false)

const schema = z.object({
  farmer_id: z.string().min(1, 'Farmer is required'),
  initial_price: z.number().positive('Initial price must be > 0')
})

type Schema = z.output<typeof schema>

const state = reactive<Partial<Schema>>({
  farmer_id: '',
  initial_price: undefined
})

const { listFarmers, createTransaction } = useBetelchain()
const toast = useToast()

const farmers = ref<Farmer[]>([])

const loadFarmers = async () => {
  try {
    farmers.value = await listFarmers()
  } catch (e) {
    toast.add({ title: 'Error', description: 'Failed to load farmers', color: 'red' })
  }
}

onMounted(loadFarmers)

const emit = defineEmits<{
  (e: 'created'): void
}>()

async function onSubmit (event: FormSubmitEvent<Schema>) {
  isSubmitting.value = true
  try {
    await createTransaction({
      farmer_id: event.data.farmer_id,
      initial_price: event.data.initial_price
    })
    toast.add({
      title: 'Success',
      description: 'Transaction created successfully',
      color: 'green'
    })
    open.value = false
    emit('created')

    Object.assign(state, {
      farmer_id: '',
      initial_price: undefined
    })
  } catch (error: any) {
    toast.add({
      title: 'Error',
      description: error.message || 'Failed to create transaction',
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
    title="New transaction"
    description="Create a new transaction with a farmer"
  >
    <!-- Trigger button -->
    <UButton
      label="New transaction"
      icon="i-lucide-plus"
      size="xs"
      @click="open = true"
    />

    <template #body>
      <UForm
        :schema="schema"
        :state="state"
        class="space-y-4"
        @submit="onSubmit"
      >
        <UFormField label="Farmer" name="farmer_id">
          <USelect
            v-model="state.farmer_id"
            :items="farmers.map(f => ({ label: `${f.farmer_code} - ${f.full_name}`, value: f.id }))"
            placeholder="Select farmer"
            :disabled="isSubmitting"
          />
        </UFormField>

        <UFormField label="Initial price (IDR)" name="initial_price">
          <UInput
            v-model.number="state.initial_price"
            type="number"
            min="0"
            placeholder="e.g. 5000000"
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
            Create
          </UButton>
        </div>
      </UForm>
    </template>
  </UModal>
</template>
