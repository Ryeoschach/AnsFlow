import React, { useEffect, useState } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout, Spin } from 'antd'
import { useAuthStore } from '@stores/auth'
import MainLayout from '@components/layout/MainLayout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Analytics from './pages/Analytics'
import Projects from './pages/Projects'
import Pipelines from './pages/Pipelines'
import PipelineDetail from './pages/PipelineDetail'
import Tools from './pages/Tools'
import Executions from './pages/Executions'
import ExecutionDetailFixed from '@pages/ExecutionDetailFixed'
import Settings from '@pages/Settings'
import Ansible from './pages/Ansible'
import Docker from './pages/Docker'
import Debug from './pages/Debug'

const { Content } = Layout

function App() {
  const { isAuthenticated, checkAuth } = useAuthStore()
  const [isInitializing, setIsInitializing] = useState(true)

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        await checkAuth()
      } catch (error) {
        console.error('Auth initialization failed:', error)
      } finally {
        setIsInitializing(false)
      }
    }
    
    initializeAuth()
  }, [checkAuth])

  // Show loading spinner while checking auth
  if (isInitializing) {
    return (
      <Layout style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Spin size="large" tip="加载中..." />
      </Layout>
    )
  }

  if (!isAuthenticated) {
    return (
      <Layout style={{ minHeight: '100vh' }}>
        <Content>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
        </Content>
      </Layout>
    )
  }

  return (
    <MainLayout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/projects" element={<Projects />} />
        <Route path="/pipelines" element={<Pipelines />} />
        <Route path="/pipelines/:id" element={<PipelineDetail />} />
        <Route path="/tools" element={<Tools />} />
        <Route path="/executions" element={<Executions />} />
        <Route path="/executions/:id" element={<ExecutionDetailFixed />} />
        <Route path="/ansible" element={<Ansible />} />
        <Route path="/docker" element={<Docker />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/debug" element={<Debug />} />
        <Route path="/login" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </MainLayout>
  )
}

export default App
