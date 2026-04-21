import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ChevronLeft, MapPin, Calendar, Trophy } from 'lucide-react'
import api from '../utils/api'
import { useAuthStore } from '../stores/authStore'
import toast from 'react-hot-toast'
import { format } from 'date-fns'

const SPORT_STATS: Record<string, { key: string; label: string }[]> = {
  cricket:    [{ key: 'runs', label: 'Runs' }, { key: 'wickets', label: 'Wickets' }, { key: 'catches', label: 'Catches' }],
  football:   [{ key: 'goals', label: 'Goals' }, { key: 'assists', label: 'Assists' }, { key: 'yellow_cards', label: 'Yellow Cards' }],
  basketball: [{ key: 'points', label: 'Points' }, { key: 'rebounds', label: 'Rebounds' }, { key: 'assists', label: 'Assists' }],
}

export default function MatchPage() {
  const { slug, matchId } = useParams()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [match, setMatch] = useState<any>(null)
  const [team, setTeam] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [resultForm, setResultForm] = useState({ home_score: '', away_score: '', result_notes: '' })
  const [showResult, setShowResult] = useState(false)

  useEffect(() => { load() }, [matchId])

  async function load() {
    setLoading(true)
    try {
      const [matchRes, teamRes] = await Promise.all([
        api.get(`/teams/${slug}/matches/${matchId}`),
        api.get(`/teams/${slug}`),
      ])
      setMatch(matchRes.data)
      setTeam(teamRes.data)
    } catch { navigate(-1) }
    setLoading(false)
  }

  async function rsvp(status: 'going' | 'not_going' | 'maybe') {
    setSubmitting(true)
    try {
      const { data } = await api.post(`/teams/${slug}/matches/${matchId}/rsvp`, { status })
      setMatch(data)
      toast.success(status === 'going' ? "Confirmed! 💪" : 'Updated')
    } catch (e: any) { toast.error(e.response?.data?.detail || 'Failed') }
    setSubmitting(false)
  }

  async function submitResult(e: React.FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    try {
      const { data } = await api.post(`/teams/${slug}/matches/${matchId}/result`, {
        home_score: parseInt(resultForm.home_score),
        away_score: parseInt(resultForm.away_score),
        result_notes: resultForm.result_notes,
      })
      setMatch(data)
      setShowResult(false)
      toast.success('Result submitted! 🏆')
    } catch (e: any) { toast.error(e.response?.data?.detail || 'Failed') }
    setSubmitting(false)
  }

  if (loading) return <div className="p-4 animate-pulse space-y-4"><div className="h-8 bg-surface-raised rounded"/><div className="h-48 bg-surface-raised rounded"/></div>

  const isCapt = team?.captain_id === user?.id
  const isCompleted = match.status === 'completed'
  const homeWon = isCompleted && match.home_score > match.away_score
  const awayWon = isCompleted && match.away_score > match.home_score

  return (
    <div className="min-h-full">
      {/* Header */}
      <div className="sticky top-0 z-40 bg-surface/90 backdrop-blur flex items-center gap-3 px-4 pt-12 pb-4 border-b border-surface-border">
        <button onClick={() => navigate(-1)} className="w-8 h-8 bg-surface-raised rounded-full flex items-center justify-center">
          <ChevronLeft size={18} className="text-white" />
        </button>
        <h1 className="font-display font-bold text-white">Match</h1>
        <span className={`ml-auto badge text-[10px] ${isCompleted ? 'bg-emerald-500/20 text-emerald-400' : 'bg-blue-500/20 text-blue-400'}`}>
          {match.status}
        </span>
      </div>

      <div className="p-4 space-y-4">
        {/* Score card */}
        <div className="card p-6">
          <div className="grid grid-cols-3 items-center gap-2">
            {/* Home */}
            <div className="text-center">
              <div className="w-14 h-14 rounded-2xl bg-brand-500/20 flex items-center justify-center text-2xl mx-auto mb-2">
                {match.sport === 'cricket' ? '🏏' : match.sport === 'football' ? '⚽' : '🏀'}
              </div>
              <p className="font-display font-bold text-white text-sm">{team?.name}</p>
              {isCompleted && (
                <p className={`font-mono font-black text-4xl mt-2 ${homeWon ? 'text-brand-500' : 'text-white/40'}`}>
                  {match.home_score}
                </p>
              )}
            </div>

            {/* VS / separator */}
            <div className="text-center">
              {isCompleted ? (
                <p className="text-white/30 font-mono text-lg">—</p>
              ) : (
                <>
                  <p className="text-white/30 font-display font-bold text-xl">VS</p>
                  <p className="text-xs text-white/30 mt-1">{format(new Date(match.scheduled_at), 'dd MMM HH:mm')}</p>
                </>
              )}
            </div>

            {/* Away */}
            <div className="text-center">
              <div className="w-14 h-14 rounded-2xl bg-surface-raised flex items-center justify-center text-2xl mx-auto mb-2">🏟️</div>
              <p className="font-display font-bold text-white text-sm">{match.opponent_name}</p>
              {isCompleted && (
                <p className={`font-mono font-black text-4xl mt-2 ${awayWon ? 'text-white' : 'text-white/40'}`}>
                  {match.away_score}
                </p>
              )}
            </div>
          </div>

          {match.result_notes && (
            <p className="text-center text-xs text-white/40 mt-4 pt-4 border-t border-surface-border">
              {match.result_notes}
            </p>
          )}
        </div>

        {/* Match details */}
        <div className="card p-4 space-y-3">
          <div className="flex items-center gap-3">
            <Calendar size={16} className="text-white/30" />
            <p className="text-sm text-white">{format(new Date(match.scheduled_at), 'EEEE dd MMMM yyyy, HH:mm')}</p>
          </div>
          <div className="flex items-center gap-3">
            <MapPin size={16} className="text-white/30" />
            <p className="text-sm text-white">{match.venue}</p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-base">{match.sport === 'cricket' ? '🏏' : match.sport === 'football' ? '⚽' : '🏀'}</span>
            <p className="text-sm text-white capitalize">{match.sport}</p>
          </div>
          {match.going_count > 0 && (
            <div className="flex items-center gap-3">
              <span className="text-sm text-white/30">👥</span>
              <p className="text-sm text-emerald-400">{match.going_count} confirmed available</p>
            </div>
          )}
        </div>

        {/* RSVP */}
        {!isCompleted && (
          <div className="card p-4">
            <h3 className="font-semibold text-white mb-3 text-sm">
              Are you available?
              {match.my_rsvp && (
                <span className={`ml-2 badge text-[10px] ${match.my_rsvp === 'going' ? 'bg-emerald-500/20 text-emerald-400' : match.my_rsvp === 'maybe' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-red-500/20 text-red-400'}`}>
                  {match.my_rsvp}
                </span>
              )}
            </h3>
            <div className="grid grid-cols-3 gap-2">
              {(['going', 'maybe', 'not_going'] as const).map(s => {
                const labels = { going: '✓ Yes', maybe: '? Maybe', not_going: '✗ No' }
                const active = match.my_rsvp === s
                const cls = s === 'going' && active ? 'bg-emerald-500 text-white' : s === 'maybe' && active ? 'bg-yellow-500 text-white' : s === 'not_going' && active ? 'bg-red-500 text-white' : 'btn-secondary'
                return (
                  <button key={s} disabled={submitting} onClick={() => rsvp(s)}
                    className={`py-3 rounded-xl text-sm font-semibold transition-all active:scale-95 ${cls}`}>
                    {labels[s]}
                  </button>
                )
              })}
            </div>
          </div>
        )}

        {/* Captain: submit result */}
        {isCapt && !isCompleted && (
          <div className="card p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-white text-sm">Submit Result</h3>
              <Trophy size={16} className="text-brand-500" />
            </div>
            {!showResult ? (
              <button onClick={() => setShowResult(true)} className="btn-primary w-full">Enter Final Score</button>
            ) : (
              <form onSubmit={submitResult} className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-white/40 mb-1 block">{team?.name}</label>
                    <input type="number" min="0" className="input text-center font-mono font-bold text-xl"
                      value={resultForm.home_score} onChange={e => setResultForm(f => ({...f, home_score: e.target.value}))} required />
                  </div>
                  <div>
                    <label className="text-xs text-white/40 mb-1 block">{match.opponent_name}</label>
                    <input type="number" min="0" className="input text-center font-mono font-bold text-xl"
                      value={resultForm.away_score} onChange={e => setResultForm(f => ({...f, away_score: e.target.value}))} required />
                  </div>
                </div>
                <input className="input text-sm" placeholder="Match notes (optional)" value={resultForm.result_notes}
                  onChange={e => setResultForm(f => ({...f, result_notes: e.target.value}))} />
                <div className="flex gap-2">
                  <button type="button" onClick={() => setShowResult(false)} className="btn-secondary flex-1">Cancel</button>
                  <button type="submit" disabled={submitting} className="btn-primary flex-1">Submit</button>
                </div>
              </form>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
