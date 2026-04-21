import { MapPin, Users } from 'lucide-react'

const SPORT_EMOJI: Record<string, string> = {
  cricket: '🏏', football: '⚽', basketball: '🏀',
}

export default function TeamCard({ team, onClick }: { team: any; onClick: () => void }) {
  return (
    <button onClick={onClick} className="card p-4 w-full text-left active:scale-[0.98] transition-transform">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-2xl bg-brand-500/20 flex items-center justify-center text-2xl flex-shrink-0">
          {team.logo_url ? (
            <img src={team.logo_url} className="w-full h-full object-cover rounded-2xl" alt="" />
          ) : (
            SPORT_EMOJI[team.sport] || '🏅'
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-display font-semibold text-white text-sm truncate">{team.name}</h3>
            <span className={`badge sport-${team.sport} text-[10px]`}>{team.sport}</span>
          </div>
          {team.location && (
            <div className="flex items-center gap-1 mt-0.5">
              <MapPin size={10} className="text-white/30" />
              <span className="text-xs text-white/40">{team.location}</span>
            </div>
          )}
          {team.description && (
            <p className="text-xs text-white/40 mt-1 line-clamp-1">{team.description}</p>
          )}
        </div>
        {team.member_count !== undefined && (
          <div className="flex items-center gap-1 text-white/30">
            <Users size={12} />
            <span className="text-xs">{team.member_count}</span>
          </div>
        )}
      </div>
    </button>
  )
}
