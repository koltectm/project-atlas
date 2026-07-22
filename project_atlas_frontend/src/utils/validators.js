import { z } from 'zod'

export const loginSchema = z.object({
  email:    z.string().email('Invalid email address'),
  password: z.string().min(8,'Password must be at least 8 characters'),
})

export const registerSchema = z.object({
  full_name:    z.string().min(2,'Full name required').max(100),
  organization: z.string().max(100).optional(),
  email:        z.string().email('Invalid email address'),
  password:     z.string().min(8,'Password must be at least 8 characters'),
  confirm:      z.string(),
}).refine((d)=>d.password===d.confirm,{message:'Passwords do not match',path:['confirm']})

export const scenarioSchema = z.object({
  scenario_name:         z.string().min(3,'At least 3 characters').max(255),
  description:           z.string().max(2000).optional(),
  time_horizon_days:     z.number().int().min(30).max(3650),
  simulation_iterations: z.number().int().min(100).max(100_000),
  is_public:             z.boolean(),
  tags:                  z.array(z.string()).max(10).optional(),
})
