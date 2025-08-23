import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export interface STTEngine {
  name: string;
  available: boolean;
  languages?: string[];
  models?: string[];
  features?: string[];
  domains?: string[];
  description?: string;
}

interface SettingsContextType {
  sttEngine: string;
  setSttEngine: (engine: string) => void;
  language: string;
  setLanguage: (language: string) => void;
  theme: 'light' | 'dark';
  setTheme: (theme: 'light' | 'dark') => void;
  notionPages: string[];
  setNotionPages: (pages: string[]) => void;
  sttEngines: Record<string, STTEngine>;
  loadSTTEngines: () => Promise<void>;
  validateEngine: (engine: string) => Promise<boolean>;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export const useSettings = (): SettingsContextType => {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
};

interface SettingsProviderProps {
  children: ReactNode;
}

export const SettingsProvider: React.FC<SettingsProviderProps> = ({ children }) => {
  const [sttEngine, setSttEngine] = useState<string>('whisper');
  const [language, setLanguage] = useState<string>('ko');
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');
  const [notionPages, setNotionPages] = useState<string[]>([]);
  const [sttEngines, setSTTEngines] = useState<Record<string, STTEngine>>({});

  const API_BASE_URL = 'http://localhost:8000/api';

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

  const loadSTTEngines = async (): Promise<void> => {
    try {
      const response = await apiCall('/settings/stt-engines');
      setSTTEngines(response.engines || {});
    } catch (error) {
      console.error('STT 엔진 로드 실패:', error);
    }
  };

  const validateEngine = async (engine: string): Promise<boolean> => {
    try {
      const params = new URLSearchParams({ engine });
      const response = await apiCall('/settings/stt-engines/validate', {
        method: 'POST',
        body: params,
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      
      return response.available === true;
    } catch (error) {
      console.error('STT 엔진 검증 실패:', error);
      return false;
    }
  };

  const saveNotionPages = async (pages: string[]) => {
    try {
      await apiCall('/settings/notion-pages', {
        method: 'POST',
        body: JSON.stringify(pages),
      });
    } catch (error) {
      console.error('Notion 페이지 저장 실패:', error);
    }
  };

  // 테마 변경 시 CSS 변수 업데이트
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  // 초기 로드
  useEffect(() => {
    loadSTTEngines();
  }, []);

  // Notion 페이지 변경 시 자동 저장
  useEffect(() => {
    if (notionPages.length > 0) {
      saveNotionPages(notionPages);
    }
  }, [notionPages]);

  const contextValue: SettingsContextType = {
    sttEngine,
    setSttEngine,
    language,
    setLanguage,
    theme,
    setTheme,
    notionPages,
    setNotionPages,
    sttEngines,
    loadSTTEngines,
    validateEngine,
  };

  return (
    <SettingsContext.Provider value={contextValue}>
      {children}
    </SettingsContext.Provider>
  );
};