import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { Home, Users, Trophy, Bell, User } from 'lucide-react'
import { useAuthStore } from '../../stores/authStore'

export default function AppLayout() {
  const { user } = useAuthStore()

  const navItems = [
    { to: '/',            icon: Home,   label: 'Home' },
    { to: '/tournaments', icon: Trophy, label: 'Cups' },
    { to: `/players/${user?.username}`, icon: User, label: 'Me' },
  ]

  return (
    <div className="flex flex-col h-full max-w-[390px] mx-auto relative">
      {/* Main content area */}
      <main className="flex-1 overflow-y-auto pb-20">
        <Outlet />
      </main>

      {/* Bottom navigation */}
      <nav className="fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-[390px]
                      bg-surface-card/95 backdrop-blur border-t border-surface-border
                      flex items-center justify-around px-2 py-2 z-50">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex flex-col items-center gap-0.5 px-4 py-1.5 rounded-xl transition-colors ${
                isActive ? 'text-brand-500' : 'text-white/40'
              }`
            }
          >
            <Icon size={22} strokeWidth={1.8} />
            <span className="text-[10px] font-medium">{label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
