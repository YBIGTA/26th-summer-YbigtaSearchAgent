"""
설정 동기화 시스템
프론트엔드 설정을 백엔드 환경변수로 동기화
"""

import os
import asyncio
from typing import Dict, Any, Optional
from .config import config


class SettingsSync:
    def __init__(self):
        self.env_mapping = {
            # API 키 매핑
            "upstage": "UPSTAGE_API_KEY",
            "upstage_1": "UPSTAGE_API_KEY1",
            "upstage_2": "UPSTAGE_API_KEY2", 
            "upstage_3": "UPSTAGE_API_KEY3",
            "upstage_4": "UPSTAGE_API_KEY4",
            "upstage_5": "UPSTAGE_API_KEY5",
            "upstage_6": "UPSTAGE_API_KEY6",
            "upstage_7": "UPSTAGE_API_KEY7",
            "upstage_8": "UPSTAGE_API_KEY8",
            "openai": "OPENAI_API_KEY",
            "returnzero_client_id": "RETURNZERO_CLIENT_ID",
            "returnzero_client_secret": "RETURNZERO_CLIENT_SECRET",
            "notion": "NOTION_API_KEY",
            "github": "GITHUB_PERSONAL_ACCESS_TOKEN",
            "gdrive_folder": "GDRIVE_FOLDER_ID",
            
            # 페이지 ID 매핑
            "notion_page_1": "NOTION_PAGE_ID_1",
            "notion_page_2": "NOTION_PAGE_ID_2",
            "notion_page_3": "NOTION_PAGE_ID_3",
            "notion_page_4": "NOTION_PAGE_ID_4",
            "notion_page_5": "NOTION_PAGE_ID_5",
        }
        
        # 초기 동기화
        self.sync_to_environment()
    
    def sync_to_environment(self):
        """설정을 환경변수로 동기화합니다."""
        print("🔄 설정을 환경변수로 동기화 중...")
        
        # API 키 동기화
        for provider, keys in config.config.get("api_keys", {}).items():
            if isinstance(keys, dict):
                for key_name, encrypted_value in keys.items():
                    try:
                        decrypted_value = config.decrypt_value(encrypted_value)
                        env_key = self.env_mapping.get(key_name)
                        if env_key:
                            os.environ[env_key] = decrypted_value
                    except Exception as e:
                        print(f"⚠️ API 키 복호화 실패 ({key_name}): {e}")
        
        # 페이지 ID 동기화
        pages = config.get("notion_pages", [])
        for i, page_id in enumerate(pages, 1):
            os.environ[f"NOTION_PAGE_ID_{i}"] = page_id
        
        print("✅ 환경변수 동기화 완료")
    
    def save_api_key(self, provider: str, key: str, index: Optional[int] = None) -> Dict[str, Any]:
        """API 키를 저장하고 환경변수에 동기화합니다."""
        try:
            # 로컬 설정에 저장
            config.set_api_key(provider, key, index)
            
            # 환경변수에 동기화
            key_name = f"{provider}_{index}" if index else provider
            env_key = self.env_mapping.get(key_name)
            if env_key:
                os.environ[env_key] = key
            
            return {
                "status": "success",
                "message": f"{provider} API 키가 저장되었습니다.",
                "provider": provider,
                "index": index
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"API 키 저장 실패: {e}",
                "provider": provider,
                "index": index
            }
    
    def get_api_keys(self, provider: str = None) -> Dict[str, Any]:
        """저장된 API 키 정보를 반환합니다 (마스킹됨)."""
        if provider:
            keys = config.get_all_api_keys(provider)
            return {
                provider: {
                    key_name: self._mask_key(key_value) 
                    for key_name, key_value in keys.items()
                }
            }
        else:
            # 모든 API 키 정보
            result = {}
            for provider in config.config.get("api_keys", {}):
                keys = config.get_all_api_keys(provider)
                result[provider] = {
                    key_name: self._mask_key(key_value)
                    for key_name, key_value in keys.items()
                }
            return result
    
    def remove_api_key(self, provider: str, index: Optional[int] = None) -> Dict[str, Any]:
        """API 키를 제거하고 환경변수에서도 삭제합니다."""
        try:
            # 로컬 설정에서 제거
            config.remove_api_key(provider, index)
            
            # 환경변수에서도 제거
            key_name = f"{provider}_{index}" if index else provider
            env_key = self.env_mapping.get(key_name)
            if env_key and env_key in os.environ:
                del os.environ[env_key]
            
            return {
                "status": "success",
                "message": f"{provider} API 키가 제거되었습니다.",
                "provider": provider,
                "index": index
            }
            
        except Exception as e:
            return {
                "status": "error", 
                "message": f"API 키 제거 실패: {e}",
                "provider": provider,
                "index": index
            }
    
    def test_api_key(self, provider: str, key: str) -> Dict[str, Any]:
        """API 키가 유효한지 테스트합니다."""
        try:
            if provider == "upstage":
                return self._test_upstage_key(key)
            elif provider == "openai":
                return self._test_openai_key(key)
            elif provider == "returnzero_client_id":
                # ReturnZero는 client_secret도 필요하므로 나중에 종합 테스트
                return {"status": "info", "message": "Client Secret과 함께 테스트됩니다."}
            elif provider == "notion":
                return self._test_notion_key(key)
            elif provider == "github":
                return self._test_github_key(key)
            else:
                return {"status": "warning", "message": "테스트를 지원하지 않는 API입니다."}
                
        except Exception as e:
            return {"status": "error", "message": f"API 키 테스트 실패: {e}"}
    
    def _test_upstage_key(self, key: str) -> Dict[str, Any]:
        """Upstage API 키를 테스트합니다."""
        import requests
        
        headers = {"Authorization": f"Bearer {key}"}
        response = requests.post(
            "https://api.upstage.ai/v1/embeddings",
            headers=headers,
            json={"input": "test", "model": "embedding-query"},
            timeout=10
        )
        
        if response.status_code == 200:
            return {"status": "success", "message": "Upstage API 키가 유효합니다."}
        elif response.status_code == 401:
            return {"status": "error", "message": "Upstage API 키가 유효하지 않습니다."}
        else:
            return {"status": "warning", "message": f"API 응답: {response.status_code}"}
    
    def _test_openai_key(self, key: str) -> Dict[str, Any]:
        """OpenAI API 키를 테스트합니다."""
        import requests
        
        headers = {"Authorization": f"Bearer {key}"}
        response = requests.get(
            "https://api.openai.com/v1/models",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return {"status": "success", "message": "OpenAI API 키가 유효합니다."}
        elif response.status_code == 401:
            return {"status": "error", "message": "OpenAI API 키가 유효하지 않습니다."}
        else:
            return {"status": "warning", "message": f"API 응답: {response.status_code}"}
    
    def _test_notion_key(self, key: str) -> Dict[str, Any]:
        """Notion API 키를 테스트합니다."""
        import requests
        
        headers = {
            "Authorization": f"Bearer {key}",
            "Notion-Version": "2022-06-28"
        }
        response = requests.post(
            "https://api.notion.com/v1/search",
            headers=headers,
            json={"query": "", "page_size": 1},
            timeout=10
        )
        
        if response.status_code == 200:
            return {"status": "success", "message": "Notion API 키가 유효합니다."}
        elif response.status_code == 401:
            return {"status": "error", "message": "Notion API 키가 유효하지 않습니다."}
        else:
            return {"status": "warning", "message": f"API 응답: {response.status_code}"}
    
    def _test_github_key(self, key: str) -> Dict[str, Any]:
        """GitHub API 키를 테스트합니다."""
        import requests
        
        headers = {"Authorization": f"token {key}"}
        response = requests.get(
            "https://api.github.com/user",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            user_data = response.json()
            return {
                "status": "success", 
                "message": f"GitHub API 키가 유효합니다. (사용자: {user_data.get('login', 'Unknown')})"
            }
        elif response.status_code == 401:
            return {"status": "error", "message": "GitHub API 키가 유효하지 않습니다."}
        else:
            return {"status": "warning", "message": f"API 응답: {response.status_code}"}
    
    def _mask_key(self, key: str) -> str:
        """API 키를 마스킹합니다."""
        if not key or len(key) < 8:
            return "••••••••"
        
        return key[:4] + "•" * (len(key) - 8) + key[-4:]
    
    def save_notion_pages(self, page_ids: list) -> Dict[str, Any]:
        """Notion 페이지 ID 목록을 저장하고 환경변수에 동기화합니다."""
        try:
            config.set("notion_pages", page_ids)
            
            # 환경변수에 동기화
            for i, page_id in enumerate(page_ids, 1):
                os.environ[f"NOTION_PAGE_ID_{i}"] = page_id
            
            # 기존 환경변수 정리
            i = len(page_ids) + 1
            while f"NOTION_PAGE_ID_{i}" in os.environ:
                del os.environ[f"NOTION_PAGE_ID_{i}"]
                i += 1
            
            return {
                "status": "success",
                "message": f"{len(page_ids)}개의 Notion 페이지 ID가 저장되었습니다."
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Notion 페이지 ID 저장 실패: {e}"
            }


# 싱글톤 인스턴스
settings_sync = SettingsSync()