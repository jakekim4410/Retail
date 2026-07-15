import { useState } from 'react'
import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Sourcing from './pages/Sourcing'
import Products from './pages/Products'
import Monitoring from './pages/Monitoring'
import Settings from './pages/Settings'

const NAV_ITEMS = [
  { path: '/',           icon: '📊', label: '대시보드',      section: 'main' },
  { path: '/sourcing',   icon: '🔍', label: '소싱·마진검증',  section: 'modules' },
  { path: '/products',   icon: '📦', label: '상품관리·등록',  section: 'modules' },
  { path: '/monitoring', icon: '📈', label: '판매 모니터링', section: 'modules' },
  { path: '/settings',   icon: '⚙️', label: '설정',          section: 'system' },
]

function Sidebar() {
  const location = useLocation()

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">🛒</div>
        <div className="sidebar-logo-title">위탁판매 자동화</div>
        <div className="sidebar-logo-sub">통합 파이프라인 시스템 v2</div>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section-label">메인</div>
        {NAV_ITEMS.filter(n => n.section === 'main').map(item => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}

        <div className="nav-section-label" style={{ marginTop: 12 }}>파이프라인 모듈</div>
        {NAV_ITEMS.filter(n => n.section === 'modules').map(item => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}

        <div className="nav-section-label" style={{ marginTop: 12 }}>시스템</div>
        {NAV_ITEMS.filter(n => n.section === 'system').map(item => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 700, color: '#22c55e' }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#22c55e', display: 'inline-block', boxShadow: '0 0 6px #22c55e' }}></span>
          라이브 모드 (실제 데이터)
        </div>
      </div>
    </aside>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="layout">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/"           element={<Dashboard />} />
            <Route path="/sourcing"   element={<Sourcing />} />
            <Route path="/products"   element={<Products />} />
            <Route path="/monitoring" element={<Monitoring />} />
            <Route path="/settings"   element={<Settings />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
