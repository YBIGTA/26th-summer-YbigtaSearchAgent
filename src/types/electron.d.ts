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

declare global {
  interface Window {
    electronAPI?: ElectronAPI;
    nodeAPI?: NodeAPI;
  }
}

export {};