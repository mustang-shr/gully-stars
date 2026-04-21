import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ChevronLeft, Plus, UserPlus, Check, Bell, MapPin, Users, Calendar } from 'lucide-react'
import api from '../utils/api'
import { useAuthStore } from '../stores/authStore'
import FeedCard from '../components/feed/FeedCard'
import toast from 'react-hot-toast'
import { formatDistanceToNow, format } from 'date-fns'

const SPORT_EMOJI: Record<string, string> = { cricket: '🏏', football: '⚽', basketball: '🏀' }

export default function TeamPage() {
  const { slug } = useParams<{ slug: string }>()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [team, setTeam] = useState<any>(null)
  const [members, setMembers] = useState<any[]>([])
  const [training, setTraining] = useState<any[]>([])
  const [matches, setMatches] = useState<any[]>([])
  const [posts, setPosts] = useState<any[]>([])
  const [tab, setTab] = useState<'feed' | 'squad' | 'fixtures' | 'training'>('feed')
  const [loading, setLoading] = useState(true)
  const [following, setFollowing] = useState(false)
  const [isMember, setIsMember] = useState(false)

  useEffect(() => { loadTeam() }, [slug])
  useEffect(() => {
    if (!team) return
    if (tab === 'feed') loadPosts()
    if (tab === 'squad') loadMembers()
    if (tab === 'fixtures') loadMatches()
    if (tab === 'training') loadTraining()
  }, [tab, team])

  async function loadTeam() {
    setLoading(true)
    try {
      const { data } = await api.get(`/teams/${slug}`)
      setTeam(data)
      // Check membership
      const mem = await api.get(`/teams/${slug}/members`)
      const found = mem.data.find((m: any) => m.user.id === user?.id)
      setIsMember(!!found)
      setLoading(false)
      loadPosts()
    } catch { navigate('/') }
  }

  async function loadPosts() {
    try { const { data } = await api.get(`/teams/${slug}/posts/`); setPosts(data) } catch {}
  }
  async function loadMembers() {
    try { const { data } = await api.get(`/teams/${slug}/members`); setMembers(data) } catch {}
  }
  async function loadMatches() {
    try { const { data } = await api.get(`/teams/${slug}/matches/`); setMatches(data) } catch {}
  }
  async function loadTraining() {
    try { const { data } = await api.get(`/teams/${slug}/training/`); setTraining(data) } catch {}
  }

  async function joinTeam() {
    try {
      await api.post(`/teams/${slug}/join`)
      toast.success('Join request sent!')
      setIsMember(true)
    } catch (e: any) { toast.error(e.response?.data?.detail || 'Failed') }
  }

  async function followTeam() {
    try {
      if (following) { await api.delete(`/teams/${slug}/follow`); setFollowing(false); toast.success('Unfollowed') }
      else { await api.post(`/teams/${slug}/follow`); setFollowing(true); toast.success('Following!') }
    } catch (e: any) { toast.error(e.response?.data?.detail || 'Failed') }
  }

  const isCapt = team?.captain_id === user?.id

  if (loading) return <LoadingSkeleton />

  return (
    <div className="flex flex-col min-h-full">
      {/* Header */}
      <div className="relative">
        {/* Cover */}
        <div className="h-32 bg-gradient-to-br from-brand-800 to-brand-600 relative">
          <button onClick={() => navigate(-1)} className="absolute top-12 left-4 w-8 h-8 bg-black/40 rounded-full flex items-center justify-center">
            <ChevronLeft size={18} className="text-white" />
          </button>
        </div>

        {/* Team info */}
        <div className="px-4 pb-4 bg-surface-card border-b border-surface-border">
          <div className="flex items-end justify-between -mt-6 mb-3">
            <div className="w-16 h-16 rounded-2xl bg-surface border-2 border-surface-card flex items-center justify-center text-3xl">
              {SPORT_EMOJI[team.sport] || '🏅'}
            </div>
            <div className="flex gap-2 pb-1">
              {!isMember && user?.role !== 'fan' && (
                <button onClick={joinTeam} className="btn-primary py-2 px-3 text-xs flex items-center gap-1">
                  <UserPlus size={13} /> Join
                </button>
              )}
              <button onClick={followTeam} className={`btn-secondary py-2 px-3 text-xs flex items-center gap-1 ${following ? 'border-brand-500 text-brand-500' : ''}`}>
                <Bell size={13} /> {following ? 'Following' : 'Follow'}
              </button>
              {isCapt && (
                <button onClick={() => navigate(`/teams/${slug}/training/new`)} className="btn-secondary py-2 px-3 text-xs flex items-center gap-1">
                  <Plus size={13} /> Session
                </button>
              )}
            </div>
          </div>

          <h1 className="font-display font-bold text-white text-xl">{team.name}</h1>
          <div className="flex items-center gap-3 mt-1">
            <span className={`badge sport-${team.sport}`}>{team.sport}</span>
            {team.location && (
              <span className="flex items-center gap-1 text-xs text-white/40">
                <MapPin size={11} />{team.location}
              </span>
            )}
            <span className="flex items-center gap-1 text-xs text-white/40">
              <Users size={11} />{team.member_count} members
            </span>
          </div>
          {team.description && <p className="text-sm text-white/50 mt-2">{team.description}</p>}
        </div>

        {/* Tabs */}
        <div className="flex bg-surface-card border-b border-surface-border px-4">
          {(['feed', 'squad', 'fixtures', 'training'] as const).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`flex-1 py-3 text-xs font-medium capitalize transition-all ${tab === t ? 'tab-active' : 'tab-inactive'}`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      <div className="flex-1 p-4 space-y-3">
        {tab === 'feed' && (
          <>
            {isCapt && (
              <button onClick={() => navigate(`/teams/${slug}/post/new`)} className="btn-secondary w-full flex items-center justify-center gap-2 py-3">
                <Plus size={16} /> Create Post
              </button>
            )}
            {posts.length === 0
              ? <Empty emoji="📸" text="No posts yet" />
              : posts.map(p => <FeedCard key={p.id} post={p} onUpdate={loadPosts} />)
            }
          </>
        )}

        {tab === 'squad' && (
          <>
            {members.length === 0
              ? <Empty emoji="👥" text="No members yet" />
              : members.map(m => (
                <div key={m.id} className="card p-3 flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-brand-500/20 flex items-center justify-center font-bold text-brand-500">
                    {m.user.full_name[0]}
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold text-sm text-white">{m.user.full_name}</p>
                    <p className="text-xs text-white/40">{m.position || m.user.role}</p>
                  </div>
                  {m.jersey_number && (
                    <span className="font-mono text-sm font-bold text-white/30">#{m.jersey_number}</span>
                  )}
                  {team.captain_id === m.user.id && (
                    <span className="badge role-captain text-[10px]">Captain</span>
                  )}
                </div>
              ))
            }
          </>
        )}

        {tab === 'fixtures' && (
          <>
            {isCapt && (
              <button onClick={() => {}} className="btn-secondary w-full flex items-center justify-center gap-2 py-3">
                <Plus size={16} /> Add Match
              </button>
            )}
            {matches.length === 0
              ? <Empty emoji="⚽" text="No matches scheduled" />
              : matches.map(m => (
                <button key={m.id} onClick={() => navigate(`/teams/${slug}/matches/${m.id}`)} className="card p-4 w-full text-left active:scale-[0.98] transition-transform">
                  <div className="flex items-center justify-between mb-1">
                    <span className={`badge text-[10px] ${m.status === 'completed' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-blue-500/20 text-blue-400'}`}>
                      {m.status}
                    </span>
                    <span className="text-xs text-white/30">{format(new Date(m.scheduled_at), 'dd MMM')}</span>
                  </div>
                  <div className="flex items-center justify-between mt-2">
                    <span className="font-semibold text-sm text-white">{team.name}</span>
                    {m.status === 'completed' ? (
                      <span className="font-mono font-bold text-lg text-white">{m.home_score} — {m.away_score}</span>
                    ) : (
                      <span className="text-white/30 text-sm">vs</span>
                    )}
                    <span className="font-semibold text-sm text-white/60">{m.opponent_name}</span>
                  </div>
                  <p className="text-xs text-white/30 mt-1">{m.venue}</p>
                </button>
              ))
            }
          </>
        )}

        {tab === 'training' && (
          <>
            {isCapt && (
              <CreateTrainingModal slug={slug!} onCreated={loadTraining} />
            )}
            {training.length === 0
              ? <Empty emoji="🏃" text="No training sessions" />
              : training.map(s => (
                <button key={s.id} onClick={() => navigate(`/teams/${slug}/training/${s.id}`)} className="card p-4 w-full text-left active:scale-[0.98] transition-transform">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-sm text-white">{s.title}</h3>
                    {s.is_cancelled && <span className="badge bg-red-500/20 text-red-400 text-[10px]">Cancelled</span>}
                  </div>
                  <div className="flex items-center gap-3 text-xs text-white/40">
                    <span>📅 {format(new Date(s.scheduled_at), 'EEE dd MMM, HH:mm')}</span>
                    <span>📍 {s.location}</span>
                  </div>
                  <div className="flex gap-3 mt-2 text-xs">
                    <span className="text-emerald-400">✓ {s.going_count} going</span>
                    <span className="text-yellow-400">? {s.maybe_count} maybe</span>
                    <span className="text-red-400">✗ {s.not_going_count} no</span>
                  </div>
                </button>
              ))
            }
          </>
        )}
      </div>
    </div>
  )
}

function CreateTrainingModal({ slug, onCreated }: { slug: string; onCreated: () => void }) {
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ title: '', location: '', scheduled_at: '', duration_minutes: 90 })

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    try {
      await api.post(`/teams/${slug}/training/`, form)
      toast.success('Training session created!')
      setOpen(false)
      onCreated()
    } catch (e: any) { toast.error(e.response?.data?.detail || 'Failed') }
  }

  return (
    <>
      <button onClick={() => setOpen(true)} className="btn-primary w-full flex items-center justify-center gap-2 py-3">
        <Plus size={16} /> Schedule Training
      </button>
      {open && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-end justify-center" onClick={() => setOpen(false)}>
          <form onSubmit={submit} onClick={e => e.stopPropagation()} className="bg-surface-card rounded-t-3xl p-6 w-full max-w-[390px] space-y-4">
            <h3 className="font-display font-bold text-white text-lg">New Training Session</h3>
            <input className="input" placeholder="Session title" value={form.title} onChange={e => setForm(f => ({...f, title: e.target.value}))} required />
            <input className="input" placeholder="Location" value={form.location} onChange={e => setForm(f => ({...f, location: e.target.value}))} required />
            <input className="input" type="datetime-local" value={form.scheduled_at} onChange={e => setForm(f => ({...f, scheduled_at: e.target.value}))} required />
            <div className="flex gap-2">
              <button type="button" onClick={() => setOpen(false)} className="btn-secondary flex-1">Cancel</button>
              <button type="submit" className="btn-primary flex-1">Create</button>
            </div>
          </form>
        </div>
      )}
    </>
  )
}

function Empty({ emoji, text }: { emoji: string; text: string }) {
  return (
    <div className="text-center py-12 text-white/30">
      <div className="text-3xl mb-2">{emoji}</div>
      <p className="text-sm">{text}</p>
    </div>
  )
}

function LoadingSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="h-32 bg-surface-raised" />
      <div className="p-4 space-y-3 bg-surface-card">
        <div className="h-6 w-40 bg-surface-raised rounded" />
        <div className="h-4 w-24 bg-surface-raised rounded" />
      </div>
    </div>
  )
}
