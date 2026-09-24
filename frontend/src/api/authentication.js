import { logIn, signUp } from './student'
import { recruiterSignup } from './recruiter'
import { validRole } from '../context/roleHome'

// Reuse existing JWT endpoints; a role selection is navigation, not authorization.
export async function authenticateAccount(role, signup, form) {
  if (!validRole(role)) throw new Error('Choose a supported role first.')
  const input = { email: form.email, password: form.password, college_id: Number(form.college_id) }
  if (!signup || role === 'admin') return logIn(input)
  return role === 'recruiter'
    ? recruiterSignup({ ...input, company: { name: form.name, industry: form.industry } })
    : signUp({ ...input, name: form.name })
}
