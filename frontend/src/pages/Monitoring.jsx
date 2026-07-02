import { useState, useEffect } from 'react'

export default function Monitoring() {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [collectLoading, setCollectLoading] = useState(false)
  const [message, setMessage] = useState(null)
  const [sortField, setSortField] = useState('total_revenue')
  const [sortOrder, setSortOrder] = useState('desc')

  async function loadData() {
    setLoading(true)
    try {
      const r = await fetch('/api/monitoring/products')
      const data = await r.json()
      setProducts(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [])

  async function handleCollect() {
    setCollectLoading(true)
    setMessage(null)
    try {
      const r = await fetch('/api/monitoring/collect?days_back=1', { method: 'POST' })
      const data = await r.json()
      setMessage({
        type: 'success',
        text: `✅ 데이터 수집 완료: 신규 ${data.new_orders}건 / 업데이트 ${data.updated_orders}건`
      })
      await loadData()
    } catch (e) {
      setMessage({ type: 'danger', text: `❌ 데이터 수집 실패: ${e.message}` })
    } finally {
      setCollectLoading(false)
    }
  }

  function handleSort(field) {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortOrder('desc')
    }
  }

  const sortedProducts = [...products].sort((a, b) => {
    let valA = a[sortField]
    let valB = b[sortField]
    if (typeof valA === 'string') {
      valA = valA.toLowerCase()
      valB = (valB || '').toLowerCase()
    }
    if (valA < valB) return sortOrder === 'asc' ? -1 : 1
    if (valA > valB) return sortOrder === 'asc' ? 1 : -1
    return 0
  })

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">📈 판매 성과 모니터링</h1>
        <p className="page-subtitle">상품별 주문/매출 집계 및 성과 분석</p>
      </div>
      <div className="page-body">

        {message && (
          <div className={`alert alert-${message.type}`}>
            {message.text}
            <button onClick={() => setMessage(null)} style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', color: 'inherit', fontSize: 16 }}>×</button>
          </div>
        )}

        <div className="card mb-24" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div className="card-title" style={{ marginBottom: 4 }}>🔄 최신 주문 데이터 동기화</div>
            <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
              쿠팡 Open API에서 최근 주문을 가져와 매출과 순이익을 계산합니다.
            </div>
          </div>
          <button className="btn btn-primary btn-lg" onClick={handleCollect} disabled={collectLoading}>
            {collectLoading ? <><div className="spinner" style={{ width: 16, height: 16 }} />수집 중...</> : '📥 주문 데이터 수집'}
          </button>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th onClick={() => handleSort('name')} style={{ cursor: 'pointer' }}>
                  상품명 {sortField === 'name' && (sortOrder === 'asc' ? '▲' : '▼')}
                </th>
                <th onClick={() => handleSort('status')} style={{ cursor: 'pointer' }}>
                  상태 {sortField === 'status' && (sortOrder === 'asc' ? '▲' : '▼')}
                </th>
                <th onClick={() => handleSort('total_sales_qty')} style={{ cursor: 'pointer', textAlign: 'right' }}>
                  총 판매량 {sortField === 'total_sales_qty' && (sortOrder === 'asc' ? '▲' : '▼')}
                </th>
                <th onClick={() => handleSort('total_revenue')} style={{ cursor: 'pointer', textAlign: 'right' }}>
                  총 매출 {sortField === 'total_revenue' && (sortOrder === 'asc' ? '▲' : '▼')}
                </th>
                <th onClick={() => handleSort('total_net_profit')} style={{ cursor: 'pointer', textAlign: 'right' }}>
                  총 순이익 {sortField === 'total_net_profit' && (sortOrder === 'asc' ? '▲' : '▼')}
                </th>
                <th onClick={() => handleSort('return_qty')} style={{ cursor: 'pointer', textAlign: 'right' }}>
                  반품 {sortField === 'return_qty' && (sortOrder === 'asc' ? '▲' : '▼')}
                </th>
                <th onClick={() => handleSort('last_sale_date')} style={{ cursor: 'pointer' }}>
                  최근 판매일 {sortField === 'last_sale_date' && (sortOrder === 'asc' ? '▲' : '▼')}
                </th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={7} style={{ textAlign: 'center', padding: 40 }}><div className="spinner" style={{ margin: '0 auto' }} /></td></tr>
              ) : sortedProducts.length === 0 ? (
                <tr><td colSpan={7} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>등록된 상품이 없습니다</td></tr>
              ) : (
                sortedProducts.map(p => (
                  <tr key={p.id}>
                    <td>
                      <div style={{ fontWeight: 600, maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.name}</div>
                      <div className="td-muted" style={{ fontSize: 11 }}>{p.source_id}</div>
                    </td>
                    <td><span className={`badge badge-${p.status}`}>{p.status === 'on_sale' ? '판매중' : p.status}</span></td>
                    <td style={{ textAlign: 'right', fontWeight: 500 }}>{p.total_sales_qty?.toLocaleString()}개</td>
                    <td style={{ textAlign: 'right', fontWeight: 600, color: 'var(--accent-primary)' }}>{p.total_revenue?.toLocaleString()}원</td>
                    <td style={{ textAlign: 'right', fontWeight: 700, color: p.total_net_profit >= 0 ? 'var(--accent-success)' : 'var(--accent-danger)' }}>
                      {p.total_net_profit >= 0 ? '+' : ''}{p.total_net_profit?.toLocaleString()}원
                    </td>
                    <td style={{ textAlign: 'right', color: p.return_qty > 0 ? 'var(--accent-danger)' : 'inherit' }}>{p.return_qty}개</td>
                    <td className="td-muted">{p.last_sale_date ? new Date(p.last_sale_date).toLocaleDateString() : '-'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

      </div>
    </div>
  )
}
