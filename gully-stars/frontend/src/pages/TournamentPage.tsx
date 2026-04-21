import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ChevronLeft, MapPin, Calendar, Users, Trophy, GitBranch } from 'lucide-react'
import api from '../utils/api'
import { useAuthStore } from '../stores/authStore'
import toast from 'react-hot-toast'
import { format } from 'date-fns'

export default function TournamentPage() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [tournament, setTournament] = useState<any>(null)
  const [standings, setStandings] = useState<any[]>([])
  const [fixtures, setFixtures] = useState<any[]>([])
  const [teams, setTeams] = useState<any[]>([])
  const [tab, setTab] = useState<'overview' | 'standings' | 'fixtures' | 'teams'>('overview')
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadTournament() }, [slug])
  useEffect(() => {
    if (!tournament) return
    if (tab === 'standings') loadStandings()
    if (tab === 'fixtures') loadFixtures()
    if (tab === 'teams') loadTeams()
  }, [tab, tournament])

  async function loadTournament() {
    setLoading(true)
    try { const { data } = await api.get(`/tournaments/${slug}`); setTournament(data) }
    catch { navigate('/') }
    setLoading(false)
  }
  async function loadStandings() {
    try { const { data } = await api.get(`/tournaments/${slug}/standings`); setStandings(data) } catch {}
  }
  async function loadFixtures() {
    try { const { data } = await api.get(`/tournaments/${slug}/fixtures`); setFixtures(data) } catch {}
  }
  async function loadTeams() {
    try { const { data } = await api.get(`/tournaments/${slug}/teams`); setTeams(data) } catch {}
  }

  async function apply() {
    try {
      await api.post(`/tournaments/${slug}/apply`)
      toast.success('Application submitted!')
      loadTeams()
    } catch (e: any) { toast.error(e.response?.data?.detail || 'Failed') }
  }

  async function generateFixtures() {
    try {
      const { data } = await api.post(`/tournaments/${slug}/generate-fixtures`)
      toast.success(`Generated ${data.fixtures?.length || 0} fixtures!`)
      loadTournament()
      setTab('fixtures')
    } catch (e: any) { toast.error(e.response?.data?.detail || 'Failed') }
  }

  if (loading) return <div className="p-4 animate-pulse space-y-3"><div className="h-32 bg-surface-raised rounded-2xl"/></div>

  const isOrganiser = tournament.organiser_id === user?.id
  const SPORT_EMOJI: Record<string, string> = { cricket: '🏏', football: '⚽', basketball: '🏀' }
  const STATUS_COLOR: Record<string, string> = {
    draft: 'bg-gray-500/20 text-gray-400',
    registration: 'bg-blue-500/20 text-blue-400',
    active: 'bg-emerald-500/20 text-emerald-400',
    completed: 'bg-purple-500/20 text-purple-400',
  }

  return (
    <div className="min-h-full">
      {/* Hero */}
      <div className="relative">
        <div className="h-36 bg-gradient-to-br from-purple-900 to-brand-800 relative">
          <button onClick={() => navigate(-1)} className="absolute top-12 left-4 w-8 h-8 bg-black/40 rounded-full flex items-center justify-center">
            <ChevronLeft size={18} className="text-white" />
          </button>
        </div>

        <div className="px-4 pb-4 bg-surface-card border-b border-surface-border">
          <div className="flex items-end -mt-8 mb-3">
            <div className="w-16 h-16 rounded-2xl bg-surface border-2 border-surface-card flex items-center justify-center text-3xl">
              {SPORT_EMOJI[tournament.sport] || '🏆'}
            </div>
            <div className="ml-auto">
              <span className={`badge ${STATUS_COLOR[tournament.status]}`}>{tournament.status}</span>
            </div>
          </div>

          <h1 className="font-display font-black text-white text-xl">{tournament.name}</h1>
          <div className="flex flex-wrap items-center gap-2 mt-1.5">
            <span className={`badge sport-${tournament.sport}`}>{tournament.sport}</span>
            <span className="badge bg-surface-raised text-white/50 text-[10px] capitalize">{tournament.format.replace('_', '-')}</span>
            {tournament.location && (
              <span className="flex items-center gap-1 text-xs text-white/40">
                <MapPin size={10} />{tournament.location}
              </span>
            )}
            <span className="flex items-center gap-1 text-xs text-white/40">
              <Users size={10} />{tournament.team_count}/{tournament.max_teams} teams
            </span>
          </div>

          {tournament.prize_info && (
            <div className="mt-3 px-3 py-2 bg-brand-500/10 border border-brand-500/20 rounded-xl">
              <p className="text-xs text-brand-400">🏆 {tournament.prize_info}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-2 mt-3">
            {tournament.status === 'registration' && user?.role === 'captain' && (
              <button onClick={apply} className="btn-primary flex-1 py-2.5 text-xs">Apply with My Team</button>
            )}
            {isOrganiser && tournament.status === 'registration' && (
              <button onClick={generateFixtures} className="btn-secondary flex-1 py-2.5 text-xs flex items-center justify-center gap-1">
                <GitBranch size={13} /> Generate Fixtures
              </button>
            )}
            <button onClick={() => navigate(`/league/${slug}`)} className="btn-secondary py-2.5 px-3 text-xs">
              Public Page
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex bg-surface-card border-b border-surface-border px-2">
          {(['overview', 'standings', 'fixtures', 'teams'] as const).map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`flex-1 py-3 text-xs font-medium capitalize transition-all ${tab === t ? 'tab-active' : 'tab-inactive'}`}>
              {t}
            </button>
          ))}
        </div>
      </div>

      <div className="p-4 space-y-3">
        {tab === 'overview' && (
          <div className="space-y-3">
            {tournament.description && (
              <div className="card p-4">
                <p className="text-sm text-white/70">{tournament.description}</p>
              </div>
            )}
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'Format', value: tournament.format.replace('_', ' '), emoji: '📋' },
                { label: 'Sport', value: tournament.sport, emoji: SPORT_EMOJI[tournament.sport] },
                { label: 'Teams', value: `${tournament.team_count}/${tournament.max_teams}`, emoji: '👥' },
                { label: 'Status', value: tournament.status, emoji: '📊' },
              ].map(({ label, value, emoji }) => (
                <div key={label} className="card p-3">
                  <span className="text-lg">{emoji}</span>
                  <p className="text-white font-semibold text-sm mt-1 capitalize">{value}</p>
                  <p className="text-white/40 text-xs">{label}</p>
                </div>
              ))}
            </div>
            {tournament.start_date && (
              <div className="card p-4 flex items-center gap-3">
                <Calendar size={18} className="text-brand-500" />
                <div>
                  <p className="text-xs text-white/40">Tournament Dates</p>
                  <p className="text-sm text-white font-medium">
                    {format(new Date(tournament.start_date), 'dd MMM')}
                    {tournament.end_date && ` — ${format(new Date(tournament.end_date), 'dd MMM yyyy')}`}
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {tab === 'standings' && (
          standings.length === 0 ? (
            <div className="text-center py-12 text-white/30">
              <Trophy size={32} className="mx-auto mb-2 opacity-30" />
              <p className="text-sm">No standings yet</p>
            </div>
          ) : (
            <StandingsTable standings={standings} />
          )
        )}

        {tab === 'fixtures' && (
          fixtures.length === 0 ? (
            <div className="text-center py-12 text-white/30">
              <p className="text-3xl mb-2">📅</p>
              <p className="text-sm">No fixtures generated yet</p>
              {isOrganiser && tournament.status === 'registration' && (
                <button onClick={generateFixtures} className="btn-primary mt-4 text-sm">Generate Fixtures</button>
              )}
            </div>
          ) : (
            <FixturesList fixtures={fixtures} />
          )
        )}

        {tab === 'teams' && (
          teams.length === 0 ? (
            <div className="text-center py-12 text-white/30">
              <p className="text-3xl mb-2">👥</p>
              <p className="text-sm">No teams applied yet</p>
            </div>
          ) : (
            teams.map((t: any) => (
              <div key={t.id} className="card p-3 flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-surface-raised flex items-center justify-center text-lg">
                  {SPORT_EMOJI[tournament.sport]}
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-sm text-white">{t.team.name}</p>
                  <p className="text-xs text-white/40">{t.team.location}</p>
                </div>
                <span className={`badge text-[10px] ${t.status === 'approved' ? 'bg-emerald-500/20 text-emerald-400' : t.status === 'pending' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-red-500/20 text-red-400'}`}>
                  {t.status}
                </span>
                {isOrganiser && t.status === 'pending' && (
                  <div className="flex gap-1">
                    <button onClick={async () => {
                      await api.put(`/tournaments/${slug}/teams/${t.team.id}/approve`, { status: 'approved' })
                      loadTeams(); toast.success('Approved!')
                    }} className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-1 rounded-lg">✓</button>
                    <button onClick={async () => {
                      await api.put(`/tournaments/${slug}/teams/${t.team.id}/approve`, { status: 'rejected' })
                      loadTeams()
                    }} className="text-xs bg-red-500/20 text-red-400 px-2 py-1 rounded-lg">✗</button>
                  </div>
                )}
              </div>
            ))
          )
        )}
      </div>
    </div>
  )
}

