import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ChevronLeft, LogOut, MapPin, Trophy } from 'lucide-react'
import api from '../utils/api'
import { useAuthStore } from '../stores/authStore'
import { format } from 'date-fns'

const SPORT_EMOJI: Record<string, string> = { cricket: '🏏', football: '⚽', basketball: '🏀' }
const STAT_LABELS: Record<string, Record<string, string>> = {
  cricket:    { runs: 'Runs', wickets: 'Wickets', catches: 'Catches', batting_avg: 'Avg', highest_score: 'HS', economy: 'Econ' },
  football:   { goals: 'Goals', assists: 'Assists', yellow_cards: 'Yellows', shots_on_target: 'Shots' },
  basketball: { points: 'Points', rebounds: 'Reb', assists: 'Ast', steals: 'Stl', blocks: 'Blk', three_pointers: '3PT' },
}

export default function PlayerProfilePage() {
  const { username } = useParams()
  const navigate = useNavigate()
  const { user: me, logout } = useAuthStore()
  const [profile, setProfile] = useState<any>(null)
  const [stats, setStats] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  const isMe = me?.username === username

  useEffect(() => { load() }, [username])

  async function load() {
    setLoading(true)
    try {
      const { data: p } = await api.get(`/users/${username}`)
      setProfile(p)
      const { data: s } = await api.get(`/users/${p.id}/stats`)
      setStats(s)
    } catch { navigate('/') }
    setLoading(false)
  }

  if (loading) return <div className="p-4 animate-pulse space-y-4"><div className="h-32 bg-surface-raised rounded-2xl"/></div>

  const ROLE_COLORS: Record<string, string> = {
    captain: 'role-captain', player: 'role-player', organiser: 'role-organiser', fan: 'role-fan',
  }

  return (
    <div className="min-h-full">
      {/* Header */}
      <div className="sticky top-0 z-40 bg-surface/90 backdrop-blur flex items-center justify-between px-4 pt-12 pb-4 border-b border-surface-border">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate(-1)} className="w-8 h-8 bg-surface-raised rounded-full flex items-center justify-center">
            <ChevronLeft size={18} />
          </button>
          <h1 className="font-display font-bold text-white">Profile</h1>
        </div>
        {isMe && (
          <button onClick={() => { logout(); navigate('/login') }} className="text-white/40 flex items-center gap-1.5 text-xs">
            <LogOut size={14} /> Sign out
          </button>
        )}
      </div>

      <div className="p-4 space-y-4">
        {/* Profile card */}
        <div className="card p-5 text-center">
          <div className="w-20 h-20 rounded-full bg-brand-500/20 flex items-center justify-center font-display font-black text-brand-500 text-3xl mx-auto mb-3">
            {profile.full_name[0]}
          </div>
          <h2 className="font-display font-bold text-white text-xl">{profile.full_name}</h2>
          <p className="text-white/40 text-sm mt-0.5">@{profile.username}</p>

          <div className="flex items-center justify-center gap-2 mt-3 flex-wrap">
            <span className={`badge ${ROLE_COLORS[profile.role] || 'bg-surface-raised text-white/40'} capitalize`}>
              {profile.role}
            </span>
            {profile.location && (
              <span className="flex items-center gap-1 text-xs text-white/40">
                <MapPin size={11} />{profile.location}
              </span>
            )}
          </div>

          {profile.bio && (
            <p className="text-sm text-white/50 mt-3">{profile.bio}</p>
          )}

          <p className="text-xs text-white/20 mt-3">
            Joined {format(new Date(profile.created_at), 'MMMM yyyy')}
          </p>
        </div>

        {/* Stats */}
        {stats.length > 0 ? (
          <div className="space-y-3">
            <h3 className="font-display font-semibold text-white text-sm px-1">Career Stats</h3>
            {stats.map((s: any) => (
              <div key={s.id} className="card p-4">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-xl">{SPORT_EMOJI[s.sport]}</span>
                  <div>
                    <p className="font-semibold text-white text-sm">{s.team.name}</p>
                    <p className="text-xs text-white/40 capitalize">{s.sport} · {s.matches_played} matches</p>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  {Object.entries(s.stats).map(([key, val]) => (
                    <div key={key} className="bg-surface-raised rounded-xl p-3 text-center">
                      <p className="font-mono font-bold text-lg text-white">{String(val)}</p>
                      <p className="text-[10px] text-white/30 mt-0.5">{STAT_LABELS[s.sport]?.[key] || key}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-10 text-white/30">
            <Trophy size={32} className="mx-auto mb-2 opacity-30" />
            <p className="text-sm">No stats yet</p>
          </div>
        )}
      </div>
    </div>
  )
}
