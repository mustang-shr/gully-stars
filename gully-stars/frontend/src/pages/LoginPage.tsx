import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import toast from 'react-hot-toast'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const { login, isLoading } = useAuthStore()
  const navigate = useNavigate()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    try {
      await login(email, password)
      navigate('/')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Login failed')
    }
  }

  function fillDemo(role: string) {
    const creds: Record<string, [string, string]> = {
      captain:   ['captain@gully.dev', 'gully123'],
      player:    ['player@gully.dev',  'gully123'],
      organiser: ['org@gully.dev',     'gully123'],
      fan:       ['fan@gully.dev',     'gully123'],
    }
    const [e, p] = creds[role]
    setEmail(e); setPassword(p)
  }

  return (
    <div className="min-h-screen bg-surface flex flex-col items-center justify-center p-6">
      {/* Logo */}
      <div className="mb-8 text-center">
        <div className="text-4xl mb-2">🏆</div>
        <h1 className="font-display text-3xl font-bold text-white">Gully Stars</h1>
        <p className="text-white/40 text-sm mt-1">Your grassroots sports home</p>
      </div>

      <div className="w-full max-w-sm">
        <form onSubmit={handleSubmit} className="card p-6 space-y-4">
          <div>
            <label className="text-xs text-white/50 font-medium mb-1.5 block">Email</label>
            <input
              className="input"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="captain@gully.dev"
              required
            />
          </div>
          <div>
            <label className="text-xs text-white/50 font-medium mb-1.5 block">Password</label>
            <input
              className="input"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>
          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary w-full mt-2 disabled:opacity-50"
          >
            {isLoading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        {/* Demo account quick-fill */}
        <div className="mt-4 card p-4">
          <p className="text-xs text-white/40 mb-3 font-medium">Quick demo login</p>
          <div className="grid grid-cols-2 gap-2">
            {['captain', 'player', 'organiser', 'fan'].map(role => (
              <button
                key={role}
                onClick={() => fillDemo(role)}
                className="btn-secondary text-xs py-2 capitalize"
              >
                {role}
              </button>
            ))}
          </div>
        </div>

        <p className="text-center text-white/40 text-sm mt-6">
          New here?{' '}
          <Link to="/register" className="text-brand-500 font-medium">Create account</Link>
        </p>
      </div>
    </div>
  )
}
