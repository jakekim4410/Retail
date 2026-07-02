import { useState } from 'react'

const STATUS_LABELS = {
  sourced: '소싱완료',
  filtered: '마진미달',
  page_generated: '페이지생성',
  pending_review: '검수대기',
  registered: '등록완료',
  on_sale: '판매중',
  price_adjust: '가격조정필요',
  delist_candidate: '하차후보',
  delisted: '하차완료',
}

const CAT_LABELS = {
  'ELEC-AUDIO': '이어폰/음향',
  'ELEC-LIGHT': '조명',
  'KITCHEN-CUP': '컵/텀블러',
  'TRAVEL-ACC': '여행소품',
  'SPORTS-YOGA': '요가/스포츠',
  'CLEAN-CLOTH': '청소용품',
  'HOME-DIFFUSER': '디퓨저',
  'CAR-ACC': '차량소품',
}

function MarginBreakdown({ m }) {
  if (!m) return null
  return (
    <div className="margin-breakdown" style={{ marginTop: 12 }}>
      <div className="margin-row">
        <span className="td-muted">판매가</span>
        <span>{m.sale_price?.toLocaleString()}원</span>
      </div>
      <div className="margin-row">
        <span className="td-muted">도매가</span>
        <span className="margin-negative">-{m.wholesale_price?.toLocaleString()}원</span>
      </div>
      <div className="margin-row">
        <span className="td-muted">쿠팡 수수료 ({m.commission_rate_pct}%)</span>
        <span className="margin-negative">-{m.commission_amount?.toLocaleString()}원</span>
      </div>
      <div className="margin-row">
        <span className="td-muted">부가세</span>
        <span className="margin-negative">-{m.vat_amount?.toLocaleString()}원</span>
      </div>
      <div className="margin-row">
        <span className="td-muted">서비스이용료(일할)</span>
        <span className="margin-negative">-{m.service_fee_daily?.toLocaleString()}원</span>
      </div>
      <div className="margin-row">
        <span className="td-muted">예상 반품비</span>
        <span className="margin-negative">-{m.estimated_return_cost?.toLocaleString()}원</span>
      </div>
      <div className="margin-row total">
        <span>순이익</span>
        <span className={m.net_margin >= 0 ? 'margin-positive' : 'margin-negative'}>
          {m.net_margin >= 0 ? '+' : ''}{m.net_margin?.toLocaleString()}원
          &nbsp;({m.net_margin_rate_pct}%)
        </span>
      </div>
      {m.suggested_price && (
        <div style={{ marginTop: 8, padding: '8px 12px', background: 'rgba(99,102,241,0.08)', borderRadius: 6, fontSize: 12, color: 'var(--accent-primary)' }}>
          💡 권장 판매가: <strong>{m.suggested_price?.toLocaleString()}원</strong>
        </div>
      )}
    </div>
  )
}

