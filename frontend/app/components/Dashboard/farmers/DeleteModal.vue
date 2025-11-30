<script setup lang="ts">
const props = withDefaults(defineProps<{
  count?: number
  selectedIds?: string[]
}>(), {
  count: 0,
  selectedIds: () => []
})

const emit = defineEmits<{
  (e: 'deleted'): void
}>()

const open = ref(false)
const isDeleting = ref(false)

const { deleteFarmer } = useBetelchain()
const toast = useToast()

async function onSubmit () {
  if (!props.selectedIds.length) {
    open.value = false
    return
  }

  try {
    isDeleting.value = true

    for (const id of props.selectedIds) {
      await deleteFarmer(id)
    }

    toast.add({
      title: 'Success',
      description: `Deleted ${props.selectedIds.length} farmer(s)`,
      color: 'green'
    })

    emit('deleted')
    open.value = false
  } catch (error: any) {
    toast.add({
      title: 'Error',
      description: error.message || 'Failed to delete farmers',
      color: 'red'
    })
  } finally {
    isDeleting.value = false
  }
}
</script>


<template>
  <UModal
    v-model:open="open"
    :title="`Delete ${count} farmer${count > 1 ? 's' : ''}`"
    :description="`Are you sure? This action cannot be undone.`"
  >
    <!-- Trigger button dibungkus dari parent lewat slot -->
    <slot :open="() => (open = true)" />

    <template #body>
      <div class="flex justify-end gap-2">
        <UButton
          label="Cancel"
          color="neutral"
          variant="subtle"
          @click="open = false"
        />
        <UButton
          label="Delete"
          color="error"
          variant="solid"
          :loading="isDeleting"
          @click="onSubmit"
        />
      </div>
    </template>
  </UModal>
</template>