function StandingsTable({ standings }: { standings: any[] }) {
  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div className="grid grid-cols-[1fr_auto_auto_auto_auto] gap-x-3 px-4 py-2 text-[10px] text-white/30 font-medium uppercase bg-surface-raised">
        <span>Team</span>
        <span>P</span>
        <span>W</span>
        <span>L</span>
        <span>Pts</span>
      </div>
      {standings.map((s: any, i: number) => (
        <div key={s.team.id} className={`grid grid-cols-[1fr_auto_auto_auto_auto] gap-x-3 px-4 py-3 items-center border-t border-surface-border ${i === 0 ? 'bg-brand-500/5' : ''}`}>
          <div className="flex items-center gap-2 min-w-0">
            <span className="text-xs text-white/30 font-mono w-4">{i + 1}</span>
            <span className="font-semibold text-sm text-white truncate">{s.team.name}</span>
            {i === 0 && <span className="text-sm">🥇</span>}
          </div>
          <span className="font-mono text-xs text-white/60 text-center">{s.played}</span>
          <span className="font-mono text-xs text-emerald-400 text-center">{s.won}</span>
          <span className="font-mono text-xs text-red-400 text-center">{s.lost}</span>
          <span className="font-mono text-sm font-bold text-brand-500 text-center">{s.points}</span>
        </div>
      ))}
    </div>
  )
}

function FixturesList({ fixtures }: { fixtures: any[] }) {
  const byRound: Record<number, any[]> = {}
  for (const f of fixtures) {
    const r = f.round || 1
    if (!byRound[r]) byRound[r] = []
    byRound[r].push(f)
  }

  return (
    <div className="space-y-4">
      {Object.entries(byRound).map(([round, roundFixtures]) => (
        <div key={round}>
          <p className="text-xs font-semibold text-white/40 uppercase mb-2">Round {round}</p>
          <div className="space-y-2">
            {roundFixtures.map((f: any) => (
              <div key={f.id} className="card p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className={`badge text-[10px] ${f.status === 'completed' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-blue-500/20 text-blue-400'}`}>{f.status}</span>
                  <span className="text-xs text-white/30">{format(new Date(f.scheduled_at), 'dd MMM HH:mm')}</span>
                </div>
                <div className="flex items-center justify-between mt-1">
                  <span className="font-semibold text-sm text-white">{f.home_team}</span>
                  <span className="font-mono font-bold text-sm text-white/60 mx-2">
                    {f.status === 'completed' ? `${f.home_score} — ${f.away_score}` : 'vs'}
                  </span>
                  <span className="font-semibold text-sm text-white/60">{f.away_team}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
