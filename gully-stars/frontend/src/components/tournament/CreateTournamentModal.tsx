import { useState } from 'react'
import api from '../../utils/api'
import toast from 'react-hot-toast'

export default function CreateTournamentModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState({
    name: '', sport: 'cricket', format: 'round_robin',
    description: '', location: '', max_teams: 8,
    prize_info: '', start_date: '', end_date: '',
  })
  const [loading, setLoading] = useState(false)
  function set(k: string, v: any) { setForm(f => ({...f, [k]: v})) }

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post('/tournaments/', {
        ...form,
        start_date: form.start_date || undefined,
        end_date: form.end_date || undefined,
      })
      toast.success('Tournament created!')
      onCreated()
    } catch (e: any) { toast.error(e.response?.data?.detail || 'Failed') }
    setLoading(false)
  }

  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-end justify-center" onClick={onClose}>
      <form onSubmit={submit} onClick={e => e.stopPropagation()}
        className="bg-surface-card rounded-t-3xl p-6 w-full max-w-[390px] space-y-4 max-h-[90vh] overflow-y-auto">
        <h3 className="font-display font-bold text-white text-xl">New Tournament</h3>

        <input className="input" placeholder="Tournament name" value={form.name} onChange={e => set('name', e.target.value)} required/>

        <div className="grid grid-cols-3 gap-2">
          {['cricket','football','basketball'].map(s => (
            <button key={s} type="button" onClick={() => set('sport', s)}
              className={`py-2 rounded-xl text-xs font-medium border transition-all capitalize ${form.sport === s ? 'border-brand-500 bg-brand-500/10 text-brand-500' : 'border-surface-border text-white/40'}`}>
              {s === 'cricket' ? '🏏' : s === 'football' ? '⚽' : '🏀'} {s}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-2">
          {[{v:'round_robin',l:'Round Robin'},{v:'bracket',l:'Bracket'}].map(f => (
            <button key={f.v} type="button" onClick={() => set('format', f.v)}
              className={`py-2 rounded-xl text-xs font-medium border transition-all ${form.format === f.v ? 'border-brand-500 bg-brand-500/10 text-brand-500' : 'border-surface-border text-white/40'}`}>
              {f.l}
            </button>
          ))}
        </div>

        <input className="input" placeholder="Location" value={form.location} onChange={e => set('location', e.target.value)}/>
        <input className="input" type="number" placeholder="Max teams (e.g. 8)" min="2" max="64"
          value={form.max_teams} onChange={e => set('max_teams', parseInt(e.target.value))}/>
        <input className="input" placeholder="Prize info (optional)" value={form.prize_info} onChange={e => set('prize_info', e.target.value)}/>

        <div className="grid grid-cols-2 gap-2">
          <div><label className="text-xs text-white/40 mb-1 block">Start Date</label>
            <input className="input text-sm" type="date" value={form.start_date} onChange={e => set('start_date', e.target.value)}/></div>
          <div><label className="text-xs text-white/40 mb-1 block">End Date</label>
            <input className="input text-sm" type="date" value={form.end_date} onChange={e => set('end_date', e.target.value)}/></div>
        </div>

        <textarea className="input resize-none" rows={2} placeholder="Description (optional)"
          value={form.description} onChange={e => set('description', e.target.value)}/>

        <div className="flex gap-2">
          <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
          <button type="submit" disabled={loading} className="btn-primary flex-1 disabled:opacity-50">
            {loading ? 'Creating...' : 'Create'}
          </button>
        </div>
      </form>
    </div>
  )
}
