import React, { createContext, useContext, useState, ReactNode } from 'react';
import { Meeting } from '../types/electron';

// API 관련 타입 정의
export interface ApiKey {
  provider: string;
  index?: number;
  masked_value: string;
  is_valid?: boolean;
}

export interface STTOptions {
  engine?: string;
  language?: string;
  enable_diarization?: boolean;
}

export interface AgentAnalysisOptions {
  analysis_options?: Record<string, any>;
  priority?: string;
}

export interface SearchOptions {
  top_k?: number;
  filters?: Record<string, any>;
  sources?: string[];
}

export interface ApiService {
  saveApiKey: (provider: string, key: string, index?: number) => Promise<any>;
  getApiKeys: (provider?: string) => Promise<ApiKey[]>;
  removeApiKey: (provider: string, index?: number) => Promise<any>;
  testApiKey: (provider: string, key: string) => Promise<any>;
}

export interface PipelineStatus {
  job_id: string;
  status: 'started' | 'processing' | 'completed' | 'failed';
  current_stage: string;
  progress: number;
  started_at?: string;
  completed_at?: string;
  error?: string;
}

export interface PipelineResults {
  job_id: string;
  status: string;
  completed_at?: string;
  results: any;
}

// 추가: 채팅/검색/상세 API 타입
export interface ChatResponse {
  response: string;
  sources: string[];
  confidence: number;
  processing_time: number;
  search_results_count: number;
}

interface ApiContextType {
  apiKeys: ApiKey[];
  isLoading: boolean;
  error: string | null;
  
  // API 키 관리
  saveApiKey: (provider: string, key: string, index?: number) => Promise<void>;
  loadApiKeys: () => Promise<void>;
  removeApiKey: (provider: string, index?: number) => Promise<void>;
  testApiKey: (provider: string, key: string) => Promise<boolean>;
  
  // 오디오 및 STT
  uploadAudio: (file: File, onProgress?: (progress: number) => void) => Promise<any>;
  processSTT: (fileId: number, options?: STTOptions) => Promise<any>;
  
  // 파일 업로드 및 회의 관리
  uploadFile: (file: File) => Promise<{ success: boolean; job_id: string; error?: string }>;
  getMeetings: () => Promise<Meeting[]>;
  
  // 파이프라인 분석
  startPipelineAnalysis: (file: File) => Promise<{ job_id: string; message: string }>;
  getPipelineStatus: (jobId: string) => Promise<PipelineStatus>;
  getPipelineResults: (jobId: string) => Promise<PipelineResults>;
  getAllReports: () => Promise<any[]>;
  getReportByJobId: (jobId: string) => Promise<any>;
  deleteReport: (jobId: string) => Promise<void>;

  // 검색/채팅
  searchDocuments: (query: string, options?: SearchOptions) => Promise<any>;
  getChatResponse: (query: string) => Promise<ChatResponse>;

  // 동기화(설정 페이지)
  syncNotion: () => Promise<any>;
  syncGitHub: () => Promise<any>;
  syncGoogleDrive: () => Promise<any>;
  getSyncStatus: () => Promise<any>;

  // 상세 페이지용(임시 플래그)
  getTranscript: (jobId: string) => Promise<any>;
  getAgentResults: (jobId: string) => Promise<any>;
  getAgentStatus: (jobId: string) => Promise<any>;
}

const ApiContext = createContext<ApiContextType | undefined>(undefined);

export const useApi = (): ApiContextType => {
  const context = useContext(ApiContext);
  if (!context) {
    throw new Error('useApi must be used within an ApiProvider');
  }
  return context;
};

interface ApiProviderProps {
  children: ReactNode;
}

