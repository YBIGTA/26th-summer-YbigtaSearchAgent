import React, { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useSettings } from '../../context/SettingsContext';

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();
  const { theme, setTheme } = useSettings();

  const isActive = (path: string) => location.pathname === path;

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  return (
    <div className="slack-layout">
      {/* 사이드바 */}
      <div className="slack-sidebar">
        <div className="slack-sidebar-header">
          <div className="slack-sidebar-title">Meeting AI</div>
          <button
            onClick={toggleTheme}
            className="btn btn-sm btn-secondary"
            title={`${theme === 'dark' ? '라이트' : '다크'} 모드로 변경`}
          >
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
        </div>

        <div className="slack-sidebar-content">
          {/* 메인 네비게이션 */}
          <div className="slack-sidebar-section">
            <div className="slack-sidebar-section-title">메뉴</div>
            <Link
              to="/upload"
              className={`slack-sidebar-item ${isActive('/upload') ? 'active' : ''}`}
            >
              <span className="slack-sidebar-item-icon">📁</span>
              파일 업로드
            </Link>
            <Link
              to="/"
              className={`slack-sidebar-item ${isActive('/') ? 'active' : ''}`}
            >
              <span className="slack-sidebar-item-icon">📊</span>
              대시보드
            </Link>
            <Link
              to="/chat"
              className={`slack-sidebar-item ${isActive('/chat') ? 'active' : ''}`}
            >
              <span className="slack-sidebar-item-icon">💬</span>
              AI 채팅
            </Link>
            <Link
              to="/settings"
              className={`slack-sidebar-item ${isActive('/settings') ? 'active' : ''}`}
            >
              <span className="slack-sidebar-item-icon">⚙️</span>
              설정
            </Link>
          </div>

          {/* 최근 회의록 */}
          <div className="slack-sidebar-section">
            <div className="slack-sidebar-section-title">최근 회의록</div>
            <div className="slack-sidebar-item">
              <span className="slack-sidebar-item-icon">🎤</span>
              2024-01-15 팀 미팅
            </div>
            <div className="slack-sidebar-item">
              <span className="slack-sidebar-item-icon">🎤</span>
              2024-01-14 프로젝트 회의
            </div>
            <div className="slack-sidebar-item">
              <span className="slack-sidebar-item-icon">🎤</span>
              2024-01-13 주간 회의
            </div>
          </div>

          {/* 빠른 액션 */}
          <div className="slack-sidebar-section">
            <div className="slack-sidebar-section-title">빠른 실행</div>
            <div className="slack-sidebar-item">
              <span className="slack-sidebar-item-icon">🔄</span>
              벡터 DB 업데이트
            </div>
            <div className="slack-sidebar-item">
              <span className="slack-sidebar-item-icon">🤖</span>
              AI 에이전트 실행
            </div>
          </div>
        </div>

        <div className="slack-sidebar-footer">
          <div className="status-badge status-success">
            <span>●</span> 연결됨
          </div>
        </div>
      </div>

      {/* 메인 콘텐츠 */}
      <div className="slack-main">
        <div className="slack-main-header">
          <div className="slack-main-title">
            {location.pathname === '/' && '대시보드'}
            {location.pathname === '/upload' && '파일 업로드'}
            {location.pathname === '/chat' && 'AI 채팅'}
            {location.pathname === '/settings' && '설정'}
            {location.pathname.startsWith('/meeting/') && '회의록 상세'}
          </div>
          
          <div className="slack-main-toolbar">
            <div className="search-bar">
              <input
                type="text"
                className="search-input"
                placeholder="회의록 검색..."
              />
              <span className="search-icon">🔍</span>
            </div>
          </div>
        </div>

        <div className="slack-main-content">
          {children}
        </div>
      </div>
    </div>
  );
};

export default Layout;