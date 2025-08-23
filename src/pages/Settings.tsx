import React, { useState, useEffect } from 'react';
import { useApi } from '../context/ApiContext';
import { useSettings } from '../context/SettingsContext';

const Settings: React.FC = () => {
  const { apiKeys, saveApiKey, loadApiKeys, removeApiKey, testApiKey, isLoading, error } = useApi();
  const { sttEngine, setSttEngine, language, setLanguage, sttEngines, loadSTTEngines, validateEngine } = useSettings();

  // API 키 입력 상태
  const [newApiKeys, setNewApiKeys] = useState<Record<string, string>>({});
  const [testResults, setTestResults] = useState<Record<string, boolean | null>>({});
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['api-keys']));

  // 지원하는 API 프로바이더
  const apiProviders = [
    { name: 'openai', label: 'OpenAI', description: 'GPT 모델 및 Whisper STT' },
    { name: 'upstage', label: 'Upstage', description: '임베딩 및 LLM 모델', supportsMultiple: true, maxKeys: 8 },
    { name: 'returnzero', label: 'ReturnZero', description: 'STT 서비스' },
    { name: 'notion', label: 'Notion', description: 'Notion 페이지 연동' },
    { name: 'github', label: 'GitHub', description: 'GitHub 저장소 연동' },
  ];

  const languages = [
    { code: 'ko', name: '한국어' },
    { code: 'en', name: 'English' },
    { code: 'ja', name: '日本語' },
    { code: 'zh', name: '中文' },
  ];

  useEffect(() => {
    loadApiKeys();
    loadSTTEngines();
  }, []);

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const handleApiKeyChange = (provider: string, value: string) => {
    setNewApiKeys(prev => ({ ...prev, [provider]: value }));
  };

  const handleSaveApiKey = async (provider: string, index?: number) => {
    const key = newApiKeys[provider];
    if (!key?.trim()) return;

    try {
      await saveApiKey(provider, key, index);
      setNewApiKeys(prev => ({ ...prev, [provider]: '' }));
      setTestResults(prev => ({ ...prev, [`${provider}_${index || 0}`]: null }));
    } catch (error) {
      console.error('API 키 저장 실패:', error);
    }
  };

  const handleTestApiKey = async (provider: string) => {
    const key = newApiKeys[provider];
    if (!key?.trim()) return;

    const testKey = `${provider}_test`;
    setTestResults(prev => ({ ...prev, [testKey]: null }));

    try {
      const isValid = await testApiKey(provider, key);
      setTestResults(prev => ({ ...prev, [testKey]: isValid }));
    } catch (error) {
      setTestResults(prev => ({ ...prev, [testKey]: false }));
    }
  };

  const handleRemoveApiKey = async (provider: string, index?: number) => {
    if (window.confirm('이 API 키를 삭제하시겠습니까?')) {
      try {
        await removeApiKey(provider, index);
      } catch (error) {
        console.error('API 키 삭제 실패:', error);
      }
    }
  };

  const renderApiKeySection = (provider: any) => {
    const existingKeys = apiKeys.filter(key => key.provider === provider.name);
    const maxKeys = provider.supportsMultiple ? provider.maxKeys : 1;

    return (
      <div key={provider.name} className="card" style={{ marginBottom: '16px' }}>
        <div className="card-header">
          <h4 className="card-title">{provider.label}</h4>
          <p className="card-description">{provider.description}</p>
        </div>

        {/* 기존 API 키 목록 */}
        {existingKeys.length > 0 && (
          <div style={{ marginBottom: '16px' }}>
            <h5 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px', color: 'var(--text-secondary)' }}>
              저장된 키
            </h5>
            {existingKeys.map((apiKey, idx) => (
              <div key={idx} className="message" style={{ padding: '8px', backgroundColor: 'var(--bg-tertiary)', borderRadius: '6px', marginBottom: '8px' }}>
                <div className="message-content">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontFamily: 'monospace', fontSize: '12px' }}>{apiKey.masked_value}</span>
                    <button
                      onClick={() => handleRemoveApiKey(provider.name, apiKey.index)}
                      className="btn btn-sm btn-danger"
                      disabled={isLoading}
                    >
                      삭제
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 새 API 키 추가 */}
        {existingKeys.length < maxKeys && (
          <div>
            <h5 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px', color: 'var(--text-secondary)' }}>
              새 키 추가
            </h5>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <input
                type="password"
                className="input"
                placeholder={`${provider.label} API 키를 입력하세요`}
                value={newApiKeys[provider.name] || ''}
                onChange={(e) => handleApiKeyChange(provider.name, e.target.value)}
                style={{ flex: 1 }}
              />
              <button
                onClick={() => handleTestApiKey(provider.name)}
                className="btn btn-secondary btn-sm"
                disabled={isLoading || !newApiKeys[provider.name]?.trim()}
              >
                테스트
              </button>
              <button
                onClick={() => handleSaveApiKey(provider.name, existingKeys.length)}
                className="btn btn-primary btn-sm"
                disabled={isLoading || !newApiKeys[provider.name]?.trim()}
              >
                저장
              </button>
            </div>

            {/* 테스트 결과 */}
            {testResults[`${provider.name}_test`] !== undefined && (
              <div style={{ marginTop: '8px' }}>
                {testResults[`${provider.name}_test`] ? (
                  <div className="status-badge status-success">✓ 유효한 API 키입니다</div>
                ) : (
                  <div className="status-badge status-danger">✗ 유효하지 않은 API 키입니다</div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '8px' }}>설정</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '16px' }}>
          API 키를 관리하고 애플리케이션 설정을 조정하세요.
        </p>
      </div>

      {error && (
        <div className="card" style={{ backgroundColor: 'var(--accent-danger)', color: 'white', marginBottom: '16px' }}>
          <div className="card-header">
            <strong>오류:</strong> {error}
          </div>
        </div>
      )}

      {/* API 키 관리 섹션 */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div 
          className="card-header" 
          style={{ cursor: 'pointer' }}
          onClick={() => toggleSection('api-keys')}
        >
          <h2 className="card-title">
            API 키 관리 {expandedSections.has('api-keys') ? '▼' : '▶'}
          </h2>
          <p className="card-description">
            외부 서비스 연동을 위한 API 키를 관리합니다.
          </p>
        </div>

        {expandedSections.has('api-keys') && (
          <div style={{ marginTop: '16px' }}>
            {apiProviders.map(provider => renderApiKeySection(provider))}
          </div>
        )}
      </div>

      {/* STT 엔진 설정 */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div 
          className="card-header"
          style={{ cursor: 'pointer' }}
          onClick={() => toggleSection('stt')}
        >
          <h2 className="card-title">
            STT 엔진 설정 {expandedSections.has('stt') ? '▼' : '▶'}
          </h2>
          <p className="card-description">
            음성 인식 엔진 및 언어 설정을 관리합니다.
          </p>
        </div>

        {expandedSections.has('stt') && (
          <div style={{ marginTop: '16px' }}>
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontWeight: 600, marginBottom: '8px' }}>
                STT 엔진
              </label>
              <select
                className="input"
                value={sttEngine}
                onChange={(e) => setSttEngine(e.target.value)}
              >
                {Object.entries(sttEngines).map(([key, engine]) => (
                  <option key={key} value={key} disabled={!engine.available}>
                    {engine.name} {!engine.available && '(사용 불가)'}
                  </option>
                ))}
              </select>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontWeight: 600, marginBottom: '8px' }}>
                기본 언어
              </label>
              <select
                className="input"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              >
                {languages.map(lang => (
                  <option key={lang.code} value={lang.code}>
                    {lang.name}
                  </option>
                ))}
              </select>
            </div>

            {/* 선택된 엔진 정보 */}
            {sttEngines[sttEngine] && (
              <div className="card" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                <div className="card-header">
                  <h4 className="card-title">{sttEngines[sttEngine].name}</h4>
                  <p className="card-description">{sttEngines[sttEngine].description}</p>
                </div>
                {sttEngines[sttEngine].features && (
                  <div>
                    <strong>지원 기능:</strong>
                    <ul style={{ marginLeft: '20px', marginTop: '4px' }}>
                      {sttEngines[sttEngine].features?.map((feature, idx) => (
                        <li key={idx}>{feature}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* 시스템 정보 */}
      <div className="card">
        <div 
          className="card-header"
          style={{ cursor: 'pointer' }}
          onClick={() => toggleSection('system')}
        >
          <h2 className="card-title">
            시스템 정보 {expandedSections.has('system') ? '▼' : '▶'}
          </h2>
          <p className="card-description">
            애플리케이션 및 시스템 상태를 확인합니다.
          </p>
        </div>

        {expandedSections.has('system') && (
          <div style={{ marginTop: '16px' }}>
            <div className="message">
              <div className="message-content">
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>API 서버 상태:</span>
                  <span className="status-badge status-success">연결됨</span>
                </div>
              </div>
            </div>
            <div className="message">
              <div className="message-content">
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>설정된 API 키:</span>
                  <span>{apiKeys.length}개</span>
                </div>
              </div>
            </div>
            <div className="message">
              <div className="message-content">
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>현재 STT 엔진:</span>
                  <span>{sttEngines[sttEngine]?.name || sttEngine}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Settings;