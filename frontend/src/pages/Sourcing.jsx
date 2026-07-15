import { useState, useEffect, useCallback } from 'react'

// ─── 카테고리 수수료율 (프론트 마진 시뮬레이터용) ────────────────────────────
const COMMISSION_RATES = {
  'ELEC-AUDIO': 0.068, 'ELEC-LIGHT': 0.068, 'ELEC-ETC': 0.068,
  'KITCHEN-CUP': 0.070, 'KITCHEN-ETC': 0.070,
  'TRAVEL-ACC': 0.075, 'SPORTS-YOGA': 0.080, 'SPORTS-ETC': 0.080,
  'CLEAN-CLOTH': 0.075, 'HOME-DIFFUSER': 0.075, 'HOME-ETC': 0.075,
  'CAR-ACC': 0.070, 'BEAUTY': 0.090, 'FASHION': 0.109, 'FOOD': 0.040,
}
const RETURN_RATES = {
  'FASHION': 0.15, 'BEAUTY': 0.05, 'ELEC-AUDIO': 0.04, 'ELEC-LIGHT': 0.03, 'SPORTS-YOGA': 0.04,
}

function calcMargin(wholesalePrice, salePrice, catCode, monthlySales = 500000) {
  if (!salePrice || salePrice <= 0) return null
  const commRate = COMMISSION_RATES[catCode] ?? 0.070
  const retRate = RETURN_RATES[catCode] ?? 0.03
  const commission = salePrice * commRate
  const supply = salePrice - commission
  const vat = supply * 10 / 110
  const serviceFee = monthlySales > 1000000 ? 55000 / 30 : 0
  const returnCost = retRate * 5000
  const net = salePrice - wholesalePrice - commission - vat - serviceFee - returnCost
  const rate = (net / salePrice) * 100
  return {
    salePrice, wholesalePrice, commission: Math.round(commission),
    vat: Math.round(vat), serviceFee: Math.round(serviceFee),
    returnCost: Math.round(returnCost), net: Math.round(net),
    rate: Math.round(rate * 10) / 10,
    commRate: Math.round(commRate * 1000) / 10,
  }
}

function gradeColor(grade) {
  return { S: '#a78bfa', A: '#34d399', B: '#60a5fa', C: '#fbbf24', F: '#f87171' }[grade] || '#888'
}

function gradeLabel(rate) {
  if (rate >= 25) return { g: 'S', label: '최우수', color: '#a78bfa' }
  if (rate >= 20) return { g: 'A', label: '우수', color: '#34d399' }
  if (rate >= 15) return { g: 'B', label: '양호', color: '#60a5fa' }
  if (rate >= 10) return { g: 'C', label: '보통', color: '#fbbf24' }
  return { g: 'F', label: '미달', color: '#f87171' }
}

// ─── 마진 시뮬레이터 컴포넌트 ────────────────────────────────────────────────
function MarginSimulator({ product, onClose }) {
  const [salePrice, setSalePrice] = useState(
    product.margin?.suggested_price || Math.round(product.wholesale_price * 1.4 / 100) * 100
  )
  const margin = calcMargin(product.wholesale_price, salePrice, product.source_category_code)
  const { g, label, color } = gradeLabel(margin?.rate ?? 0)
  const minPrice = Math.round(product.wholesale_price * 1.1 / 100) * 100
  const maxPrice = Math.round(product.wholesale_price * 3.0 / 100) * 100

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', zIndex: 1000,
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24
    }} onClick={onClose}>
      <div style={{
        background: 'var(--bg-card)', border: '1px solid var(--border-default)',
        borderRadius: 16, padding: 28, width: '100%', maxWidth: 520,
        boxShadow: '0 24px 80px rgba(0,0,0,0.5)',
      }} onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 20 }}>
          <div>
            <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 4 }}>마진 시뮬레이터</div>
            <div style={{ fontWeight: 700, fontSize: 15, maxWidth: 360, lineHeight: 1.4 }}>{product.name}</div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: 20 }}>✕</button>
        </div>

        {/* 판매가 슬라이더 */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
            <label style={{ fontSize: 13, color: 'var(--text-secondary)' }}>판매가 설정</label>
            <span style={{ fontSize: 16, fontWeight: 700, color: 'var(--accent-primary)' }}>{salePrice.toLocaleString()}원</span>
          </div>
          <input
            type="range"
            min={minPrice} max={maxPrice} step={100}
            value={salePrice}
            onChange={e => setSalePrice(Number(e.target.value))}
            style={{ width: '100%', accentColor: 'var(--accent-primary)' }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
            <span>{minPrice.toLocaleString()}원</span>
            <span>도매가: {product.wholesale_price.toLocaleString()}원</span>
            <span>{maxPrice.toLocaleString()}원</span>
          </div>
        </div>

        {/* 마진 등급 배지 */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12,
          padding: '16px', borderRadius: 12, marginBottom: 20,
          background: `linear-gradient(135deg, ${color}18, ${color}08)`,
          border: `1px solid ${color}40`
        }}>
          <div style={{ fontSize: 36, fontWeight: 900, color }}>{g}</div>
          <div>
            <div style={{ fontWeight: 700, color, fontSize: 18 }}>{margin?.rate ?? 0}%</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>순마진율 · {label}</div>
          </div>
          <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
            <div style={{ fontWeight: 700, fontSize: 18, color: (margin?.net ?? 0) >= 0 ? '#34d399' : '#f87171' }}>
              {(margin?.net ?? 0) >= 0 ? '+' : ''}{(margin?.net ?? 0).toLocaleString()}원
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>건당 순이익</div>
          </div>
        </div>

        {/* 비용 상세 */}
        <div style={{ display: 'grid', gap: 6 }}>
          {[
            ['판매가', salePrice, 'var(--text-primary)', false],
            ['도매가', product.wholesale_price, '#f87171', true],
            [`쿠팡 수수료 (${margin?.commRate}%)`, margin?.commission, '#f87171', true],
            ['부가세 (역산)', margin?.vat, '#f87171', true],
            ['반품비 (예상)', margin?.returnCost, '#f87171', true],
          ].map(([label, val, color, minus]) => (
            <div key={label} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, padding: '6px 0', borderBottom: '1px solid var(--border-subtle)' }}>
              <span style={{ color: 'var(--text-secondary)' }}>{label}</span>
              <span style={{ color, fontWeight: 500 }}>{minus ? '-' : ''}{val?.toLocaleString()}원</span>
            </div>
          ))}
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14, padding: '10px 0', fontWeight: 700 }}>
            <span>순이익</span>
            <span style={{ color: (margin?.net ?? 0) >= 0 ? '#34d399' : '#f87171' }}>
              {(margin?.net ?? 0) >= 0 ? '+' : ''}{(margin?.net ?? 0).toLocaleString()}원 ({margin?.rate ?? 0}%)
            </span>
          </div>
        </div>

        <div style={{ marginTop: 16, fontSize: 11, color: 'var(--text-muted)', textAlign: 'center' }}>
          💡 쿠팡 수수료 기준 · 부가세 역산 · 반품비 포함 실제 정산 기준
        </div>
      </div>
    </div>
  )
}

