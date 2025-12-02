<script setup lang="ts">
import { z } from 'zod'
import type { FormSubmitEvent } from '@nuxt/ui'
import type { Farmer } from '~/types/betelchain'

const props = defineProps<{
  farmer: Farmer
}>()

const emit = defineEmits<{
  (e: 'updated'): void
}>()

const open = ref(false)

const schema = z.object({
  full_name: z.string().min(3, 'Minimum 3 characters'),
  phone: z.string().min(10, 'Valid phone number required'),
  bank_name: z.string().optional(),
  account_number: z.string().optional(),
  account_holder_name: z.string().optional(),
  address: z.string().optional(),
  village: z.string().optional(),
  district: z.string().optional(),
  city: z.string().optional(),
  province: z.string().optional()
})

type Schema = z.output<typeof schema>

const state = reactive<Partial<Schema>>({
  full_name: props.farmer.full_name,
  phone: props.farmer.phone,
  bank_name: props.farmer.bank_name || '',
  account_number: props.farmer.account_number || '',
  account_holder_name: props.farmer.account_holder_name || '',
  address: props.farmer.address || '',
  village: props.farmer.village || '',
  district: props.farmer.district || '',
  city: props.farmer.city || '',
  province: props.farmer.province || ''
})

const { updateFarmer } = useBetelchain()
const toast = useToast()

const isSubmitting = ref(false)

async function onSubmit (event: FormSubmitEvent<Schema>) {
  isSubmitting.value = true
  try {
    await updateFarmer(props.farmer.id, event.data as any)
    toast.add({
      title: 'Success',
      description: `Farmer ${event.data.full_name} updated successfully`,
      color: 'green'
    })
    open.value = false
    emit('updated')
  } catch (error: any) {
    toast.add({
      title: 'Error',
      description: error.message || 'Failed to update farmer',
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
    :title="`Edit Farmer: ${farmer.full_name}`"
    description="Update farmer information"
    size="lg"
  >
    <!-- Trigger button dari parent lewat slot -->
    <slot :open="() => (open = true)" />

    <template #body>
      <UForm
        :schema="schema"
        :state="state"
        class="space-y-4"
        @submit="onSubmit"
      >
        <!-- Basic Information -->
        <div>
          <h4 class="text-sm font-semibold mb-3">Basic Information</h4>
          <div class="space-y-3">
            <UFormField label="Full Name *" name="full_name">
              <UInput
                v-model="state.full_name"
                placeholder="Farmer full name"
                :disabled="isSubmitting"
              />
            </UFormField>

            <UFormField label="Phone Number *" name="phone">
              <UInput
                v-model="state.phone"
                type="tel"
                placeholder="08xx xxxx xxxx"
                :disabled="isSubmitting"
              />
            </UFormField>
          </div>
        </div>

        <!-- Bank Information -->
        <div>
          <h4 class="text-sm font-semibold mb-3">Bank Information</h4>
          <div class="space-y-3">
            <UFormField label="Bank Name" name="bank_name">
              <UInput
                v-model="state.bank_name"
                placeholder="e.g., BRI, BCA, Mandiri"
                :disabled="isSubmitting"
              />
            </UFormField>

            <UFormField label="Account Number" name="account_number">
              <UInput
                v-model="state.account_number"
                placeholder="Bank account number"
                :disabled="isSubmitting"
              />
            </UFormField>

            <UFormField label="Account Holder Name" name="account_holder_name">
              <UInput
                v-model="state.account_holder_name"
                placeholder="Name on bank account"
                :disabled="isSubmitting"
              />
            </UFormField>
          </div>
        </div>

        <!-- Address -->
        <div>
          <h4 class="text-sm font-semibold mb-3">Address</h4>
          <div class="space-y-3">
            <UFormField label="Full Address" name="address">
              <UTextarea
                v-model="state.address"
                placeholder="Street address"
                :rows="2"
                :disabled="isSubmitting"
              />
            </UFormField>

            <div class="grid grid-cols-2 gap-3">
              <UFormField label="Village" name="village">
                <UInput
                  v-model="state.village"
                  placeholder="Village name"
                  :disabled="isSubmitting"
                />
              </UFormField>

              <UFormField label="District" name="district">
                <UInput
                  v-model="state.district"
                  placeholder="District name"
                  :disabled="isSubmitting"
                />
              </UFormField>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <UFormField label="City" name="city">
                <UInput
                  v-model="state.city"
                  placeholder="City name"
                  :disabled="isSubmitting"
                />
              </UFormField>

              <UFormField label="Province" name="province">
                <UInput
                  v-model="state.province"
                  placeholder="Province name"
                  :disabled="isSubmitting"
                />
              </UFormField>
            </div>
          </div>
        </div>

        <div class="flex justify-end gap-2 pt-4">
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
            Update
          </UButton>
        </div>
      </UForm>
    </template>
  </UModal>
</template>
