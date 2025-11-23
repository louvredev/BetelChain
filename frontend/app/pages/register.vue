<script setup lang="ts">
definePageMeta({
  layout: 'auth'
})

const form = ref({
  name: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const loading = ref(false)
const toast = useToast()

async function onSubmit() {
  loading.value = true

  // Simulate API call
  setTimeout(() => {
    toast.add({
      title: 'Registration successful!',
      description: 'Please login to continue...',
      icon: 'i-lucide-check-circle',
      color: 'success'
    })

    // Redirect to login
    navigateTo('/login')

    loading.value = false
  }, 1000)
}
</script>

<template>
  <div class="flex-1 flex items-center justify-center p-4">
    <UCard class="w-full max-w-md">
      <template #header>
        <div class="flex items-center justify-between">
          <h2 class="text-2xl font-bold">Register</h2>
          <UButton
            to="/"
            color="neutral"
            variant="ghost"
            icon="i-lucide-home"
            label="Home"
          />
        </div>
      </template>

      <UAuthForm
        :fields="[
          {
            name: 'name',
            label: 'Full Name',
            type: 'text',
            placeholder: 'Enter your full name'
          },
          {
            name: 'email',
            label: 'Email',
            type: 'email',
            placeholder: 'Enter your email'
          },
          {
            name: 'password',
            label: 'Password',
            type: 'password',
            placeholder: 'Create a password'
          },
          {
            name: 'confirmPassword',
            label: 'Confirm Password',
            type: 'password',
            placeholder: 'Confirm your password'
          }
        ]"
        :loading="loading"
        submit-label="Create account"
        @submit="onSubmit"
      >
        <template #footer>
          <div class="text-center mt-4">
            <p class="text-sm text-muted">
              Already have an account?
              <UButton
                to="/login"
                variant="link"
                :padded="false"
                label="Sign in"
              />
            </p>
          </div>
        </template>
      </UAuthForm>
    </UCard>
  </div>
</template>