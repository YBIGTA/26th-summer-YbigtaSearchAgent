import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import Chat from './pages/Chat';
import Settings from './pages/Settings';
import MeetingDetail from './pages/MeetingDetail';
import DatabaseExplorer from './pages/DatabaseExplorer';
import { ApiProvider } from './context/ApiContext';
import { SettingsProvider } from './context/SettingsContext';
import './styles/slack-theme.css';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <SettingsProvider>
      <ApiProvider>
        <Router>
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/upload" element={<Upload />} />
              <Route path="/chat" element={<Chat />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/meeting/:id" element={<MeetingDetail />} />
              <Route path="/database" element={<DatabaseExplorer />} />
            </Routes>
          </Layout>
        </Router>
      </ApiProvider>
    </SettingsProvider>
  </React.StrictMode>
);