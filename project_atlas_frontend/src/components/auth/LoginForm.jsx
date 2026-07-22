import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useNavigate, useLocation } from 'react-router-dom'
import { Mail, Lock } from 'lucide-react'
import toast from 'react-hot-toast'
import { useState } from 'react'
import useAuthStore from '@/store/authStore.js'
import { loginSchema } from '@/utils/validators.js'
import { Input } from '@/components/ui/Input.jsx'
import { Button } from '@/components/ui/Button.jsx'
import { AlertBanner } from '@/components/ui/AlertBanner.jsx'
import { supabase } from '@/config/supabase.js'

export function LoginForm() {
  const login    = useAuthStore((s) => s.login)
  const navigate = useNavigate()
  const location = useLocation()
  const from     = location.state?.from?.pathname || '/dashboard'
  const [serverError, setServerError] = useState(null)
  const [magicSent,   setMagicSent]   = useState(false)

  const { register, handleSubmit, getValues, formState:{ errors, isSubmitting } } = useForm({
    resolver: zodResolver(loginSchema),
    defaultValues: { email:'', password:'' },
  })

  const onSubmit = async (data) => {
    setServerError(null)
    const result = await login(data.email, data.password)
    if (result.success) { toast.success('Welcome back!'); navigate(from, { replace:true }) }
    else setServerError(result.error)
  }

  const handleForgotPassword = async () => {
    const email = getValues('email')
    if (!email) { toast.error('Enter your email address first'); return }
    const { error } = await supabase.auth.resetPasswordForEmail(email, { redirectTo:`${window.location.origin}/auth?reset=true` })
    if (error) toast.error(error.message); else setMagicSent(true)
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
      {serverError && <AlertBanner variant="error" dismissible>{serverError}</AlertBanner>}
      {magicSent   && <AlertBanner variant="success">Password reset link sent — check your email.</AlertBanner>}
      <Input label="Email address" type="email" autoComplete="email" icon={Mail} placeholder="you@organisation.com" error={errors.email?.message} required {...register('email')} />
      <Input label="Password" type="password" autoComplete="current-password" icon={Lock} placeholder="••••••••" error={errors.password?.message} required {...register('password')} />
      <div className="flex justify-end"><button type="button" onClick={handleForgotPassword} className="text-xs text-primary-400 hover:text-primary-300 transition-colors">Forgot password?</button></div>
      <Button type="submit" variant="primary" size="lg" loading={isSubmitting} className="w-full">{isSubmitting?'Signing in…':'Sign in'}</Button>
    </form>
  )
}
