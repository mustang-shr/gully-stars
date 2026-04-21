import { useState } from 'react'
import { formatDistanceToNow } from 'date-fns'
import { Flame, Handshake, Heart, Trophy, MessageCircle, MoreHorizontal } from 'lucide-react'
import api from '../../utils/api'
import toast from 'react-hot-toast'

const REACTIONS = [
  { type: 'fire',   emoji: '🔥', icon: Flame },
  { type: 'clap',   emoji: '👏', icon: Handshake },
  { type: 'heart',  emoji: '❤️', icon: Heart },
  { type: 'trophy', emoji: '🏆', icon: Trophy },
]

export default function FeedCard({ post, onUpdate }: { post: any; onUpdate?: () => void }) {
  const [showReactions, setShowReactions] = useState(false)
  const [comments, setComments] = useState<any[]>([])
  const [showComments, setShowComments] = useState(false)
  const [newComment, setNewComment] = useState('')
  const [loadingComments, setLoadingComments] = useState(false)

  const totalReactions = Object.values(post.reaction_counts as Record<string, number>).reduce((a, b) => a + b, 0)

  async function react(type: string) {
    try {
      await api.post(`/posts/${post.id}/react`, { reaction_type: type })
      setShowReactions(false)
      onUpdate?.()
    } catch { toast.error('Failed to react') }
  }

  async function loadComments() {
    if (showComments) { setShowComments(false); return }
    setLoadingComments(true)
    try {
      const { data } = await api.get(`/posts/${post.id}/comments/`)
      setComments(data)
      setShowComments(true)
    } catch {}
    setLoadingComments(false)
  }

  async function submitComment(e: React.FormEvent) {
    e.preventDefault()
    if (!newComment.trim()) return
    try {
      const { data } = await api.post(`/posts/${post.id}/comments/`, { content: newComment })
      setComments(c => [...c, data])
      setNewComment('')
      onUpdate?.()
    } catch { toast.error('Failed to post comment') }
  }

  return (
    <div className="card p-4">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-brand-500/20 flex items-center justify-center font-display font-bold text-brand-500 text-sm">
            {post.author.full_name[0]}
          </div>
          <div>
            <p className="font-semibold text-sm text-white">{post.author.full_name}</p>
            <p className="text-xs text-white/40">
              {formatDistanceToNow(new Date(post.created_at), { addSuffix: true })}
            </p>
          </div>
        </div>
        {post.post_type !== 'text' && (
          <span className="badge bg-surface-raised text-white/40 text-[10px]">{post.post_type}</span>
        )}
      </div>

      {/* Media */}
      {post.media_url && (
        <div className="mb-3 rounded-xl overflow-hidden bg-surface-raised">
          {post.post_type === 'photo' && (
            <img src={post.media_url} alt="Post" className="w-full object-cover max-h-72" />
          )}
          {post.post_type === 'video' && (
            <video src={post.media_url} controls className="w-full" />
          )}
        </div>
      )}

      {/* Caption */}
      {post.caption && (
        <p className="text-sm text-white/80 leading-relaxed mb-3">{post.caption}</p>
      )}

      {/* Reaction summary */}
      {totalReactions > 0 && (
        <div className="flex items-center gap-1 mb-3">
          {Object.entries(post.reaction_counts as Record<string, number>).map(([type, count]) => {
            const r = REACTIONS.find(x => x.type === type)
            return r && count > 0 ? (
              <span key={type} className="text-sm">{r.emoji}</span>
            ) : null
          })}
          <span className="text-xs text-white/40 ml-1">{totalReactions}</span>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-1 pt-2 border-t border-surface-border relative">
        {/* React button */}
        <div className="relative">
          <button
            onClick={() => setShowReactions(v => !v)}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
              post.my_reaction ? 'text-brand-500 bg-brand-500/10' : 'text-white/40 hover:bg-surface-raised'
            }`}
          >
            {post.my_reaction
              ? REACTIONS.find(r => r.type === post.my_reaction)?.emoji || '🔥'
              : '🔥'}
            React
          </button>

          {showReactions && (
            <div className="absolute bottom-full left-0 mb-2 bg-surface-card border border-surface-border
                            rounded-2xl p-2 flex gap-2 shadow-xl z-20 animate-in slide-in-from-bottom-2">
              {REACTIONS.map(r => (
                <button
                  key={r.type}
                  onClick={() => react(r.type)}
                  className="text-xl hover:scale-125 transition-transform p-1"
                  title={r.type}
                >
                  {r.emoji}
                </button>
              ))}
            </div>
          )}
        </div>

        <button
          onClick={loadComments}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium text-white/40 hover:bg-surface-raised transition-colors"
        >
          <MessageCircle size={14} />
          {post.comment_count > 0 ? post.comment_count : 'Comment'}
        </button>
      </div>

      {/* Comments */}
      {showComments && (
        <div className="mt-3 pt-3 border-t border-surface-border space-y-3">
          {loadingComments ? (
            <div className="text-xs text-white/30">Loading...</div>
          ) : comments.length === 0 ? (
            <div className="text-xs text-white/30">No comments yet</div>
          ) : (
            comments.map(c => (
              <div key={c.id} className="flex items-start gap-2">
                <div className="w-7 h-7 rounded-full bg-surface-raised flex items-center justify-center text-xs font-bold text-white/60 flex-shrink-0">
                  {c.author.full_name[0]}
                </div>
                <div className="flex-1">
                  <span className="text-xs font-semibold text-white mr-2">{c.author.full_name}</span>
                  <span className="text-xs text-white/70">{c.content}</span>
                </div>
              </div>
            ))
          )}

          <form onSubmit={submitComment} className="flex gap-2 mt-2">
            <input
              className="input text-xs py-2 flex-1"
              value={newComment}
              onChange={e => setNewComment(e.target.value)}
              placeholder="Add a comment..."
            />
            <button type="submit" className="btn-primary py-2 px-3 text-xs">Post</button>
          </form>
        </div>
      )}
    </div>
  )
}
