import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';

interface Speaker {
  id: string;
  name: string;
  color: string;
}

interface Utterance {
  id: string;
  speaker_id: string;
  text: string;
  start_time: number;
  end_time: number;
  confidence: number;
}

interface AgendaItem {
  id: string;
  title: string;
  description: string;
  start_time: number;
  end_time: number;
}

interface MeetingDetailData {
  id: string;
  title: string;
  date: string;
  duration: string;
  status: 'completed' | 'processing' | 'error';
  speakers: Speaker[];
  utterances: Utterance[];
  agendas: AgendaItem[];
  summary: string;
  key_points: string[];
  action_items: string[];
  participants_analysis: Record<string, any>;
}

const MeetingDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [meeting, setMeeting] = useState<MeetingDetailData | null>(null);
  const [activeTab, setActiveTab] = useState<'transcript' | 'summary' | 'analysis'>('transcript');
  const [selectedSpeaker, setSelectedSpeaker] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // 데모 데이터
  useEffect(() => {
    // 실제로는 API 호출
    setTimeout(() => {
      setMeeting({
        id: id || '1',
        title: '2024년 1분기 팀 미팅',
        date: '2024-01-15',
        duration: '45분',
        status: 'completed',
        speakers: [
          { id: '1', name: '김팀장', color: '#007a5a' },
          { id: '2', name: '박개발자', color: '#1164a3' },
          { id: '3', name: '이디자이너', color: '#e01e5a' },
          { id: '4', name: '최기획자', color: '#ecb22e' }
        ],
        utterances: [
          {
            id: '1',
            speaker_id: '1',
            text: '안녕하세요, 오늘 1분기 팀 미팅을 시작하겠습니다. 먼저 프로젝트 진행 상황을 점검해보죠.',
            start_time: 0,
            end_time: 8.5,
            confidence: 0.95
          },
          {
            id: '2',
            speaker_id: '2',
            text: '네, 백엔드 API 개발은 거의 완료되었습니다. 현재 테스트를 진행 중이고, 이번 주 내에 완료 예정입니다.',
            start_time: 9.0,
            end_time: 18.2,
            confidence: 0.92
          },
          {
            id: '3',
            speaker_id: '3',
            text: 'UI 디자인은 80% 정도 완료되었어요. 사용자 피드백을 반영해서 몇 가지 수정사항이 있는데, 이 부분도 이번 주에 마무리하겠습니다.',
            start_time: 19.5,
            end_time: 32.1,
            confidence: 0.88
          },
          {
            id: '4',
            speaker_id: '4',
            text: '기획 문서 업데이트는 완료했습니다. 다음 분기 로드맵도 준비되어 있으니 검토 부탁드립니다.',
            start_time: 33.0,
            end_time: 42.8,
            confidence: 0.91
          }
        ],
        agendas: [
          {
            id: '1',
            title: '프로젝트 진행 상황 점검',
            description: '각 팀원별 작업 현황 공유',
            start_time: 0,
            end_time: 1200
          },
          {
            id: '2',
            title: '다음 분기 계획 수립',
            description: '2분기 목표 및 일정 논의',
            start_time: 1200,
            end_time: 2700
          }
        ],
        summary: '2024년 1분기 마지막 팀 미팅에서 각 팀원의 작업 진행 상황을 점검하고, 2분기 계획을 논의했습니다. 대부분의 작업이 계획대로 진행되고 있으며, 이번 주 내에 1분기 목표를 달성할 수 있을 것으로 예상됩니다.',
        key_points: [
          '백엔드 API 개발 거의 완료, 테스트 진행 중',
          'UI 디자인 80% 완료, 사용자 피드백 반영 중',
          '기획 문서 업데이트 완료',
          '2분기 로드맵 준비 완료'
        ],
        action_items: [
          '백엔드 API 테스트 완료 - 박개발자 (이번 주)',
          'UI 디자인 수정사항 적용 - 이디자이너 (이번 주)',
          '2분기 로드맵 검토 - 전 팀원 (다음 주)'
        ],
        participants_analysis: {
          '1': { speaking_time: 480, participation_rate: 0.35, keywords: ['프로젝트', '진행', '계획'] },
          '2': { speaking_time: 320, participation_rate: 0.25, keywords: ['API', '개발', '테스트'] },
          '3': { speaking_time: 280, participation_rate: 0.22, keywords: ['디자인', '피드백', '수정'] },
          '4': { speaking_time: 220, participation_rate: 0.18, keywords: ['기획', '문서', '로드맵'] }
        }
      });
      setIsLoading(false);
    }, 1000);
  }, [id]);

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '48px' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>⏳</div>
        <h2>회의록을 불러오는 중...</h2>
      </div>
    );
  }

  if (!meeting) {
    return (
      <div style={{ textAlign: 'center', padding: '48px' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>❌</div>
        <h2>회의록을 찾을 수 없습니다</h2>
        <Link to="/" className="btn btn-primary" style={{ marginTop: '16px' }}>
          대시보드로 돌아가기
        </Link>
      </div>
    );
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getSpeaker = (speakerId: string) => {
    return meeting.speakers.find(s => s.id === speakerId);
  };

  const filteredUtterances = selectedSpeaker 
    ? meeting.utterances.filter(u => u.speaker_id === selectedSpeaker)
    : meeting.utterances;

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      {/* 헤더 */}
      <div style={{ marginBottom: '32px' }}>
        <div style={{ marginBottom: '16px' }}>
          <Link to="/" style={{ color: 'var(--accent-primary)', textDecoration: 'none' }}>
            ← 대시보드로 돌아가기
          </Link>
        </div>
        
        <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '8px' }}>
          {meeting.title}
        </h1>
        
        <div style={{ 
          display: 'flex', 
          gap: '24px', 
          color: 'var(--text-secondary)',
          fontSize: '14px',
          marginBottom: '16px'
        }}>
          <span>📅 {meeting.date}</span>
          <span>⏱️ {meeting.duration}</span>
          <span>👥 {meeting.speakers.length}명 참여</span>
        </div>

        <div className="status-badge status-success">
          ✓ 분석 완료
        </div>
      </div>

      {/* 탭 네비게이션 */}
      <div style={{ 
        borderBottom: '1px solid var(--border-primary)', 
        marginBottom: '24px' 
      }}>
        <div style={{ display: 'flex', gap: '0' }}>
          {[
            { key: 'transcript', label: '전사록', icon: '📝' },
            { key: 'summary', label: '요약', icon: '📋' },
            { key: 'analysis', label: '분석', icon: '📊' }
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              style={{
                padding: '12px 16px',
                border: 'none',
                background: 'none',
                color: activeTab === tab.key ? 'var(--accent-primary)' : 'var(--text-secondary)',
                borderBottom: activeTab === tab.key ? '2px solid var(--accent-primary)' : '2px solid transparent',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: activeTab === tab.key ? 600 : 400,
                transition: 'all 0.2s ease'
              }}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* 전사록 탭 */}
      {activeTab === 'transcript' && (
        <div>
          {/* 화자 필터 */}
          <div className="card" style={{ marginBottom: '24px' }}>
            <div className="card-header">
              <h3 className="card-title">화자 필터</h3>
              <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                <button
                  onClick={() => setSelectedSpeaker(null)}
                  className={`btn btn-sm ${!selectedSpeaker ? 'btn-primary' : 'btn-secondary'}`}
                >
                  전체
                </button>
                {meeting.speakers.map(speaker => (
                  <button
                    key={speaker.id}
                    onClick={() => setSelectedSpeaker(speaker.id)}
                    className={`btn btn-sm ${selectedSpeaker === speaker.id ? 'btn-primary' : 'btn-secondary'}`}
                    style={{
                      backgroundColor: selectedSpeaker === speaker.id ? speaker.color : undefined
                    }}
                  >
                    {speaker.name}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* 발화 목록 */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">전사 내용</h3>
              <p className="card-description">
                {filteredUtterances.length}개의 발화 · 평균 신뢰도 {
                  (filteredUtterances.reduce((sum, u) => sum + u.confidence, 0) / filteredUtterances.length * 100).toFixed(1)
                }%
              </p>
            </div>

            <div style={{ marginTop: '16px' }}>
              {filteredUtterances.map(utterance => {
                const speaker = getSpeaker(utterance.speaker_id);
                return (
                  <div key={utterance.id} className="message">
                    <div 
                      className="message-avatar"
                      style={{ backgroundColor: speaker?.color }}
                    >
                      {speaker?.name.charAt(0)}
                    </div>
                    <div className="message-content">
                      <div className="message-header">
                        <span className="message-author">{speaker?.name}</span>
                        <span className="message-time">
                          {formatTime(utterance.start_time)} - {formatTime(utterance.end_time)}
                        </span>
                        <span 
                          className="status-badge"
                          style={{
                            backgroundColor: utterance.confidence > 0.9 ? 'var(--accent-success)' : 
                                           utterance.confidence > 0.8 ? 'var(--accent-warning)' : 'var(--accent-danger)',
                            color: 'white',
                            opacity: 0.8
                          }}
                        >
                          {(utterance.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="message-text">{utterance.text}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* 요약 탭 */}
      {activeTab === 'summary' && (
        <div>
          {/* 회의 요약 */}
          <div className="card" style={{ marginBottom: '24px' }}>
            <div className="card-header">
              <h3 className="card-title">회의 요약</h3>
            </div>
            <div style={{ marginTop: '16px', lineHeight: 1.6 }}>
              {meeting.summary}
            </div>
          </div>

          {/* 주요 포인트 */}
          <div className="card" style={{ marginBottom: '24px' }}>
            <div className="card-header">
              <h3 className="card-title">주요 포인트</h3>
            </div>
            <div style={{ marginTop: '16px' }}>
              {meeting.key_points.map((point, index) => (
                <div key={index} className="message">
                  <div className="message-avatar" style={{ backgroundColor: 'var(--accent-secondary)' }}>
                    {index + 1}
                  </div>
                  <div className="message-content">
                    <div className="message-text">{point}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 액션 아이템 */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">액션 아이템</h3>
            </div>
            <div style={{ marginTop: '16px' }}>
              {meeting.action_items.map((item, index) => (
                <div key={index} className="message">
                  <div className="message-avatar" style={{ backgroundColor: 'var(--accent-warning)' }}>
                    📋
                  </div>
                  <div className="message-content">
                    <div className="message-text">{item}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 분석 탭 */}
      {activeTab === 'analysis' && (
        <div>
          {/* 참여자 분석 */}
          <div className="card" style={{ marginBottom: '24px' }}>
            <div className="card-header">
              <h3 className="card-title">참여자 분석</h3>
            </div>
            <div style={{ marginTop: '16px' }}>
              {meeting.speakers.map(speaker => {
                const analysis = meeting.participants_analysis[speaker.id];
                return (
                  <div key={speaker.id} className="message">
                    <div 
                      className="message-avatar"
                      style={{ backgroundColor: speaker.color }}
                    >
                      {speaker.name.charAt(0)}
                    </div>
                    <div className="message-content">
                      <div className="message-header">
                        <span className="message-author">{speaker.name}</span>
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <span className="status-badge" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                            발화시간: {Math.floor(analysis.speaking_time / 60)}분 {analysis.speaking_time % 60}초
                          </span>
                          <span className="status-badge" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                            참여도: {(analysis.participation_rate * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                      <div className="message-text">
                        주요 키워드: {analysis.keywords.join(', ')}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 안건별 분석 */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">안건별 분석</h3>
            </div>
            <div style={{ marginTop: '16px' }}>
              {meeting.agendas.map(agenda => (
                <div key={agenda.id} className="message">
                  <div className="message-avatar" style={{ backgroundColor: 'var(--accent-primary)' }}>
                    📋
                  </div>
                  <div className="message-content">
                    <div className="message-header">
                      <span className="message-author">{agenda.title}</span>
                      <span className="message-time">
                        {formatTime(agenda.start_time)} - {formatTime(agenda.end_time)}
                      </span>
                    </div>
                    <div className="message-text">{agenda.description}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MeetingDetail;