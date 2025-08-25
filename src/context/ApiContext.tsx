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
  
  // AI 에이전트
  startAgentAnalysis: (transcriptId: number, options?: AgentAnalysisOptions) => Promise<any>;
  getAgentStatus: (jobId: string) => Promise<any>;
  getAgentResults: (jobId: string) => Promise<any>;
  
  // 검색
  hybridSearch: (query: string, options?: SearchOptions) => Promise<any>;
  vectorSearch: (query: string, options?: SearchOptions) => Promise<any>;
  keywordSearch: (query: string, options?: SearchOptions) => Promise<any>;
  searchDocuments: (query: string, options?: SearchOptions) => Promise<any>;
  
  // 채팅
  getChatResponse: (query: string) => Promise<any>;
  
  // 지식베이스 동기화
  syncNotion: () => Promise<any>;
  syncGitHub: () => Promise<any>;
  syncGoogleDrive: () => Promise<any>;
  getSyncStatus: () => Promise<any>;
  
  // 트랜스크립트
  getTranscripts: () => Promise<any>;
  getTranscript: (id: number) => Promise<any>;
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
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE_URL}/meetings/analyze-upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      return {
        job_id: result.job_id || result.id,
        message: result.message || '분석이 시작되었습니다.'
      };
      
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

  // STT 처리
  const processSTT = async (fileId: number, options: STTOptions = {}): Promise<any> => {
    try {
      const response = await fetch(`${API_BASE_URL}/stt/${fileId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(options),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : 'STT 처리에 실패했습니다.');
    }
  };

  // AI 에이전트 분석
  const startAgentAnalysis = async (transcriptId: number, options: AgentAnalysisOptions = {}): Promise<any> => {
    try {
      const response = await fetch(`${API_BASE_URL}/agents/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcript_id: transcriptId, ...options }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : '에이전트 분석 시작에 실패했습니다.');
    }
  };

  const getAgentStatus = async (jobId: string): Promise<any> => {
    try {
      const response = await fetch(`${API_BASE_URL}/agents/status/${jobId}`);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : '에이전트 상태 조회에 실패했습니다.');
    }
  };

  const getAgentResults = async (jobId: string): Promise<any> => {
    try {
      const response = await fetch(`${API_BASE_URL}/agents/results/${jobId}`);
      
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
      const response = await fetch(`${API_BASE_URL}/search/hybrid`, {
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
      throw new Error(err instanceof Error ? err.message : '하이브리드 검색에 실패했습니다.');
    }
  };

  const vectorSearch = async (query: string, options: SearchOptions = {}): Promise<any> => {
    try {
      const response = await fetch(`${API_BASE_URL}/search/vector`, {
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

      const response = await fetch(`${API_BASE_URL}/pipeline/start`, {
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
      const response = await fetch(`${API_BASE_URL}/meetings`);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.meetings || [];
    } catch (err) {
      console.error('회의 목록 조회 오류:', err);
      return [];
    }
  };

  // 검색 및 채팅
  const searchDocuments = async (query: string, options?: SearchOptions): Promise<any> => {
    try {
      const response = await fetch(`${API_BASE_URL}/search/hybrid`, {
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
      throw new Error(err instanceof Error ? err.message : '문서 검색에 실패했습니다.');
    }
  };

  const getChatResponse = async (query: string): Promise<any> => {
    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          question: query,
          top_k: 5,
          search_type: "hybrid"
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        response: data.answer,
        sources: data.sources || [],
        confidence: 0.9, // 기본값
        processing_time: data.processing_time || 0,
        suggestions: data.suggestions || []
      };
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : '채팅 응답 생성에 실패했습니다.');
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
    processSTT,
    
    // 파일 업로드 및 회의 관리
    uploadFile,
    getMeetings,
    
    // 파이프라인 분석
    startPipelineAnalysis,
    getPipelineStatus,
    getPipelineResults,
    
    // AI 에이전트
    startAgentAnalysis,
    getAgentStatus,
    getAgentResults,
    
    // 검색
    hybridSearch,
    vectorSearch,
    keywordSearch,
    searchDocuments,
    
    // 채팅
    getChatResponse,
    
    // 지식베이스 동기화
    syncNotion,
    syncGitHub,
    syncGoogleDrive,
    getSyncStatus,
    
    // 트랜스크립트
    getTranscripts,
    getTranscript,
  };

  return (
    <ApiContext.Provider value={contextValue}>
      {children}
    </ApiContext.Provider>
  );
};