import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useNavigate } from 'react-router-dom'
import { Mail, Lock, User, Building2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { useState } from 'react'
import useAuthStore from '@/store/authStore.js'
import { registerSchema } from '@/utils/validators.js'
import { Input } from '@/components/ui/Input.jsx'
import { Button } from '@/components/ui/Button.jsx'
import { AlertBanner } from '@/components/ui/AlertBanner.jsx'

export function RegisterForm() {
  const register_ = useAuthStore((s) => s.register)
  const navigate  = useNavigate()
  const [serverError, setServerError] = useState(null)

  const { register, handleSubmit, formState:{ errors, isSubmitting } } = useForm({
    resolver: zodResolver(registerSchema),
    defaultValues: { full_name:'', organization:'', email:'', password:'', confirm:'' },
  })

  const onSubmit = async (data) => {
    setServerError(null)
    const result = await register_({ email:data.email, password:data.password, full_name:data.full_name, organization:data.organization||undefined })
    if (result.success) { toast.success('Account created — welcome!'); navigate('/dashboard', { replace:true }) }
    else setServerError(result.error)
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
      {serverError && <AlertBanner variant="error" dismissible>{serverError}</AlertBanner>}
      <div className="grid grid-cols-2 gap-3">
        <Input label="Full name" type="text" autoComplete="name" icon={User} placeholder="Jane Smith" error={errors.full_name?.message} required {...register('full_name')} />
        <Input label="Organisation" type="text" autoComplete="organization" icon={Building2} placeholder="University / Company" error={errors.organization?.message} {...register('organization')} />
      </div>
      <Input label="Email address" type="email" autoComplete="email" icon={Mail} placeholder="you@organisation.com" error={errors.email?.message} required {...register('email')} />
      <Input label="Password" type="password" autoComplete="new-password" icon={Lock} placeholder="Min 8 characters" error={errors.password?.message} required {...register('password')} />
      <Input label="Confirm password" type="password" autoComplete="new-password" icon={Lock} placeholder="Repeat password" error={errors.confirm?.message} required {...register('confirm')} />
      <p className="text-xs text-gray-500">New accounts are assigned the <em>viewer</em> role. Contact an admin for analyst access.</p>
      <Button type="submit" variant="primary" size="lg" loading={isSubmitting} className="w-full">{isSubmitting?'Creating account…':'Create account'}</Button>
    </form>
  )
}
