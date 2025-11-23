<script setup lang="ts">
definePageMeta({
  layout: 'auth'
})

const form = ref({
  email: '',
  password: ''
})

const loading = ref(false)
const toast = useToast()

async function onSubmit() {
  loading.value = true

  // Simulate API call
  setTimeout(() => {
    toast.add({
      title: 'Login successful!',
      description: 'Redirecting to dashboard...',
      icon: 'i-lucide-check-circle',
      color: 'success'
    })

    // Redirect to dashboard
    navigateTo('/dashboard')

    loading.value = false
  }, 1000)
}
</script>

<template>
  <div class="flex-1 flex items-center justify-center p-4">
    <UCard class="w-full max-w-md">
      <template #header>
        <div class="flex items-center justify-between">
          <h2 class="text-2xl font-bold">Login</h2>
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
            name: 'email',
            label: 'Email',
            type: 'email',
            placeholder: 'Enter your email'
          },
          {
            name: 'password',
            label: 'Password',
            type: 'password',
            placeholder: 'Enter your password'
          }
        ]"
        :loading="loading"
        submit-label="Sign in"
        @submit="onSubmit"
      >
        <template #footer>
          <div class="text-center mt-4">
            <p class="text-sm text-muted">
              Don't have an account?
              <UButton
                to="/register"
                variant="link"
                :padded="false"
                label="Sign up"
              />
            </p>
          </div>
        </template>
      </UAuthForm>
    </UCard>
  </div>
</template>