import { useState, useEffect, useCallback } from 'react'

const STATUS_LABELS = {
  sourced: '소싱완료',
  filtered: '마진미달',
  page_generated: '페이지생성완료',
  pending_review: '검수대기',
  registered: '등록완료',
  on_sale: '판매중',
  price_adjust: '가격조정필요',
  delist_candidate: '하차후보',
  delisted: '하차완료',
}

const FLOW_STEPS = [
  { status: 'sourced',        action: '상세페이지 생성', nextStatus: 'page_generated', api: (id) => fetch(`/api/detail-page/generate`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({product_id: id}) }) },
  { status: 'page_generated', action: '쿠팡 등록 승인', nextStatus: 'registered',     api: (id) => fetch(`/api/registration/approve/${id}`, { method: 'POST' }) },
  { status: 'registered',     action: '판매 시작',       nextStatus: 'on_sale',        api: (id) => fetch(`/api/registration/set-on-sale/${id}`, { method: 'POST' }) },
  { status: 'delist_candidate', action: '하차 처리',     nextStatus: 'delisted',       api: (id) => fetch(`/api/registration/delist/${id}`, { method: 'POST' }) },
]

export default function Products() {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('all')
  const [actionLoading, setActionLoading] = useState({})
  const [message, setMessage] = useState(null)
  const [genBatchLoading, setGenBatchLoading] = useState(false)
  const [optimizerLoading, setOptimizerLoading] = useState(false)
  const [editingHtmlTarget, setEditingHtmlTarget] = useState(null)

  const loadProducts = useCallback(async () => {
    setLoading(true)
    const url = statusFilter === 'all'
      ? '/api/sourcing/db-products'
      : `/api/sourcing/db-products?status=${statusFilter}`
    const r = await fetch(url)
    const data = await r.json()
    setProducts(data)
    setLoading(false)
  }, [statusFilter])

  useEffect(() => { loadProducts() }, [loadProducts])

  async function doAction(product, stepDef) {
    setActionLoading(p => ({ ...p, [product.id]: true }))
    try {
      const r = await stepDef.api(product.id)
      const data = await r.json()
      if (data.success !== false) {
        setMessage({ type: 'success', text: `✅ [${product.name}] ${stepDef.action} 완료` })
        await loadProducts()
      } else {
        setMessage({ type: 'danger', text: `❌ 오류: ${JSON.stringify(data.detail || data)}` })
      }
    } catch (e) {
      setMessage({ type: 'danger', text: `❌ ${e.message}` })
    } finally {
      setActionLoading(p => ({ ...p, [product.id]: false }))
    }
  }

  async function generateBatch() {
    setGenBatchLoading(true)
    const r = await fetch('/api/detail-page/generate-batch', { method: 'POST' })
    const data = await r.json()
    setMessage({ type: 'success', text: `✅ 일괄 생성 완료: 성공 ${data.success}건 / 실패 ${data.failed}건` })
    setGenBatchLoading(false)
    loadProducts()
  }

  async function runOptimizer() {
    setOptimizerLoading(true)
    const r = await fetch('/api/optimizer/run', { method: 'POST' })
    const data = await r.json()
    setMessage({
      type: 'success',
      text: `🔄 최적화 완료 — 하차후보 ${data.delist_tagged?.length || 0}건, 가격조정 ${data.price_adjust_tagged?.length || 0}건`
    })
    setOptimizerLoading(false)
    loadProducts()
  }

  async function openHtmlEditor(product) {
    try {
      const r = await fetch(`/api/detail-page/preview/${product.id}`)
      if (!r.ok) throw new Error('상세페이지를 불러오지 못했습니다.')
      const html = await r.text()
      setEditingHtmlTarget({ ...product, html })
    } catch (e) {
      setMessage({ type: 'danger', text: `❌ ${e.message}` })
    }
  }

  async function saveHtmlEdit() {
    try {
      const r = await fetch(`/api/detail-page/${editingHtmlTarget.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ html: editingHtmlTarget.html })
      })
      if (r.ok) {
        setMessage({ type: 'success', text: '✅ HTML 수정이 저장되었습니다.' })
        setEditingHtmlTarget(null)
      } else {
        const data = await r.json()
        setMessage({ type: 'danger', text: `❌ 오류: ${data.detail || '저장 실패'}` })
      }
    } catch (e) {
      setMessage({ type: 'danger', text: `❌ ${e.message}` })
    }
  }

  const statusCounts = products.reduce((acc, p) => {
    acc[p.status] = (acc[p.status] || 0) + 1
    return acc
  }, {})

  const filtered = statusFilter === 'all' ? products : products.filter(p => p.status === statusFilter)

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">📦 상품 관리·등록</h1>
        <p className="page-subtitle">상세페이지 생성 → 검수 → 쿠팡 등록 반자동 흐름</p>
      </div>
      <div className="page-body">

        {editingHtmlTarget && (
          <div style={{position:'fixed', top:0, left:0, right:0, bottom:0, background:'rgba(0,0,0,0.6)', zIndex:999, display:'flex', alignItems:'center', justifyContent:'center'}}>
            <div className="card" style={{width:'90%', maxWidth:1000, padding:24, display:'flex', flexDirection:'column', gap:16, maxHeight:'90vh'}}>
              <h2 style={{margin:0, fontSize:20}}>📝 [{editingHtmlTarget.name}] HTML 수정</h2>
              <textarea
                style={{flex:1, width:'100%', minHeight:400, fontFamily:'monospace', padding:12, borderRadius:8, border:'1px solid var(--border-color)', background:'var(--bg-base)', color:'var(--text-primary)', resize:'none'}}
                value={editingHtmlTarget.html}
                onChange={e => setEditingHtmlTarget({...editingHtmlTarget, html: e.target.value})}
              />
              <div style={{display:'flex', justifyContent:'flex-end', gap:8}}>
                <button className="btn btn-secondary" onClick={() => setEditingHtmlTarget(null)}>취소</button>
                <button className="btn btn-primary" onClick={saveHtmlEdit}>저장</button>
              </div>
            </div>
          </div>
        )}

        {message && (
          <div className={`alert alert-${message.type}`} style={{ marginBottom: 16 }}>
            {message.text}
            <button onClick={() => setMessage(null)} style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', color: 'inherit', fontSize: 16 }}>×</button>
          </div>
        )}

        {/* 상태 요약 칩 */}
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 20 }}>
          <button className={`btn btn-sm ${statusFilter === 'all' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setStatusFilter('all')}>
            전체 ({products.length})
          </button>
          {Object.entries(statusCounts).map(([s, n]) => (
            <button key={s} className={`btn btn-sm ${statusFilter === s ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setStatusFilter(s)}>
              <span className={`badge badge-${s}`}>{STATUS_LABELS[s] || s}</span> {n}
            </button>
          ))}
        </div>

        {/* 액션 버튼 */}
        <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap' }}>
          <button className="btn btn-secondary" onClick={generateBatch} disabled={genBatchLoading}>
            {genBatchLoading ? <><div className="spinner" style={{ width: 14, height: 14 }} />생성 중...</> : '📝 소싱완료 상품 상세페이지 일괄 생성'}
          </button>
          <button className="btn btn-secondary" onClick={runOptimizer} disabled={optimizerLoading}>
            {optimizerLoading ? <><div className="spinner" style={{ width: 14, height: 14 }} />실행 중...</> : '🔄 최적화 루프 실행'}
          </button>
        </div>

        {/* 상품 테이블 */}
        {loading ? (
          <div className="loading-overlay"><div className="spinner" />로딩 중...</div>
        ) : filtered.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '48px 24px' }}>
            <div style={{ fontSize: 40, marginBottom: 12 }}>📦</div>
            <div style={{ color: 'var(--text-secondary)' }}>
              {statusFilter === 'all' ? '소싱 탭에서 스캔을 먼저 실행해 주세요' : `${STATUS_LABELS[statusFilter]} 상품이 없습니다`}
            </div>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>상품명</th>
                  <th>도매가</th>
                  <th>판매가</th>
                  <th>마진율</th>
                  <th>상태</th>
                  <th>쿠팡ID</th>
                  <th>액션</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(p => {
                  const step = FLOW_STEPS.find(s => s.status === p.status)
                  const isLoading = actionLoading[p.id]
                  return (
                    <tr key={p.id}>
                      <td className="td-muted" style={{ fontSize: 11 }}>{p.id}</td>
                      <td>
                        <div style={{ fontWeight: 600, maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.name}</div>
                        <div className="td-muted" style={{ fontSize: 11 }}>{p.source_id} · {p.brand}</div>
                      </td>
                      <td>{p.wholesale_price?.toLocaleString()}원</td>
                      <td><strong>{p.sale_price?.toLocaleString()}원</strong></td>
                      <td>
                        <span style={{
                          color: p.margin_rate >= 10 ? 'var(--accent-success)' : p.margin_rate >= 0 ? 'var(--accent-warning)' : 'var(--accent-danger)',
                          fontWeight: 700,
                        }}>
                          {p.margin_rate}%
                        </span>
                      </td>
                      <td><span className={`badge badge-${p.status}`}>{STATUS_LABELS[p.status] || p.status}</span></td>
                      <td>
                        {p.coupang_product_id
                          ? <span className="td-mono">{p.coupang_product_id}</span>
                          : <span className="td-muted">—</span>
                        }
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                          {step && (
                            <button
                              className="btn btn-success btn-sm"
                              onClick={() => doAction(p, step)}
                              disabled={isLoading}
                            >
                              {isLoading ? <div className="spinner" style={{ width: 12, height: 12 }} /> : step.action}
                            </button>
                          )}
                          {p.status === 'page_generated' && (
                            <>
                              <button
                                className="btn btn-secondary btn-sm"
                                onClick={() => openHtmlEditor(p)}
                                disabled={isLoading}
                              >
                                HTML 편집
                              </button>
                              <button
                                className="btn btn-sm"
                                onClick={() => doAction(p, { action: '수동 등록', api: (id) => fetch(`/api/registration/manual-register/${id}`, { method: 'POST' }) })}
                                disabled={isLoading}
                                style={{ backgroundColor: 'var(--accent-warning)', color: '#fff', border: 'none' }}
                              >
                                수동 등록
                              </button>
                            </>
                          )}
                          {(p.status === 'on_sale' || p.status === 'page_generated' || p.status === 'registered') && (
                            <a href={`/api/detail-page/preview/${p.id}`} target="_blank" rel="noreferrer" className="btn btn-secondary btn-sm">
                              미리보기
                            </a>
                          )}
                          {(p.status === 'on_sale' || p.status === 'price_adjust') && (
                            <button
                              className="btn btn-danger btn-sm"
                              onClick={() => doAction(p, FLOW_STEPS.find(s => s.status === 'delist_candidate') || { action: '하차', api: (id) => fetch(`/api/registration/delist/${id}`, { method: 'POST' }) })}
                              disabled={isLoading}
                            >
                              하차
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
