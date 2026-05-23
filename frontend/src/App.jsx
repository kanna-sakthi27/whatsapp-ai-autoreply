import React, { useState, useEffect, createContext, useContext } from 'react'
import { Routes, Route, useLocation } from 'react-router-dom'
import { Box } from '@mui/material'
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import StatsCards from './components/StatsCards'
import MessageList from './components/MessageList'
import SendMessage from './components/SendMessage'
import ApprovalQueue from './components/ApprovalQueue'
import AIProviderConfig from './components/AIProviderConfig'
import GuardRailsConfig from './components/GuardRailsConfig'
import GeneralSettings from './components/GeneralSettings'
import LogViewer from './components/LogViewer'
import ConnectionStatus from './components/ConnectionStatus'
import Toast from './components/Toast'
import client from './api/client'

export const AppContext = createContext()
export const useApp = () => useContext(AppContext)

function DashboardHome() {
  return (
    <>
      <Header title="Dashboard" />
      <StatsCards />
    </>
  )
}

function App() {
  const [toasts, setToasts] = useState([])
  const [stats, setStats] = useState(null)

  const addToast = (message, severity = 'info') => {
    const id = Date.now()
    setToasts((prev) => [...prev, { id, message, severity }])
    setTimeout(() => setToasts((prev) => prev.filter(t => t.id !== id)), 4000)
  }

  const fetchStats = async () => {
    try {
      const res = await client.get('/stats')
      setStats(res.data)
    } catch (err) {
      console.error('Stats fetch error:', err)
    }
  }

  useEffect(() => {
    fetchStats()
    const interval = setInterval(fetchStats, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <AppContext.Provider value={{ toasts, addToast, stats, fetchStats }}>
      <div className="app-layout">
        <Sidebar />
        <main className="app-content">
          <Routes>
            <Route path="/" element={<DashboardHome />} />
            <Route path="/messages" element={<><Header title="Messages" /><MessageList /></>} />
            <Route path="/send" element={<><Header title="Send Message" /><SendMessage /></>} />
            <Route path="/approval" element={<><Header title="Approval Queue" /><ApprovalQueue /></>} />
            <Route path="/settings/ai" element={<><Header title="AI Provider" /><AIProviderConfig /></>} />
            <Route path="/settings/guardrails" element={<><Header title="Guard Rails" /><GuardRailsConfig /></>} />
            <Route path="/settings/general" element={<><Header title="General Settings" /><GeneralSettings /></>} />
            <Route path="/logs" element={<><Header title="Log Viewer" /><LogViewer /></>} />
            <Route path="/status" element={<><Header title="Connection Status" /><ConnectionStatus /></>} />
          </Routes>
        </main>
        <Toast />
      </div>
    </AppContext.Provider>
  )
}

export default App
