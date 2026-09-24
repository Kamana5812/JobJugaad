export const portals = [
  { role: 'student', label: 'Student', name: 'Career Copilot', line: 'Know where you stand. Plan your next step.', description: 'Build your profile, understand every readiness factor, and follow your offers.', eyebrow: 'YOUR NEXT CHAPTER', tone: 'bg-warning-soft text-navy', features: ['Profile & resume', 'Explained readiness', 'Offer tracking'] },
  { role: 'recruiter', label: 'Recruiter', name: 'Talent Finder', line: 'Find the fit. See the why.', description: 'Create a drive, inspect candidate matches, and make a shortlist with a clear reason.', eyebrow: 'YOUR NEXT GREAT HIRE', tone: 'bg-growth-soft text-navy', features: ['Drive requirements', 'Explained matching', 'Human-reviewed shortlists'] },
  { role: 'admin', label: 'Admin', name: 'Placement Command Center', line: 'Keep your campus moving forward.', description: 'Coordinate interviews, review support needs, and follow placement outcomes.', eyebrow: 'YOUR CAMPUS, CONNECTED', tone: 'bg-navy text-white', features: ['Conflict-aware scheduling', 'Placement support', 'Outcome analytics'] },
]
export function PortalIcon({ role, className = 'h-7 w-7' }) {
  return <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    {role === 'student' ? <><path d="m2 9 10-5 10 5-10 5L2 9Z" /><path d="M6 11v6c4 3 8 3 12 0v-6M22 9v7" /></> : role === 'recruiter' ? <><rect x="3" y="7" width="18" height="14" rx="3" /><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M3 12c6 4 12 4 18 0M12 12v4" /></> : <><rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" /><rect x="3" y="14" width="7" height="7" rx="1.5" /><path d="m14 18 3 3 5-7" /></>}
  </svg>
}
