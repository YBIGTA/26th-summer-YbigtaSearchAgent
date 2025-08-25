"""
애플리케이션 설정 관리
환경 변수 및 사용자 설정 처리
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet


class ConfigManager:
    def __init__(self):
        self.app_name = "YBIGTA-Meeting-Analyzer"
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / "config.json"
        self.key_file = self.config_dir / ".key"
        
        # 설정 디렉토리 생성
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 암호화 키 초기화
        self.cipher = self._init_cipher()
        
        # 설정 로드
        self.config = self._load_config()
    
    def _get_config_dir(self) -> Path:
        """OS별 설정 디렉토리 경로를 반환합니다."""
        if os.name == 'nt':  # Windows
            base = os.environ.get('APPDATA', '.')
        elif os.name == 'posix':
            if 'darwin' in os.sys.platform:  # macOS
                base = os.path.expanduser('~/Library/Application Support')
            else:  # Linux
                base = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
        else:
            base = '.'
        
        return Path(base) / self.app_name
    
    def _init_cipher(self) -> Fernet:
        """암호화 키를 초기화합니다."""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            # 새 키 생성
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # 키 파일 권한 설정 (Unix 계열)
            if os.name == 'posix':
                os.chmod(self.key_file, 0o600)
        
        return Fernet(key)
    
    def _load_config(self) -> Dict[str, Any]:
        """설정 파일을 로드합니다."""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 기본 설정
            return {
                "api_keys": {},
                "stt_engine": "whisper",
                "default_language": "ko",
                "theme": "dark",
                "auto_save": True,
                "sync_on_startup": False
            }
    
    def save_config(self):
        """설정을 파일에 저장합니다."""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def encrypt_value(self, value: str) -> str:
        """값을 암호화합니다."""
        return self.cipher.encrypt(value.encode()).decode()
    
    def decrypt_value(self, encrypted: str) -> str:
        """암호화된 값을 복호화합니다."""
        return self.cipher.decrypt(encrypted.encode()).decode()
    
    # === API 키 관리 ===
    
    def set_api_key(self, provider: str, key: str, index: int = None):
        """API 키를 저장합니다."""
        encrypted_key = self.encrypt_value(key)
        
        if provider not in self.config["api_keys"]:
            self.config["api_keys"][provider] = {}
        
        if index is not None:
            key_name = f"{provider}_{index}"
        else:
            key_name = provider
        
        self.config["api_keys"][provider][key_name] = encrypted_key
        self.save_config()
    
    def get_api_key(self, provider: str, index: int = None) -> Optional[str]:
        """API 키를 가져옵니다."""
        if provider not in self.config["api_keys"]:
            return None
        
        if index is not None:
            key_name = f"{provider}_{index}"
        else:
            key_name = provider
        
        encrypted = self.config["api_keys"][provider].get(key_name)
        if encrypted:
            return self.decrypt_value(encrypted)
        return None
    
    def get_all_api_keys(self, provider: str) -> Dict[str, str]:
        """특정 프로바이더의 모든 API 키를 가져옵니다."""
        if provider not in self.config["api_keys"]:
            return {}
        
        keys = {}
        for key_name, encrypted in self.config["api_keys"][provider].items():
            keys[key_name] = self.decrypt_value(encrypted)
        
        return keys
    
    def remove_api_key(self, provider: str, index: int = None):
        """API 키를 제거합니다."""
        if provider in self.config["api_keys"]:
            if index is not None:
                key_name = f"{provider}_{index}"
                self.config["api_keys"][provider].pop(key_name, None)
            else:
                self.config["api_keys"][provider].pop(provider, None)
            
            # 프로바이더에 키가 없으면 프로바이더도 제거
            if not self.config["api_keys"][provider]:
                del self.config["api_keys"][provider]
            
            self.save_config()
    
    # === 일반 설정 ===
    
    def get(self, key: str, default: Any = None) -> Any:
        """설정 값을 가져옵니다."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """설정 값을 저장합니다."""
        self.config[key] = value
        self.save_config()
    
    def get_data_dir(self) -> Path:
        """데이터 디렉토리 경로를 반환합니다."""
        data_dir = self.config_dir / "data"
        data_dir.mkdir(exist_ok=True)
        return data_dir
    
    def get_db_path(self) -> Path:
        """데이터베이스 파일 경로를 반환합니다."""
        return self.get_data_dir() / "app.db"
    
    def get_index_dir(self) -> Path:
        """인덱스 디렉토리 경로를 반환합니다."""
        index_dir = self.get_data_dir() / "indexes"
        index_dir.mkdir(exist_ok=True)
        return index_dir
    
    def get_audio_dir(self) -> Path:
        """오디오 파일 디렉토리 경로를 반환합니다."""
        audio_dir = self.get_data_dir() / "audio"
        audio_dir.mkdir(exist_ok=True)
        return audio_dir
    
    def get_cache_dir(self) -> Path:
        """캐시 디렉토리 경로를 반환합니다."""
        cache_dir = self.get_data_dir() / "cache"
        cache_dir.mkdir(exist_ok=True)
        return cache_dir


# 싱글톤 인스턴스
config = ConfigManager()