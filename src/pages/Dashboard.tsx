import React, { useState, useCallback, useEffect } from 'react';
import { useApi } from '../context/ApiContext';
import { Meeting } from '../types/electron';

const Dashboard: React.FC = () => {
  const { getMeetings, getPipelineStatus, getPipelineResults } = useApi();
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activePolling, setActivePolling] = useState<Set<string>>(new Set());
  const [finalReport, setFinalReport] = useState<any>(null);
  const [isReportLoading, setIsReportLoading] = useState(false);

  // 테스트용 샘플 보고서 데이터
  const sampleReport = {
    "executive_summary": {
      "meeting_overview": "총 120.5초 길이의 회의에서 4명의 화자가 참여했습니다.",
      "key_findings": [
        "주요 안건: 프로젝트 일정 및 리소스 계획",
        "주요 안건: 기술 스택 및 아키텍처 검토",
        "검증된 주장: React Native가 Flutter보다 개발 효율적"
      ],
      "action_items": [
        "보안 인증 시스템 설계",
        "React Native 개발 환경 구축",
        "AWS 인프라 설계서 작성"
      ],
      "recommendations": [
        "제시된 반박 의견들을 검토해보시기 바랍니다.",
        "추가 증거 자료를 참고하여 의사결정하시기 바랍니다."
      ]
    },
    "detailed_analysis": {
      "transcript_analysis": {
        "total_duration": 120.5,
        "total_segments": 45,
        "speakers_detected": 4,
        "average_confidence": 0.92,
        "language": "ko",
        "processing_timestamp": "2024-01-08T10:30:00Z"
      },
      "speaker_analysis": {
        "speaker_1": {
          "utterance_count": 12,
          "total_words": 156,
          "total_duration": 45.2
        },
        "speaker_2": {
          "utterance_count": 8,
          "total_words": 98,
          "total_duration": 32.1
        },
        "speaker_3": {
          "utterance_count": 15,
          "total_words": 203,
          "total_duration": 28.7
        },
        "speaker_4": {
          "utterance_count": 10,
          "total_words": 134,
          "total_duration": 14.5
        }
      }
    },
    "technical_details": {
      "processing_pipeline": {
        "stt_engine": "returnzero",
        "diarization_enabled": true,
        "agents_used": ["agendas", "claims", "counter_arguments", "evidence", "summary"]
      },
      "quality_metrics": {
        "stt_confidence": 0.92,
        "speakers_detected": 4,
        "processing_time": "2시간 30분"
      }
    },
    "generated_at": "2024-01-08T10:30:00Z",
    "format_version": "1.0"
  };

  // 파이프라인 상태 폴링 함수
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

  // 회의 목록 로드
  useEffect(() => {
    const loadMeetings = async () => {
      try {
        const meetingsData = await getMeetings();
        setMeetings(meetingsData);
        
        // 진행 중인 파이프라인이 있으면 폴링 시작
        const processingMeetings = meetingsData.filter((m: Meeting) => m.status === 'processing');
        processingMeetings.forEach((meeting: Meeting) => {
          setActivePolling(prev => new Set(prev).add(meeting.id));
          pollPipelineStatus(meeting.id, meeting.id);
        });
      } catch (error) {
        console.error('회의 목록 로드 오류:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadMeetings();
  }, [getMeetings, pollPipelineStatus]);

  // 통계 계산
  const stats = {
    total: meetings.length,
    completed: meetings.filter(m => m.status === 'completed').length,
    processing: meetings.filter(m => m.status === 'processing').length,
    error: meetings.filter(m => m.status === 'error').length
  };

  // 파이프라인 결과에서 최종 보고서 생성
  const generateFinalReport = useCallback(async (jobId: string) => {
    setIsReportLoading(true);
    try {
      // 백엔드 API에서 최종 보고서 가져오기
      const response = await fetch(`${process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000'}/api/meetings/${jobId}/report`);
      if (response.ok) {
        const reportData = await response.json();
        setFinalReport(reportData);
      } else {
        // API 응답이 없으면 sampleReport 사용
        setFinalReport(sampleReport);
      }
    } catch (error) {
      console.error('보고서 생성 오류:', error);
      // 에러 시 sampleReport 사용
      setFinalReport(sampleReport);
    } finally {
      setIsReportLoading(false);
    }
  }, []);

  // 파이프라인 상태 모니터링 및 보고서 생성
  useEffect(() => {
    const processingMeetings = meetings.filter((m: Meeting) => m.status === 'processing');
    processingMeetings.forEach((meeting: Meeting) => {
      // 파이프라인 완료 시 보고서 생성
      if (meeting.pipeline_results && meeting.pipeline_results.status === 'completed') {
        generateFinalReport(meeting.id);
      }
    });
  }, [meetings, generateFinalReport]);

  return (
    <div style={{ 
      maxWidth: '1200px', 
      margin: '0 auto', 
      padding: '20px',
      backgroundColor: '#ffffff',
      minHeight: '100vh'
    }}>
      {/* 헤더 섹션 */}
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '8px', color: '#1d1c1d' }}>
          📊 대시보드
        </h1>
        <p style={{ color: '#616061', fontSize: '16px' }}>
          회의 분석 현황과 주요 지표를 한눈에 확인하세요.
        </p>
      </div>

      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center">
            <div className="p-3 bg-blue-100 rounded-lg">
              <span className="text-2xl">📊</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">전체 회의</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center">
            <div className="p-3 bg-green-100 rounded-lg">
              <span className="text-2xl">✅</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">완료</p>
              <p className="text-2xl font-bold text-gray-900">{stats.completed}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center">
            <div className="p-3 bg-blue-100 rounded-lg">
              <span className="text-2xl">🔄</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">처리 중</p>
              <p className="text-2xl font-bold text-gray-900">{stats.processing}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center">
            <div className="p-3 bg-red-100 rounded-lg">
              <span className="text-2xl">❌</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">오류</p>
              <p className="text-2xl font-bold text-gray-900">{stats.error}</p>
            </div>
          </div>
        </div>
      </div>

      {/* 회의 목록 */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <h2 className="card-title">📋 회의 목록</h2>
          <p className="card-description">
            업로드된 회의 파일들의 분석 현황을 확인하세요.
          </p>
        </div>
        <div style={{ marginTop: '16px' }}>
          {isLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <p className="text-gray-600">회의 목록을 불러오는 중...</p>
            </div>
          ) : meetings.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-4xl mb-4">📁</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">아직 업로드된 회의가 없습니다</h3>
              <p className="text-gray-600 mb-4">
                파일 업로드 페이지에서 회의 음성 파일을 업로드하여 분석을 시작하세요.
              </p>
              <button
                onClick={() => window.location.href = '/upload'}
                className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
              >
                📁 파일 업로드하기
              </button>
            </div>
          ) : (
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
                        onClick={() => setFinalReport(meeting.pipeline_results || sampleReport)}
                        className="text-sm text-green-700 hover:text-green-900 underline"
                      >
                        📊 분석 결과 보기 →
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 테스트 보고서 버튼 */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <h2 className="card-title">🧪 개발자 테스트 도구</h2>
          <p className="card-description">
            UI 테스트를 위한 샘플 보고서를 확인할 수 있습니다.
          </p>
        </div>
        <div style={{ marginTop: '16px' }}>
          <button
            onClick={() => setFinalReport(sampleReport)}
            className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            🧪 테스트 보고서 보기
          </button>
        </div>
      </div>

      {/* 최종 보고서 */}
      {finalReport && (
        <div className="card" style={{ marginBottom: '24px' }}>
          <div className="card-header">
            <h2 className="card-title">📊 최종 분석 보고서</h2>
            <p className="card-description">
              AI 에이전트가 분석한 회의 내용의 종합 보고서입니다.
            </p>
          </div>
          <div style={{ marginTop: '16px' }}>
            <div className="space-y-6">
              {/* 실행 요약 */}
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-200">
                <h3 className="text-lg font-semibold text-blue-900 mb-4">🎯 실행 요약</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-medium text-blue-800 mb-2">핵심 결과</h4>
                    <div className="space-y-2">
                      {finalReport.executive_summary?.key_findings?.map((finding: string, index: number) => (
                        <div key={index} className="flex items-start space-x-2">
                          <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                          <p className="text-blue-700 text-sm">{finding}</p>
                        </div>
                      )) || (
                        <p className="text-blue-700 text-sm">핵심 결과가 없습니다.</p>
                      )}
                    </div>
                  </div>
                  <div>
                    <h4 className="font-medium text-blue-800 mb-2">생성 시간</h4>
                    <p className="text-blue-700 text-sm">
                      {finalReport.generated_at ? new Date(finalReport.generated_at).toLocaleString('ko-KR') : '시간 정보가 없습니다.'}
                    </p>
                    <h4 className="font-medium text-blue-800 mb-2 mt-4">화자 수</h4>
                    <p className="text-blue-700 text-sm">
                      {finalReport.detailed_analysis?.speaker_analysis ? Object.keys(finalReport.detailed_analysis.speaker_analysis).length : 'N/A'}명
                    </p>
                  </div>
                </div>
              </div>

              {/* 주요 결정사항 */}
              <div className="bg-gradient-to-r from-emerald-50 to-teal-50 p-6 rounded-xl border border-emerald-200">
                <h3 className="text-lg font-semibold text-emerald-900 mb-4">📋 주요 결정사항</h3>
                <div className="space-y-4">
                  {finalReport.executive_summary?.action_items?.map((item: string, index: number) => (
                    <div key={index} className="p-4 bg-white rounded-lg border border-emerald-100">
                      <h4 className="font-medium text-emerald-800">{item}</h4>
                    </div>
                  )) || (
                    <p className="text-emerald-700 text-sm">주요 결정사항이 없습니다.</p>
                  )}
                </div>
              </div>

              {/* 권장사항 */}
              <div className="bg-gradient-to-r from-purple-50 to-violet-50 p-6 rounded-xl border border-purple-200">
                <h3 className="text-lg font-semibold text-purple-900 mb-4">💡 권장사항</h3>
                <div className="space-y-3">
                  {finalReport.executive_summary?.recommendations?.map((rec: string, index: number) => (
                    <div key={index} className="flex items-start space-x-3">
                      <div className="w-2 h-2 bg-purple-500 rounded-full mt-2 flex-shrink-0"></div>
                      <p className="text-purple-800 text-sm">{rec}</p>
                    </div>
                  )) || (
                    <p className="text-purple-700 text-sm">권장사항이 없습니다.</p>
                  )}
                </div>
              </div>

              {/* 보고서 액션 */}
              <div className="flex space-x-4 pt-4 border-t border-gray-200">
                <button
                  className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                  onClick={() => {
                    const reportText = JSON.stringify(finalReport, null, 2);
                    const blob = new Blob([reportText], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `meeting_report_${Date.now()}.json`;
                    a.click();
                    URL.revokeObjectURL(url);
                  }}
                >
                  📥 JSON 다운로드
                </button>
                <button
                  className="px-6 py-3 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                  onClick={() => setFinalReport(null)}
                >
                  ❌ 보고서 닫기
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 회의록 분석 진행 상황 */}
      <div style={{ marginBottom: '32px' }}>
        <h2 style={{ fontSize: '24px', fontWeight: '600', marginBottom: '20px', color: '#1d1c1d' }}>
          📊 회의록 분석 진행 상황
        </h2>
        
        {/* 분석 단계별 진행 상황 */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
          {/* STT 진행 상황 */}
          <div style={{
            padding: '24px',
            backgroundColor: 'white',
            borderRadius: '16px',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)',
            border: '1px solid #e9ecef'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: '50%',
                backgroundColor: '#e3f2fd',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <span style={{ fontSize: '24px' }}>🎤</span>
              </div>
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#1976d2', marginBottom: '4px' }}>
                  음성 인식 (STT)
                </h3>
                <p style={{ fontSize: '14px', color: '#6c757d' }}>
                  음성을 텍스트로 변환
                </p>
              </div>
            </div>
            
            <div style={{ marginBottom: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '14px', color: '#495057' }}>진행률</span>
                <span style={{ fontSize: '14px', fontWeight: '600', color: '#1976d2' }}>85%</span>
              </div>
              <div style={{
                width: '100%',
                height: '8px',
                backgroundColor: '#e9ecef',
                borderRadius: '4px',
                overflow: 'hidden'
              }}>
                <div style={{
                  width: '85%',
                  height: '100%',
                  backgroundColor: '#1976d2',
                  borderRadius: '4px',
                  transition: 'width 0.3s ease'
                }} />
              </div>
            </div>
            
            <div style={{ fontSize: '13px', color: '#6c757d' }}>
              <div style={{ marginBottom: '4px' }}>• 인식된 텍스트: 2,847자</div>
              <div style={{ marginBottom: '4px' }}>• 신뢰도: 92.3%</div>
              <div>• 처리 시간: 3분 24초</div>
            </div>
          </div>

          {/* 화자 분리 및 발화 기록 */}
          <div style={{
            padding: '24px',
            backgroundColor: 'white',
            borderRadius: '16px',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)',
            border: '1px solid #e9ecef'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: '50%',
                backgroundColor: '#f3e5f5',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <span style={{ fontSize: '24px' }}>👥</span>
              </div>
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#7b1fa2', marginBottom: '4px' }}>
                  화자 분리
                </h3>
                <p style={{ fontSize: '14px', color: '#6c757d' }}>
                  발화자별 구분 및 기록
                </p>
              </div>
            </div>
            
            <div style={{ marginBottom: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '14px', color: '#495057' }}>진행률</span>
                <span style={{ fontSize: '14px', fontWeight: '600', color: '#7b1fa2' }}>100%</span>
              </div>
              <div style={{
                width: '100%',
                height: '8px',
                backgroundColor: '#e9ecef',
                borderRadius: '4px',
                overflow: 'hidden'
              }}>
                <div style={{
                  width: '100%',
                  height: '100%',
                  backgroundColor: '#7b1fa2',
                  borderRadius: '4px'
                }} />
              </div>
            </div>
            
            <div style={{ fontSize: '13px', color: '#6c757d' }}>
              <div style={{ marginBottom: '4px' }}>• 감지된 화자: 4명</div>
              <div style={{ marginBottom: '4px' }}>• 총 발화 횟수: 127회</div>
              <div>• 화자별 발화 시간 분포 완료</div>
            </div>
          </div>

          {/* AI 에이전트 실행 상태 */}
          <div style={{
            padding: '24px',
            backgroundColor: 'white',
            borderRadius: '16px',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)',
            border: '1px solid #e9ecef'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: '50%',
                backgroundColor: '#e8f5e8',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <span style={{ fontSize: '24px' }}>🤖</span>
              </div>
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#2e7d32', marginBottom: '4px' }}>
                  AI 에이전트
                </h3>
                <p style={{ fontSize: '14px', color: '#6c757d' }}>
                  다중 에이전트 분석 실행
                </p>
              </div>
            </div>
            
            <div style={{ marginBottom: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '14px', color: '#495057' }}>진행률</span>
                <span style={{ fontSize: '14px', fontWeight: '600', color: '#2e7d32' }}>75%</span>
              </div>
              <div style={{
                width: '100%',
                height: '8px',
                backgroundColor: '#e9ecef',
                borderRadius: '4px',
                overflow: 'hidden'
              }}>
                <div style={{
                  width: '75%',
                  height: '100%',
                  backgroundColor: '#2e7d32',
                  borderRadius: '4px',
                  transition: 'width 0.3s ease'
                }} />
              </div>
            </div>
            
            <div style={{ fontSize: '13px', color: '#6c757d' }}>
              <div style={{ marginBottom: '4px' }}>• AgendaMiner: ✅ 완료</div>
              <div style={{ marginBottom: '4px' }}>• ClaimChecker: ✅ 완료</div>
              <div style={{ marginBottom: '4px' }}>• CounterArguer: 🔄 진행중</div>
              <div>• EvidenceHunter: ⏳ 대기중</div>
            </div>
          </div>

          {/* 최종 보고서 생성 */}
          <div style={{
            padding: '24px',
            backgroundColor: 'white',
            borderRadius: '16px',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)',
            border: '1px solid #e9ecef'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: '50%',
                backgroundColor: '#fff3e0',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <span style={{ fontSize: '24px' }}>📋</span>
              </div>
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#f57c00', marginBottom: '4px' }}>
                  최종 보고서
                </h3>
                <p style={{ fontSize: '14px', color: '#6c757d' }}>
                  종합 분석 결과 정리
                </p>
              </div>
            </div>
            
            {/* 보고서 내용 미리보기 */}
            <div style={{ marginBottom: '20px' }}>
              {isReportLoading ? (
                <div style={{
                  padding: '20px',
                  textAlign: 'center',
                  color: '#6c757d'
                }}>
                  <div style={{
                    width: '40px',
                    height: '40px',
                    border: '3px solid #f57c00',
                    borderTop: '3px solid transparent',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite',
                    margin: '0 auto 16px'
                  }} />
                  <p>보고서를 생성하고 있습니다...</p>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{
                    padding: '12px',
                    backgroundColor: '#fff8e1',
                    borderRadius: '8px',
                    border: '1px solid #ffcc02'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                      <span style={{ fontSize: '16px' }}>✅</span>
                      <span style={{ fontSize: '14px', fontWeight: '600', color: '#e65100' }}>실행 요약</span>
                    </div>
                    <p style={{ fontSize: '13px', color: '#795548', lineHeight: '1.4' }}>
                      {finalReport?.executive_summary?.meeting_overview || 
                       '프로젝트 일정 조정으로 2024년 3월 완료 예정, 팀원 2명 추가로 개발 속도 향상, React Native와 AWS 기술 스택 검토로 안정성 개선'}
                    </p>
                  </div>
                  
                  <div style={{
                    padding: '12px',
                    backgroundColor: '#e8f5e8',
                    borderRadius: '8px',
                    border: '1px solid #4caf50'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                      <span style={{ fontSize: '16px' }}>✅</span>
                      <span style={{ fontSize: '14px', fontWeight: '600', color: '#2e7d32' }}>핵심 결과</span>
                    </div>
                    <p style={{ fontSize: '13px', color: '#388e3c', lineHeight: '1.4' }}>
                      {finalReport?.executive_summary?.key_findings?.join(', ') || 
                       'React Native로 모바일 앱 개발 결정, AWS 인프라로 클라우드 마이그레이션, 보안 인증 시스템 구축 우선순위 설정'}
                    </p>
                  </div>
                  
                  <div style={{
                    padding: '12px',
                    backgroundColor: '#e3f2fd',
                    borderRadius: '8px',
                    border: '1px solid #2196f3'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                      <span style={{ fontSize: '16px' }}>✅</span>
                      <span style={{ fontSize: '14px', fontWeight: '600', color: '#1565c0' }}>권장사항</span>
                    </div>
                    <p style={{ fontSize: '13px', color: '#1976d2', lineHeight: '1.4' }}>
                      {finalReport?.executive_summary?.recommendations?.join(', ') || 
                       '보안 인증 시스템 구축을 최우선으로 진행, 단계별 마일스톤 설정으로 진행 상황 모니터링, 정기적인 기술 검토 미팅 진행'}
                    </p>
                  </div>
                  
                  <div style={{
                    padding: '12px',
                    backgroundColor: '#fce4ec',
                    borderRadius: '8px',
                    border: '1px solid #e91e63'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                      <span style={{ fontSize: '16px' }}>✅</span>
                      <span style={{ fontSize: '14px', fontWeight: '600', color: '#c2185b' }}>액션 아이템</span>
                    </div>
                    <p style={{ fontSize: '13px', color: '#ad1457', lineHeight: '1.4' }}>
                      {finalReport?.executive_summary?.action_items?.join(', ') || 
                       '보안 인증 시스템 설계, React Native 개발 환경 구축, AWS 인프라 설계서 작성'}
                    </p>
                  </div>
                </div>
              )}
            </div>
            
            {/* 보고서 다운로드 버튼 */}
            <div style={{
              display: 'flex',
              gap: '12px',
              justifyContent: 'center'
            }}>
              <button
                style={{
                  padding: '12px 20px',
                  backgroundColor: finalReport ? '#f57c00' : '#e9ecef',
                  color: finalReport ? 'white' : '#6c757d',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '14px',
                  fontWeight: '600',
                  cursor: finalReport ? 'pointer' : 'not-allowed',
                  transition: 'all 0.2s ease',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}
                onMouseEnter={(e) => {
                  if (finalReport) {
                    e.currentTarget.style.backgroundColor = '#e65100';
                    e.currentTarget.style.transform = 'translateY(-1px)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (finalReport) {
                    e.currentTarget.style.backgroundColor = '#f57c00';
                    e.currentTarget.style.transform = 'translateY(0)';
                  }
                }}
                onClick={() => {
                  if (finalReport) {
                    const reportText = JSON.stringify(finalReport, null, 2);
                    const blob = new Blob([reportText], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `회의록_분석_보고서_${new Date().toISOString().split('T')[0]}.json`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                  }
                }}
              >
                <span>📥</span>
                {finalReport ? '최종 보고서 다운로드' : '보고서 생성 대기 중'}
              </button>
              
              <button
                style={{
                  padding: '12px 20px',
                  backgroundColor: finalReport ? '#fff3e0' : '#f8f9fa',
                  color: finalReport ? '#f57c00' : '#9e9e9e',
                  border: `1px solid ${finalReport ? '#f57c00' : '#e9ecef'}`,
                  borderRadius: '8px',
                  fontSize: '14px',
                  fontWeight: '600',
                  cursor: finalReport ? 'pointer' : 'not-allowed',
                  transition: 'all 0.2s ease',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}
                onMouseEnter={(e) => {
                  if (finalReport) {
                    e.currentTarget.style.backgroundColor = '#ffe0b2';
                  }
                }}
                onMouseLeave={(e) => {
                  if (finalReport) {
                    e.currentTarget.style.backgroundColor = '#fff3e0';
                  }
                }}
                onClick={() => {
                  if (finalReport) {
                    // 보고서 상세 보기 모달 또는 페이지로 이동
                    alert('보고서 상세 보기 기능은 개발 중입니다.');
                  }
                }}
              >
                <span>👁️</span>
                상세 보기
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;