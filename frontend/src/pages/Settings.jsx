import { useState, useEffect } from 'react'

const API = ''

function StatusBadge({ configured }) {
  return configured
    ? <span style={{ color: '#22c55e', fontWeight: 700, fontSize: 12 }}>✅ 연결됨</span>
    : <span style={{ color: '#ef4444', fontWeight: 700, fontSize: 12 }}>❌ 미설정</span>
}

export default function Settings() {
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API}/api/settings/status`)
      .then(r => r.json())
      .then(d => { setStatus(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">⚙️ 시스템 설정</h1>
        <p className="page-subtitle">API 연동 키 및 자동화 정책 설정</p>
      </div>
      <div className="page-body">

        {/* 연동 상태 카드 */}
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-title">🔌 실시간 연동 현황</div>
          {loading ? (
            <div style={{ color: 'var(--text-muted)' }}>확인 중...</div>
          ) : !status ? (
            <div style={{ color: '#ef4444' }}>백엔드에 연결할 수 없습니다. Render 서버 상태를 확인해 주세요.</div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginTop: 12 }}>
              <div style={{ padding: 16, background: 'var(--surface-secondary)', borderRadius: 8 }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>오너클랜</div>
                <StatusBadge configured={status.ownerclan?.configured} />
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>소싱 API (ID/PW 방식)</div>
              </div>
              <div style={{ padding: 16, background: 'var(--surface-secondary)', borderRadius: 8 }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>쿠팡 Open API</div>
                <StatusBadge configured={status.coupang?.configured} />
                {status.coupang?.vendor_id && (
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>Vendor: {status.coupang.vendor_id}</div>
                )}
              </div>
              <div style={{ padding: 16, background: 'var(--surface-secondary)', borderRadius: 8 }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>Gemini (Google)</div>
                <StatusBadge configured={status.gemini?.configured} />
                {status.gemini?.configured && (
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>{status.gemini.model}</div>
                )}
              </div>
              <div style={{ padding: 16, background: 'var(--surface-secondary)', borderRadius: 8 }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>Slack 알림</div>
                <StatusBadge configured={status.slack?.configured} />
              </div>
            </div>
          )}
          {status && (
            <div style={{
              marginTop: 16, padding: '8px 12px',
              background: 'rgba(34,197,94,0.1)',
              border: '1px solid rgba(34,197,94,0.3)',
              borderRadius: 8, fontSize: 12,
              color: '#22c55e'
            }}>
              ✅ 실제 API 모드로 실행 중입니다. (로친 전용)
            </div>
          )}
        </div>

        <div className="grid-2">
          {/* API Keys 설정 가이드 */}
          <div className="card">
            <div className="card-title">🔑 Render 환경변수 설정 가이드</div>

            <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.8, marginBottom: 16 }}>
              API 키는 보안을 위해 Render 대시보드 → Environment에서 직접 설정합니다.
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {[
                { label: '오너클랜 판매사 ID', key: 'OWNERCLAN_USERNAME', example: '오너클랜 로그인 아이디' },
                { label: '오너클랜 비밀번호', key: 'OWNERCLAN_PASSWORD', example: '오너클랜 로그인 비밀번호' },
                { label: '쿠팡 Vendor ID', key: 'COUPANG_VENDOR_ID', example: 'A00123456' },
                { label: '쿠팡 Access Key', key: 'COUPANG_ACCESS_KEY', example: 'coupang에서 발급받은 키' },
                { label: '쿠팡 Secret Key', key: 'COUPANG_SECRET_KEY', example: 'coupang에서 발급받은 시크릿' },
                { label: 'Gemini API Key', key: 'GEMINI_API_KEY', example: 'AIzaSy...' },
                { label: 'Slack Webhook URL', key: 'SLACK_WEBHOOK_URL', example: 'https://hooks.slack.com/...' },
                { label: '네이버 데이터랩 Client ID', key: 'NAVER_CLIENT_ID', example: '네이버 개발자센터 발급' },
                { label: '네이버 데이터랩 Secret', key: 'NAVER_CLIENT_SECRET', example: '네이버 개발자센터 발급' },
              ].map(({ label, key, example }) => (
                <div key={key} style={{ padding: '10px 12px', background: 'var(--surface-secondary)', borderRadius: 8 }}>
                  <div style={{ fontSize: 12, color: 'var(--text-primary)', fontWeight: 600, marginBottom: 4 }}>{label}</div>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <code style={{ fontSize: 11, padding: '2px 6px', background: 'rgba(139,92,246,0.15)', borderRadius: 4, color: 'var(--accent-primary)' }}>{key}</code>
                    <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{example}</span>
                  </div>
                </div>
              ))}
            </div>

            <a
              href="https://dashboard.render.com"
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-primary"
              style={{ marginTop: 16, display: 'inline-block', textDecoration: 'none', textAlign: 'center' }}
            >
              🚀 Render 환경변수 설정하러 가기
            </a>
          </div>

          {/* 자동화 정책 */}
          <div className="card">
            <div className="card-title">🤖 현재 자동화 정책 (Render에서 수정)</div>

            {status?.policy && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <div style={{ padding: 16, background: 'var(--surface-secondary)', borderRadius: 8 }}>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>최저 목표 마진율</div>
                  <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--accent-primary)' }}>
                    {status.policy.margin_threshold_percent}%
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                    이 기준 미만 상품은 자동 필터링 · Render에서 MARGIN_THRESHOLD_PERCENT 수정
                  </div>
                </div>

                <div style={{ padding: 16, background: 'var(--surface-secondary)', borderRadius: 8 }}>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>판매 부진 기준일</div>
                  <div style={{ fontSize: 28, fontWeight: 800, color: '#f59e0b' }}>
                    {status.policy.poor_sales_days}일
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                    이 기간 판매 0건 → 하차 후보 · Render에서 POOR_SALES_DAYS 수정
                  </div>
                </div>

                <div style={{ padding: 16, background: 'rgba(239,68,68,0.05)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 8 }}>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>⚠️ 자동 스케줄</div>
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.8 }}>
                    • 매일 오전 6시 — 쿠팡 주문 수집<br/>
                    • 매일 오전 7시 — 최적화 루프 (하차/가격조정)<br/>
                    • 매주 월요일 — Slack 주간 보고
                  </div>
                </div>
              </div>
            )}

            <div style={{ marginTop: 20, padding: 14, background: 'rgba(139,92,246,0.06)', borderRadius: 8, border: '1px solid rgba(139,92,246,0.15)' }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--accent-primary)', marginBottom: 8 }}>📋 쿠팡 Open API 발급 방법</div>
              <ol style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.9, paddingLeft: 16, margin: 0 }}>
                <li>쿠팡 Wing 판매자 센터 로그인</li>
                <li>상단 메뉴 → 계정정보 → Open API 키 관리</li>
                <li>Vendor ID / Access Key / Secret Key 복사</li>
                <li>Render 환경변수에 붙여넣기</li>
              </ol>
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}
