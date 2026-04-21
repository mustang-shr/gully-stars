import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'

// Pages
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import OnboardingPage from './pages/OnboardingPage'
import HomePage from './pages/HomePage'
import TeamPage from './pages/TeamPage'
import TrainingPage from './pages/TrainingPage'
import MatchPage from './pages/MatchPage'
import TournamentPage from './pages/TournamentPage'
import TournamentBracketPage from './pages/TournamentBracketPage'
import PlayerProfilePage from './pages/PlayerProfilePage'
import CreateTeamPage from './pages/CreateTeamPage'
import PublicLeaguePage from './pages/PublicLeaguePage'
import TournamentsListPage from './pages/TournamentsListPage'

// Layout
import AppLayout from './components/layout/AppLayout'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user } = useAuthStore()
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  const { hydrate } = useAuthStore()

  useEffect(() => {
    hydrate()
  }, [hydrate])

  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/onboarding" element={<OnboardingPage />} />
      <Route path="/league/:slug" element={<PublicLeaguePage />} />

      {/* Protected — inside AppLayout (bottom nav) */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<HomePage />} />
        <Route path="tournaments" element={<TournamentsListPage />} />
        <Route path="teams/new" element={<CreateTeamPage />} />
        <Route path="teams/:slug" element={<TeamPage />} />
        <Route path="teams/:slug/training/:sessionId" element={<TrainingPage />} />
        <Route path="teams/:slug/matches/:matchId" element={<MatchPage />} />
        <Route path="tournaments/:slug" element={<TournamentPage />} />
        <Route path="tournaments/:slug/bracket" element={<TournamentBracketPage />} />
        <Route path="players/:username" element={<PlayerProfilePage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
