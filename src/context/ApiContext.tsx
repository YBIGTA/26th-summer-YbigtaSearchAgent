import React, { createContext, useContext, useState, useEffect, useRef, ReactNode } from 'react';

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

export interface ReportUpdate {
  id: number;
  job_id: string;
  title: string;
  status: string;
  progress: number;
  current_stage?: string;
  updated_at?: string;
  has_partial_results: boolean;
  speakers_detected?: number;
  duration?: number;
}

export interface LiveUpdates {
  updates: ReportUpdate[];
  timestamp: string;
  total_updates: number;
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
  getAllReports: () => Promise<any[]>;
  getReportByJobId: (jobId: string) => Promise<any>;
  deleteReport: (jobId: string) => Promise<void>;
  // 실시간 업데이트 관련
  liveUpdates: ReportUpdate[];
  startLiveUpdates: () => void;
  stopLiveUpdates: () => void;
  isLiveUpdatesActive: boolean;
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
  
  // 실시간 업데이트 상태
  const [liveUpdates, setLiveUpdates] = useState<ReportUpdate[]>([]);
  const [isLiveUpdatesActive, setIsLiveUpdatesActive] = useState(false);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const lastUpdateTimeRef = useRef<string>('');

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
          console.error(`업로드가 타임아웃되었습니다 (${dynamicTimeout/1000}초)`);
          throw new Error(`업로드 시간이 초과되었습니다. 파일 크기가 큰 경우 시간이 오래 걸릴 수 있습니다. (${dynamicTimeout/1000}초 제한)`);
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
        if (response.status === 404) {
          return null; // 보고서가 없으면 null 반환
        }
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
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
      throw new Error(err instanceof Error ? err.message : '보고서 삭제에 실패했습니다.');
    }
  };

  // 실시간 업데이트 함수들
  const fetchLiveUpdates = async () => {
    try {
      const params = new URLSearchParams();
      if (lastUpdateTimeRef.current) {
        params.append('since', lastUpdateTimeRef.current);
      }
      
      const url = `/reports/live-updates${params.toString() ? `?${params.toString()}` : ''}`;
      const response = await fetch(`${API_BASE_URL}${url}`);
      
      if (response.ok) {
        const data: LiveUpdates = await response.json();
        
        if (data.updates.length > 0) {
          console.log('📱 실시간 업데이트:', data.updates.length, '개');
          
          setLiveUpdates(prevUpdates => {
            // 기존 업데이트와 새 업데이트를 job_id 기준으로 병합
            const updatedMap = new Map<string, ReportUpdate>();
            
            // 기존 업데이트 추가
            prevUpdates.forEach(update => {
              updatedMap.set(update.job_id, update);
            });
            
            // 새 업데이트로 덮어쓰기
            data.updates.forEach(update => {
              updatedMap.set(update.job_id, update);
            });
            
            return Array.from(updatedMap.values())
              .sort((a, b) => new Date(b.updated_at || '').getTime() - new Date(a.updated_at || '').getTime())
              .slice(0, 50); // 최근 50개만 유지
          });
          
          // 마지막 업데이트 시간 갱신
          lastUpdateTimeRef.current = data.timestamp;
        }
      }
    } catch (error) {
      console.error('실시간 업데이트 가져오기 실패:', error);
      // 에러가 발생해도 폴링은 계속 진행
    }
  };

  const startLiveUpdates = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }
    
    setIsLiveUpdatesActive(true);
    
    // 즉시 한 번 실행
    fetchLiveUpdates();
    
    // 3초마다 폴링
    pollingIntervalRef.current = setInterval(fetchLiveUpdates, 3000);
    
    console.log('🔄 실시간 업데이트 시작 (3초 간격)');
  };

  const stopLiveUpdates = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    
    setIsLiveUpdatesActive(false);
    console.log('⏹️ 실시간 업데이트 중지');
  };

  // 컴포넌트 언마운트 시 정리
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

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
    getAllReports,
    getReportByJobId,
    deleteReport,
    // 실시간 업데이트
    liveUpdates,
    startLiveUpdates,
    stopLiveUpdates,
    isLiveUpdatesActive,
  };

  return (
    <ApiContext.Provider value={contextValue}>
      {children}
    </ApiContext.Provider>
  );
};