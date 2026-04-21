import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Trophy, MapPin, Users, Calendar } from 'lucide-react'
import api from '../utils/api'
import { useAuthStore } from '../stores/authStore'
import toast from 'react-hot-toast'
import { format } from 'date-fns'
import CreateTournamentModal from '../components/tournament/CreateTournamentModal'

const SPORT_EMOJI: Record<string, string> = { cricket: '🏏', football: '⚽', basketball: '🏀' }
const STATUS_COLOR: Record<string, string> = {
  draft: 'bg-gray-500/20 text-gray-400',
  registration: 'bg-blue-500/20 text-blue-400',
  active: 'bg-emerald-500/20 text-emerald-400',
  completed: 'bg-purple-500/20 text-purple-400',
}

export default function TournamentsListPage() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [tournaments, setTournaments] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)

  useEffect(() => { load() }, [])

  async function load() {
    setLoading(true)
    try { const { data } = await api.get('/tournaments/'); setTournaments(data) }
    catch {}
    setLoading(false)
  }

  return (
    <div className="flex flex-col min-h-full">
      <div className="sticky top-0 z-40 bg-surface/90 backdrop-blur px-4 pt-12 pb-4 border-b border-surface-border">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-display text-xl font-bold text-white">Tournaments</h1>
            <p className="text-xs text-white/40 mt-0.5">Cups & leagues near you</p>
          </div>
          {user?.role === 'organiser' && (
            <button onClick={() => setShowCreate(true)} className="w-9 h-9 bg-brand-500 rounded-xl flex items-center justify-center">
              <Plus size={18} className="text-white" />
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 p-4 space-y-3">
        {loading ? (
          [1,2,3].map(i => (
            <div key={i} className="card p-4 animate-pulse space-y-2">
              <div className="h-5 bg-surface-raised rounded w-2/3"/>
              <div className="h-4 bg-surface-raised rounded w-1/2"/>
            </div>
          ))
        ) : tournaments.length === 0 ? (
          <div className="text-center py-20 text-white/30">
            <Trophy size={40} className="mx-auto mb-3 opacity-30"/>
            <p>No tournaments yet</p>
            {user?.role === 'organiser' && (
              <button onClick={() => setShowCreate(true)} className="btn-primary mt-4">Create Tournament</button>
            )}
          </div>
        ) : (
          tournaments.map(t => (
            <button key={t.id} onClick={() => navigate(`/tournaments/${t.slug}`)}
              className="card p-4 w-full text-left active:scale-[0.98] transition-transform">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{SPORT_EMOJI[t.sport] || '🏆'}</span>
                  <div>
                    <h3 className="font-display font-bold text-white text-sm">{t.name}</h3>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className={`badge sport-${t.sport} text-[10px]`}>{t.sport}</span>
                      <span className="badge bg-surface-raised text-white/40 text-[10px] capitalize">{t.format?.replace('_','-')}</span>
                    </div>
                  </div>
                </div>
                <span className={`badge text-[10px] ${STATUS_COLOR[t.status] || ''}`}>{t.status}</span>
              </div>
              <div className="flex items-center gap-3 text-xs text-white/30">
                {t.location && <span className="flex items-center gap-1"><MapPin size={10}/>{t.location}</span>}
                <span className="flex items-center gap-1"><Users size={10}/>{t.team_count}/{t.max_teams}</span>
                {t.start_date && <span className="flex items-center gap-1"><Calendar size={10}/>{format(new Date(t.start_date), 'dd MMM')}</span>}
              </div>
              {t.prize_info && <p className="text-xs text-brand-400 mt-1.5">🏆 {t.prize_info}</p>}
            </button>
          ))
        )}
      </div>

      {showCreate && <CreateTournamentModal onClose={() => setShowCreate(false)} onCreated={() => { setShowCreate(false); load() }} />}
    </div>
  )
}
