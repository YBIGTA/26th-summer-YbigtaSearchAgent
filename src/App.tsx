import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard';
import Settings from './pages/Settings';
import MeetingDetail from './pages/MeetingDetail';
import Upload from './pages/Upload';
import { ApiProvider } from './context/ApiContext';
import { SettingsProvider } from './context/SettingsContext';
import './styles/slack-theme.css';

function App() {
  const [isElectron, setIsElectron] = useState(false);

  useEffect(() => {
    // Electron 환경 감지
    setIsElectron(typeof window !== 'undefined' && !!window.electronAPI);

    // Electron 메뉴 이벤트 리스너
    if (window.electronAPI) {
      window.electronAPI.onMenuUploadFile(() => {
        // 파일 업로드 다이얼로그 열기
        console.log('Menu: Upload file triggered');
      });

      window.electronAPI.onMenuOpenSettings(() => {
        // 설정 페이지로 이동
        console.log('Menu: Open settings triggered');
        window.location.href = '/settings';
      });
    }

    return () => {
      // 클린업
      if (window.electronAPI) {
        window.electronAPI.removeAllListeners('menu-upload-file');
        window.electronAPI.removeAllListeners('menu-open-settings');
      }
    };
  }, []);

  return (
    <div className="App">
      <ApiProvider>
        <SettingsProvider>
          <Router>
            <Layout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/upload" element={<Upload />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/meeting/:id" element={<MeetingDetail />} />
              </Routes>
            </Layout>
          </Router>
        </SettingsProvider>
      </ApiProvider>
    </div>
  );
}

export default App;