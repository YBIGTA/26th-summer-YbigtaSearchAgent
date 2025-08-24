import React, { createContext, useContext, useState, ReactNode } from 'react';

// API 관련 타입 정의
export interface ApiKey {
  provider: string;
  index?: number;
  masked_value: string;
  is_valid?: boolean;
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
  saveApiKey: (provider: string, key: string, index?: number) => Promise<void>;
  loadApiKeys: () => Promise<void>;
  removeApiKey: (provider: string, index?: number) => Promise<void>;
  testApiKey: (provider: string, key: string) => Promise<boolean>;
  uploadAudio: (file: File, onProgress?: (progress: number) => void) => Promise<any>;
  startPipelineAnalysis: (file: File) => Promise<{ job_id: string; message: string }>;
  getPipelineStatus: (jobId: string) => Promise<PipelineStatus>;
  getPipelineResults: (jobId: string) => Promise<PipelineResults>;
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
    console.log('=== startPipelineAnalysis 호출됨 ===');
    console.log('API_BASE_URL:', API_BASE_URL);
    console.log('파일 정보:', {
      name: file.name,
      size: file.size,
      type: file.type
    });
    
    setIsLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      console.log('FormData 생성 완료');
      console.log('FormData entries:');
      const entries = Array.from(formData.entries());
      entries.forEach(([key, value]) => {
        console.log('  ', key, ':', value);
        if (value instanceof File) {
          console.log('    파일 이름:', value.name);
          console.log('    파일 크기:', value.size);
          console.log('    파일 타입:', value.type);
        }
      });

      console.log('API 요청 시작:', `${API_BASE_URL}/meetings/analyze-upload`);

      // AbortController로 타임아웃 처리
      const controller = new AbortController();
      const timeoutId = setTimeout(() => {
        console.log('요청 타임아웃! 30초 경과');
        controller.abort();
      }, 30000);

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
          console.error('API 에러 응답:', errorData);
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
          console.error('요청이 타임아웃되었습니다');
          throw new Error('요청 시간이 초과되었습니다 (30초)');
        }
        
        console.error('Fetch 에러:', fetchError);
        throw fetchError;
      }
      
    } catch (err) {
      console.error('startPipelineAnalysis 에러:', err);
      console.error('에러 타입:', typeof err);
      console.error('에러 상세:', {
        message: err instanceof Error ? err.message : String(err),
        stack: err instanceof Error ? err.stack : undefined
      });
      
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

  const contextValue: ApiContextType = {
    apiKeys,
    isLoading,
    error,
    saveApiKey,
    loadApiKeys,
    removeApiKey,
    testApiKey,
    uploadAudio,
    startPipelineAnalysis,
    getPipelineStatus,
    getPipelineResults,
  };

  return (
    <ApiContext.Provider value={contextValue}>
      {children}
    </ApiContext.Provider>
  );
};