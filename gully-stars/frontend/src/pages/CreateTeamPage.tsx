import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronLeft } from 'lucide-react'
import api from '../utils/api'
import toast from 'react-hot-toast'

const SPORTS = [
  { value: 'cricket',    label: 'Cricket',    emoji: '🏏' },
  { value: 'football',   label: 'Football',   emoji: '⚽' },
  { value: 'basketball', label: 'Basketball', emoji: '🏀' },
]

export default function CreateTeamPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    name: '', sport: 'cricket', description: '', location: '', visibility: 'public',
  })
  const [loading, setLoading] = useState(false)

  function set(k: string, v: string) { setForm(f => ({...f, [k]: v})) }

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await api.post('/teams/', form)
      toast.success(`${data.name} created! 🏆`)
      navigate(`/teams/${data.slug}`)
    } catch (e: any) { toast.error(e.response?.data?.detail || 'Failed') }
    setLoading(false)
  }

  return (
    <div className="min-h-full">
      <div className="sticky top-0 z-40 bg-surface/90 backdrop-blur flex items-center gap-3 px-4 pt-12 pb-4 border-b border-surface-border">
        <button onClick={() => navigate(-1)} className="w-8 h-8 bg-surface-raised rounded-full flex items-center justify-center">
          <ChevronLeft size={18} />
        </button>
        <h1 className="font-display font-bold text-white">Create Team</h1>
      </div>

      <form onSubmit={submit} className="p-4 space-y-4">
        {/* Sport */}
        <div>
          <label className="text-xs text-white/50 font-medium mb-2 block">Sport</label>
          <div className="grid grid-cols-3 gap-2">
            {SPORTS.map(s => (
              <button key={s.value} type="button" onClick={() => set('sport', s.value)}
                className={`p-3 rounded-xl border flex flex-col items-center gap-1 transition-all ${form.sport === s.value ? 'border-brand-500 bg-brand-500/10' : 'border-surface-border bg-surface-raised'}`}>
                <span className="text-2xl">{s.emoji}</span>
                <span className="text-xs font-medium text-white">{s.label}</span>
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="text-xs text-white/50 font-medium mb-1.5 block">Team Name</label>
          <input className="input" placeholder="Gully Tigers" value={form.name} onChange={e => set('name', e.target.value)} required />
        </div>

        <div>
          <label className="text-xs text-white/50 font-medium mb-1.5 block">Location</label>
          <input className="input" placeholder="Mumbai" value={form.location} onChange={e => set('location', e.target.value)} />
        </div>

        <div>
          <label className="text-xs text-white/50 font-medium mb-1.5 block">Description</label>
          <textarea className="input resize-none" rows={3} placeholder="Tell us about your team..."
            value={form.description} onChange={e => set('description', e.target.value)} />
        </div>

        <div>
          <label className="text-xs text-white/50 font-medium mb-2 block">Visibility</label>
          <div className="grid grid-cols-2 gap-2">
            {[
              { value: 'public', label: '🌐 Public', desc: 'Anyone can join' },
              { value: 'invite_only', label: '🔒 Invite Only', desc: 'Captain approves' },
            ].map(v => (
              <button key={v.value} type="button" onClick={() => set('visibility', v.value)}
                className={`p-3 rounded-xl border text-left transition-all ${form.visibility === v.value ? 'border-brand-500 bg-brand-500/10' : 'border-surface-border bg-surface-raised'}`}>
                <p className="text-sm font-semibold text-white">{v.label}</p>
                <p className="text-xs text-white/40 mt-0.5">{v.desc}</p>
              </button>
            ))}
          </div>
        </div>

        <button type="submit" disabled={loading} className="btn-primary w-full py-4 text-base disabled:opacity-50">
          {loading ? 'Creating...' : 'Create Team 🏆'}
        </button>
      </form>
    </div>
  )
}
