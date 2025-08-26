import React, { useState, useCallback, useEffect, useMemo } from 'react';
import { useApi } from '../context/ApiContext';
import { Meeting } from '../types/electron';

const Dashboard: React.FC = () => {
  const { startPipelineAnalysis, getPipelineStatus, getPipelineResults, getAllReports, getReportByJobId, deleteReport, isLoading, error } = useApi();
  const [dragActive, setDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [activePolling, setActivePolling] = useState<Set<string>>(new Set());
  
  // 검색 및 필터링 상태
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'completed' | 'processing' | 'error'>('all');
  const [sortBy, setSortBy] = useState<'date' | 'title' | 'status'>('date');

  // 보고서 상태 (UI 유지용 최소 보완)
  const [isReportLoading, setIsReportLoading] = useState(false);
  const [finalReport, setFinalReport] = useState<any | null>(null);
  const sampleReport = { executive_summary: { key_findings: [], action_items: [] } };

  const generateMeetingReport = useCallback(async (meeting: Meeting) => {
    try {
      return meeting?.pipeline_results ?? sampleReport;
    } catch (e) {
      return sampleReport;
    }
  }, []);

  const filteredAndSortedMeetings = useMemo(() => {
    let arr = [...meetings];
    if (statusFilter !== 'all') {
      arr = arr.filter(m => m.status === statusFilter);
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      arr = arr.filter(m => (m.title || '').toLowerCase().includes(q) || (m.summary || '').toLowerCase().includes(q));
    }
    if (sortBy === 'title') arr.sort((a, b) => (a.title || '').localeCompare(b.title || ''));
    else if (sortBy === 'status') arr.sort((a, b) => (a.status || '').localeCompare(b.status || ''));
    else arr.sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''));
    return arr;
  }, [meetings, searchQuery, statusFilter, sortBy]);

  const stageProgress = {
    agent_analysis: Math.max(0, Math.min(100, meetings.find(m => m.status === 'processing')?.progress || 0))
  };

  // 저장된 보고서 불러오기
  const loadSavedReports = useCallback(async () => {
    try {
      const reports = await getAllReports();
      const convertedMeetings: Meeting[] = reports.map(report => ({
        id: report.job_id || report.id,
        title: report.title || report.original_filename || 'Unknown Meeting',
        date: report.created_at ? new Date(report.created_at).toISOString().split('T')[0] : new Date().toISOString().split('T')[0],
        duration: report.duration_seconds ? `${Math.round(report.duration_seconds / 60)}분` : '알 수 없음',
        speakers: report.num_speakers || 0,
        status: report.status === 'completed' ? 'completed' as const : 
               report.status === 'processing' ? 'processing' as const : 
               report.status === 'failed' ? 'error' as const : 'processing' as const,
        summary: report.status === 'completed' ? '분석 완료!' :
                report.status === 'failed' ? `오류: ${report.error_message || '알 수 없는 오류'}` :
                report.current_stage ? getStageMessage(report.current_stage, report.progress || 0) : '처리 중...',
        job_id: report.job_id,
        progress: report.progress || (report.status === 'completed' ? 100 : 0),
        current_stage: report.current_stage || (report.status === 'completed' ? 'completed' : 'unknown'),
        error_message: report.error_message,
        created_at: report.created_at || new Date().toISOString(),
        file_path: report.file_path || '',
        file_size: report.file_size || 0,
        pipeline_results: report.results || null
      } as any));
      
      setMeetings(convertedMeetings);
      
      // 처리 중인 작업들에 대해 폴링 시작
      const processingReports = convertedMeetings.filter(m => m.status === 'processing' && m.job_id);
      if (processingReports.length > 0) {
        setActivePolling(prev => {
          const newSet = new Set(prev);
          processingReports.forEach(report => {
            if (report.job_id) {
              newSet.add(report.job_id);
            }
          });
          return newSet;
        });
      }
      
      console.log(`✅ 저장된 보고서 ${reports.length}개 불러옴`);
    } catch (err) {
      console.error('저장된 보고서 불러오기 실패:', err);
      // 오류가 발생해도 빈 배열로 초기화하여 사용자 경험을 해치지 않음
      setMeetings([]);
    }
  }, [getAllReports]);

  // 컴포넌트 마운트 시 저장된 보고서 불러오기
  useEffect(() => {
    loadSavedReports();
  }, [loadSavedReports]);

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
        
        // 완료 시 성공 메시지 표시
        if (status.status === 'completed') {
          console.log(`✅ 회의 분석 완료: ${meetingId}`);
        }
      }
    } catch (err) {
      console.error('파이프라인 상태 폴링 오류:', err);
      
      // 네트워크 오류 등의 경우에는 계속 재시도
      // 너무 많은 실패가 발생하면 폴링 중단을 고려할 수 있음
    }
  }, [getPipelineStatus, activePolling]);

  // 단계별 메시지 생성
  const getStageMessage = (stage: string, progress: number) => {
    const stageMessages: Record<string, string> = {
      'validation': '파일 검증 중...',
      'stt_processing': 'STT 음성 인식 중... (시간이 오래 걸릴 수 있습니다)',
      'diarization': '화자 분리 중...',
      'transcript_processing': '전사록 처리 중...',
      'agent_analysis': 'AI 에이전트 분석 중... (5개 에이전트 동시 실행)',
      'report_generation': '최종 보고서 생성 중...',
      'storage': '결과 저장 중...',
      'completed': '분석 완료!',
      'uploading': '파일 업로드 중...',
      'restarting': '분석을 다시 시작하는 중...'
    };
    
    const message = stageMessages[stage] || '처리 중...';
    return progress ? `${message} (${progress}%)` : message;
  };

  // 회의 목록 로드
  useEffect(() => {
    const intervals: NodeJS.Timeout[] = [];

    Array.from(activePolling).forEach(jobId => {
      const meetingId = meetings.find(m => m.job_id === jobId)?.id;
      if (meetingId) {
        const interval = setInterval(() => {
          pollPipelineStatus(jobId, meetingId);
        }, 2000); // 2초마다 폴링
        intervals.push(interval);
      }
    });

    return () => {
      intervals.forEach(clearInterval);
    };
  }, [activePolling, meetings, pollPipelineStatus]);

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

  // 지원하는 오디오 포맷 확장
  const SUPPORTED_AUDIO_EXTENSIONS = [
    'mp3', 'wav', 'm4a', 'flac', 'ogg', 'opus', 'webm',
    'aac', 'wma', 'amr', 'ac3', 'aiff', 'au', 'oga',
    'mp2', 'weba', '3gp', 'spx', 'ape', 'mka'
  ];

  // 지원하는 비디오 포맷 확장
  const SUPPORTED_VIDEO_EXTENSIONS = [
    'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'wmv',
    'mpg', 'mpeg', 'm4v', 'ogv', 'mts', 'ts', 'vob',
    '3gp', '3g2', 'divx', 'xvid', 'asf', 'rm', 'rmvb'
  ];

  // MIME 타입 매핑 (브라우저 호환성 향상)
  const MIME_TYPE_MAP: Record<string, string> = {
    'm4a': 'audio/mp4',
    'wav': 'audio/wav',
    'mp3': 'audio/mpeg',
    'flac': 'audio/flac',
    'ogg': 'audio/ogg',
    'opus': 'audio/opus',
    'webm': 'audio/webm',
    'aac': 'audio/aac',
    'wma': 'audio/x-ms-wma',
    'amr': 'audio/amr',
    'mp4': 'video/mp4',
    'avi': 'video/x-msvideo',
    'mov': 'video/quicktime',
    'mkv': 'video/x-matroska'
  };

  const handleFiles = async (files: FileList) => {
    const file = files[0];
    if (!file) return;

    console.log('=== 파일 업로드 시작 ===');
    console.log('파일 이름:', file.name);
    console.log('파일 크기:', (file.size / 1024 / 1024).toFixed(2), 'MB');
    console.log('브라우저 MIME 타입:', file.type || 'undefined');
    
    // 파일 확장자 추출
    const fileExtension = file.name.toLowerCase().split('.').pop() || '';
    console.log('파일 확장자:', fileExtension);

    // 모든 지원 확장자 통합
    const allSupportedExtensions = [...SUPPORTED_AUDIO_EXTENSIONS, ...SUPPORTED_VIDEO_EXTENSIONS];

    // 확장자 기반 검증 (MIME 타입 무시)
    if (!allSupportedExtensions.includes(fileExtension)) {
      console.error('지원되지 않는 파일 형식:', fileExtension);
      const audioFormats = SUPPORTED_AUDIO_EXTENSIONS.slice(0, 8).join(', ');
      const videoFormats = SUPPORTED_VIDEO_EXTENSIONS.slice(0, 5).join(', ');
      alert(`지원되지 않는 파일 형식입니다.\n\n오디오: ${audioFormats} 등\n비디오: ${videoFormats} 등\n\n현재 파일: .${fileExtension}`);
      return;
    }

    console.log('파일 검증 통과');

    // 파일 크기 검증 (500MB로 증가)
    const maxSize = 500 * 1024 * 1024; // 500MB
    if (file.size > maxSize) {
      alert(`파일 크기가 너무 큽니다. 500MB 이하의 파일을 업로드해주세요.\n현재 파일: ${(file.size / 1024 / 1024).toFixed(2)}MB`);
      return;
    }

    try {
      // 진행률 표시 시작
      setUploadProgress(0);
      
      // 임시 회의 추가 (업로드 중 표시)
      const tempMeetingId = `temp-${Date.now()}`;
      const tempMeeting: Meeting = {
        id: tempMeetingId,
        title: file.name.replace(/\.[^/.]+$/, ''),
        date: new Date().toISOString().split('T')[0],
        duration: '분석 중...',
        speakers: 0,
        status: 'processing',
        summary: '업로드 및 분석 대기 중...',
        job_id: tempMeetingId,
        progress: 0,
        current_stage: '업로드 준비',
        created_at: new Date().toISOString(),
        file_path: '',
        file_size: file.size
      } as any;
      setMeetings(prev => [tempMeeting, ...prev]);

      console.log('파이프라인 분석 시작 중...');
      console.log('예상 MIME 타입:', MIME_TYPE_MAP[fileExtension || ''] || file.type || 'application/octet-stream');
      
      // 파이프라인 분석 시작
      const result = await startPipelineAnalysis(file);
      
      console.log('파이프라인 분석 시작 성공:', result);
      
      // 업로드 완료 후 회의 정보 업데이트
      setMeetings(prev => prev.map(meeting => 
        meeting.id === tempMeetingId 
          ? {
              ...meeting,
              job_id: result.job_id,
              summary: '분석 시작됨 - 파일 검증 중...',
              progress: 5
            }
          : meeting
      ));

      // 폴링 시작
      setActivePolling(prev => {
        const newSet = new Set(prev);
        newSet.add(result.job_id);
        return newSet;
      });
      
      setUploadProgress(100);
      setTimeout(() => setUploadProgress(null), 1000);
      
    } catch (err) {
      console.error('파이프라인 분석 시작 실패:', err);
      console.error('에러 상세:', {
        message: err instanceof Error ? err.message : String(err),
        stack: err instanceof Error ? err.stack : undefined,
        type: typeof err
      });
      alert(`분석 시작에 실패했습니다: ${err instanceof Error ? err.message : '알 수 없는 오류'}`);
      
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


  const handleRetryAnalysis = async (meeting: Meeting) => {
    if (!meeting.job_id) {
      alert('재시도할 수 없습니다. Job ID가 없습니다.');
      return;
    }

    if (confirm('이 회의 분석을 다시 시작하시겠습니까?')) {
      try {
        // 회의 상태를 다시 처리 중으로 변경
        setMeetings(prev => prev.map(m => 
          m.id === meeting.id 
            ? {
                ...m,
                status: 'processing' as const,
                progress: 0,
                current_stage: 'restarting',
                error_message: undefined,
                summary: '분석을 다시 시작합니다...'
              }
            : m
        ));

        // 폴링 시작
        setActivePolling(prev => {
          const newSet = new Set(prev);
          newSet.add(meeting.job_id!);
          return newSet;
        });

        console.log(`재시도 시작: ${meeting.job_id}`);
        
      } catch (error) {
        console.error('재시도 시작 실패:', error);
        alert('재시도를 시작할 수 없습니다. 잠시 후 다시 시도해주세요.');
        
        // 상태를 다시 에러로 되돌리기
        setMeetings(prev => prev.map(m => 
          m.id === meeting.id 
            ? {
                ...m,
                status: 'error' as const,
                error_message: meeting.error_message
              }
            : m
        ));
      }
    }
  };

  const handleDeleteReport = async (meeting: Meeting) => {
    if (!meeting.job_id) {
      alert('삭제할 수 없습니다. Job ID가 없습니다.');
      return;
    }

    if (confirm(`"${meeting.title}" 보고서를 완전히 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.`)) {
      try {
        await deleteReport(meeting.job_id);
        
        // 로컬 상태에서도 제거
        setMeetings(prev => prev.filter(m => m.id !== meeting.id));
        
        // 폴링도 중단
        setActivePolling(prev => {
          const newSet = new Set(prev);
          newSet.delete(meeting.job_id!);
          return newSet;
        });
        
        console.log(`✅ 보고서 삭제 완료: ${meeting.title}`);
        alert('보고서가 성공적으로 삭제되었습니다.');
        
      } catch (error) {
        console.error('보고서 삭제 실패:', error);
        alert(`보고서 삭제에 실패했습니다: ${error instanceof Error ? error.message : '알 수 없는 오류'}`);
      }
    }
  };

  const handleDownloadResults = async (meeting: Meeting, format: 'json' | 'txt' | 'csv' = 'json') => {
    if (!meeting.job_id || meeting.status !== 'completed') {
      alert('완료된 분석 결과만 다운로드할 수 있습니다.');
      return;
    }

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
  };

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
            marginTop: '16px',
            padding: '16px',
            backgroundColor: 'var(--bg-secondary)',
            borderRadius: '8px',
            border: '1px solid var(--border-primary)'
          }}>
            <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '8px' }}>
              🚀 시작하기
            </h3>
            <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '12px' }}>
              파일을 업로드하면 다음 단계로 자동 분석됩니다:
            </p>
            <ol style={{ fontSize: '14px', color: 'var(--text-secondary)', paddingLeft: '20px' }}>
              <li>📄 파일 검증</li>
              <li>🎵 음성 인식 (ReturnZero VITO API)</li>
              <li>👥 화자 분리</li>
              <li>📝 전사록 생성</li>
              <li>🤖 AI 에이전트 분석 (5개 에이전트)</li>
              <li>📊 최종 보고서 생성</li>
            </ol>
            <div style={{ marginTop: '12px', fontSize: '12px', color: 'var(--text-muted)' }}>
              ⏱️ 분석 시간: 일반적으로 3-5분, 큰 파일은 10분 이상 소요될 수 있습니다.
              <br />
              📁 지원 파일: 최대 500MB까지 업로드 가능합니다.
            </div>
          </div>
      </div>

      {/* 파일 업로드 영역 */}
      <div className="card" style={{ marginBottom: '32px' }}>
        <div className="card-header">
          <h2 className="card-title">📋 회의 목록</h2>
          <p className="card-description">
            업로드된 회의 파일들의 분석 현황을 확인하세요.
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
          {meetings.length === 0 ? (
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>📁</div>
              <h3 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '8px' }}>
                파일을 여기에 드래그하세요
              </h3>
              <p style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>
                또는 클릭하여 파일을 선택하세요
              </p>
              <div style={{ fontSize: '14px', color: 'var(--text-muted)' }}>
                지원 형식: MP3, WAV, M4A, MP4, AVI, MOV (최대 500MB)
              </div>
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

        {/* 업로드 진행률 */}
        {uploadProgress !== null && (
          <div style={{ marginTop: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span>파일 업로드 및 분석 시작 중...</span>
              <span>{uploadProgress}%</span>
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
                            <div style={{ fontSize: '13px', lineHeight: '1.5', opacity: 0.9 }}>표시할 핵심 결과가 없습니다.</div>
                          )}
                        </div>
                        <div style={{ 
                          marginTop: '8px', 
                          fontSize: '12px', 
                          color: 'var(--text-secondary)',
                          textAlign: 'center'
                        }}>
                          큰 파일의 경우 업로드와 분석에 수 분이 소요될 수 있습니다.
                          <br />
                          업로드가 완료되면 자동으로 분석이 시작됩니다.
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        </div>
      </div>

      {/* 통계 카드들 */}
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
            <h3 className="card-title">오류</h3>
            <div style={{ fontSize: '32px', fontWeight: 700, color: 'var(--accent-danger)' }}>
              {meetings.filter(m => m.status === 'error').length}
            </div>
          </div>
        </div>
      </div>


      {/* 최근 회의록 목록 */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">최근 회의록</h2>
          <p className="card-description">
            업로드된 회의록을 확인하고 상세 분석 결과를 확인하세요.
          </p>
        </div>

        {/* 검색 및 필터링 컨트롤 */}
        {meetings.length > 0 && (
          <div style={{ 
            marginTop: '16px', 
            padding: '16px',
            backgroundColor: 'var(--bg-secondary)',
            borderRadius: '8px',
            border: '1px solid var(--border-primary)'
          }}>
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: '2fr 1fr 1fr', 
              gap: '12px',
              alignItems: 'end'
            }}>
              {/* 검색 입력 */}
              <div>
                <label style={{ 
                  display: 'block', 
                  fontSize: '12px', 
                  fontWeight: 600, 
                  marginBottom: '4px',
                  color: 'var(--text-secondary)'
                }}>
                  검색
                </label>
                <input
                  type="text"
                  placeholder="제목, 내용, 날짜로 검색..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    border: '1px solid var(--border-primary)',
                    borderRadius: '4px',
                    backgroundColor: 'var(--bg-primary)',
                    color: 'var(--text-primary)',
                    fontSize: '14px'
                  }}
                />
              </div>
              
              {/* 상태 필터 */}
              <div>
                <label style={{ 
                  display: 'block', 
                  fontSize: '12px', 
                  fontWeight: 600, 
                  marginBottom: '4px',
                  color: 'var(--text-secondary)'
                }}>
                  상태 필터
                </label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as any)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    border: '1px solid var(--border-primary)',
                    borderRadius: '4px',
                    backgroundColor: 'var(--bg-primary)',
                    color: 'var(--text-primary)',
                    fontSize: '14px'
                  }}
                >
                  <option value="all">전체</option>
                  <option value="processing">처리 중</option>
                  <option value="completed">완료</option>
                  <option value="error">오류</option>
                </select>
              </div>
              
              {/* 정렬 옵션 */}
              <div>
                <label style={{ 
                  display: 'block', 
                  fontSize: '12px', 
                  fontWeight: 600, 
                  marginBottom: '4px',
                  color: 'var(--text-secondary)'
                }}>
                  정렬
                </label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    border: '1px solid var(--border-primary)',
                    borderRadius: '4px',
                    backgroundColor: 'var(--bg-primary)',
                    color: 'var(--text-primary)',
                    fontSize: '14px'
                  }}
                >
                  <option value="date">날짜순</option>
                  <option value="title">제목순</option>
                  <option value="status">상태순</option>
                </select>
              </div>
            </div>
            
            {/* 검색 결과 요약 */}
            <div style={{ 
              marginTop: '12px', 
              fontSize: '12px', 
              color: 'var(--text-secondary)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <span>
                {filteredAndSortedMeetings.length}개의 회의 (총 {meetings.length}개 중)
                {searchQuery && ` · "${searchQuery}" 검색 결과`}
                {statusFilter !== 'all' && ` · ${statusFilter} 상태만`}
              </span>
              
              {(searchQuery || statusFilter !== 'all') && (
                <button
                  onClick={() => {
                    setSearchQuery('');
                    setStatusFilter('all');
                  }}
                  style={{
                    padding: '4px 8px',
                    fontSize: '11px',
                    backgroundColor: 'transparent',
                    color: 'var(--accent-primary)',
                    border: '1px solid var(--accent-primary)',
                    borderRadius: '3px',
                    cursor: 'pointer'
                  }}
                >
                  필터 초기화
                </button>
              )}
            </div>
          </div>
        )}

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
          ) : filteredAndSortedMeetings.length === 0 ? (
            <div style={{ 
              textAlign: 'center', 
              padding: '48px', 
              color: 'var(--text-secondary)' 
            }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔍</div>
              <h3>검색 결과가 없습니다</h3>
              <p>다른 검색어를 시도하거나 필터를 조정해보세요.</p>
              <button
                onClick={() => {
                  setSearchQuery('');
                  setStatusFilter('all');
                }}
                style={{
                  marginTop: '16px',
                  padding: '8px 16px',
                  backgroundColor: 'var(--accent-primary)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                모든 회의 보기
              </button>
            </div>
          ) : (
            <div>
              {filteredAndSortedMeetings.map((meeting) => (
                <div key={meeting.id} className="message" style={{ marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div className="message-avatar">
                    {meeting.status === 'completed' ? '✅' : meeting.status === 'processing' ? '⏳' : '❌'}
                  </div>
                  <div className="message-body" style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <div style={{ fontWeight: 600 }}>{meeting.title}</div>
                        <div style={{ fontSize: '12px', opacity: 0.8 }}>{meeting.summary}</div>
                      </div>
                      <div style={{ fontSize: '12px', opacity: 0.8 }}>{meeting.progress}%</div>
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