// ─── 상품 카드 컴포넌트 ──────────────────────────────────────────────────────
function ProductCard({ product, targetMargin, onSimulate }) {
  const margin = product.margin || calcMargin(product.wholesale_price, product.margin?.suggested_price, product.source_category_code)
  const rate = margin?.net_margin_rate_pct ?? margin?.rate ?? 0
  const { g, label, color } = gradeLabel(rate)
  const net = margin?.net_margin ?? margin?.net ?? 0
  const suggested = margin?.suggested_price ?? margin?.salePrice ?? 0
  const img = product.image_urls?.[0] || `https://picsum.photos/seed/${product.source_id}/300/300`

  return (
    <div style={{
      background: 'var(--bg-card)', border: `1px solid ${rate >= targetMargin ? 'var(--border-default)' : 'rgba(248,113,113,0.2)'}`,
      borderRadius: 12, overflow: 'hidden', display: 'flex', flexDirection: 'column',
      transition: 'transform 0.2s, box-shadow 0.2s', cursor: 'pointer',
    }}
      onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-3px)'; e.currentTarget.style.boxShadow = '0 12px 40px rgba(0,0,0,0.3)' }}
      onMouseLeave={e => { e.currentTarget.style.transform = ''; e.currentTarget.style.boxShadow = '' }}
      onClick={() => onSimulate(product)}
    >
      {/* 이미지 */}
      <div style={{ position: 'relative', paddingTop: '66%', background: 'var(--bg-elevated)', flexShrink: 0 }}>
        <img src={img} alt={product.name}
          style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover' }}
          onError={e => { e.target.src = `https://picsum.photos/seed/${product.source_id}x/300/300` }}
        />
        {/* 등급 배지 */}
        <div style={{
          position: 'absolute', top: 8, right: 8,
          background: color, color: '#fff', borderRadius: 6,
          padding: '3px 8px', fontWeight: 800, fontSize: 13,
          boxShadow: `0 2px 8px ${color}60`
        }}>{g} {label}</div>
        {/* 재고 배지 */}
        {product.stock > 0 && (
          <div style={{
            position: 'absolute', bottom: 8, left: 8,
            background: 'rgba(0,0,0,0.65)', color: '#aaa', borderRadius: 4,
            padding: '2px 6px', fontSize: 11
          }}>재고 {product.stock?.toLocaleString()}개</div>
        )}
      </div>

      {/* 내용 */}
      <div style={{ padding: 14, flex: 1, display: 'flex', flexDirection: 'column', gap: 6 }}>
        <div style={{ fontSize: 11, color: 'var(--accent-secondary)', fontWeight: 600 }}>
          {product.source_category_name || product.source_category_code}
        </div>
        <a 
          href={`https://ownerclan.com/V2/product/view.php?code=${product.source_id}`} 
          target="_blank" 
          rel="noopener noreferrer"
          onClick={e => e.stopPropagation()}
          style={{ fontWeight: 600, fontSize: 13, lineHeight: 1.4, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', color: 'var(--text-primary)', textDecoration: 'none' }}
          onMouseEnter={e => e.target.style.textDecoration = 'underline'}
          onMouseLeave={e => e.target.style.textDecoration = 'none'}
        >
          {product.name}
        </a>
        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{product.brand}</div>

        <div style={{ marginTop: 'auto', paddingTop: 8, borderTop: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
          <div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>도매가</div>
            <div style={{ fontWeight: 700, fontSize: 14 }}>{product.wholesale_price?.toLocaleString()}원</div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>권장판매가</div>
            <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--accent-primary)' }}>{suggested?.toLocaleString()}원</div>
          </div>
        </div>

        {/* 마진 바 */}
        <div style={{ marginTop: 6 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 4 }}>
            <span style={{ color: 'var(--text-muted)' }}>순마진율</span>
            <span style={{ fontWeight: 700, color }}>{rate}% · {net >= 0 ? '+' : ''}{net?.toLocaleString()}원</span>
          </div>
          <div style={{ height: 4, borderRadius: 2, background: 'var(--border-subtle)', overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${Math.min(Math.max(rate, 0), 40) / 40 * 100}%`, background: color, borderRadius: 2, transition: 'width 0.5s' }} />
          </div>
        </div>

        <button
          style={{
            marginTop: 8, width: '100%', padding: '7px', borderRadius: 7, border: 'none',
            background: `${color}20`, color, fontWeight: 600, fontSize: 12, cursor: 'pointer',
            transition: 'background 0.2s'
          }}
          onClick={e => { e.stopPropagation(); onSimulate(product) }}
        >🔢 마진 시뮬레이터 열기</button>
      </div>
    </div>
  )
}

// ─── 카테고리 탐색 탭 ────────────────────────────────────────────────────────
function BrowseTab({ targetMargin }) {
  const [categories, setCategories] = useState([])
  const [selectedCat, setSelectedCat] = useState(null)
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(false)
  const [loadingCats, setLoadingCats] = useState(true)
  const [simulatorProduct, setSimulatorProduct] = useState(null)
  const [maxWholesale, setMaxWholesale] = useState('')
  const [minMargin, setMinMargin] = useState('')
  const [total, setTotal] = useState(0)

  // 카테고리 로드
  useEffect(() => {
    setLoadingCats(true)
    fetch('/api/sourcing/categories')
      .then(r => r.json())
      .then(data => setCategories(Array.isArray(data) ? data : []))
      .catch(() => setCategories([]))
      .finally(() => setLoadingCats(false))
  }, [])

  // 상품 로드
  const loadProducts = useCallback(async (catCode) => {
    setLoading(true)
    setProducts([])
    try {
      const params = new URLSearchParams({ page_size: 50, target_margin_pct: targetMargin })
      if (catCode) params.set('category_code', catCode)
      if (maxWholesale) params.set('max_wholesale', maxWholesale)
      if (minMargin) params.set('min_margin_pct', minMargin)
      const resp = await fetch(`/api/sourcing/browse?${params}`)
      const data = await resp.json()
      setProducts(data.products || [])
      setTotal(data.total || 0)
    } catch (e) {
      alert('상품 조회 오류: ' + e.message)
    } finally {
      setLoading(false)
    }
  }, [targetMargin, maxWholesale, minMargin])

  const handleCatSelect = (code) => {
    const c = code === selectedCat ? null : code
    setSelectedCat(c)
    loadProducts(c)
  }

  return (
    <div>
      {/* 카테고리 그리드 */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 12, fontWeight: 600 }}>
          📂 카테고리 선택 {selectedCat && <span style={{ color: 'var(--accent-primary)' }}>· {categories.find(c => c.code === selectedCat)?.name}</span>}
        </div>
        {loadingCats ? (
          <div style={{ display: 'flex', gap: 8 }}>
            {[...Array(6)].map((_, i) => (
              <div key={i} style={{ height: 36, width: 100, background: 'var(--bg-elevated)', borderRadius: 8, animation: 'pulse 1.5s infinite' }} />
            ))}
          </div>
        ) : (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            <button
              onClick={() => { setSelectedCat(null); loadProducts(null) }}
              style={{
                padding: '6px 14px', borderRadius: 20, border: '1px solid',
                borderColor: !selectedCat ? 'var(--accent-primary)' : 'var(--border-default)',
                background: !selectedCat ? 'rgba(99,102,241,0.15)' : 'transparent',
                color: !selectedCat ? 'var(--accent-primary)' : 'var(--text-secondary)',
                cursor: 'pointer', fontSize: 13, fontWeight: 600, transition: 'all 0.2s'
              }}
            >전체</button>
            {categories.map(cat => (
              <button key={cat.code}
                onClick={() => handleCatSelect(cat.code)}
                style={{
                  padding: '6px 14px', borderRadius: 20, border: '1px solid',
                  borderColor: selectedCat === cat.code ? 'var(--accent-primary)' : 'var(--border-default)',
                  background: selectedCat === cat.code ? 'rgba(99,102,241,0.15)' : 'transparent',
                  color: selectedCat === cat.code ? 'var(--accent-primary)' : 'var(--text-secondary)',
                  cursor: 'pointer', fontSize: 13, fontWeight: 500, transition: 'all 0.2s',
                  display: 'flex', alignItems: 'center', gap: 4
                }}
              >
                <span>{cat.icon}</span>
                <span>{cat.name}</span>
                <span style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 2 }}>({cat.count})</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* 필터 바 */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>최소 마진율 (%)</div>
          <input type="number" value={minMargin} onChange={e => setMinMargin(e.target.value)}
            placeholder="예: 15" min={0} max={50}
            style={{ width: 110, padding: '7px 10px', background: 'var(--bg-input)', border: '1px solid var(--border-default)', borderRadius: 7, color: 'var(--text-primary)', fontSize: 13 }}
          />
        </div>
        <div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>최대 도매가 (원)</div>
          <input type="number" value={maxWholesale} onChange={e => setMaxWholesale(e.target.value)}
            placeholder="예: 30000" min={0}
            style={{ width: 130, padding: '7px 10px', background: 'var(--bg-input)', border: '1px solid var(--border-default)', borderRadius: 7, color: 'var(--text-primary)', fontSize: 13 }}
          />
        </div>
        <button onClick={() => loadProducts(selectedCat)}
          style={{ padding: '7px 20px', borderRadius: 7, background: 'var(--accent-primary)', color: '#fff', border: 'none', cursor: 'pointer', fontWeight: 600, fontSize: 13 }}>
          🔍 검색
        </button>
      </div>

      {/* 결과 헤더 */}
      {products.length > 0 && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            총 <strong style={{ color: 'var(--text-primary)' }}>{total}개</strong> 상품 (마진율 높은 순)
          </div>
        </div>
      )}

      {/* 로딩 */}
      {loading && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 16 }}>
          {[...Array(8)].map((_, i) => (
            <div key={i} style={{ height: 320, background: 'var(--bg-card)', borderRadius: 12, animation: 'pulse 1.5s infinite' }} />
          ))}
        </div>
      )}

      {/* 상품 그리드 */}
      {!loading && products.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 16 }}>
          {products.map(p => (
            <ProductCard key={p.source_id} product={p} targetMargin={targetMargin} onSimulate={setSimulatorProduct} />
          ))}
        </div>
      )}

      {/* 빈 상태 */}
      {!loading && products.length === 0 && (
        <div style={{ textAlign: 'center', padding: '60px 24px', color: 'var(--text-muted)' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>📦</div>
          <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 8 }}>
            {selectedCat ? '해당 카테고리에 상품이 없습니다' : '카테고리를 선택하거나 검색하세요'}
          </div>
          <div style={{ fontSize: 13 }}>카테고리를 선택하면 소싱 가능 상품과 마진을 즉시 확인할 수 있습니다</div>
        </div>
      )}

      {/* 마진 시뮬레이터 모달 */}
      {simulatorProduct && <MarginSimulator product={simulatorProduct} onClose={() => setSimulatorProduct(null)} />}
    </div>
  )
}

// ─── 자동 스캔 탭 ─────────────────────────────────────────────────────────
function ScanTab({ targetMargin }) {
  const [scanResult, setScanResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [tab, setTab] = useState('passed')
  const [expandedId, setExpandedId] = useState(null)
  const [simulatorProduct, setSimulatorProduct] = useState(null)

  const products = scanResult
    ? (tab === 'passed' ? scanResult.passed_products : scanResult.filtered_products)
    : []

  async function runScan() {
    setLoading(true)
    setScanResult(null)
    try {
      const resp = await fetch(
        `/api/sourcing/scan?target_margin_pct=${targetMargin}&monthly_sales_estimate=500000&page_size=20`,
        { method: 'POST' }
      )
      const text = await resp.text()
      let data
      try { data = JSON.parse(text) } catch { throw new Error(resp.ok ? 'Invalid JSON' : (text || `HTTP ${resp.status}`)) }
      if (!resp.ok) throw new Error(data.detail || data.message || '스캔 서버 오류')
      setScanResult(data)
    } catch (e) {
      alert('스캔 오류: ' + e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      {/* 스캔 실행 영역 */}
      <div style={{
        display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap',
        padding: '20px', background: 'var(--bg-elevated)', borderRadius: 12, marginBottom: 20,
        border: '1px solid var(--border-default)'
      }}>
        <div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>최소 마진율 기준 (%)</div>
          <div style={{ padding: '8px 14px', background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 8, fontWeight: 700, color: 'var(--accent-primary)', fontSize: 16 }}>
            {targetMargin}%
          </div>
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>스캔 방식</div>
          <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            오너클랜 신상품 최대 20개를 수집하여 마진 기준 통과/실패를 자동 분류하고 DB에 저장합니다
          </div>
        </div>
        <button
          onClick={runScan} disabled={loading}
          style={{
            padding: '10px 28px', borderRadius: 10, border: 'none',
            background: loading ? 'var(--bg-elevated)' : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            color: loading ? 'var(--text-muted)' : '#fff',
            fontWeight: 700, fontSize: 14, cursor: loading ? 'not-allowed' : 'pointer',
            display: 'flex', alignItems: 'center', gap: 8, transition: 'all 0.2s',
            boxShadow: loading ? 'none' : '0 4px 20px rgba(99,102,241,0.4)'
          }}
        >
          {loading ? (
            <><div style={{ width: 16, height: 16, border: '2px solid var(--text-muted)', borderTopColor: 'var(--accent-primary)', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />스캔 중...</>
          ) : <>🚀 소싱 스캔 실행</>}
        </button>
      </div>

      {/* 스캔 결과 요약 */}
      {scanResult && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 20 }}>
            {[
              { label: '전체 스캔', val: scanResult.total_scanned, unit: '건', color: 'var(--text-primary)', icon: '📊' },
              { label: '마진 통과', val: scanResult.passed, unit: '건', color: '#34d399', icon: '✅' },
              { label: '마진 미달', val: scanResult.filtered, unit: '건', color: '#f87171', icon: '❌' },
            ].map(({ label, val, unit, color, icon }) => (
              <div key={label} style={{ background: 'var(--bg-card)', borderRadius: 10, padding: '16px 20px', border: '1px solid var(--border-default)' }}>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>{icon} {label}</div>
                <div style={{ fontSize: 24, fontWeight: 800, color }}>{val}<span style={{ fontSize: 13, marginLeft: 4 }}>{unit}</span></div>
              </div>
            ))}
          </div>


          {/* 결과 탭 */}
          <div style={{ display: 'flex', gap: 4, marginBottom: 16 }}>
            {[
              { key: 'passed', label: `✅ 마진 통과 (${scanResult.passed})` },
              { key: 'filtered', label: `❌ 마진 미달 (${scanResult.filtered})` },
            ].map(t => (
              <button key={t.key} onClick={() => setTab(t.key)}
                style={{
                  padding: '8px 18px', borderRadius: 8, border: '1px solid',
                  borderColor: tab === t.key ? 'var(--accent-primary)' : 'var(--border-default)',
                  background: tab === t.key ? 'rgba(99,102,241,0.15)' : 'transparent',
                  color: tab === t.key ? 'var(--accent-primary)' : 'var(--text-secondary)',
                  cursor: 'pointer', fontSize: 13, fontWeight: 600, transition: 'all 0.2s'
                }}>{t.label}</button>
            ))}
          </div>

          {/* 결과 테이블 */}
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>상품명</th>
                  <th>카테고리</th>
                  <th>도매가</th>
                  <th>권장 판매가</th>
                  <th>순마진율</th>
                  <th>건당 순이익</th>
                  <th>등급</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {products.map(p => {
                  const m = p.margin
                  const rate = m?.net_margin_rate_pct ?? 0
                  const { g, color } = gradeLabel(rate)
                  const isExp = expandedId === p.source_id
                  return (
                    <>
                      <tr key={p.source_id}>
                        <td>
                          <a 
                            href={`https://ownerclan.com/V2/product/view.php?code=${p.source_id}`} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            style={{ fontWeight: 600, maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: 'var(--text-primary)', textDecoration: 'none', display: 'block' }}
                            onMouseEnter={e => e.target.style.textDecoration = 'underline'}
                            onMouseLeave={e => e.target.style.textDecoration = 'none'}
                          >
                            {p.name}
                          </a>
                          <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{p.brand}</div>
                        </td>
                        <td><span style={{ fontSize: 11, color: 'var(--accent-secondary)' }}>{p.source_category_name || p.source_category_code}</span></td>
                        <td>{p.wholesale_price?.toLocaleString()}원</td>
                        <td><strong style={{ color: 'var(--accent-primary)' }}>{m?.suggested_price?.toLocaleString()}원</strong></td>
                        <td><span style={{ color, fontWeight: 700 }}>{rate}%</span></td>
                        <td style={{ fontWeight: 600 }}>{m?.net_margin?.toLocaleString()}원</td>
                        <td>
                          <span style={{
                            display: 'inline-block', padding: '2px 10px', borderRadius: 12,
                            background: `${color}20`, color, fontWeight: 700, fontSize: 13
                          }}>{g}</span>
                        </td>
                        <td>
                          <div style={{ display: 'flex', gap: 6 }}>
                            <button className="btn btn-secondary btn-sm" onClick={() => setSimulatorProduct(p)}>시뮬레이터</button>
                            <button className="btn btn-secondary btn-sm" onClick={() => setExpandedId(isExp ? null : p.source_id)}>
                              {isExp ? '닫기' : '상세'}
                            </button>
                          </div>
                        </td>
                      </tr>
                      {isExp && (
                        <tr key={`${p.source_id}-d`}>
                          <td colSpan={8} style={{ padding: '8px 16px 16px', background: 'rgba(99,102,241,0.03)' }}>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                              <div>
                                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>마진 상세 분석</div>
                                {m && [
                                  ['판매가', m.sale_price, false],
                                  ['도매가', m.wholesale_price, true],
                                  [`쿠팡수수료 (${m.commission_rate_pct}%)`, m.commission_amount, true],
                                  ['부가세', m.vat_amount, true],
                                  ['반품비(예상)', m.estimated_return_cost, true],
                                ].map(([l, v, minus]) => (
                                  <div key={l} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, padding: '5px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                                    <span style={{ color: 'var(--text-muted)' }}>{l}</span>
                                    <span style={{ color: minus ? '#f87171' : 'var(--text-primary)' }}>{minus ? '-' : ''}{v?.toLocaleString()}원</span>
                                  </div>
                                ))}
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, padding: '8px 0', fontWeight: 700 }}>
                                  <span>순이익</span>
                                  <span style={{ color: (m?.net_margin ?? 0) >= 0 ? '#34d399' : '#f87171' }}>
                                    {(m?.net_margin ?? 0) >= 0 ? '+' : ''}{m?.net_margin?.toLocaleString()}원
                                  </span>
                                </div>
                              </div>
                              <div>
                                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>스펙 정보</div>
                                {Object.entries(p.specs || {}).map(([k, v]) => (
                                  <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, padding: '5px 0', borderBottom: '1px solid var(--border-subtle)' }}>
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
        <div style={{ textAlign: 'center', padding: '60px 24px', color: 'var(--text-muted)' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>🤖</div>
          <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 8 }}>자동 소싱 스캔 대기 중</div>
          <div style={{ fontSize: 13 }}>스캔 실행 시 오너클랜 신상품을 수집하고 마진 기준으로 자동 분류합니다</div>
        </div>
      )}

      {simulatorProduct && <MarginSimulator product={simulatorProduct} onClose={() => setSimulatorProduct(null)} />}
    </div>
  )
}

// ─── 트렌드 스캔 탭 ─────────────────────────────────────────────────────────
function TrendScanTab({ targetMargin }) {
  const [scanResult, setScanResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [tab, setTab] = useState('passed')
  const [expandedId, setExpandedId] = useState(null)
  const [simulatorProduct, setSimulatorProduct] = useState(null)
  const [categoryName, setCategoryName] = useState('전체')

  const products = scanResult
    ? (tab === 'passed' ? scanResult.passed_products : scanResult.filtered_products)
    : []

  async function runTrendScan() {
    setLoading(true)
    setScanResult(null)
    try {
      const resp = await fetch(
        `/api/sourcing/trend-scan?target_margin_pct=${targetMargin}&monthly_sales_estimate=500000&page_size=20&category_name=${encodeURIComponent(categoryName)}`,
        { method: 'POST' }
      )
      const text = await resp.text()
      let data
      try { data = JSON.parse(text) } catch { throw new Error(resp.ok ? 'Invalid JSON' : (text || `HTTP ${resp.status}`)) }
      if (!resp.ok) throw new Error(data.detail || data.message || '스캔 서버 오류')
      setScanResult(data)
    } catch (e) {
      alert('트렌드 스캔 오류: ' + e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div style={{
        display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap',
        padding: '20px', background: 'var(--bg-elevated)', borderRadius: 12, marginBottom: 20,
        border: '1px solid var(--border-default)'
      }}>
        <div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>관심 카테고리 (키워드 추출용)</div>
          <input 
            type="text" 
            value={categoryName} 
            onChange={e => setCategoryName(e.target.value)}
            style={{ padding: '8px 14px', background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 8, color: 'var(--text-primary)', fontSize: 14, width: 150 }}
          />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>트렌드 스캔 방식</div>
          <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            시즌 및 트렌드 기반으로 유입량이 높은 키워드를 자동 추출하여 오너클랜에서 유망 상품을 찾습니다 (데이터랩/AI 연동).
          </div>
        </div>
        <button
          onClick={runTrendScan} disabled={loading}
          style={{
            padding: '10px 28px', borderRadius: 10, border: 'none',
            background: loading ? 'var(--bg-elevated)' : 'linear-gradient(135deg, #10b981, #059669)',
            color: loading ? 'var(--text-muted)' : '#fff',
            fontWeight: 700, fontSize: 14, cursor: loading ? 'not-allowed' : 'pointer',
            display: 'flex', alignItems: 'center', gap: 8, transition: 'all 0.2s',
            boxShadow: loading ? 'none' : '0 4px 20px rgba(16,185,129,0.4)'
          }}
        >
          {loading ? (
            <><div style={{ width: 16, height: 16, border: '2px solid var(--text-muted)', borderTopColor: '#10b981', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />분석 중...</>
          ) : <>📈 트렌드 소싱 실행</>}
        </button>
      </div>

      {scanResult && (
        <>
          <div style={{ padding: '16px', background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)', borderRadius: 10, marginBottom: 20 }}>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 8, fontWeight: 600 }}>✨ 추출된 실시간 트렌드 키워드</div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {scanResult.keywords?.map(kw => (
                <span key={kw} style={{ padding: '6px 12px', background: '#fff', borderRadius: 20, fontSize: 13, fontWeight: 700, color: '#059669', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
                  #{kw}
                </span>
              ))}
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 20 }}>
            {[
              { label: '전체 검색', val: scanResult.total_scanned, unit: '건', color: 'var(--text-primary)', icon: '📊' },
              { label: '마진 통과', val: scanResult.passed, unit: '건', color: '#34d399', icon: '✅' },
              { label: '마진 미달', val: scanResult.filtered, unit: '건', color: '#f87171', icon: '❌' },
            ].map(({ label, val, unit, color, icon }) => (
              <div key={label} style={{ background: 'var(--bg-card)', borderRadius: 10, padding: '16px 20px', border: '1px solid var(--border-default)' }}>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>{icon} {label}</div>
                <div style={{ fontSize: 24, fontWeight: 800, color }}>{val}<span style={{ fontSize: 13, marginLeft: 4 }}>{unit}</span></div>
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', gap: 4, marginBottom: 16 }}>
            {[
              { key: 'passed', label: `✅ 마진 통과 (${scanResult.passed})` },
              { key: 'filtered', label: `❌ 마진 미달 (${scanResult.filtered})` },
            ].map(t => (
              <button key={t.key} onClick={() => setTab(t.key)}
                style={{
                  padding: '8px 18px', borderRadius: 8, border: '1px solid',
                  borderColor: tab === t.key ? 'var(--accent-primary)' : 'var(--border-default)',
                  background: tab === t.key ? 'rgba(99,102,241,0.15)' : 'transparent',
                  color: tab === t.key ? 'var(--accent-primary)' : 'var(--text-secondary)',
                  cursor: 'pointer', fontSize: 13, fontWeight: 600, transition: 'all 0.2s'
                }}>{t.label}</button>
            ))}
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>상품명 / 키워드</th>
                  <th>카테고리</th>
                  <th>도매가</th>
                  <th>권장 판매가</th>
                  <th>순마진율</th>
                  <th>건당 순이익</th>
                  <th>등급</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {products.map(p => {
                  const m = p.margin
                  const rate = m?.net_margin_rate_pct ?? 0
                  const { g, color } = gradeLabel(rate)
                  const isExp = expandedId === p.source_id
                  return (
                    <>
                      <tr key={p.source_id}>
                        <td>
                          <a 
                            href={`https://ownerclan.com/V2/product/view.php?code=${p.source_id}`} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            style={{ fontWeight: 600, maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: 'var(--text-primary)', textDecoration: 'none', display: 'block' }}
                            onMouseEnter={e => e.target.style.textDecoration = 'underline'}
                            onMouseLeave={e => e.target.style.textDecoration = 'none'}
                          >
                            {p.name}
                          </a>
                          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>검색어: <span style={{ color: '#10b981', fontWeight: 600 }}>{p.trend_keyword}</span></div>
                        </td>
                        <td><span style={{ fontSize: 11, color: 'var(--accent-secondary)' }}>{p.source_category_name || p.source_category_code}</span></td>
                        <td>{p.wholesale_price?.toLocaleString()}원</td>
                        <td><strong style={{ color: 'var(--accent-primary)' }}>{m?.suggested_price?.toLocaleString()}원</strong></td>
                        <td><span style={{ color, fontWeight: 700 }}>{rate}%</span></td>
                        <td style={{ fontWeight: 600 }}>{m?.net_margin?.toLocaleString()}원</td>
                        <td>
                          <span style={{
                            display: 'inline-block', padding: '2px 10px', borderRadius: 12,
                            background: `${color}20`, color, fontWeight: 700, fontSize: 13
                          }}>{g}</span>
                        </td>
                        <td>
                          <div style={{ display: 'flex', gap: 6 }}>
                            <button className="btn btn-secondary btn-sm" onClick={() => setSimulatorProduct(p)}>시뮬레이터</button>
                            <button className="btn btn-secondary btn-sm" onClick={() => setExpandedId(isExp ? null : p.source_id)}>
                              {isExp ? '닫기' : '상세'}
                            </button>
                          </div>
                        </td>
                      </tr>
                      {isExp && (
                        <tr key={`${p.source_id}-d`}>
                          <td colSpan={8} style={{ padding: '8px 16px 16px', background: 'rgba(99,102,241,0.03)' }}>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                              <div>
                                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>마진 상세 분석</div>
                                {m && [
                                  ['판매가', m.sale_price, false],
                                  ['도매가', m.wholesale_price, true],
                                  [`쿠팡수수료 (${m.commission_rate_pct}%)`, m.commission_amount, true],
                                  ['부가세', m.vat_amount, true],
                                  ['반품비(예상)', m.estimated_return_cost, true],
                                ].map(([l, v, minus]) => (
                                  <div key={l} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, padding: '5px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                                    <span style={{ color: 'var(--text-muted)' }}>{l}</span>
                                    <span style={{ color: minus ? '#f87171' : 'var(--text-primary)' }}>{minus ? '-' : ''}{v?.toLocaleString()}원</span>
                                  </div>
                                ))}
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, padding: '8px 0', fontWeight: 700 }}>
                                  <span>순이익</span>
                                  <span style={{ color: (m?.net_margin ?? 0) >= 0 ? '#34d399' : '#f87171' }}>
                                    {(m?.net_margin ?? 0) >= 0 ? '+' : ''}{m?.net_margin?.toLocaleString()}원
                                  </span>
                                </div>
                              </div>
                              <div>
                                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>스펙 정보</div>
                                {Object.entries(p.specs || {}).map(([k, v]) => (
                                  <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, padding: '5px 0', borderBottom: '1px solid var(--border-subtle)' }}>
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
        <div style={{ textAlign: 'center', padding: '60px 24px', color: 'var(--text-muted)' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>📈</div>
          <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 8 }}>실시간 트렌드 기반 소싱 대기 중</div>
          <div style={{ fontSize: 13 }}>네이버 데이터랩 및 AI가 분석한 검색 유입량이 가장 높은 키워드의 유망 상품을 찾아냅니다</div>
        </div>
      )}

      {simulatorProduct && <MarginSimulator product={simulatorProduct} onClose={() => setSimulatorProduct(null)} />}
    </div>
  )
}

// ─── 메인 컴포넌트 ────────────────────────────────────────────────────────────
export default function Sourcing() {
  const [activeTab, setActiveTab] = useState('browse')
  const [targetMargin, setTargetMargin] = useState(10)

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">🔍 소싱·마진 검증</h1>
        <p className="page-subtitle">카테고리 탐색으로 소싱 아이템을 발굴하고 실시간 마진을 검증하세요</p>
      </div>
      <div className="page-body">

        {/* 전역 마진 기준 설정 */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 20, padding: '14px 20px',
          background: 'var(--bg-card)', border: '1px solid var(--border-default)',
          borderRadius: 12, marginBottom: 24, flexWrap: 'wrap'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 13, color: 'var(--text-secondary)', fontWeight: 600, whiteSpace: 'nowrap' }}>📊 목표 마진율 기준:</span>
            <input
              type="range" min={5} max={40} value={targetMargin}
              onChange={e => setTargetMargin(Number(e.target.value))}
              style={{ width: 150, accentColor: 'var(--accent-primary)' }}
            />
            <span style={{ fontWeight: 800, color: 'var(--accent-primary)', fontSize: 18, minWidth: 45 }}>{targetMargin}%</span>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            {[10, 15, 20, 25].map(v => (
              <button key={v} onClick={() => setTargetMargin(v)}
                style={{
                  padding: '4px 12px', borderRadius: 16, border: '1px solid',
                  borderColor: targetMargin === v ? 'var(--accent-primary)' : 'var(--border-default)',
                  background: targetMargin === v ? 'rgba(99,102,241,0.15)' : 'transparent',
                  color: targetMargin === v ? 'var(--accent-primary)' : 'var(--text-muted)',
                  cursor: 'pointer', fontSize: 12, fontWeight: 600
                }}>{v}%</button>
            ))}
          </div>
          {/* 등급 안내 */}
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
            {[['S', '#a78bfa', '≥25%'], ['A', '#34d399', '≥20%'], ['B', '#60a5fa', '≥15%'], ['C', '#fbbf24', '≥10%'], ['F', '#f87171', '<10%']].map(([g, c, r]) => (
              <div key={g} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11 }}>
                <span style={{ width: 18, height: 18, borderRadius: 4, background: c, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, color: '#fff', fontSize: 11 }}>{g}</span>
                <span style={{ color: 'var(--text-muted)' }}>{r}</span>
              </div>
            ))}
          </div>
        </div>

        {/* 메인 탭 */}
        <div style={{ display: 'flex', gap: 4, marginBottom: 24 }}>
          {[
            { key: 'browse', label: '📂 카테고리 탐색 소싱', desc: '카테고리별 상품 브라우징' },
            { key: 'scan', label: '🤖 자동 스캔', desc: '마진 기준 일괄 분류' },
            { key: 'trend', label: '📈 실시간 트렌드 소싱', desc: '유입량 기반 유망 상품 발굴' },
          ].map(t => (
            <button key={t.key} onClick={() => setActiveTab(t.key)}
              style={{
                padding: '10px 22px', borderRadius: 10, border: '1px solid',
                borderColor: activeTab === t.key ? 'var(--accent-primary)' : 'var(--border-default)',
                background: activeTab === t.key ? 'rgba(99,102,241,0.12)' : 'var(--bg-card)',
                color: activeTab === t.key ? 'var(--accent-primary)' : 'var(--text-secondary)',
                cursor: 'pointer', fontWeight: 700, fontSize: 14, transition: 'all 0.2s',
                boxShadow: activeTab === t.key ? '0 0 0 1px rgba(99,102,241,0.3)' : 'none'
              }}
            >{t.label}</button>
          ))}
        </div>

        {/* 탭 컨텐츠 */}
        {activeTab === 'browse' && <BrowseTab targetMargin={targetMargin} />}
        {activeTab === 'scan' && <ScanTab targetMargin={targetMargin} />}
        {activeTab === 'trend' && <TrendScanTab targetMargin={targetMargin} />}

      </div>

      <style>{`
        @keyframes pulse { 0%, 100% { opacity: 1 } 50% { opacity: 0.4 } }
        @keyframes spin { to { transform: rotate(360deg) } }
      `}</style>
    </div>
  )
}
