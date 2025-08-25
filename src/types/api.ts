// API 응답 타입 정의

export interface ApiResponse<T = any> {
  status: string;
  message?: string;
  data?: T;
  error?: string;
}

// 회의 관련 타입 - types/meeting.ts에서 import하여 사용
export type { Meeting } from './meeting';

export interface Transcript {
  id: number;
  title: string;
  date: string;
  duration: number;
  speakers: number;
  utterances: Utterance[];
}

export interface Utterance {
  id: string;
  speaker: string;
  text: string;
  start_time: number;
  end_time: number;
  confidence: number;
}

// STT 관련 타입
export interface STTRequest {
  file_id: number;
  engine?: string;
  language?: string;
  enable_diarization?: boolean;
}

export interface STTResult {
  status: string;
  file_id: number;
  diarization_enabled: boolean;
  result: {
    text: string;
    segments: any[];
    speaker_analysis?: any;
  };
}

// 검색 관련 타입
export interface SearchRequest {
  query: string;
  top_k?: number;
  filters?: Record<string, any>;
  sources?: string[];
}

export interface SearchResult {
  query: string;
  results: {
    documents: string[];
    scores: number[];
    metadata: any[];
  };
  total_found: number;
}

// 에이전트 분석 관련 타입
export interface AnalysisRequest {
  transcript_id: number;
  analysis_options?: Record<string, any>;
  priority?: string;
}

export interface AgentJob {
  job_id: string;
  status: 'initializing' | 'running' | 'completed' | 'failed' | 'cancelled';
  transcript_id: number;
  progress: number;
  started_at?: string;
  completed_at?: string;
  error?: string;
  results?: any;
}

export interface AgentConfig {
  agent_type: string;
  enabled: boolean;
  config?: Record<string, any>;
}

// 파이프라인 관련 타입
export interface PipelineRequest {
  audio_file_path: string;
  analysis_options?: Record<string, any>;
}

export interface PipelineJob {
  job_id: string;
  status: string;
  current_stage?: string;
  progress: number;
  started_at: string;
  completed_at?: string;
  error?: string;
  audio_file: string;
}

// 동기화 관련 타입
export interface SyncStatus {
  notion: {
    last_sync: string;
    status: string;
    documents_count: number;
  };
  github: {
    last_sync: string;
    status: string;
    repositories_count: number;
  };
  google_drive: {
    last_sync: string;
    status: string;
    documents_count: number;
  };
}

// 설정 관련 타입
export interface STTEngine {
  name: string;
  display_name: string;
  supported_languages: string[];
  enabled: boolean;
}

export interface ApiKeyConfig {
  provider: string;
  key: string;
  enabled: boolean;
  last_tested?: string;
}

