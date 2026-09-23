export const roleHome = role => ({ student: '/student/profile', recruiter: '/recruiter', admin: '/admin' })[role] || '/login'
