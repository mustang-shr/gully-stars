import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Search, Bell } from 'lucide-react'
import api from '../utils/api'
import { useAuthStore } from '../stores/authStore'
import FeedCard from '../components/feed/FeedCard'
import TeamCard from '../components/team/TeamCard'
import { formatDistanceToNow } from 'date-fns'

export default function HomePage() {
  const { user } = useAuthStore()
  const [posts, setPosts] = useState<any[]>([])
  const [teams, setTeams] = useState<any[]>([])
  const [tab, setTab] = useState<'feed' | 'teams' | 'discover'>('feed')
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    if (tab === 'feed') loadFeed()
    if (tab === 'teams' || tab === 'discover') loadTeams()
  }, [tab])

  async function loadFeed() {
    setLoading(true)
    try {
      const { data } = await api.get('/feed/')
      setPosts(data)
    } catch {}
    setLoading(false)
  }

  async function loadTeams() {
    setLoading(true)
    try {
      const { data } = await api.get('/teams/')
      setTeams(data)
    } catch {}
    setLoading(false)
  }

  return (
    <div className="flex flex-col min-h-full">
      {/* Header */}
      <div className="sticky top-0 z-40 bg-surface/90 backdrop-blur px-4 pt-12 pb-3 border-b border-surface-border">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="font-display text-xl font-bold text-white">
              Hey, {user?.full_name.split(' ')[0]} 👋
            </h1>
            <p className="text-xs text-white/40 mt-0.5 capitalize">{user?.role}</p>
          </div>
          <div className="flex items-center gap-2">
            {(user?.role === 'captain' || user?.role === 'organiser') && (
              <button
                onClick={() => navigate('/teams/new')}
                className="w-9 h-9 bg-brand-500 rounded-xl flex items-center justify-center"
              >
                <Plus size={18} className="text-white" />
              </button>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-6">
          {(['feed', 'teams', 'discover'] as const).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`text-sm font-medium pb-2 transition-all capitalize ${
                tab === t ? 'tab-active' : 'tab-inactive'
              }`}
            >
              {t === 'teams' ? 'My Teams' : t}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 px-4 py-4 space-y-4">
        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="card p-4 space-y-3 animate-pulse">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-surface-raised" />
                  <div className="space-y-1.5 flex-1">
                    <div className="h-3 bg-surface-raised rounded w-32" />
                    <div className="h-2 bg-surface-raised rounded w-20" />
                  </div>
                </div>
                <div className="h-4 bg-surface-raised rounded w-full" />
                <div className="h-4 bg-surface-raised rounded w-3/4" />
              </div>
            ))}
          </div>
        ) : tab === 'feed' ? (
          posts.length === 0 ? (
            <EmptyFeed onDiscover={() => setTab('discover')} />
          ) : (
            posts.map(post => (
              <FeedCard key={post.id} post={post} onUpdate={loadFeed} />
            ))
          )
        ) : (
          teams.length === 0 ? (
            <div className="text-center py-16 text-white/40">
              <div className="text-4xl mb-3">🏟️</div>
              <p>No teams found</p>
            </div>
          ) : (
            teams.map(team => (
              <TeamCard key={team.id} team={team} onClick={() => navigate(`/teams/${team.slug}`)} />
            ))
          )
        )}
      </div>
    </div>
  )
}

function EmptyFeed({ onDiscover }: { onDiscover: () => void }) {
  return (
    <div className="text-center py-20">
      <div className="text-5xl mb-4">🏟️</div>
      <h3 className="font-display font-semibold text-white mb-2">Your feed is empty</h3>
      <p className="text-white/40 text-sm mb-6">Follow teams to see their posts here</p>
      <button onClick={onDiscover} className="btn-primary">Discover Teams</button>
    </div>
  )
}
