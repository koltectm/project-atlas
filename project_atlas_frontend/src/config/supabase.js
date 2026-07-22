import { createClient } from '@supabase/supabase-js'
import { SUPABASE_URL, SUPABASE_ANON } from './constants.js'

if (!SUPABASE_URL || !SUPABASE_ANON) {
  console.error(
    '[Atlas] Missing Supabase credentials. ' +
    'Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in .env.local'
  )
}

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON, {
  auth: {
    autoRefreshToken: true,
    persistSession:   true,
    detectSessionInUrl: true,
    storage:           window.localStorage,
  },
})
