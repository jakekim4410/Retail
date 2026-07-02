import { useState, useEffect } from 'react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar
} from 'recharts'

const API = ''  // Vite proxy

function useFetch(url) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(url)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [url])

  return { data, loading, error }
}

function KpiCard({ label, value, sub, icon, type = 'primary' }) {
  return (
    <div className={`kpi-card ${type} fade-in`}>
      <div className="kpi-icon">{icon}</div>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
      {sub && <div className="kpi-sub">{sub}</div>}
    </div>
  )
}

function PipelineViz({ counts }) {
  const steps = [
    { icon: '🔍', label: '소싱', count: counts.sourced || 0 },
    { icon: '💰', label: '마진검증', count: (counts.sourced || 0) + (counts.filtered || 0) },
    { icon: '📝', label: '상세페이지', count: counts.page_generated || 0 },
    { icon: '⏳', label: '검수대기', count: counts.pending_review || 0 },
    { icon: '✅', label: '등록완료', count: counts.registered || 0 },
    { icon: '🛒', label: '판매중', count: counts.on_sale || 0 },
  ]
  return (
    <div className="pipeline">
      {steps.map((step, i) => (
        <>
          <div className="pipeline-step" key={step.label}>
            <div className={`pipeline-icon ${step.count > 0 ? 'active' : ''}`}>
              {step.icon}
            </div>
            <div className="pipeline-count">{step.count}</div>
            <div className="pipeline-label">{step.label}</div>
          </div>
          {i < steps.length - 1 && (
            <div className="pipeline-arrow" key={`arrow-${i}`}>→</div>
          )}
        </>
      ))}
    </div>
  )
}

const TOOLTIP_STYLE = {
  backgroundColor: '#141629',
  border: '1px solid rgba(99,102,241,0.3)',
  borderRadius: 8,
  color: '#f0f2ff',
  fontSize: 12,
}

export default function Dashboard() {
  const { data: summary, loading: loadingSum } = useFetch('/api/monitoring/dashboard')
  const { data: trend, loading: loadingTrend } = useFetch('/api/monitoring/trend?days=30')

  const fmt = n => (n || 0).toLocaleString('ko-KR') + '원'
  const counts = summary?.product_status_counts || {}

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">📊 통합 대시보드</h1>
        <p className="page-subtitle">소싱부터 판매까지 전체 파이프라인 현황</p>
      </div>
      <div className="page-body">

        {/* 파이프라인 시각화 */}
        <PipelineViz counts={counts} />

        {/* KPI 카드 */}
        {loadingSum ? (
          <div className="loading-overlay"><div className="spinner" />KPI 로딩 중...</div>
        ) : (
          <div className="kpi-grid mb-24">
            <KpiCard
              label="이번달 매출"
              value={fmt(summary?.monthly_revenue)}
              sub={`주문 ${summary?.monthly_orders || 0}건`}
              icon="💳"
              type="primary"
            />
            <KpiCard
              label="이번달 순이익"
              value={fmt(summary?.monthly_net_profit)}
              sub={`순마진율 ${summary?.net_margin_rate || 0}%`}
              icon="📈"
              type="success"
            />
            <KpiCard
              label="누적 총 매출"
              value={fmt(summary?.total_revenue)}
              sub={`총 주문 ${summary?.total_orders || 0}건`}
              icon="🏆"
              type="primary"
            />
            <KpiCard
              label="하차 후보"
              value={summary?.delist_candidate_count || 0}
              sub="14일 이상 판매 0건"
              icon="⚠️"
              type="danger"
            />
            <KpiCard
              label="가격 조정 필요"
              value={summary?.price_adjust_count || 0}
              sub="마진율 기준 미달"
              icon="💰"
              type="warning"
            />
            <KpiCard
              label="판매 중 상품"
              value={counts.on_sale || 0}
              sub={`등록완료: ${counts.registered || 0}건`}
              icon="🛒"
              type="success"
            />
          </div>
        )}

        {/* 매출 트렌드 차트 */}
        <div className="chart-container mb-24">
          <div className="card-title">📉 최근 30일 매출 트렌드</div>
          {loadingTrend ? (
            <div className="loading-overlay"><div className="spinner" />차트 로딩 중...</div>
          ) : trend && trend.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={trend} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="gradRevenue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#6366f1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gradProfit" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.1)" />
                <XAxis dataKey="date" tick={{ fill: '#9ca3c8', fontSize: 11 }} tickFormatter={v => v?.slice(5)} />
                <YAxis tick={{ fill: '#9ca3c8', fontSize: 11 }} tickFormatter={v => `${(v/10000).toFixed(0)}만`} />
                <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v, n) => [`${v.toLocaleString()}원`, n === 'revenue' ? '매출' : '순이익']} />
                <Area type="monotone" dataKey="revenue"    stroke="#6366f1" fill="url(#gradRevenue)" strokeWidth={2} />
                <Area type="monotone" dataKey="net_profit" stroke="#10b981" fill="url(#gradProfit)"  strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="loading-overlay">
              <div>
                <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: 8 }}>
                  아직 판매 데이터가 없습니다
                </p>
                <p style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
                  모니터링 탭에서 <strong>주문 수집</strong>을 실행하면 차트가 나타납니다
                </p>
              </div>
            </div>
          )}
        </div>

        {/* 상태별 상품 수 */}
        <div className="chart-container">
          <div className="card-title">📦 상품 상태 분포</div>
          {Object.keys(counts).length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart
                data={Object.entries(counts).map(([k, v]) => ({
                  status: k,
                  count: v,
                }))}
                margin={{ top: 10, right: 10, left: 0, bottom: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.1)" />
                <XAxis dataKey="status" tick={{ fill: '#9ca3c8', fontSize: 11 }} angle={-30} textAnchor="end" />
                <YAxis tick={{ fill: '#9ca3c8', fontSize: 11 }} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="loading-overlay" style={{ padding: 30 }}>
              <span style={{ color: 'var(--text-muted)' }}>소싱 탭에서 상품을 스캔하면 나타납니다</span>
            </div>
          )}
        </div>

      </div>
    </div>
  )
}
