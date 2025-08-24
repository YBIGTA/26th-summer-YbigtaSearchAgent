import React, { useState, useCallback, useRef } from 'react';
import { useApi } from '../context/ApiContext';
import { Meeting } from '../types/electron';

const Upload: React.FC = () => {
  const { uploadFile, getPipelineStatus, getPipelineResults } = useApi();
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [activePolling, setActivePolling] = useState<Set<string>>(new Set());
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 파일 업로드 처리
  const handleFileUpload = useCallback(async (file: File) => {
    if (!file) return;

    setIsUploading(true);
    setUploadProgress(0);

    try {
      // 파일 업로드
      const result = await uploadFile(file);
      
      if (result.success) {
        // 새 회의 추가
        const newMeeting: Meeting = {
          id: result.job_id,
          title: file.name,
          status: 'processing',
          progress: 0,
          current_stage: 'uploading',
          summary: '파일 업로드 완료, 분석 시작 중...',
          created_at: new Date().toISOString(),
          file_path: file.name,
          file_size: file.size,
          pipeline_results: null
        };

        setMeetings(prev => [newMeeting, ...prev]);
        
        // 파이프라인 상태 폴링 시작
        setActivePolling(prev => new Set(prev).add(result.job_id));
        pollPipelineStatus(result.job_id, result.job_id);
        
        // 파일 입력 초기화
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      } else {
        alert(`업로드 실패: ${result.error}`);
      }
    } catch (error) {
      console.error('파일 업로드 오류:', error);
      alert('파일 업로드 중 오류가 발생했습니다.');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  }, [uploadFile]);

  // 파일 드래그 앤 드롭 처리
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  }, [handleFileUpload]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
  }, []);

  // 파이프라인 상태 폴링
  const pollPipelineStatus = useCallback(async (jobId: string, meetingId: string) => {
    if (!activePolling.has(jobId)) return;

    try {
      const status = await getPipelineStatus(jobId);
      
      setMeetings(prev => prev.map(meeting => 
        meeting.id === meetingId 
          ? {
              ...meeting,
              progress: status.progress,
              current_stage: status.current_stage,
              status: status.status === 'completed' ? 'completed' : 
                     status.status === 'failed' ? 'error' : 'processing',
              error_message: status.error,
              summary: status.status === 'completed' ? '분석 완료!' :
                      status.status === 'failed' ? `오류: ${status.error}` :
                      getStageMessage(status.current_stage, status.progress)
            }
          : meeting
      ));

      // 파이프라인 완료 시 결과 조회
      if (status.status === 'completed') {
        try {
          const results = await getPipelineResults(jobId);
          if (results) {
            setMeetings(prev => prev.map(meeting => 
              meeting.id === meetingId 
                ? { ...meeting, pipeline_results: results }
                : meeting
            ));
          }
        } catch (error) {
          console.error('파이프라인 결과 조회 오류:', error);
        }
        
        // 폴링 중지
        setActivePolling(prev => {
          const newSet = new Set(prev);
          newSet.delete(jobId);
          return newSet;
        });
      } else if (status.status === 'failed') {
        // 폴링 중지
        setActivePolling(prev => {
          const newSet = new Set(prev);
          newSet.delete(jobId);
          return newSet;
        });
      } else {
        // 계속 폴링
        setTimeout(() => pollPipelineStatus(jobId, meetingId), 2000);
      }
    } catch (error) {
      console.error('파이프라인 상태 조회 오류:', error);
      // 오류 발생 시에도 폴링 중지
      setActivePolling(prev => {
        const newSet = new Set(prev);
        newSet.delete(jobId);
        return newSet;
      });
    }
  }, [activePolling, getPipelineStatus, getPipelineResults]);

  // 단계별 메시지 생성
  const getStageMessage = (stage: string, progress: number) => {
    const stageMessages: { [key: string]: string } = {
      'uploading': '파일 업로드 중...',
      'stt': '음성 인식 중...',
      'diarization': '화자 분리 중...',
      'transcript': '회의록 생성 중...',
      'agent_analysis': 'AI 에이전트 분석 중...',
      'report_generation': '보고서 생성 중...'
    };
    
    return stageMessages[stage] || `처리 중... (${progress}%)`;
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      {/* 헤더 섹션 */}
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '8px' }}>
          📁 파일 업로드
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '16px' }}>
          회의 음성 파일을 업로드하고 분석 파이프라인을 모니터링하세요.
        </p>
      </div>

      {/* 파일 업로드 영역 */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <h2 className="card-title">🎤 회의 파일 업로드</h2>
          <p className="card-description">
            오디오 파일을 드래그하거나 클릭하여 업로드하세요.
          </p>
        </div>
        <div style={{ marginTop: '16px' }}>
          <div
            style={{
              border: '2px dashed var(--border-primary)',
              borderRadius: '12px',
              padding: '48px 24px',
              textAlign: 'center',
              backgroundColor: 'var(--bg-secondary)',
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onClick={() => fileInputRef.current?.click()}
            onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--accent-primary)'}
            onMouseLeave={(e) => e.currentTarget.style.borderColor = 'var(--border-primary)'}
          >
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>
              {isUploading ? '🔄' : '📁'}
            </div>
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '8px' }}>
              {isUploading ? '업로드 중...' : '파일을 여기에 드래그하거나 클릭하세요'}
            </h3>
            <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
              지원 형식: MP3, WAV, M4A, MOV (최대 100MB)
            </p>
            
            {/* 업로드 진행률 */}
            {isUploading && (
              <div style={{ width: '100%', maxWidth: '300px', margin: '0 auto' }}>
                <div style={{ 
                  width: '100%', 
                  height: '8px', 
                  backgroundColor: 'var(--border-primary)', 
                  borderRadius: '4px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    width: `${uploadProgress}%`,
                    height: '100%',
                    backgroundColor: 'var(--accent-primary)',
                    transition: 'width 0.3s ease'
                  }} />
                </div>
                <div style={{ marginTop: '8px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                  {uploadProgress}%
                </div>
              </div>
            )}
            
            <input
              ref={fileInputRef}
              type="file"
              accept="audio/*,video/*"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) {
                  handleFileUpload(file);
                }
              }}
              style={{ display: 'none' }}
            />
          </div>
        </div>
      </div>

      {/* 파이프라인 모니터링 */}
      {meetings.length > 0 && (
        <div className="card" style={{ marginBottom: '24px' }}>
          <div className="card-header">
            <h2 className="card-title">🔄 파이프라인 모니터링</h2>
            <p className="card-description">
              업로드된 파일의 분석 진행 상황을 실시간으로 확인하세요.
            </p>
          </div>
          <div style={{ marginTop: '16px' }}>
            <div className="space-y-4">
              {meetings.map(meeting => (
                <div key={meeting.id} className="p-4 border border-gray-200 rounded-lg bg-white">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h3 className="text-lg font-semibold">{meeting.title}</h3>
                      <p className="text-sm text-gray-600">{meeting.summary}</p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      meeting.status === 'completed' ? 'bg-green-100 text-green-800' :
                      meeting.status === 'error' ? 'bg-red-100 text-red-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {meeting.status === 'completed' ? '완료' :
                       meeting.status === 'error' ? '오류' : '처리 중'}
                    </span>
                  </div>
                  
                  {/* 진행률 바 */}
                  {meeting.status === 'processing' && (
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm text-gray-600">
                        <span>{getStageMessage(meeting.current_stage, meeting.progress)}</span>
                        <span>{meeting.progress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${meeting.progress}%` }}
                        />
                      </div>
                    </div>
                  )}
                  
                  {/* 오류 메시지 */}
                  {meeting.error_message && (
                    <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                      <p className="text-sm text-red-800">❌ {meeting.error_message}</p>
                    </div>
                  )}
                  
                  {/* 완료된 경우 결과 링크 */}
                  {meeting.status === 'completed' && (
                    <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                      <p className="text-sm text-green-800 mb-2">✅ 분석이 완료되었습니다!</p>
                      <button
                        onClick={() => window.location.href = '/'}
                        className="text-sm text-green-700 hover:text-green-900 underline"
                      >
                        대시보드에서 결과 확인하기 →
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 파이프라인 단계 설명 */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <h2 className="card-title">📋 파이프라인 단계</h2>
          <p className="card-description">
            회의 파일이 처리되는 전체 과정을 단계별로 설명합니다.
          </p>
        </div>
        <div style={{ marginTop: '16px' }}>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              { stage: 'uploading', title: '파일 업로드', description: '음성/비디오 파일 검증 및 서버 전송', icon: '📁' },
              { stage: 'stt', title: '음성 인식', description: 'ReturnZero VITO API를 통한 음성-텍스트 변환', icon: '🎵' },
              { stage: 'diarization', title: '화자 분리', description: '여러 화자의 음성을 개별적으로 분리', icon: '👥' },
              { stage: 'transcript', title: '회의록 생성', description: '화자별 발화 내용을 시간순으로 정리', icon: '📝' },
              { stage: 'agent_analysis', title: 'AI 분석', description: '5개 AI 에이전트의 순차적 분석', icon: '🤖' },
              { stage: 'report_generation', title: '보고서 생성', description: '분석 결과를 종합한 최종 보고서', icon: '📊' }
            ].map((step, index) => (
              <div key={step.stage} className="p-4 border border-gray-200 rounded-lg bg-white">
                <div className="flex items-center space-x-3 mb-3">
                  <div className="text-2xl">{step.icon}</div>
                  <div>
                    <h4 className="font-medium text-gray-900">{step.title}</h4>
                    <p className="text-sm text-gray-600">{step.description}</p>
                  </div>
                </div>
                <div className="text-xs text-gray-500">단계 {index + 1}/6</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Upload;

export {};
