import React, { useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useApi } from '../context/ApiContext';

interface Meeting {
  id: string;
  title: string;
  date: string;
  duration: string;
  speakers: number;
  status: 'completed' | 'processing' | 'error';
  summary?: string;
}

const Dashboard: React.FC = () => {
  const { uploadAudio, isLoading, error } = useApi();
  const [dragActive, setDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [showMetadata, setShowMetadata] = useState(false);
  const [metadataQuery, setMetadataQuery] = useState('');
  const [queryResults, setQueryResults] = useState<string>('');

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  }, []);

  const handleFiles = async (files: FileList) => {
    const file = files[0];
    if (!file) return;

    // 오디오/비디오 파일 검증
    const supportedTypes = [
      'audio/mpeg', 'audio/wav', 'audio/mp3', 'audio/m4a',
      'video/mp4', 'video/avi', 'video/mov'
    ];

    if (!supportedTypes.some(type => file.type.includes(type.split('/')[1]))) {
      alert('지원되지 않는 파일 형식입니다. MP3, WAV, M4A, MP4, AVI, MOV 파일을 업로드해주세요.');
      return;
    }

    // 파일 크기 검증 (100MB 제한)
    const maxSize = 100 * 1024 * 1024; // 100MB
    if (file.size > maxSize) {
      alert('파일 크기가 너무 큽니다. 100MB 이하의 파일을 업로드해주세요.');
      return;
    }

    try {
      // 진행률 표시 시작
      setUploadProgress(0);
      
      // 임시 회의 추가 (업로드 중 표시)
      const tempMeeting: Meeting = {
        id: `temp-${Date.now()}`,
        title: file.name.replace(/\.[^/.]+$/, ''),
        date: new Date().toISOString().split('T')[0],
        duration: '업로드 중...',
        speakers: 0,
        status: 'processing',
        summary: '파일 업로드 중...'
      };
      setMeetings(prev => [tempMeeting, ...prev]);

      // 실제 API 호출
      const result = await uploadAudio(file, (progress) => {
        setUploadProgress(progress);
      });

      // 업로드 완료 후 회의 정보 업데이트
      setMeetings(prev => prev.map(meeting => 
        meeting.id === tempMeeting.id 
          ? {
              ...meeting,
              id: result.file_id?.toString() || meeting.id,
              duration: '처리 중...',
              summary: '음성 변환 및 분석 중...'
            }
          : meeting
      ));
      
      setTimeout(() => setUploadProgress(null), 1000);
      
    } catch (err) {
      console.error('파일 업로드 실패:', err);
      alert(`파일 업로드에 실패했습니다: ${err instanceof Error ? err.message : '알 수 없는 오류'}`);
      
      // 임시 회의 제거
      setMeetings(prev => prev.filter(meeting => !meeting.id.startsWith('temp-')));
      setUploadProgress(null);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(e.target.files);
    }
  };

  const handleMetadataQuery = async () => {
    if (!metadataQuery.trim()) {
      setQueryResults('검색어를 입력해주세요.');
      return;
    }

    setQueryResults('검색 중...');
    
    // 시뮬레이션된 메타데이터 검색 결과
    setTimeout(() => {
      if (meetings.length === 0) {
        setQueryResults('아직 업로드된 회의가 없어 검색할 데이터가 없습니다. 먼저 회의 파일을 업로드해주세요.');
      } else {
        setQueryResults(`"${metadataQuery}"에 대한 메타데이터 검색 결과:\n\n검색 기능은 실제 회의 데이터가 업로드된 후 사용 가능합니다. 현재는 데모 모드입니다.`);
      }
    }, 1000);
  };

  const getStatusBadge = (status: Meeting['status']) => {
    switch (status) {
      case 'completed':
        return <span className="status-badge status-success">완료</span>;
      case 'processing':
        return <span className="status-badge status-warning">처리 중</span>;
      case 'error':
        return <span className="status-badge status-danger">오류</span>;
      default:
        return null;
    }
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      {/* 헤더 섹션 */}
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '8px' }}>
          Meeting AI Dashboard
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '16px' }}>
          회의 음성을 업로드하여 자동으로 전사하고 분석해보세요.
        </p>
      </div>

      {/* 파일 업로드 영역 */}
      <div className="card" style={{ marginBottom: '32px' }}>
        <div className="card-header">
          <h2 className="card-title">새 회의 업로드</h2>
          <p className="card-description">
            오디오 또는 비디오 파일을 드래그하거나 클릭하여 업로드하세요.
          </p>
        </div>

        <div
          className={`dropzone ${dragActive ? 'active' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => document.getElementById('fileInput')?.click()}
        >
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>📁</div>
            <h3 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '8px' }}>
              파일을 여기에 드래그하세요
            </h3>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>
              또는 클릭하여 파일을 선택하세요
            </p>
            <div style={{ fontSize: '14px', color: 'var(--text-muted)' }}>
              지원 형식: MP3, WAV, M4A, MP4, AVI, MOV (최대 100MB)
            </div>
          </div>

          <input
            id="fileInput"
            type="file"
            accept="audio/*,video/*"
            onChange={handleFileInput}
            style={{ display: 'none' }}
          />
        </div>

        {/* 에러 메시지 */}
        {error && (
          <div style={{ 
            marginTop: '16px', 
            padding: '12px',
            backgroundColor: '#fee2e2',
            color: '#dc2626',
            borderRadius: '4px',
            border: '1px solid #fca5a5'
          }}>
            ❌ {error}
          </div>
        )}

        {/* 업로드 진행률 */}
        {uploadProgress !== null && (
          <div style={{ marginTop: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span>업로드 중...</span>
              <span>{uploadProgress}%</span>
            </div>
            <div style={{ 
              width: '100%', 
              height: '8px', 
              backgroundColor: 'var(--bg-tertiary)', 
              borderRadius: '4px',
              overflow: 'hidden'
            }}>
              <div
                style={{
                  width: `${uploadProgress}%`,
                  height: '100%',
                  backgroundColor: 'var(--accent-primary)',
                  transition: 'width 0.2s ease'
                }}
              />
            </div>
          </div>
        )}
      </div>

      {/* 통계 카드들 */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
        gap: '16px',
        marginBottom: '32px'
      }}>
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">총 회의</h3>
            <div style={{ fontSize: '32px', fontWeight: 700, color: 'var(--accent-primary)' }}>
              {meetings.length}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">완료됨</h3>
            <div style={{ fontSize: '32px', fontWeight: 700, color: 'var(--accent-success)' }}>
              {meetings.filter(m => m.status === 'completed').length}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">처리 중</h3>
            <div style={{ fontSize: '32px', fontWeight: 700, color: 'var(--accent-warning)' }}>
              {meetings.filter(m => m.status === 'processing').length}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">메타데이터</h3>
            <button 
              onClick={() => setShowMetadata(!showMetadata)}
              style={{ 
                fontSize: '14px', 
                padding: '8px 16px',
                backgroundColor: 'var(--accent-primary)',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              {showMetadata ? '숨기기' : '보기'}
            </button>
          </div>
        </div>
      </div>

      {/* 메타데이터 정보 */}
      {showMetadata && (
        <div className="card" style={{ marginBottom: '32px' }}>
          <div className="card-header">
            <h2 className="card-title">메타데이터 정보</h2>
            <p className="card-description">
              회의 분석에서 추출되는 메타데이터에 대한 설명입니다.
            </p>
          </div>
          <div style={{ marginTop: '16px', lineHeight: '1.6' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '12px' }}>추출되는 메타데이터:</h3>
            <ul style={{ paddingLeft: '20px', color: 'var(--text-secondary)' }}>
              <li><strong>회의 제목:</strong> 파일명 또는 자동 생성된 제목</li>
              <li><strong>날짜 및 시간:</strong> 업로드 시간 또는 파일 생성 시간</li>
              <li><strong>지속 시간:</strong> 오디오/비디오 파일의 총 재생 시간</li>
              <li><strong>참석자 수:</strong> 음성 인식을 통한 화자 구분 결과</li>
              <li><strong>키워드:</strong> 회의 내용에서 추출된 주요 키워드</li>
              <li><strong>요약:</strong> AI가 생성한 회의 내용 요약</li>
              <li><strong>감정 분석:</strong> 대화의 전반적인 톤과 감정 상태</li>
              <li><strong>액션 아이템:</strong> 회의에서 결정된 할 일과 책임자</li>
            </ul>
            
            <div style={{ marginTop: '24px', padding: '16px', backgroundColor: 'var(--bg-secondary)', borderRadius: '8px' }}>
              <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px' }}>메타데이터 검색</h4>
              <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
                <input
                  type="text"
                  placeholder="키워드, 날짜, 참석자 등으로 검색..."
                  value={metadataQuery}
                  onChange={(e) => setMetadataQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleMetadataQuery()}
                  style={{
                    flex: 1,
                    padding: '8px 12px',
                    border: '1px solid var(--border-primary)',
                    borderRadius: '4px',
                    backgroundColor: 'var(--bg-primary)',
                    color: 'var(--text-primary)'
                  }}
                />
                <button
                  onClick={handleMetadataQuery}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: 'var(--accent-primary)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  검색
                </button>
              </div>
              
              {queryResults && (
                <div style={{
                  padding: '12px',
                  backgroundColor: 'var(--bg-primary)',
                  borderRadius: '4px',
                  border: '1px solid var(--border-primary)',
                  fontSize: '14px',
                  color: 'var(--text-secondary)',
                  whiteSpace: 'pre-line'
                }}>
                  {queryResults}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 최근 회의록 목록 */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">최근 회의록</h2>
          <p className="card-description">
            업로드된 회의록을 확인하고 상세 분석 결과를 확인하세요.
          </p>
        </div>

        <div style={{ marginTop: '16px' }}>
          {meetings.length === 0 ? (
            <div style={{ 
              textAlign: 'center', 
              padding: '48px', 
              color: 'var(--text-secondary)' 
            }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>📝</div>
              <h3>아직 업로드된 회의가 없습니다</h3>
              <p>위의 업로드 영역을 사용하여 첫 번째 회의를 업로드해보세요.</p>
            </div>
          ) : (
            <div>
              {meetings.map((meeting, index) => (
                <div key={meeting.id} className="message" style={{ marginBottom: '8px' }}>
                  <div className="message-avatar">
                    {meeting.status === 'completed' ? '✅' : 
                     meeting.status === 'processing' ? '⏳' : '❌'}
                  </div>
                  <div className="message-content">
                    <div className="message-header">
                      <Link 
                        to={`/meeting/${meeting.id}`}
                        className="message-author"
                        style={{ textDecoration: 'none', color: 'var(--text-primary)' }}
                      >
                        {meeting.title}
                      </Link>
                      <div className="message-time">{meeting.date}</div>
                      {getStatusBadge(meeting.status)}
                    </div>
                    <div className="message-text">
                      {meeting.summary}
                    </div>
                    <div style={{ 
                      marginTop: '8px', 
                      display: 'flex', 
                      gap: '16px', 
                      fontSize: '12px',
                      color: 'var(--text-muted)'
                    }}>
                      <span>⏱️ {meeting.duration}</span>
                      <span>👥 {meeting.speakers}명</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;