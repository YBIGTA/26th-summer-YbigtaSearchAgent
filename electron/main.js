const { app, BrowserWindow, Menu, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

// 개발 모드 확인
const isDev = process.env.ELECTRON_IS_DEV === '1';
const port = process.env.PORT || 3000;

let mainWindow;
let backendProcess;

// 백엔드 서버 시작
function startBackendServer() {
  const backendPath = isDev 
    ? path.join(__dirname, '..', 'src', 'backend', 'main.py')
    : path.join(process.resourcesPath, 'backend', 'main.py');
  
  console.log('Starting backend server:', backendPath);
  
  // Python 백엔드 시작
  backendProcess = spawn('python', [backendPath], {
    cwd: isDev ? path.join(__dirname, '..') : process.resourcesPath,
    env: { ...process.env, PYTHONPATH: isDev ? path.join(__dirname, '..', 'src') : process.resourcesPath }
  });

  backendProcess.stdout.on('data', (data) => {
    console.log(`Backend stdout: ${data}`);
  });

  backendProcess.stderr.on('data', (data) => {
    console.error(`Backend stderr: ${data}`);
  });

  backendProcess.on('close', (code) => {
    console.log(`Backend process exited with code ${code}`);
  });
}

// 메인 윈도우 생성
function createWindow() {
  // 메인 윈도우 생성
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 700,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, '..', 'build', 'icon.png'),
    titleBarStyle: 'default',
    show: false
  });

  // 윈도우가 준비되면 표시
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    
    if (isDev) {
      mainWindow.webContents.openDevTools();
    }
  });

  // URL 로드
  const startUrl = isDev 
    ? `http://localhost:${port}` 
    : `file://${path.join(__dirname, '..', 'build', 'index.html')}`;
  
  mainWindow.loadURL(startUrl);

  // 윈도우가 닫힐 때
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // 메뉴 설정
  createMenu();
}

// 애플리케이션 메뉴 생성
function createMenu() {
  const template = [
    {
      label: '파일',
      submenu: [
        {
          label: '오디오 파일 업로드',
          accelerator: 'CmdOrCtrl+O',
          click: () => {
            mainWindow.webContents.send('menu-upload-file');
          }
        },
        {
          label: '설정',
          accelerator: 'CmdOrCtrl+,',
          click: () => {
            mainWindow.webContents.send('menu-open-settings');
          }
        },
        { type: 'separator' },
        {
          label: '종료',
          accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: '편집',
      submenu: [
        { role: 'undo', label: '실행 취소' },
        { role: 'redo', label: '다시 실행' },
        { type: 'separator' },
        { role: 'cut', label: '잘라내기' },
        { role: 'copy', label: '복사' },
        { role: 'paste', label: '붙여넣기' },
        { role: 'selectall', label: '모두 선택' }
      ]
    },
    {
      label: '보기',
      submenu: [
        { role: 'reload', label: '새로 고침' },
        { role: 'forceReload', label: '강제 새로 고침' },
        { role: 'toggleDevTools', label: '개발자 도구' },
        { type: 'separator' },
        { role: 'resetZoom', label: '실제 크기' },
        { role: 'zoomIn', label: '확대' },
        { role: 'zoomOut', label: '축소' },
        { type: 'separator' },
        { role: 'togglefullscreen', label: '전체 화면' }
      ]
    },
    {
      label: '도움말',
      submenu: [
        {
          label: 'YBIGTA Meeting Analyzer 정보',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'YBIGTA Meeting Analyzer',
              message: 'YBIGTA Meeting Analyzer v1.0.0',
              detail: '스마트 회의 분석 도구\\n\\n© 2024 YBIGTA. All rights reserved.'
            });
          }
        }
      ]
    }
  ];

  // macOS 메뉴 조정
  if (process.platform === 'darwin') {
    template.unshift({
      label: app.getName(),
      submenu: [
        { role: 'about', label: `${app.getName()} 정보` },
        { type: 'separator' },
        { role: 'services', label: '서비스' },
        { type: 'separator' },
        { role: 'hide', label: `${app.getName()} 숨기기` },
        { role: 'hideothers', label: '다른 앱 숨기기' },
        { role: 'unhide', label: '모두 보기' },
        { type: 'separator' },
        { role: 'quit', label: `${app.getName()} 종료` }
      ]
    });
  }

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// IPC 핸들러
ipcMain.handle('get-app-version', () => {
  return app.getVersion();
});

ipcMain.handle('show-open-dialog', async (event, options) => {
  const result = await dialog.showOpenDialog(mainWindow, options);
  return result;
});

ipcMain.handle('show-save-dialog', async (event, options) => {
  const result = await dialog.showSaveDialog(mainWindow, options);
  return result;
});

// 앱 이벤트 핸들러
app.whenReady().then(() => {
  // 백엔드 서버 시작
  startBackendServer();
  
  // 메인 윈도우 생성
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  // 백엔드 프로세스 종료
  if (backendProcess) {
    backendProcess.kill();
  }
  
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  // 백엔드 프로세스 종료
  if (backendProcess) {
    backendProcess.kill();
  }
});

// 보안 설정
app.on('web-contents-created', (event, contents) => {
  contents.on('new-window', (navigationEvent, navigationUrl, frameName, disposition, options) => {
    navigationEvent.preventDefault();
    
    // 외부 링크는 기본 브라우저에서 열기
    require('electron').shell.openExternal(navigationUrl);
  });
});

// 프로덕션 빌드에서 개발자 도구 비활성화
if (!isDev) {
  app.on('web-contents-created', (event, contents) => {
    contents.on('devtools-opened', () => {
      contents.closeDevTools();
    });
  });
}