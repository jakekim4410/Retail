export default function Settings() {
  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">⚙️ 시스템 설정</h1>
        <p className="page-subtitle">API 연동 키 및 자동화 정책 설정</p>
      </div>
      <div className="page-body">

        <div className="alert alert-info">
          💡 환경변수(.env) 기반으로 동작합니다. 실제 운영 시 백엔드 <code>.env</code> 파일에 값을 입력하고 서버를 재시작해야 적용됩니다.
        </div>

        <div className="grid-2">
          {/* API Keys */}
          <div className="card">
            <div className="card-title">🔑 외부 시스템 연동</div>
            
            <div className="form-group">
              <label className="form-label">오너클랜 API Key</label>
              <input type="password" placeholder="발급받은 오너클랜 API 키" className="form-input" disabled />
            </div>
            <div className="form-group">
              <label className="form-label">오너클랜 API Secret</label>
              <input type="password" placeholder="발급받은 오너클랜 시크릿" className="form-input" disabled />
            </div>
            
            <hr style={{ border: 0, borderBottom: '1px solid var(--border-subtle)', margin: '20px 0' }} />
            
            <div className="form-group">
              <label className="form-label">쿠팡 Access Key</label>
              <input type="password" placeholder="쿠팡 Open API Access Key" className="form-input" disabled />
            </div>
            <div className="form-group">
              <label className="form-label">쿠팡 Secret Key</label>
              <input type="password" placeholder="쿠팡 Open API Secret Key" className="form-input" disabled />
            </div>
            <div className="form-group">
              <label className="form-label">쿠팡 Vendor ID</label>
              <input type="text" placeholder="예: A00123456" className="form-input" disabled />
            </div>

            <hr style={{ border: 0, borderBottom: '1px solid var(--border-subtle)', margin: '20px 0' }} />

            <div className="form-group">
              <label className="form-label">Claude API Key (Anthropic)</label>
              <input type="password" placeholder="sk-ant-..." className="form-input" disabled />
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>※ 미입력 시 규칙 기반 템플릿으로 상품 설명이 자동 생성됩니다.</div>
            </div>
          </div>

          {/* 정책 설정 */}
          <div className="card">
            <div className="card-title">🤖 자동화 룰 정책</div>

            <div className="form-group">
              <label className="form-label">최저 목표 마진율 (%)</label>
              <input type="number" defaultValue={10} className="form-input" disabled />
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>소싱 시 마진율이 이 기준 미만이면 자동으로 필터링됩니다. (초기값: 10%)</div>
            </div>

            <div className="form-group">
              <label className="form-label">판매 부진 판단 기준일</label>
              <input type="number" defaultValue={14} className="form-input" disabled />
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>상품 등록 후 이 기간 동안 판매가 0건이면 "하차 후보"로 분류됩니다.</div>
            </div>

            <div className="form-group">
              <label className="form-label">Slack Webhook URL</label>
              <input type="text" placeholder="https://hooks.slack.com/services/..." className="form-input" disabled />
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>자동 하차 후보 및 마진 미달 알림을 받을 슬랙 채널 URL</div>
            </div>

            <div className="form-group" style={{ marginTop: 24, padding: 16, background: 'rgba(239,68,68,0.05)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 8 }}>
              <label className="form-label text-danger" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <input type="checkbox" disabled />
                가격 자동 조정 (위험)
              </label>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 4 }}>
                도매가가 올라 마진율이 미달될 때 쿠팡 판매가를 자동으로 올립니다. (오류 시 고객 클레임 위험이 있어 신중히 켜야 합니다)
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}
