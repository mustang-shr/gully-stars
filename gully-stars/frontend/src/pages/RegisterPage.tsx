import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore, UserRole } from '../stores/authStore'
import toast from 'react-hot-toast'

const ROLES: { value: UserRole; label: string; emoji: string; desc: string }[] = [
  { value: 'player',    label: 'Player',    emoji: '⚽', desc: 'Join a team, confirm availability, track stats' },
  { value: 'captain',   label: 'Captain',   emoji: '🏆', desc: 'Manage roster, schedule training, report scores' },
  { value: 'organiser', label: 'Organiser', emoji: '📋', desc: 'Create & run tournaments' },
  { value: 'fan',       label: 'Fan',       emoji: '📣', desc: 'Follow teams, react to game posts' },
]

export default function RegisterPage() {
  const [step, setStep] = useState(1)
  const [form, setForm] = useState({
    email: '', username: '', password: '', full_name: '',
    role: 'player' as UserRole,
  })
  const { register, isLoading } = useAuthStore()
  const navigate = useNavigate()

  function set(field: string, val: string) {
    setForm(f => ({ ...f, [field]: val }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    try {
      await register(form)
      navigate('/')
      toast.success('Welcome to Gully Stars! 🏆')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Registration failed')
    }
  }

  return (
    <div className="min-h-screen bg-surface flex flex-col items-center justify-center p-6">
      <div className="mb-6 text-center">
        <div className="text-3xl mb-1">🏆</div>
        <h1 className="font-display text-2xl font-bold text-white">Create Account</h1>
        <div className="flex items-center gap-2 justify-center mt-3">
          {[1, 2].map(s => (
            <div key={s} className={`h-1.5 w-8 rounded-full transition-colors ${s <= step ? 'bg-brand-500' : 'bg-surface-border'}`} />
          ))}
        </div>
      </div>

      <div className="w-full max-w-sm">
        {step === 1 && (
          <div className="card p-6 space-y-4">
            <h2 className="font-display font-semibold text-white">Who are you?</h2>
            <div className="space-y-2">
              {ROLES.map(r => (
                <button
                  key={r.value}
                  onClick={() => { set('role', r.value); setStep(2) }}
                  className={`w-full text-left p-4 rounded-xl border transition-all ${
                    form.role === r.value
                      ? 'border-brand-500 bg-brand-500/10'
                      : 'border-surface-border bg-surface-raised'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{r.emoji}</span>
                    <div>
                      <div className="font-semibold text-sm text-white">{r.label}</div>
                      <div className="text-xs text-white/40 mt-0.5">{r.desc}</div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {step === 2 && (
          <form onSubmit={handleSubmit} className="card p-6 space-y-4">
            <button type="button" onClick={() => setStep(1)} className="text-white/40 text-sm">← Back</button>
            <h2 className="font-display font-semibold text-white">Your details</h2>
            {[
              { field: 'full_name', label: 'Full Name', type: 'text', placeholder: 'Rohit Sharma' },
              { field: 'username',  label: 'Username',  type: 'text', placeholder: 'rohit_7' },
              { field: 'email',     label: 'Email',     type: 'email', placeholder: 'you@example.com' },
              { field: 'password',  label: 'Password',  type: 'password', placeholder: '••••••••' },
            ].map(({ field, label, type, placeholder }) => (
              <div key={field}>
                <label className="text-xs text-white/50 font-medium mb-1.5 block">{label}</label>
                <input
                  className="input"
                  type={type}
                  value={form[field as keyof typeof form]}
                  onChange={e => set(field, e.target.value)}
                  placeholder={placeholder}
                  required
                  minLength={field === 'password' ? 6 : undefined}
                />
              </div>
            ))}
            <button type="submit" disabled={isLoading} className="btn-primary w-full disabled:opacity-50">
              {isLoading ? 'Creating...' : 'Join Gully Stars 🏆'}
            </button>
          </form>
        )}

        <p className="text-center text-white/40 text-sm mt-4">
          Already have an account?{' '}
          <Link to="/login" className="text-brand-500 font-medium">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
