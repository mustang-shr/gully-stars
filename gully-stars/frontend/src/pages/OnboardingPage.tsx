import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'

export default function OnboardingPage() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  useEffect(() => { navigate(user ? '/' : '/register') }, [user, navigate])
  return null
}
