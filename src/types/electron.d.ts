interface ElectronAPI {
  getVersion: () => Promise<string>;
  showOpenDialog: (options: any) => Promise<any>;
  showSaveDialog: (options: any) => Promise<any>;
  onMenuUploadFile: (callback: () => void) => void;
  onMenuOpenSettings: (callback: () => void) => void;
  removeAllListeners: (channel: string) => void;
}

interface NodeAPI {
  platform: string;
  arch: string;
  versions: any;
}

// 회의 관련 타입 정의
export interface Meeting {
  id: string;
  title: string;
  status: 'processing' | 'completed' | 'error';
  progress: number;
  current_stage: string;
  summary: string;
  created_at: string;
  file_path: string;
  file_size: number;
  pipeline_results?: any;
  error_message?: string;
}

// 파이프라인 상태 타입
export interface PipelineStatus {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  current_stage: string;
  error?: string;
}

// 에이전트 분석 옵션 타입
export interface AgentAnalysisOptions {
  agent_type: string;
}

declare global {
  interface Window {
    electronAPI?: ElectronAPI;
    nodeAPI?: NodeAPI;
  }
}

export {};