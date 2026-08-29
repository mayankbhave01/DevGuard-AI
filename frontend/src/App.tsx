import { Routes,Route } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'
import AuthPage from './pages/AuthPage'
import DashboardPage from './pages/DashboardPage'
import NewScanPage from './pages/NewScanPage'
import HistoryPage from './pages/HistoryPage'
import ScanDetailPage from './pages/ScanDetailPage'
export default function App(){return <Routes><Route path="/login" element={<AuthPage mode="login"/>}/><Route path="/register" element={<AuthPage mode="register"/>}/><Route element={<ProtectedRoute><Layout/></ProtectedRoute>}><Route path="/" element={<DashboardPage/>}/><Route path="/scan" element={<NewScanPage/>}/><Route path="/history" element={<HistoryPage/>}/><Route path="/scans/:id" element={<ScanDetailPage/>}/></Route></Routes>}
