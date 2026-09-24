export const validRole = role => ['student', 'recruiter', 'admin'].includes(role) ? role : null
export const roleHome = role => validRole(role) ? ({ student: '/student', recruiter: '/recruiter', admin: '/admin' })[role] : '/auth'
export const authPath = (role, mode = 'login') => `/auth?role=${role}&mode=${role === 'admin' ? 'login' : mode}`
