import React, { ReactNode, useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useSettings } from '../../context/SettingsContext';
import { useApi } from '../../context/ApiContext';
import { Meeting } from '../../types/electron';

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();
  const { theme, setTheme } = useSettings();
  const { getMeetings } = useApi();
  const [recentMeetings, setRecentMeetings] = useState<Meeting[]>([]);
  const [isLoadingMeetings, setIsLoadingMeetings] = useState(false);

  const isActive = (path: string) => location.pathname === path;

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  // 최근 회의록 데이터 가져오기
  useEffect(() => {
    const fetchRecentMeetings = async () => {
      setIsLoadingMeetings(true);
      try {
        const meetings = await getMeetings();
        // 최근 3개 회의록만 표시
        setRecentMeetings(meetings.slice(0, 3));
      } catch (error) {
        console.error('최근 회의록 조회 오류:', error);
      } finally {
        setIsLoadingMeetings(false);
      }
    };

    fetchRecentMeetings();
  }, [getMeetings]);

  // 회의록 상태에 따른 색상 및 아이콘
  const getMeetingStatusInfo = (status: string) => {
    switch (status) {
      case 'completed':
        return { icon: '✅', color: '#4caf50', text: '완료' };
      case 'processing':
        return { icon: '🔄', color: '#ff9800', text: '진행중' };
      case 'error':
        return { icon: '❌', color: '#f44336', text: '오류' };
      default:
        return { icon: '⏳', color: '#9e9e9e', text: '대기' };
    }
  };

  // 회의록 제목 줄이기
  const truncateTitle = (title: string, maxLength: number = 20) => {
    return title.length > maxLength ? title.substring(0, maxLength) + '...' : title;
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
            {isLoadingMeetings ? (
              <div className="slack-sidebar-item">
                <span className="slack-sidebar-item-icon">⏳</span>
                로딩 중...
              </div>
            ) : recentMeetings.length > 0 ? (
              recentMeetings.map((meeting) => {
                const statusInfo = getMeetingStatusInfo(meeting.status);
                return (
                  <Link
                    key={meeting.id}
                    to={`/meeting/${meeting.id}`}
                    className="slack-sidebar-item"
                    style={{ textDecoration: 'none' }}
                  >
                    <span className="slack-sidebar-item-icon">🎤</span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ 
                        fontSize: '13px', 
                        fontWeight: '500',
                        color: '#1d1c1d',
                        marginBottom: '2px'
                      }}>
                        {truncateTitle(meeting.title || '제목 없음')}
                      </div>
                      <div style={{ 
                        fontSize: '11px', 
                        color: '#6c757d',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}>
                        <span style={{ color: statusInfo.color }}>{statusInfo.icon}</span>
                        <span>{statusInfo.text}</span>
                        <span>•</span>
                        <span>{new Date(meeting.created_at).toLocaleDateString('ko-KR')}</span>
                      </div>
                    </div>
                  </Link>
                );
              })
            ) : (
              <Link
                to="/upload"
                className="slack-sidebar-item"
                style={{ 
                  textDecoration: 'none',
                  backgroundColor: '#f8f9fa',
                  border: '1px dashed #dee2e6',
                  borderRadius: '8px',
                  margin: '4px 0',
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#e9ecef';
                  e.currentTarget.style.borderColor = '#adb5bd';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = '#f8f9fa';
                  e.currentTarget.style.borderColor = '#dee2e6';
                }}
              >
                <span className="slack-sidebar-item-icon" style={{ color: '#6c757d' }}>➕</span>
                <div style={{ 
                  fontSize: '13px', 
                  color: '#6c757d',
                  fontWeight: '500'
                }}>
                  새 회의록 생성
                </div>
              </Link>
            )}
          </div>

          {/* 빠른 실행 */}
          <div className="slack-sidebar-section">
            <div className="slack-sidebar-section-title">빠른 실행</div>
            <button
              className="slack-sidebar-item"
              style={{ 
                background: 'none', 
                border: 'none', 
                width: '100%', 
                textAlign: 'left',
                cursor: 'pointer',
                padding: '8px 12px',
                borderRadius: '6px',
                transition: 'background-color 0.2s ease'
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(0,0,0,0.05)'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              onClick={() => {
                // DB조회 GUI 페이지로 이동
                window.open('/database', '_blank');
              }}
            >
              <span className="slack-sidebar-item-icon">🔍</span>
              DB조회 GUI
            </button>
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