import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

let supabase: ReturnType<typeof createClient> | null = null

if (supabaseUrl && supabaseAnonKey) {
supabase = createClient(supabaseUrl, supabaseAnonKey)
} else {
console.warn('Supabase env not set, supabase client is null')
}

export const useSupabase = () => {
return {
supabase
}
}