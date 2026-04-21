import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ChevronLeft } from 'lucide-react'
import api from '../utils/api'

export default function TournamentBracketPage() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const [fixtures, setFixtures] = useState<any[]>([])
  const [tournament, setTournament] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => { load() }, [slug])

  async function load() {
    try {
      const [t, f] = await Promise.all([
        api.get(`/tournaments/${slug}`),
        api.get(`/tournaments/${slug}/fixtures`),
      ])
      setTournament(t.data)
      setFixtures(f.data)
    } catch { navigate(-1) }
    setLoading(false)
  }

  if (loading) return <div className="p-4 animate-pulse"><div className="h-64 bg-surface-raised rounded-2xl"/></div>

  // Group by round
  const byRound: Record<number, any[]> = {}
  for (const f of fixtures) {
    const r = f.round || 1
    if (!byRound[r]) byRound[r] = []
    byRound[r].push(f)
  }
  const rounds = Object.keys(byRound).map(Number).sort()

  return (
    <div className="min-h-full">
      <div className="sticky top-0 z-40 bg-surface/90 backdrop-blur flex items-center gap-3 px-4 pt-12 pb-4 border-b border-surface-border">
        <button onClick={() => navigate(-1)} className="w-8 h-8 bg-surface-raised rounded-full flex items-center justify-center">
          <ChevronLeft size={18} />
        </button>
        <div>
          <h1 className="font-display font-bold text-white">{tournament?.name}</h1>
          <p className="text-xs text-white/40 capitalize">{tournament?.format?.replace('_', '-')} Bracket</p>
        </div>
      </div>

      <div className="p-4">
        {rounds.length === 0 ? (
          <div className="text-center py-20 text-white/30">
            <p className="text-4xl mb-3">🏟️</p>
            <p>No fixtures yet</p>
          </div>
        ) : tournament?.format === 'bracket' ? (
          // Visual bracket for elimination
          <div className="overflow-x-auto">
            <div className="flex gap-4 min-w-max pb-4">
              {rounds.map(round => (
                <div key={round} className="flex flex-col justify-around gap-4" style={{ minWidth: 160 }}>
                  <p className="text-xs font-semibold text-white/40 uppercase text-center mb-2">
                    {round === rounds[rounds.length - 1] ? 'Final' : round === rounds[rounds.length - 2] ? 'Semi-Final' : `Round ${round}`}
                  </p>
                  {byRound[round].map((f: any) => (
                    <BracketMatch key={f.id} fixture={f} />
                  ))}
                </div>
              ))}
            </div>
          </div>
        ) : (
          // Round-robin: show as table
          <div className="space-y-3">
            {rounds.map(round => (
              <div key={round}>
                <p className="text-xs font-semibold text-white/40 uppercase mb-2">Matchday {round}</p>
                {byRound[round].map((f: any) => (
                  <BracketMatch key={f.id} fixture={f} />
                ))}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function BracketMatch({ fixture: f }: { fixture: any }) {
  const isComplete = f.status === 'completed'
  const homeWon = isComplete && f.home_score > f.away_score
  const awayWon = isComplete && f.away_score > f.home_score

  return (
    <div className="card overflow-hidden">
      <div className={`px-3 py-2 flex items-center justify-between ${homeWon ? 'bg-brand-500/10' : ''}`}>
        <span className={`text-sm font-semibold ${homeWon ? 'text-white' : 'text-white/60'}`}>{f.home_team}</span>
        <span className={`font-mono font-bold text-sm ${homeWon ? 'text-brand-500' : 'text-white/30'}`}>
          {isComplete ? f.home_score : '—'}
        </span>
      </div>
      <div className="h-px bg-surface-border" />
      <div className={`px-3 py-2 flex items-center justify-between ${awayWon ? 'bg-brand-500/10' : ''}`}>
        <span className={`text-sm font-semibold ${awayWon ? 'text-white' : 'text-white/60'}`}>{f.away_team}</span>
        <span className={`font-mono font-bold text-sm ${awayWon ? 'text-brand-500' : 'text-white/30'}`}>
          {isComplete ? f.away_score : '—'}
        </span>
      </div>
    </div>
  )
}
