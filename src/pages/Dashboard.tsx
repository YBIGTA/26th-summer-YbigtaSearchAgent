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

  // 개별 회의의 보고서 생성
  const generateMeetingReport = useCallback(async (meeting: Meeting) => {
    setIsReportLoading(true);
    try {
      // 먼저 파이프라인 결과를 가져와서 보고서 생성
      if (meeting.job_id) {
        try {
          // 파이프라인 결과 조회
          const pipelineResponse = await fetch(`${process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000'}/api/pipeline/results/${meeting.job_id}`);
          if (pipelineResponse.ok) {
            const pipelineData = await pipelineResponse.json();
            if (pipelineData.results && pipelineData.results.final_report) {
              // 백엔드에서 생성된 보고서가 있으면 사용
              return pipelineData.results.final_report;
            }
          }
        } catch (pipelineError) {
          console.log('파이프라인 결과 조회 실패, 기본 데이터 사용:', pipelineError);
        }
      }
      
      // 파이프라인 결과가 없으면 회의 데이터 기반으로 보고서 생성
      if (meeting.pipeline_results) {
        return meeting.pipeline_results;
      }
      
      // 아무것도 없으면 기본 보고서 사용
      return sampleReport;
    } catch (error) {
      console.error('보고서 생성 오류:', error);
      return sampleReport;
    } finally {
      setIsReportLoading(false);
    }
  }, []);

  // 최신 완료된 회의의 보고서를 자동으로 표시
  useEffect(() => {
    if (meetings.length === 0) {
      setFinalReport(null);
      return;
    }
    
    // 완료된 회의가 있으면 가장 최근 것 사용
    const completedMeetings = meetings.filter((m: Meeting) => m.status === 'completed');
    if (completedMeetings.length > 0) {
      const latestMeeting = completedMeetings[0];
      generateMeetingReport(latestMeeting).then(setFinalReport);
      return;
    }

    // 진행 중인 회의가 있으면 해당 데이터 사용
    const processingMeetings = meetings.filter((m: Meeting) => m.status === 'processing');
    if (processingMeetings.length > 0) {
      const latestProcessing = processingMeetings[0];
      if (latestProcessing.pipeline_results) {
        setFinalReport(latestProcessing.pipeline_results);
      } else {
        // 파이프라인 결과가 없으면 빈 상태로 표시
        setFinalReport(null);
      }
      return;
    }
    
    // 아무것도 없으면 빈 상태로 표시
    setFinalReport(null);
  }, [meetings, generateMeetingReport]);

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
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '24px', marginBottom: '32px' }}>
        {/* 전체 회의 */}
          <div style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          borderRadius: '20px',
          padding: '32px',
          color: 'white',
          position: 'relative',
          overflow: 'hidden',
          boxShadow: '0 8px 32px rgba(102, 126, 234, 0.3)',
          transition: 'transform 0.3s ease, box-shadow 0.3s ease'
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'translateY(-4px)';
          e.currentTarget.style.boxShadow = '0 12px 40px rgba(102, 126, 234, 0.4)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = '0 8px 32px rgba(102, 126, 234, 0.3)';
        }}>
          <div style={{
            position: 'absolute',
            top: '-20px',
            right: '-20px',
            width: '80px',
            height: '80px',
            background: 'rgba(255, 255, 255, 0.1)',
            borderRadius: '50%'
          }} />
          <div style={{ position: 'relative', zIndex: 1 }}>
            <div style={{ fontSize: '36px', marginBottom: '16px' }}>📊</div>
            <div style={{ fontSize: '28px', fontWeight: '800', marginBottom: '8px' }}>
              {stats.total}
            </div>
            <div style={{ fontSize: '16px', opacity: 0.9, fontWeight: '500' }}>
              전체 회의
          </div>
            <div style={{ fontSize: '12px', opacity: 0.7, marginTop: '8px' }}>
              업로드된 총 회의 수
            </div>
          </div>
      </div>

        {/* 완료 */}
        <div style={{
          background: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
          borderRadius: '20px',
          padding: '32px',
          color: 'white',
          position: 'relative',
          overflow: 'hidden',
          boxShadow: '0 8px 32px rgba(17, 153, 142, 0.3)',
          transition: 'transform 0.3s ease, box-shadow 0.3s ease'
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'translateY(-4px)';
          e.currentTarget.style.boxShadow = '0 12px 40px rgba(17, 153, 142, 0.4)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = '0 8px 32px rgba(17, 153, 142, 0.3)';
        }}>
          <div style={{
            position: 'absolute',
            top: '-20px',
            right: '-20px',
            width: '80px',
            height: '80px',
            background: 'rgba(255, 255, 255, 0.1)',
            borderRadius: '50%'
          }} />
          <div style={{ position: 'relative', zIndex: 1 }}>
            <div style={{ fontSize: '36px', marginBottom: '16px' }}>✅</div>
            <div style={{ fontSize: '28px', fontWeight: '800', marginBottom: '8px' }}>
              {stats.completed}
            </div>
            <div style={{ fontSize: '16px', opacity: 0.9, fontWeight: '500' }}>
              완료
            </div>
            <div style={{ fontSize: '12px', opacity: 0.7, marginTop: '8px' }}>
              분석이 완료된 회의
            </div>
          </div>
        </div>

        {/* 처리 중 */}
        <div style={{
          background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
          borderRadius: '20px',
          padding: '32px',
          color: 'white',
          position: 'relative',
          overflow: 'hidden',
          boxShadow: '0 8px 32px rgba(79, 172, 254, 0.3)',
          transition: 'transform 0.3s ease, box-shadow 0.3s ease'
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'translateY(-4px)';
          e.currentTarget.style.boxShadow = '0 12px 40px rgba(79, 172, 254, 0.4)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = '0 8px 32px rgba(79, 172, 254, 0.3)';
        }}>
          <div style={{
            position: 'absolute',
            top: '-20px',
            right: '-20px',
            width: '80px',
            height: '80px',
            background: 'rgba(255, 255, 255, 0.1)',
            borderRadius: '50%'
          }} />
          <div style={{ position: 'relative', zIndex: 1 }}>
            <div style={{ fontSize: '36px', marginBottom: '16px' }}>🔄</div>
            <div style={{ fontSize: '28px', fontWeight: '800', marginBottom: '8px' }}>
              {stats.processing}
            </div>
            <div style={{ fontSize: '16px', opacity: 0.9, fontWeight: '500' }}>
              처리 중
            </div>
            <div style={{ fontSize: '12px', opacity: 0.7, marginTop: '8px' }}>
              현재 분석 진행 중인 회의
            </div>
          </div>
        </div>

        {/* 오류 */}
        <div style={{
          background: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
          borderRadius: '20px',
          padding: '32px',
          color: 'white',
          position: 'relative',
          overflow: 'hidden',
          boxShadow: '0 8px 32px rgba(250, 112, 154, 0.3)',
          transition: 'transform 0.3s ease, box-shadow 0.3s ease'
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'translateY(-4px)';
          e.currentTarget.style.boxShadow = '0 12px 40px rgba(250, 112, 154, 0.4)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = '0 8px 32px rgba(250, 112, 154, 0.3)';
        }}>
          <div style={{
            position: 'absolute',
            top: '-20px',
            right: '-20px',
            width: '80px',
            height: '80px',
            background: 'rgba(255, 255, 255, 0.1)',
            borderRadius: '50%'
          }} />
          <div style={{ position: 'relative', zIndex: 1 }}>
            <div style={{ fontSize: '36px', marginBottom: '16px' }}>❌</div>
            <div style={{ fontSize: '28px', fontWeight: '800', marginBottom: '8px' }}>
              {stats.error}
            </div>
            <div style={{ fontSize: '16px', opacity: 0.9, fontWeight: '500' }}>
              오류
            </div>
            <div style={{ fontSize: '12px', opacity: 0.7, marginTop: '8px' }}>
              처리 중 오류가 발생한 회의
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
                      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                        <button 
                          onClick={async () => {
                            const report = await generateMeetingReport(meeting);
                            setFinalReport(report);
                          }}
                          className="text-sm text-green-700 hover:text-green-900 underline"
                        >
                          📊 대시보드에서 보기
                        </button>
                        <button 
                          onClick={() => window.location.href = `/meeting/${meeting.id}`}
                          className="text-sm text-blue-700 hover:text-blue-900 underline"
                        >
                          🔍 상세 인사이트 보기 →
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 에이전트 회의 요약 리포트 */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <h2 className="card-title">🤖 에이전트 회의 요약 리포트</h2>
          <p className="card-description">
            AI 에이전트가 분석한 회의 내용의 종합 보고서를 확인하세요.
          </p>
          {/* 현재 표시 중인 회의 정보 */}
          {finalReport && meetings.length > 0 && (
          <div style={{ 
              marginTop: '12px', 
              padding: '12px 16px',
              backgroundColor: '#f8f9fa',
              borderRadius: '8px',
              border: '1px solid #e9ecef'
            }}>
              <div style={{ fontSize: '13px', color: '#6c757d', marginBottom: '4px' }}>
                현재 표시 중인 회의:
              </div>
              <div style={{ fontSize: '14px', fontWeight: '600', color: '#495057' }}>
                {(() => {
                  const completedMeetings = meetings.filter(m => m.status === 'completed');
                  const latestMeeting = completedMeetings[0];
                  return latestMeeting ? latestMeeting.title || '최신 완료된 회의' : '샘플 보고서';
                })()}
              </div>
              <div style={{ fontSize: '12px', color: '#6c757d', marginTop: '4px' }}>
                다른 회의 보고서를 보려면 위의 회의 목록에서 "📊 대시보드에서 보기"를 클릭하세요.
              </div>
          </div>
        )}
            </div>
        <div style={{ marginTop: '16px' }}>
          <div style={{ display: 'grid', gap: '24px' }}>
            {/* 실행 요약 */}
            <div style={{ 
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              borderRadius: '20px',
              padding: '28px',
              color: 'white',
              position: 'relative',
              overflow: 'hidden',
              boxShadow: '0 8px 32px rgba(102, 126, 234, 0.3)'
            }}>
              {/* 배경 장식 */}
              <div style={{
                position: 'absolute',
                top: '-50px',
                right: '-50px',
                width: '150px',
                height: '150px',
                borderRadius: '50%',
                background: 'rgba(255, 255, 255, 0.1)',
                pointerEvents: 'none'
              }} />
              <div style={{
                position: 'absolute',
                bottom: '-30px',
                left: '-30px',
                width: '100px',
                height: '100px',
                borderRadius: '50%',
                background: 'rgba(255, 255, 255, 0.08)',
                pointerEvents: 'none'
              }} />
              
              <div style={{ position: 'relative', zIndex: 1 }}>
                <div style={{ fontSize: '32px', marginBottom: '16px' }}>🎯</div>
                <h3 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '20px', color: 'white' }}>
                  실행 요약
                </h3>
                
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                  {/* 핵심 결과 */}
                  <div>
                    <h4 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '12px', opacity: 0.9 }}>
                      핵심 결과
                    </h4>
                    <div style={{ display: 'grid', gap: '8px' }}>
                      {finalReport?.executive_summary?.key_findings?.length > 0 ? (
                        finalReport.executive_summary.key_findings.map((finding: string, index: number) => (
                          <div key={index} style={{ 
                            display: 'flex', 
                            alignItems: 'flex-start', 
                            gap: '8px',
                            padding: '8px 12px',
                            backgroundColor: 'rgba(255, 255, 255, 0.15)',
                            borderRadius: '8px'
                          }}>
                            <div style={{ 
                              width: '6px', 
                              height: '6px', 
                              backgroundColor: 'rgba(255, 255, 255, 0.8)', 
                              borderRadius: '50%', 
                              marginTop: '6px',
                              flexShrink: 0
                            }}></div>
                            <p style={{ fontSize: '13px', lineHeight: '1.5', opacity: 0.9 }}>{finding}</p>
            </div>
                        ))
                      ) : (
                        <div style={{ textAlign: 'center', padding: '16px' }}>
                          <div style={{ fontSize: '24px', marginBottom: '8px', opacity: 0.7 }}>📋</div>
                          <p style={{ fontSize: '13px', fontWeight: '500', marginBottom: '4px', opacity: 0.9 }}>
                            아직 회의록이 업로드되지 않았습니다
                          </p>
                          <p style={{ fontSize: '11px', opacity: 0.7, lineHeight: '1.4' }}>
                            회의 파일을 업로드하면 AI 에이전트가 자동으로 핵심 결과를 분석합니다
                          </p>
          </div>
        )}
                    </div>
      </div>

                  {/* 메타데이터 */}
                  <div>
                    <div style={{ marginBottom: '16px' }}>
                      <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '6px', opacity: 0.8 }}>
                        생성 시간
                      </h4>
                      <p style={{ fontSize: '13px', opacity: 0.9 }}>
                        {finalReport?.generated_at ? 
                          new Date(finalReport.generated_at).toLocaleString('ko-KR') : 
                          '분석 대기 중...'
                        }
                      </p>
                    </div>
                    <div>
                      <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '6px', opacity: 0.8 }}>
                        화자 수
                      </h4>
                      <p style={{ fontSize: '13px', opacity: 0.9 }}>
                        {finalReport?.detailed_analysis?.speaker_analysis ? 
                          `${Object.keys(finalReport.detailed_analysis.speaker_analysis).length}명` : 
                          '화자 분석 대기 중...'
                        }
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* 주요 결정사항 */}
      <div style={{ 
              background: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
              borderRadius: '20px',
              padding: '28px',
              color: '#2d3748',
              position: 'relative',
              overflow: 'hidden',
              boxShadow: '0 8px 32px rgba(168, 237, 234, 0.3)'
            }}>
              <div style={{ position: 'relative', zIndex: 1 }}>
                <div style={{ fontSize: '32px', marginBottom: '16px' }}>📋</div>
                <h3 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '20px' }}>
                  주요 결정사항
                </h3>
                <div style={{ display: 'grid', gap: '12px' }}>
                  {finalReport?.executive_summary?.action_items?.length > 0 ? (
                    finalReport.executive_summary.action_items.map((item: string, index: number) => (
                      <div key={index} style={{ 
                        padding: '16px 20px',
                        backgroundColor: 'rgba(255, 255, 255, 0.8)',
                        borderRadius: '12px',
                        border: '1px solid rgba(45, 55, 72, 0.1)',
                        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)'
                      }}>
                        <div style={{ 
                          display: 'flex',
                          alignItems: 'flex-start',
                          gap: '12px'
                        }}>
                          <span style={{ fontSize: '16px', marginTop: '2px' }}>✅</span>
                          <h4 style={{ fontSize: '14px', fontWeight: '600', lineHeight: '1.5' }}>{item}</h4>
            </div>
          </div>
                    ))
                  ) : (
                    <div style={{ textAlign: 'center', padding: '32px 16px' }}>
                      <div style={{ fontSize: '48px', marginBottom: '12px', opacity: 0.6 }}>✅</div>
                      <p style={{ fontSize: '15px', fontWeight: '600', marginBottom: '6px' }}>
                        결정사항을 분석 중입니다
                      </p>
                      <p style={{ fontSize: '13px', opacity: 0.7, lineHeight: '1.4' }}>
                        회의에서 논의된 주요 결정사항들이 여기에 표시됩니다
                      </p>
        </div>
                  )}
            </div>
          </div>
        </div>

            {/* 권장사항 */}
            <div style={{
              background: 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)',
              borderRadius: '20px',
              padding: '28px',
              color: '#744210',
              position: 'relative',
              overflow: 'hidden',
              boxShadow: '0 8px 32px rgba(255, 236, 210, 0.4)'
            }}>
              <div style={{ position: 'relative', zIndex: 1 }}>
                <div style={{ fontSize: '32px', marginBottom: '16px' }}>💡</div>
                <h3 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '20px' }}>
                  권장사항
                </h3>
                <div style={{ display: 'grid', gap: '10px' }}>
                  {finalReport?.executive_summary?.recommendations?.length > 0 ? (
                    finalReport.executive_summary.recommendations.map((rec: string, index: number) => (
                      <div key={index} style={{ 
                        display: 'flex', 
                        alignItems: 'flex-start', 
                        gap: '12px',
                        padding: '12px 16px',
                        backgroundColor: 'rgba(255, 255, 255, 0.7)',
                        borderRadius: '10px'
                      }}>
                        <div style={{ 
                          width: '6px', 
                          height: '6px', 
                          backgroundColor: '#d97706', 
                          borderRadius: '50%', 
                          marginTop: '8px',
                          flexShrink: 0
                        }}></div>
                        <p style={{ fontSize: '14px', lineHeight: '1.6', fontWeight: '500' }}>{rec}</p>
            </div>
                    ))
                  ) : (
                    <div style={{ textAlign: 'center', padding: '32px 16px' }}>
                      <div style={{ fontSize: '48px', marginBottom: '12px', opacity: 0.6 }}>💡</div>
                      <p style={{ fontSize: '15px', fontWeight: '600', marginBottom: '6px' }}>
                        AI 권장사항을 생성 중입니다
                      </p>
                      <p style={{ fontSize: '13px', opacity: 0.7, lineHeight: '1.4' }}>
                        회의 내용을 바탕으로 한 실행 가능한 권장사항들이 여기에 표시됩니다
                      </p>
                    </div>
                  )}
                </div>
          </div>
        </div>

            {/* 보고서 액션 */}
            <div className="flex space-x-4 pt-4 border-t border-gray-200">
            <button 
                className={`px-6 py-3 rounded-lg transition-colors ${
                  finalReport ? 
                    'bg-blue-500 text-white hover:bg-blue-600' : 
                    'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
                disabled={!finalReport}
                onClick={() => {
                  if (finalReport) {
                    const reportText = JSON.stringify(finalReport, null, 2);
                    const blob = new Blob([reportText], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `meeting_report_${Date.now()}.json`;
                    a.click();
                    URL.revokeObjectURL(url);
                  }
                }}
              >
                📥 {finalReport ? 'JSON 다운로드' : '보고서 생성 대기 중'}
              </button>
              <button
                className="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
                onClick={() => {
                  // 테스트용 샘플 보고서 로드
                  setFinalReport(sampleReport);
                }}
              >
                🧪 샘플 보고서 로드 (테스트용)
            </button>
            </div>
          </div>
        </div>
      </div>



      {/* 회의록 분석 진행 상황 */}
        <div className="card" style={{ marginBottom: '32px' }}>
          <div className="card-header">
          <h2 className="card-title">⚡ 실시간 분석 현황</h2>
          <p className="card-description">현재 처리 중인 회의록의 실시간 진행 상황을 모니터링합니다.</p>
          </div>
        
        <div style={{ marginTop: '24px' }}>
          {/* 진행 중인 회의가 있는 경우 실제 데이터 표시 */}
          {(() => {
            const processingMeetings = meetings.filter((m: Meeting) => m.status === 'processing');
            const activeMeeting = processingMeetings.length > 0 ? processingMeetings[0] : null;
            
            // 단계별 진행률 계산
            const getStageProgress = (currentStage: string, progress: number) => {
              const stages = ['uploading', 'stt', 'diarization', 'transcript', 'agent_analysis', 'report_generation'];
              const currentIndex = stages.indexOf(currentStage);
              return {
                stt: currentIndex > 1 ? 100 : currentIndex === 1 ? progress : 0,
                diarization: currentIndex > 2 ? 100 : currentIndex === 2 ? progress : 0,
                agent_analysis: currentIndex > 4 ? 100 : currentIndex === 4 ? progress : 0,
                report_generation: currentIndex > 5 ? 100 : currentIndex === 5 ? progress : 0
              };
            };
            
            const stageProgress = activeMeeting ? getStageProgress(activeMeeting.current_stage || '', activeMeeting.progress || 0) : {
              stt: 0, diarization: 0, agent_analysis: 0, report_generation: 0
            };
            
            // 화자 분석 데이터 (실제 데이터에서 추출 또는 대기 상태)
            const speakerAnalysis = finalReport?.detailed_analysis?.speaker_analysis || null;
            const speakerCount = speakerAnalysis ? Object.keys(speakerAnalysis).length : 0;
            const totalUtterances = speakerAnalysis ? Object.values(speakerAnalysis).reduce((sum: number, speaker: any) => sum + (speaker.utterance_count || 0), 0) : 0;

            return (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
                {/* STT 진행 상황 */}
                <div style={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  borderRadius: '20px',
                  padding: '28px',
                    color: 'white',
                  position: 'relative',
                  overflow: 'hidden',
                  boxShadow: '0 8px 32px rgba(102, 126, 234, 0.3)'
                }}>
                  <div style={{
                    position: 'absolute',
                    top: '-30px',
                    right: '-30px',
                    width: '100px',
                    height: '100px',
                    background: 'rgba(255, 255, 255, 0.1)',
                    borderRadius: '50%'
                  }} />
                  <div style={{ position: 'relative', zIndex: 1 }}>
                    <div style={{ fontSize: '32px', marginBottom: '16px' }}>🎤</div>
                    <h3 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '8px', color: 'white' }}>
                      음성 인식 (STT)
                    </h3>
                    <p style={{ fontSize: '14px', opacity: 0.9, marginBottom: '20px', lineHeight: '1.5' }}>
                      ReturnZero VITO API를 통한 음성-텍스트 변환
                    </p>
                    
                    {/* 진행률 */}
                    <div style={{ marginBottom: '20px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                        <span style={{ fontSize: '14px', opacity: 0.9 }}>진행률</span>
                        <span style={{ fontSize: '14px', fontWeight: '600' }}>{stageProgress.stt}%</span>
                      </div>
                <div style={{
                        width: '100%',
                        height: '6px',
                        backgroundColor: 'rgba(255, 255, 255, 0.3)',
                        borderRadius: '3px',
                        overflow: 'hidden'
                      }}>
                        <div style={{
                          width: `${stageProgress.stt}%`,
                          height: '100%',
                          backgroundColor: 'rgba(255, 255, 255, 0.9)',
                          borderRadius: '3px',
                          transition: 'width 0.3s ease'
                        }} />
                </div>
            </div>
                    
                    <div style={{ fontSize: '12px', opacity: 0.8, lineHeight: '1.4' }}>
                      {activeMeeting && activeMeeting.current_stage === 'stt' ? (
                        <div>
                          <div>• 음성 인식 진행 중...</div>
                          <div>• 처리 중: {activeMeeting.title}</div>
                          <div>• 상태: {getStageMessage(activeMeeting.current_stage, activeMeeting.progress)}</div>
          </div>
                      ) : stageProgress.stt === 100 ? (
                        <div>
                          <div>• 음성 인식 완료</div>
                          <div>• 텍스트 변환 성공</div>
                          <div>• 다음 단계 진행 중</div>
                        </div>
                      ) : (
                        <div>
                          <div>• 음성 인식 대기 중</div>
                          <div>• 회의 파일을 업로드하세요</div>
                          <div>• ReturnZero API 준비 완료</div>
        </div>
      )}
                    </div>
                  </div>
                </div>

                {/* 화자 분리 */}
                <div style={{
                  background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
                  borderRadius: '20px',
                  padding: '28px',
                  color: 'white',
                  position: 'relative',
                  overflow: 'hidden',
                  boxShadow: '0 8px 32px rgba(79, 172, 254, 0.3)'
                }}>
                  <div style={{
                    position: 'absolute',
                    top: '-30px',
                    right: '-30px',
                    width: '100px',
                    height: '100px',
                    background: 'rgba(255, 255, 255, 0.1)',
                    borderRadius: '50%'
                  }} />
                  <div style={{ position: 'relative', zIndex: 1 }}>
                    <div style={{ fontSize: '32px', marginBottom: '16px' }}>👥</div>
                    <h3 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '8px', color: 'white' }}>
                      화자 분리
                    </h3>
                    <p style={{ fontSize: '14px', opacity: 0.9, marginBottom: '20px', lineHeight: '1.5' }}>
                      여러 화자의 음성을 개별적으로 분리
                    </p>
                    
                    {/* 진행률 */}
                    <div style={{ marginBottom: '20px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                        <span style={{ fontSize: '14px', opacity: 0.9 }}>진행률</span>
                        <span style={{ fontSize: '14px', fontWeight: '600' }}>{stageProgress.diarization}%</span>
                      </div>
            <div style={{ 
                        width: '100%',
                        height: '6px',
                        backgroundColor: 'rgba(255, 255, 255, 0.3)',
                        borderRadius: '3px',
                        overflow: 'hidden'
                      }}>
                        <div style={{
                          width: `${stageProgress.diarization}%`,
                          height: '100%',
                          backgroundColor: 'rgba(255, 255, 255, 0.9)',
                          borderRadius: '3px',
                          transition: 'width 0.3s ease'
                        }} />
                      </div>
                    </div>
                    
                    <div style={{ fontSize: '12px', opacity: 0.8, lineHeight: '1.4' }}>
                      {activeMeeting && activeMeeting.current_stage === 'diarization' ? (
                        <div>
                          <div>• 화자 분리 진행 중...</div>
                          <div>• 음성 패턴 분석 중</div>
                          <div>• 처리 중: {activeMeeting.title}</div>
                        </div>
                      ) : speakerCount > 0 ? (
                        <div>
                          <div>• 감지된 화자: {speakerCount}명</div>
                          <div>• 총 발화 횟수: {totalUtterances}회</div>
                          <div>• 화자별 발화 시간 분포 완료</div>
                        </div>
                      ) : stageProgress.diarization === 100 ? (
                        <div>
                          <div>• 화자 분리 완료</div>
                          <div>• 개별 화자 식별 성공</div>
                          <div>• 발화 시간 분석 완료</div>
            </div>
          ) : (
            <div>
                          <div>• 화자 분리 대기 중</div>
                          <div>• STT 완료 후 진행 예정</div>
                          <div>• pyannote.audio 준비 완료</div>
                  </div>
                      )}
                    </div>
                  </div>
                    </div>
                    
                {/* AI 에이전트 실행 상태 */}
                        <div style={{ 
                  background: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
                  borderRadius: '20px',
                  padding: '28px',
                  color: '#2d3748',
                  position: 'relative',
                  overflow: 'hidden',
                  boxShadow: '0 8px 32px rgba(168, 237, 234, 0.3)'
                }}>
                  <div style={{
                    position: 'absolute',
                    top: '-30px',
                    right: '-30px',
                    width: '100px',
                    height: '100px',
                    background: 'rgba(255, 255, 255, 0.2)',
                    borderRadius: '50%'
                  }} />
                  <div style={{ position: 'relative', zIndex: 1 }}>
                    <div style={{ fontSize: '32px', marginBottom: '16px' }}>🤖</div>
                    <h3 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '8px' }}>
                      AI 에이전트
                    </h3>
                    <p style={{ fontSize: '14px', opacity: 0.8, marginBottom: '20px', lineHeight: '1.5' }}>
                      5개 AI 에이전트의 순차적 분석
                    </p>
                    
                    {/* 진행률 */}
                    <div style={{ marginBottom: '20px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                        <span style={{ fontSize: '14px', opacity: 0.8 }}>진행률</span>
                        <span style={{ fontSize: '14px', fontWeight: '600' }}>{stageProgress.agent_analysis}%</span>
                        </div>
                        <div style={{ 
                          width: '100%', 
                        height: '6px',
                        backgroundColor: 'rgba(45, 55, 72, 0.2)',
                        borderRadius: '3px',
                          overflow: 'hidden'
                        }}>
                        <div style={{
                          width: `${stageProgress.agent_analysis}%`,
                              height: '100%',
                          backgroundColor: '#2d3748',
                          borderRadius: '3px',
                          transition: 'width 0.3s ease'
                        }} />
                        </div>
                    </div>
                    
                    <div style={{ fontSize: '12px', opacity: 0.7, lineHeight: '1.4' }}>
                      {activeMeeting && activeMeeting.current_stage === 'agent_analysis' ? (
                        <div>
                          <div>• AI 에이전트 분석 진행 중</div>
                          <div>• 회의 내용 다각도 분석</div>
                          <div>• 처리 중: {activeMeeting.title}</div>
                        </div>
                      ) : stageProgress.agent_analysis === 100 ? (
                        <div>
                          <div>• AgendaMiner: ✅ 완료</div>
                          <div>• ClaimChecker: ✅ 완료</div>
                          <div>• CounterArguer: ✅ 완료</div>
                          <div>• EvidenceHunter: ✅ 완료</div>
                          <div>• Summarizer: ✅ 완료</div>
                        </div>
                      ) : stageProgress.agent_analysis > 0 ? (
                        <div>
                          <div>• 에이전트 분석 진행 중...</div>
                          <div>• 안건 추출 및 주장 검증</div>
                          <div>• 반박 논리 및 증거 수집</div>
                        </div>
                      ) : (
                        <div>
                          <div>• AI 에이전트 대기 중</div>
                          <div>• 회의록 생성 완료 후 진행</div>
                          <div>• Solar-Pro2 LLM 준비 완료</div>
                      </div>
                    )}
                    </div>
                  </div>
                </div>

                {/* 최종 보고서 생성 */}
                      <div style={{
                  background: 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)',
                  borderRadius: '20px',
                  padding: '28px',
                  color: '#744210',
                  position: 'relative',
                  overflow: 'hidden',
                  boxShadow: '0 8px 32px rgba(255, 236, 210, 0.4)'
                }}>
                  <div style={{
                    position: 'absolute',
                    top: '-30px',
                    right: '-30px',
                    width: '100px',
                    height: '100px',
                    background: 'rgba(255, 255, 255, 0.3)',
                    borderRadius: '50%'
                  }} />
                  <div style={{ position: 'relative', zIndex: 1 }}>
                    <div style={{ fontSize: '32px', marginBottom: '16px' }}>📊</div>
                    <h3 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '8px' }}>
                      최종 보고서
                    </h3>
                    <p style={{ fontSize: '14px', opacity: 0.8, marginBottom: '20px', lineHeight: '1.5' }}>
                      분석 결과를 종합한 최종 보고서
                    </p>
                
                    {/* 진행률 */}
                    <div style={{ marginBottom: '20px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                        <span style={{ fontSize: '14px', opacity: 0.8 }}>진행률</span>
                        <span style={{ fontSize: '14px', fontWeight: '600' }}>
                          {finalReport ? '100%' : stageProgress.report_generation > 0 ? `${stageProgress.report_generation}%` : '대기 중'}
                        </span>
                      </div>
                      <div style={{
                        width: '100%',
                        height: '6px',
                        backgroundColor: 'rgba(116, 66, 16, 0.2)',
                        borderRadius: '3px',
                        overflow: 'hidden'
                      }}>
                        <div style={{
                          width: finalReport ? '100%' : `${stageProgress.report_generation}%`,
                          height: '100%',
                          backgroundColor: '#744210',
                          borderRadius: '3px',
                          transition: 'width 0.3s ease'
                        }} />
                      </div>
                    </div>
                    
                    {/* 보고서 상태 */}
                    <div style={{ fontSize: '12px', opacity: 0.7, lineHeight: '1.4' }}>
                      {isReportLoading || (activeMeeting && activeMeeting.current_stage === 'report_generation') ? (
                        <div>
                          <div>• 보고서 생성 중...</div>
                          <div>• AI 에이전트 결과 종합</div>
                          <div>• 최종 검토 진행 중</div>
                        </div>
                      ) : finalReport ? (
                        <div>
                          <div>• 실행 요약: ✅ 완료</div>
                          <div>• 핵심 결과: ✅ 완료</div>
                          <div>• 권장사항: ✅ 완료</div>
                          <div>• 액션 아이템: ✅ 완료</div>
                        </div>
                      ) : (
                        <div>
                          <div>• 파이프라인 완료 대기 중</div>
                          <div>• AI 에이전트 분석 필요</div>
                          <div>• 보고서 자동 생성 예정</div>
                      </div>
                    )}
                    </div>
                    
                    {/* 보고서 다운로드 버튼 */}
                    <div style={{ 
                      display: 'flex', 
                      gap: '8px',
                      marginTop: '20px'
                    }}>
                      <button
                        style={{
                          flex: 1,
                          padding: '12px 16px',
                          backgroundColor: finalReport ? 'rgba(255, 255, 255, 0.2)' : 'rgba(116, 66, 16, 0.2)',
                          color: finalReport ? '#744210' : 'rgba(116, 66, 16, 0.5)',
                          border: `1px solid ${finalReport ? 'rgba(255, 255, 255, 0.3)' : 'rgba(116, 66, 16, 0.3)'}`,
                          borderRadius: '10px',
                          fontSize: '12px',
                          fontWeight: '600',
                          cursor: finalReport ? 'pointer' : 'not-allowed',
                          transition: 'all 0.2s ease',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '6px'
                        }}
                        onMouseEnter={(e) => {
                          if (finalReport) {
                            e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.3)';
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (finalReport) {
                            e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.2)';
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
                        다운로드
                      </button>
                      
                      <button
                        style={{
                          flex: 1,
                          padding: '12px 16px',
                          backgroundColor: finalReport ? 'rgba(255, 255, 255, 0.2)' : 'rgba(116, 66, 16, 0.2)',
                          color: finalReport ? '#744210' : 'rgba(116, 66, 16, 0.5)',
                          border: `1px solid ${finalReport ? 'rgba(255, 255, 255, 0.3)' : 'rgba(116, 66, 16, 0.3)'}`,
                          borderRadius: '10px',
                          fontSize: '12px',
                          fontWeight: '600',
                          cursor: finalReport ? 'pointer' : 'not-allowed',
                          transition: 'all 0.2s ease',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '6px'
                        }}
                        onMouseEnter={(e) => {
                          if (finalReport) {
                            e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.3)';
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (finalReport) {
                            e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.2)';
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
                        상세보기
                      </button>
                    </div>
                  </div>
                </div>
            </div>
            );
          })()}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;