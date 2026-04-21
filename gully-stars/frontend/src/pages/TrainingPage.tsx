import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ChevronLeft, MapPin, Clock, Calendar } from 'lucide-react'
import api from '../utils/api'
import { useAuthStore } from '../stores/authStore'
import toast from 'react-hot-toast'
import { format } from 'date-fns'

export default function TrainingPage() {
  const { slug, sessionId } = useParams()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [session, setSession] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => { load() }, [sessionId])

  async function load() {
    setLoading(true)
    try {
      const { data } = await api.get(`/teams/${slug}/training/${sessionId}`)
      setSession(data)
    } catch { navigate(-1) }
    setLoading(false)
  }

  async function rsvp(status: 'going' | 'not_going' | 'maybe') {
    setSubmitting(true)
    try {
      const { data } = await api.post(`/teams/${slug}/training/${sessionId}/rsvp`, { status })
      setSession(data)
      toast.success(status === 'going' ? "You're in! 🙌" : status === 'maybe' ? "Marked as maybe" : "Marked as not going")
    } catch (e: any) { toast.error(e.response?.data?.detail || 'Failed') }
    setSubmitting(false)
  }

  if (loading) return <div className="p-4 animate-pulse space-y-4"><div className="h-8 bg-surface-raised rounded"/><div className="h-32 bg-surface-raised rounded"/></div>

  return (
    <div className="min-h-full">
      {/* Header */}
      <div className="sticky top-0 z-40 bg-surface/90 backdrop-blur flex items-center gap-3 px-4 pt-12 pb-4 border-b border-surface-border">
        <button onClick={() => navigate(-1)} className="w-8 h-8 bg-surface-raised rounded-full flex items-center justify-center">
          <ChevronLeft size={18} className="text-white" />
        </button>
        <h1 className="font-display font-bold text-white">Training Session</h1>
      </div>

      <div className="p-4 space-y-4">
        {/* Main card */}
        <div className="card p-5">
          <div className="flex items-start justify-between mb-4">
            <h2 className="font-display font-bold text-white text-xl flex-1 pr-4">{session.title}</h2>
            {session.is_cancelled && (
              <span className="badge bg-red-500/20 text-red-400 flex-shrink-0">Cancelled</span>
            )}
          </div>

          <div className="space-y-3">
            <div className="flex items-center gap-3 text-sm">
              <div className="w-8 h-8 rounded-lg bg-brand-500/20 flex items-center justify-center flex-shrink-0">
                <Calendar size={16} className="text-brand-500" />
              </div>
              <div>
                <p className="text-white font-medium">{format(new Date(session.scheduled_at), 'EEEE, dd MMMM yyyy')}</p>
                <p className="text-white/40 text-xs">{format(new Date(session.scheduled_at), 'HH:mm')} · {session.duration_minutes} min</p>
              </div>
            </div>

            <div className="flex items-center gap-3 text-sm">
              <div className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center flex-shrink-0">
                <MapPin size={16} className="text-purple-400" />
              </div>
              <p className="text-white">{session.location}</p>
            </div>

            {session.description && (
              <p className="text-sm text-white/50 pt-1 border-t border-surface-border">{session.description}</p>
            )}
          </div>
        </div>

        {/* Attendance */}
        <div className="card p-4">
          <h3 className="font-semibold text-white mb-3 text-sm">Attendance</h3>
          <div className="grid grid-cols-3 gap-2">
            <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-3 text-center">
              <p className="font-mono font-bold text-2xl text-emerald-400">{session.going_count}</p>
              <p className="text-xs text-emerald-400/60 mt-0.5">Going</p>
            </div>
            <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-3 text-center">
              <p className="font-mono font-bold text-2xl text-yellow-400">{session.maybe_count}</p>
              <p className="text-xs text-yellow-400/60 mt-0.5">Maybe</p>
            </div>
            <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 text-center">
              <p className="font-mono font-bold text-2xl text-red-400">{session.not_going_count}</p>
              <p className="text-xs text-red-400/60 mt-0.5">Not going</p>
            </div>
          </div>
        </div>

        {/* RSVP */}
        {!session.is_cancelled && (
          <div className="card p-4">
            <h3 className="font-semibold text-white mb-3 text-sm">
              Your response
              {session.my_rsvp && (
                <span className={`ml-2 badge text-[10px] ${
                  session.my_rsvp === 'going' ? 'bg-emerald-500/20 text-emerald-400' :
                  session.my_rsvp === 'maybe' ? 'bg-yellow-500/20 text-yellow-400' :
                  'bg-red-500/20 text-red-400'
                }`}>{session.my_rsvp}</span>
              )}
            </h3>
            <div className="grid grid-cols-3 gap-2">
              {(['going', 'maybe', 'not_going'] as const).map(status => {
                const labels = { going: '✓ Going', maybe: '? Maybe', not_going: '✗ No' }
                const colors = {
                  going: session.my_rsvp === 'going' ? 'bg-emerald-500 text-white' : 'btn-secondary',
                  maybe: session.my_rsvp === 'maybe' ? 'bg-yellow-500 text-white' : 'btn-secondary',
                  not_going: session.my_rsvp === 'not_going' ? 'bg-red-500 text-white' : 'btn-secondary',
                }
                return (
                  <button
                    key={status}
                    disabled={submitting}
                    onClick={() => rsvp(status)}
                    className={`py-3 rounded-xl text-sm font-semibold transition-all active:scale-95 disabled:opacity-50 ${colors[status]}`}
                  >
                    {labels[status]}
                  </button>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