export const ApiProvider: React.FC<ApiProviderProps> = ({ children }) => {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api';

  const apiCall = async (endpoint: string, options: RequestInit = {}) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  };

  const saveApiKey = async (provider: string, key: string, index?: number): Promise<void> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams({ provider, key });
      if (index !== undefined) {
        params.append('index', index.toString());
      }

      await apiCall('/settings/api-keys', {
        method: 'POST',
        body: params,
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      // 성공 후 API 키 목록 새로고침
      await loadApiKeys();
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const loadApiKeys = async (): Promise<void> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await apiCall('/settings/api-keys');
      
      // API 키 데이터를 평면 배열로 변환
      const keys: ApiKey[] = [];
      for (const [provider, providerKeys] of Object.entries(response.keys || {})) {
        if (typeof providerKeys === 'object' && providerKeys) {
          for (const [keyName, maskedValue] of Object.entries(providerKeys as Record<string, string>)) {
            const indexMatch = keyName.match(/_(\d+)$/);
            keys.push({
              provider,
              index: indexMatch ? parseInt(indexMatch[1], 10) : undefined,
              masked_value: maskedValue,
            });
          }
        }
      }
      
      setApiKeys(keys);
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const removeApiKey = async (provider: string, index?: number): Promise<void> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams({ provider });
      if (index !== undefined) {
        params.append('index', index.toString());
      }

      await apiCall(`/settings/api-keys?${params}`, {
        method: 'DELETE',
      });

      // 성공 후 API 키 목록 새로고침
      await loadApiKeys();
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const testApiKey = async (provider: string, key: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams({ provider, key });
      const response = await apiCall('/settings/api-keys/test', {
        method: 'POST',
        body: params,
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      
      return response.status === 'success';
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const uploadAudio = async (file: File, onProgress?: (progress: number) => void): Promise<any> => {
    setIsLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE_URL}/audio/upload`, {
        method: 'POST',
        body: formData,
        // FormData 사용시 Content-Type 헤더는 브라우저가 자동으로 설정
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      // 성공적으로 업로드된 경우 진행률을 100%로 설정
      if (onProgress) {
        onProgress(100);
      }
      
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : '파일 업로드에 실패했습니다.');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const startPipelineAnalysis = async (file: File): Promise<{ job_id: string; message: string }> => {
    setIsLoading(true);
    setError(null);

    try {
      // 파일 확장자 추출
      const extension = file.name.toLowerCase().split('.').pop() || '';
      
      // MIME 타입 매핑 (브라우저 호환성 향상)
      const mimeTypeMap: Record<string, string> = {
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
      
      // MIME 타입 결정 (우선순위: 매핑 > 브라우저 타입 > 기본값)
      let mimeType = file.type;
      if (!mimeType || mimeType === '' || mimeType === 'application/octet-stream') {
        mimeType = mimeTypeMap[extension] || 'application/octet-stream';
        console.log(`MIME 타입 보정: ${file.type || 'empty'} → ${mimeType}`);
      }
      
      // 파일 재생성 (MIME 타입 명시)
      let fileToUpload = file;
      if (mimeType !== file.type) {
        const fileBuffer = await file.arrayBuffer();
        const correctedBlob = new Blob([fileBuffer], { type: mimeType });
        fileToUpload = new File([correctedBlob], file.name, {
          type: mimeType,
          lastModified: file.lastModified
        });
        console.log('파일 MIME 타입 보정 완료');
      }
      
      const formData = new FormData();
      formData.append('file', fileToUpload);

      console.log('FormData 생성 완료');
      console.log('업로드 파일 정보:');
      console.log('  원본 MIME:', file.type || 'empty');
      console.log('  보정 MIME:', mimeType);
      console.log('  파일명:', file.name);
      console.log('  크기:', (file.size / 1024 / 1024).toFixed(2), 'MB');

      console.log('API 요청 시작:', `${API_BASE_URL}/meetings/analyze-upload`);

      // 파일 크기에 따른 동적 타임아웃 계산
      const fileSizeMB = file.size / (1024 * 1024);
      const baseTimeout = 30000; // 기본 30초
      const sizeTimeout = Math.max(fileSizeMB * 2000, 60000); // MB당 2초, 최소 60초
      const maxTimeout = 300000; // 최대 5분
      const dynamicTimeout = Math.min(baseTimeout + sizeTimeout, maxTimeout);
      
      console.log(`동적 타임아웃 설정: ${dynamicTimeout/1000}초 (파일 크기: ${fileSizeMB.toFixed(1)}MB)`);

      // AbortController로 동적 타임아웃 처리
      const controller = new AbortController();
      const timeoutId = setTimeout(() => {
        console.log(`업로드 타임아웃! ${dynamicTimeout/1000}초 경과`);
        controller.abort();
      }, dynamicTimeout);

      try {
        const response = await fetch(`${API_BASE_URL}/meetings/analyze-upload`, {
          method: 'POST',
          body: formData,
          signal: controller.signal,
          // FormData 사용시 Content-Type 헤더를 명시적으로 설정하지 않아야 함
          // 브라우저가 boundary를 포함한 multipart/form-data로 자동 설정
        });
        
        clearTimeout(timeoutId);
        console.log('API 응답 수신 완료!');
        console.log('API 응답 상태:', response.status, response.statusText);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

        const result = await response.json();
        console.log('API 응답 성공:', result);
        
        return {
          job_id: result.job_id || result.id,
          message: result.message || '분석이 시작되었습니다.'
        };
        
      } catch (fetchError) {
        clearTimeout(timeoutId);
        
        if (fetchError instanceof Error && fetchError.name === 'AbortError') {
          console.error(`업로드가 타임아웃되었습니다 (${dynamicTimeout/1000}초)`);
          throw new Error(`업로드 시간이 초과되었습니다. 파일 크기가 큰 경우 시간이 오래 걸릴 수 있습니다. (${dynamicTimeout/1000}초 제한)`);
        }
        
        console.error('Fetch 에러:', fetchError);
        throw fetchError;
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : '파이프라인 분석 시작에 실패했습니다.');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const getPipelineStatus = async (jobId: string): Promise<PipelineStatus> => {
    try {
      const response = await fetch(`${API_BASE_URL}/pipeline/status/${jobId}`);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : '상태 조회에 실패했습니다.');
    }
  };

  const getPipelineResults = async (jobId: string): Promise<PipelineResults> => {
    try {
      const response = await fetch(`${API_BASE_URL}/pipeline/results/${jobId}`);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : '결과 조회에 실패했습니다.');
    }
  };

  // 보고서 관련 API 함수들
  const getAllReports = async (): Promise<any[]> => {
    try {
      const response = await fetch(`${API_BASE_URL}/reports`);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return result.reports || [];
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : '보고서 목록 조회에 실패했습니다.');
    }
  };

  const getReportByJobId = async (jobId: string): Promise<any> => {
    try {
      const response = await fetch(`${API_BASE_URL}/reports/${jobId}`);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : '에이전트 결과 조회에 실패했습니다.');
    }
  };

  // 검색 기능
  const hybridSearch = async (query: string, options: SearchOptions = {}): Promise<any> => {
    try {
      // 백엔드의 hybrid_search가 작동하지 않으므로 knowledge/projects API 사용
      const projectsResponse = await fetch(`${API_BASE_URL}/knowledge/projects`);
      
      if (!projectsResponse.ok) {
        throw new Error('프로젝트 데이터를 가져올 수 없습니다.');
      }

      const projectsData = await projectsResponse.json();
      const searchTerm = query.trim().toLowerCase();
      
      // 모든 프로젝트 소스에서 검색
      const allProjects = [
        ...(projectsData.projects?.github || []),
        ...(projectsData.projects?.notion || []),
        ...(projectsData.projects?.gdrive || [])
      ];
      
      const matchedProjects = allProjects.filter((project: any) => 
        project.title.toLowerCase().includes(searchTerm) ||
        project.description.toLowerCase().includes(searchTerm) ||
        project.type.toLowerCase().includes(searchTerm)
      );
      
      // 검색 결과 반환
      return {
        results: matchedProjects,
        query: query,
        total_count: matchedProjects.length,
        sources: matchedProjects.map((p: any) => p.title)
      };
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : '보고서 조회에 실패했습니다.');
    }
  };

  const deleteReport = async (jobId: string): Promise<void> => {
    try {
      const response = await fetch(`${API_BASE_URL}/reports/${jobId}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : '벡터 검색에 실패했습니다.');
    }
  };

  const keywordSearch = async (query: string, options: SearchOptions = {}): Promise<any> => {
    try {
      const response = await fetch(`${API_BASE_URL}/search/keyword`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, ...options }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : '키워드 검색에 실패했습니다.');
    }
  };

  // 지식베이스 동기화
  const syncNotion = async (): Promise<any> => {
    try {
      const response = await fetch(`${API_BASE_URL}/sync/notion`, { method: 'POST' });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : 'Notion 동기화에 실패했습니다.');
    }
  };

  const syncGitHub = async (): Promise<any> => {
    try {
      const response = await fetch(`${API_BASE_URL}/sync/github`, { method: 'POST' });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : 'GitHub 동기화에 실패했습니다.');
    }
  };

  const syncGoogleDrive = async (): Promise<any> => {
    try {
      const response = await fetch(`${API_BASE_URL}/sync/drive`, { method: 'POST' });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : 'Google Drive 동기화에 실패했습니다.');
    }
  };

  const getSyncStatus = async (): Promise<any> => {
    try {
      const response = await fetch(`${API_BASE_URL}/sync/status`);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : '동기화 상태 조회에 실패했습니다.');
    }
  };

  // 트랜스크립트
  const getTranscripts = async (): Promise<any> => {
    try {
      const response = await fetch(`${API_BASE_URL}/transcripts`);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : '트랜스크립트 목록 조회에 실패했습니다.');
    }
  };

  const getTranscript = async (id: number): Promise<any> => {
    try {
      const response = await fetch(`${API_BASE_URL}/transcripts/${id}`);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : '트랜스크립트 조회에 실패했습니다.');
    }
  };

  // 파일 업로드 및 회의 관리
  const uploadFile = async (file: File): Promise<{ success: boolean; job_id: string; error?: string }> => {
    try {
      const formData = new FormData();
      formData.append('file', file);

      // 백엔드의 실제 API 엔드포인트 사용
      const response = await fetch(`${API_BASE_URL}/meetings/analyze-upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return { success: true, job_id: result.job_id };
    } catch (err) {
      return { 
        success: false, 
        job_id: '', 
        error: err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.' 
      };
    }
  };

  const getMeetings = async (): Promise<Meeting[]> => {
    try {
      // 백엔드의 실제 API 엔드포인트 사용
      const response = await fetch(`${API_BASE_URL}/pipeline/jobs`);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // 백엔드 데이터를 프론트엔드 Meeting 타입에 맞게 변환
      const meetings: Meeting[] = data.jobs?.map((job: any) => ({
        id: job.job_id || job.id,
        job_id: job.job_id || job.id,
        title: job.file_name || job.title || `회의 ${job.job_id}`,
        status: job.status || 'processing',
        progress: job.progress || 0,
        current_stage: job.current_stage || '업로드 완료',
        summary: job.summary || '분석 진행 중...',
        created_at: job.created_at || new Date().toISOString(),
        file_path: job.file_path || '',
        file_size: job.file_size || 0,
        pipeline_results: job.results || null,
        error_message: job.error_message || null
      })) || [];

      return meetings;
    } catch (err) {
      console.error('회의 목록 조회 오류:', err);
      return [];
    }
  };

  // 검색 및 채팅
  const searchDocuments = async (query: string, options?: SearchOptions): Promise<any> => {
    try {
      const raw = (query ?? '').trim();
      const isPunctOnly = !/[A-Za-z0-9\u3131-\uD7A3]/.test(raw); // 문자/숫자 없으면 true
      const effectiveQuery = isPunctOnly ? query : raw;

      const body = {
        query: effectiveQuery,
        top_k: options?.top_k ?? 5,
        search_type: 'hybrid',
        filters: options?.filters ?? null,
        sources: options?.sources ?? null,
      };

      const resp = await fetch(`${API_BASE_URL}/v1/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (!resp.ok) {
        const errJson = await resp.json().catch(() => ({}));
        throw new Error(errJson.detail || `HTTP ${resp.status}`);
      }

      const data = await resp.json();
      const docs = data?.results?.results?.documents ?? [];
      return {
        results: docs,
        query,
        total_count: docs.length,
        sources: docs.map((d: any) => d?.metadata?.title).filter(Boolean),
      };
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : '문서 검색에 실패했습니다.');
    }
  };

  const getChatResponse = async (query: string): Promise<any> => {
    try {
      const raw = (query ?? '').trim();
      const isPunctOnly = !/[A-Za-z0-9\u3131-\uD7A3]/.test(raw);
      const effectiveQuestion = isPunctOnly ? query : raw;

      const resp = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: effectiveQuestion,
          top_k: 5,
          search_type: 'hybrid',
        }),
      });

      if (!resp.ok) {
        const errJson = await resp.json().catch(() => ({}));
        throw new Error(errJson.detail || `HTTP ${resp.status}`);
      }

      const data = await resp.json();
      return {
        response: data?.answer ?? '',
        sources: data?.sources ?? [],
        confidence: 0.0,
        processing_time: data?.processing_time ?? 0,
        search_results_count: Array.isArray(data?.sources) ? data.sources.length : 0,
      };
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : '챗봇 응답 생성에 실패했습니다.');
    }
  };

  const contextValue: ApiContextType = {
    apiKeys,
    isLoading,
    error,
    
    // API 키 관리
    saveApiKey,
    loadApiKeys,
    removeApiKey,
    testApiKey,
    
    // 오디오 및 STT
    uploadAudio,
    processSTT: async (_fileId: number, _options?: STTOptions) => {
      throw new Error('processSTT is not implemented');
    },
    
    // 파일 업로드 및 회의 관리
    uploadFile,
    getMeetings,
    
    // 파이프라인 분석
    startPipelineAnalysis,
    getPipelineStatus,
    getPipelineResults,
    getAllReports,
    getReportByJobId,
    deleteReport,

    // 검색/채팅
    searchDocuments,
    getChatResponse,

    // 동기화(설정 페이지) - 임시 구현
    syncNotion: async () => ({ success: false, message: 'Not implemented' }),
    syncGitHub: async () => ({ success: false, message: 'Not implemented' }),
    syncGoogleDrive: async () => ({ success: false, message: 'Not implemented' }),
    getSyncStatus: async () => ({ status: 'idle' }),

    // 상세 페이지용
    getTranscript: async (jobId: string) => {
      try {
        // 먼저 회의 보고서를 시도
        const response = await fetch(`${API_BASE_URL}/meetings/${jobId}/report`);
        
        if (!response.ok) {
          // 보고서가 없으면 트랜스크립트를 시도
          const transcriptResponse = await fetch(`${API_BASE_URL}/transcripts/${jobId}`);
          
          if (!transcriptResponse.ok) {
            const errorData = await transcriptResponse.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP error! status: ${transcriptResponse.status}`);
          }
          
          const data = await transcriptResponse.json();
          return data;
        }

        const data = await response.json();
        return data;
      } catch (err) {
        throw new Error(err instanceof Error ? err.message : '트랜스크립트 조회에 실패했습니다.');
      }
    },
    getAgentResults: async (_jobId: string) => { throw new Error('getAgentResults is not implemented'); },
    getAgentStatus: async (_jobId: string) => { return { status: 'unknown' }; },
  };

  return (
    <ApiContext.Provider value={contextValue}>
      {children}
    </ApiContext.Provider>
  );
};