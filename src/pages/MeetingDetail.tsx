import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useApi, PipelineResults } from '../context/ApiContext';
import AudioPlayer from '../components/Meeting/AudioPlayer';

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
  raw_results?: any;
  audio_file?: string; // 오디오 파일 URL 추가
}

const MeetingDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { 
    getPipelineResults, 
    getTranscript, 
    getAgentResults,
    getAgentStatus 
  } = useApi();
  const [meeting, setMeeting] = useState<MeetingDetailData | null>(null);
  const [activeTab, setActiveTab] = useState<'transcript' | 'summary' | 'analysis'>('transcript');
  const [selectedSpeaker, setSelectedSpeaker] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 컴포넌트 마운트 시 데이터 불러오기
  useEffect(() => {
    if (id) {
      loadMeetingData();
    }
  }, [id]);

  // 회의 데이터 불러오기
  const loadMeetingData = async () => {
    if (!id) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      // 먼저 트랜스크립트 정보 불러오기
      const transcript = await getTranscript(parseInt(id));
      console.log('트랜스크립트 데이터:', transcript);
      
      if (transcript) {
        // 기본 회의 정보 설정
        const basicMeetingData: MeetingDetailData = {
          id: id,
          title: transcript.title || `회의 ${id}`,
          date: transcript.date || new Date().toISOString().split('T')[0],
          duration: transcript.duration ? `${Math.floor(transcript.duration / 60)}분` : '분석됨',
          status: transcript.status || 'completed',
          speakers: [],
          utterances: [],
          agendas: [],
          summary: transcript.summary || '분석 완료',
          key_points: [],
          action_items: [],
          participants_analysis: {},
          raw_results: transcript,
          audio_file: transcript.audio_file || transcript.file_path || null // 오디오 파일 URL 설정
        };
        
        setMeeting(basicMeetingData);
        
        // 파이프라인 결과가 있다면 추가 데이터 로드
        if (transcript.job_id) {
          try {
            const pipelineResults = await getPipelineResults(transcript.job_id);
            const enhancedData = transformPipelineResults(pipelineResults);
            setMeeting(enhancedData);
          } catch (pipelineErr) {
            console.log('파이프라인 결과 없음, 기본 데이터만 사용');
          }
        }
      }
    } catch (err) {
      console.error('회의 데이터 불러오기 실패:', err);
      setError(err instanceof Error ? err.message : '데이터를 불러올 수 없습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  // 파이프라인 결과에서 MeetingDetailData로 변환
  const transformPipelineResults = (results: PipelineResults): MeetingDetailData => {
    const pipelineData = results.results;
    const transcript = pipelineData.transcript || {};
    const sttData = pipelineData.stt || {};
    const agentAnalysis = pipelineData.agent_analysis || {};
    
    // 화자 정보 생성
    const speakers: Speaker[] = [];
    const speakerStats = transcript.speaker_summary || {};
    Object.keys(speakerStats).forEach((speakerName, index) => {
      const colors = ['#007a5a', '#1164a3', '#e01e5a', '#ecb22e', '#36c5f0', '#2eb67d'];
      speakers.push({
        id: speakerName,
        name: speakerName,
        color: colors[index % colors.length]
      });
    });

    // 발화 정보 변환
    const utterances: Utterance[] = (sttData.segments || transcript.segments || []).map((segment: any, index: number) => ({
      id: index.toString(),
      speaker_id: segment.speaker || 'Unknown',
      text: segment.text || '',
      start_time: segment.start || 0,
      end_time: segment.end || 0,
      confidence: segment.confidence || 0
    }));

    // 아젠다 정보 변환
    const agendas: AgendaItem[] = (agentAnalysis.agendas?.agendas || []).map((agenda: any) => ({
      id: agenda.id?.toString() || '',
      title: agenda.title || '',
      description: agenda.description || '',
      start_time: 0,
      end_time: 0
    }));

    // 요약 및 주요 포인트
    const summaryData = agentAnalysis.summary || {};
    const executiveSummary = summaryData.executive_summary || {};
    
    return {
      id: results.job_id,
      title: pipelineData.validation?.file_name?.replace(/\.[^/.]+$/, '') || '회의 분석',
      date: new Date(results.completed_at || Date.now()).toISOString().split('T')[0],
      duration: transcript.metadata?.total_duration ? 
                Math.floor(transcript.metadata.total_duration / 60) + '분' : '분석됨',
      status: 'completed',
      speakers,
      utterances,
      agendas,
      summary: executiveSummary.executive_recommendation || 
               summaryData.detailed_analysis?.agenda_analysis ? 
               `총 ${summaryData.detailed_analysis.agenda_analysis.total_agendas}개 아젠다가 논의되었습니다.` : 
               '회의 분석이 완료되었습니다.',
      key_points: executiveSummary.key_outcomes || 
                 (agentAnalysis.agendas?.agendas || []).map((a: any) => a.title),
      action_items: summaryData.action_items?.map((item: any) => item.task) || [],
      participants_analysis: Object.fromEntries(
        speakers.map(speaker => [
          speaker.id,
          {
            speaking_time: speakerStats[speaker.name]?.total_duration || 0,
            participation_rate: speakerStats[speaker.name]?.utterance_count / utterances.length || 0,
            keywords: ['분석', '회의', '논의']
          }
        ])
      ),
      raw_results: pipelineData
    };
  };

  // 중복된 useEffect 제거 (위에서 loadMeetingData 함수로 대체됨)

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '48px' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>⏳</div>
        <h2>회의록을 불러오는 중...</h2>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ textAlign: 'center', padding: '48px' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>❌</div>
        <h2>오류가 발생했습니다</h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
          {error}
        </p>
        <Link to="/" className="btn btn-primary">
          대시보드로 돌아가기
        </Link>
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
          {/* 오디오 플레이어 */}
          {meeting.audio_file && (
            <div className="card" style={{ marginBottom: '24px' }}>
              <div className="card-header">
                <h3 className="card-title">🎵 오디오 재생</h3>
                <p className="card-description">회의 녹음 파일을 재생하고 탐색할 수 있습니다.</p>
              </div>
              <div style={{ marginTop: '16px' }}>
                <AudioPlayer
                  audioUrl={meeting.audio_file}
                  title={meeting.title}
                  onTimeUpdate={(currentTime, duration) => {
                    // 시간 업데이트 시 필요한 로직
                    console.log('현재 시간:', currentTime, '전체 길이:', duration);
                  }}
                />
              </div>
            </div>
          )}

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