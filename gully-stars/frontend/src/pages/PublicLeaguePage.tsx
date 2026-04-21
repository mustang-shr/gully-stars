import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { MapPin, Users, Trophy, Calendar } from 'lucide-react'
import { format } from 'date-fns'

const BASE = '/api/v1'

export default function PublicLeaguePage() {
  const { slug } = useParams()
  const [tournament, setTournament] = useState<any>(null)
  const [standings, setStandings] = useState<any[]>([])
  const [fixtures, setFixtures] = useState<any[]>([])
  const [tab, setTab] = useState<'standings' | 'fixtures'>('standings')
  const [loading, setLoading] = useState(true)

  useEffect(() => { load() }, [slug])

  async function load() {
    try {
      const [t, s, f] = await Promise.all([
        fetch(`${BASE}/tournaments/${slug}`).then(r => r.json()),
        fetch(`${BASE}/tournaments/${slug}/standings`).then(r => r.json()),
        fetch(`${BASE}/tournaments/${slug}/fixtures`).then(r => r.json()),
      ])
      setTournament(t)
      setStandings(Array.isArray(s) ? s : [])
      setFixtures(Array.isArray(f) ? f : [])
    } catch {}
    setLoading(false)
  }

  if (loading) return (
    <div className="min-h-screen bg-surface flex items-center justify-center">
      <div className="text-white/30">Loading...</div>
    </div>
  )

  if (!tournament) return (
    <div className="min-h-screen bg-surface flex items-center justify-center">
      <div className="text-white/30">Tournament not found</div>
    </div>
  )

  const SPORT_EMOJI: Record<string, string> = { cricket: '🏏', football: '⚽', basketball: '🏀' }

  return (
    <div className="min-h-screen bg-surface max-w-[390px] mx-auto">
      {/* Hero */}
      <div className="bg-gradient-to-br from-purple-900 to-brand-800 px-4 pt-12 pb-6">
        <div className="text-center">
          <div className="text-4xl mb-2">{SPORT_EMOJI[tournament.sport] || '🏆'}</div>
          <h1 className="font-display font-black text-white text-2xl">{tournament.name}</h1>
          <div className="flex items-center justify-center gap-2 mt-2 flex-wrap">
            <span className={`badge sport-${tournament.sport} text-[10px]`}>{tournament.sport}</span>
            <span className="badge bg-white/10 text-white/60 text-[10px] capitalize">{tournament.format?.replace('_', '-')}</span>
          </div>
          {tournament.location && (
            <div className="flex items-center justify-center gap-1 mt-2 text-white/50 text-xs">
              <MapPin size={11} />{tournament.location}
            </div>
          )}
          {tournament.prize_info && (
            <div className="mt-3 px-4 py-2 bg-white/10 rounded-xl inline-block">
              <p className="text-sm text-white">🏆 {tournament.prize_info}</p>
            </div>
          )}
        </div>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-3 border-b border-surface-border bg-surface-card">
        {[
          { label: 'Teams', val: `${tournament.team_count}/${tournament.max_teams}` },
          { label: 'Matches', val: fixtures.length },
          { label: 'Status', val: tournament.status },
        ].map(({ label, val }) => (
          <div key={label} className="py-3 text-center border-r border-surface-border last:border-0">
            <p className="font-semibold text-white text-sm capitalize">{val}</p>
            <p className="text-[10px] text-white/30">{label}</p>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex bg-surface-card border-b border-surface-border px-4">
        {(['standings', 'fixtures'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`flex-1 py-3 text-sm font-medium capitalize transition-all ${tab === t ? 'tab-active' : 'tab-inactive'}`}>
            {t}
          </button>
        ))}
      </div>

      <div className="p-4">
        {tab === 'standings' && (
          standings.length === 0 ? (
            <div className="text-center py-12 text-white/30"><Trophy size={32} className="mx-auto mb-2 opacity-30" /><p>No standings yet</p></div>
          ) : (
            <div className="card overflow-hidden">
              <div className="grid grid-cols-[1fr_auto_auto_auto_auto] gap-x-3 px-4 py-2 text-[10px] text-white/30 font-medium uppercase bg-surface-raised">
                <span>Team</span><span>P</span><span>W</span><span>L</span><span>Pts</span>
              </div>
              {standings.map((s: any, i: number) => (
                <div key={s.team.id} className={`grid grid-cols-[1fr_auto_auto_auto_auto] gap-x-3 px-4 py-3 items-center border-t border-surface-border ${i === 0 ? 'bg-brand-500/5' : ''}`}>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-white/30 font-mono w-4">{i+1}</span>
                    <span className="font-semibold text-sm text-white truncate">{s.team.name}</span>
                  </div>
                  <span className="font-mono text-xs text-white/60 text-center">{s.played}</span>
                  <span className="font-mono text-xs text-emerald-400 text-center">{s.won}</span>
                  <span className="font-mono text-xs text-red-400 text-center">{s.lost}</span>
                  <span className="font-mono text-sm font-bold text-brand-500 text-center">{s.points}</span>
                </div>
              ))}
            </div>
          )
        )}

        {tab === 'fixtures' && (
          fixtures.length === 0 ? (
            <div className="text-center py-12 text-white/30"><Calendar size={32} className="mx-auto mb-2 opacity-30"/><p>No fixtures yet</p></div>
          ) : (
            <div className="space-y-2">
              {fixtures.map((f: any) => (
                <div key={f.id} className="card p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className={`badge text-[10px] ${f.status === 'completed' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-blue-500/20 text-blue-400'}`}>{f.status}</span>
                    <span className="text-xs text-white/30">{format(new Date(f.scheduled_at), 'dd MMM HH:mm')}</span>
                  </div>
                  <div className="flex items-center justify-between mt-1">
                    <span className="font-semibold text-sm text-white">{f.home_team}</span>
                    <span className="font-mono font-bold text-sm text-white/50 mx-2">
                      {f.status === 'completed' ? `${f.home_score} — ${f.away_score}` : 'vs'}
                    </span>
                    <span className="font-semibold text-sm text-white/60">{f.away_team}</span>
                  </div>
                </div>
              ))}
            </div>
          )
        )}
      </div>

      <div className="text-center py-6 text-white/20 text-xs">
        Powered by <span className="text-brand-500 font-semibold">Gully Stars</span>
      </div>
    </div>
  )
}