export default function Sourcing() {
  const [scanResult, setScanResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [tab, setTab] = useState('passed')
  const [targetMargin, setTargetMargin] = useState(10)
  const [expandedId, setExpandedId] = useState(null)

  async function runScan() {
    setLoading(true)
    setScanResult(null)
    try {
      const resp = await fetch(
        `/api/sourcing/scan?target_margin_pct=${targetMargin}&monthly_sales_estimate=500000&page_size=20`,
        { method: 'POST' }
      )
      
      let data;
      const text = await resp.text();
      try {
        data = JSON.parse(text);
      } catch (err) {
        throw new Error(resp.ok ? "Invalid JSON format from server" : (text || `HTTP Error ${resp.status}`));
      }

      if (!resp.ok) {
        throw new Error(data.detail || data.message || "스캔 중 서버 오류가 발생했습니다.")
      }
      setScanResult(data)
    } catch (e) {
      alert('스캔 오류: ' + e.message)
    } finally {
      setLoading(false)
    }
  }

  const products = scanResult
    ? (tab === 'passed' ? scanResult.passed_products : scanResult.filtered_products)
    : []

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">🔍 소싱·마진 검증</h1>
        <p className="page-subtitle">오너클랜 신상품 수집 및 마진율 자동 계산</p>
      </div>
      <div className="page-body">

        {/* 스캔 제어 */}
        <div className="card mb-24">
          <div className="card-title">⚙️ 소싱 스캔 설정</div>
          <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
            <div className="form-group" style={{ marginBottom: 0, minWidth: 200 }}>
              <label className="form-label">최저 마진율 기준 (%)</label>
              <input
                type="number"
                className="form-input"
                value={targetMargin}
                onChange={e => setTargetMargin(Number(e.target.value))}
                min={1} max={50}
                style={{ width: 140 }}
              />
            </div>
            <button className="btn btn-primary btn-lg" onClick={runScan} disabled={loading}>
              {loading ? <><div className="spinner" style={{ width: 16, height: 16 }} />스캔 중...</> : '🚀 소싱 스캔 실행'}
            </button>
          </div>

          {scanResult && (
            <div style={{ marginTop: 16, display: 'flex', gap: 24, flexWrap: 'wrap' }}>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                전체 스캔: <strong style={{ color: 'var(--text-primary)' }}>{scanResult.total_scanned}건</strong>
              </div>
              <div style={{ fontSize: 13 }}>
                ✅ 통과: <strong className="text-success">{scanResult.passed}건</strong>
              </div>
              <div style={{ fontSize: 13 }}>
                ❌ 필터링: <strong className="text-danger">{scanResult.filtered}건</strong>
              </div>
              {scanResult.mock && (
                <div className="alert alert-info" style={{ marginBottom: 0, padding: '4px 12px' }}>
                  ⚡ Mock 데이터로 실행됨
                </div>
              )}
            </div>
          )}
        </div>

        {/* 결과 탭 */}
        {scanResult && (
          <>
            <div className="tabs">
              <button className={`tab ${tab === 'passed' ? 'active' : ''}`} onClick={() => setTab('passed')}>
                ✅ 마진 통과 ({scanResult.passed})
              </button>
              <button className={`tab ${tab === 'filtered' ? 'active' : ''}`} onClick={() => setTab('filtered')}>
                ❌ 필터링됨 ({scanResult.filtered})
              </button>
            </div>

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>상품명</th>
                    <th>카테고리</th>
                    <th>도매가</th>
                    <th>권장 판매가</th>
                    <th>순마진율</th>
                    <th>순이익</th>
                    <th>상태</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {products.map(p => {
                    const m = p.margin
                    const isExpanded = expandedId === p.source_id
                    return (
                      <>
                        <tr key={p.source_id}>
                          <td>
                            <div style={{ fontWeight: 600, maxWidth: 240, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {p.name}
                            </div>
                            <div className="td-muted" style={{ fontSize: 11 }}>{p.brand}</div>
                          </td>
                          <td><span style={{ fontSize: 11, color: 'var(--accent-secondary)' }}>{CAT_LABELS[p.source_category_code] || p.source_category_code}</span></td>
                          <td>{p.wholesale_price?.toLocaleString()}원</td>
                          <td><strong>{m?.suggested_price?.toLocaleString()}원</strong></td>
                          <td>
                            <span style={{ color: m?.passed ? 'var(--accent-success)' : 'var(--accent-danger)', fontWeight: 700 }}>
                              {m?.net_margin_rate_pct}%
                            </span>
                          </td>
                          <td style={{ fontWeight: 600 }}>{m?.net_margin?.toLocaleString()}원</td>
                          <td><span className={`badge badge-${m?.passed ? 'on_sale' : 'filtered'}`}>{m?.passed ? '✅ 통과' : '❌ 미달'}</span></td>
                          <td>
                            <button className="btn btn-secondary btn-sm" onClick={() => setExpandedId(isExpanded ? null : p.source_id)}>
                              {isExpanded ? '닫기' : '상세'}
                            </button>
                          </td>
                        </tr>
                        {isExpanded && (
                          <tr key={`${p.source_id}-detail`}>
                            <td colSpan={8} style={{ padding: '4px 16px 16px', background: 'rgba(99,102,241,0.03)' }}>
                              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                                <div>
                                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>마진 상세 분석</div>
                                  <MarginBreakdown m={m} />
                                </div>
                                <div>
                                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>스펙</div>
                                  {Object.entries(p.specs || {}).map(([k, v]) => (
                                    <div key={k} style={{ fontSize: 12, padding: '4px 0', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between' }}>
                                      <span style={{ color: 'var(--text-muted)' }}>{k}</span>
                                      <span>{v}</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            </td>
                          </tr>
                        )}
                      </>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </>
        )}

        {!scanResult && !loading && (
          <div className="card" style={{ textAlign: 'center', padding: '60px 24px' }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>🔍</div>
            <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>
              소싱 스캔을 실행해 주세요
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
              오너클랜 신상품을 수집하고 마진율을 자동으로 계산합니다
            </div>
          </div>
        )}

      </div>
    </div>
  )
}
