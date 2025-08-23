const { contextBridge, ipcRenderer } = require('electron');

// Electron API를 안전하게 렌더러 프로세스에 노출
contextBridge.exposeInMainWorld('electronAPI', {
  // 앱 정보
  getVersion: () => ipcRenderer.invoke('get-app-version'),
  
  // 다이얼로그
  showOpenDialog: (options) => ipcRenderer.invoke('show-open-dialog', options),
  showSaveDialog: (options) => ipcRenderer.invoke('show-save-dialog', options),
  
  // 메뉴 이벤트 리스너
  onMenuUploadFile: (callback) => {
    ipcRenderer.on('menu-upload-file', callback);
  },
  onMenuOpenSettings: (callback) => {
    ipcRenderer.on('menu-open-settings', callback);
  },
  
  // 클린업
  removeAllListeners: (channel) => {
    ipcRenderer.removeAllListeners(channel);
  }
});

// Node.js API 일부 노출 (필요시)
contextBridge.exposeInMainWorld('nodeAPI', {
  platform: process.platform,
  arch: process.arch,
  versions: process.versions
});