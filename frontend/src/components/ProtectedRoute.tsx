import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
export default function ProtectedRoute({ children }: { children: ReactNode }) {
  return localStorage.getItem('devguard_token') ? children : <Navigate to="/login" replace />
}
