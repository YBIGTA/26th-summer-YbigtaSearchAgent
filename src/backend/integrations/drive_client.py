"""
Google Drive API 클라이언트
Google Drive 문서 수집 및 처리
"""

import os
import io
import tempfile
from typing import List, Dict, Any, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from langchain_core.documents import Document
from langchain_community.document_loaders import UnstructuredFileLoader


class GoogleDriveClient:
    def __init__(self, credentials_path: str = "gdrive-credentials.json"):
        self.credentials_path = credentials_path
        self.folder_id = os.getenv("GDRIVE_FOLDER_ID")
        self.service = self._initialize_service()
        
    def _initialize_service(self):
        """Google Drive API 서비스를 초기화합니다."""
        creds = service_account.Credentials.from_service_account_file(
            self.credentials_path,
            scopes=["https://www.googleapis.com/auth/drive.readonly"]
        )
        return build("drive", "v3", credentials=creds)
    
    def list_files_in_folder(self, folder_id: str = None, recursive: bool = True, since: Optional[str] = None) -> List[Dict[str, Any]]:
        """폴더 내의 모든 파일을 나열합니다.
        
        Args:
            folder_id: 폴더 ID (None이면 환경변수에서 가져옴)
            recursive: 하위 폴더까지 재귀적으로 검색할지 여부
            since: ISO 8601 형식의 날짜 문자열. 이 시간 이후에 수정된 파일만 가져옵니다.
        """
        folder_id = folder_id or self.folder_id
        all_files = []
        
        def list_files_recursive(current_folder_id: str, path: str = ""):
            # 기본 쿼리 조건
            query_parts = [f"'{current_folder_id}' in parents", "trashed = false"]
            
            # since 파라미터가 있으면 수정 시간 필터 추가
            if since:
                # Google Drive API는 RFC 3339 형식을 사용하므로 ISO 8601을 변환
                modified_time_filter = f"modifiedTime > '{since}'"
                query_parts.append(modified_time_filter)
                print(f"📅 {since} 이후에 수정된 파일만 필터링합니다.")
            
            query = " and ".join(query_parts)
            page_token = None
            
            while True:
                results = self.service.files().list(
                    q=query,
                    spaces='drive',
                    fields="nextPageToken, files(id, name, mimeType, modifiedTime, createdTime)",
                    pageToken=page_token
                ).execute()
                
                items = results.get('files', [])
                
                for item in items:
                    item['path'] = path
                    if item['mimeType'] == 'application/vnd.google-apps.folder':
                        if recursive:
                            list_files_recursive(item['id'], f"{path}/{item['name']}")
                    else:
                        all_files.append(item)
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
        
        list_files_recursive(folder_id)
        return all_files
    
    def download_file(self, file_id: str, file_name: str, mime_type: str) -> str:
        """파일을 다운로드하고 임시 파일 경로를 반환합니다."""
        # Google Docs 내보내기 형식 매핑
        export_mime_types = {
            'application/vnd.google-apps.document': ('text/plain', '.txt'),
            'application/vnd.google-apps.spreadsheet': ('text/csv', '.csv'),
            'application/vnd.google-apps.presentation': ('text/plain', '.txt'),
        }
        
        try:
            if mime_type in export_mime_types:
                # Google Workspace 파일 내보내기
                export_mime, ext = export_mime_types[mime_type]
                request = self.service.files().export_media(
                    fileId=file_id,
                    mimeType=export_mime
                )
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            else:
                # 일반 파일 다운로드
                request = self.service.files().get_media(fileId=file_id)
                _, ext = os.path.splitext(file_name)
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            
            # 파일 다운로드
            downloader = MediaIoBaseDownload(temp_file, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            temp_file.close()
            return temp_file.name
            
        except Exception as e:
            print(f"❌ 파일 다운로드 실패 ({file_name}): {e}")
            return None
    
    def process_file(self, file_info: Dict[str, Any]) -> Document:
        """파일을 처리하여 Document 객체로 변환합니다."""
        file_id = file_info['id']
        file_name = file_info['name']
        mime_type = file_info['mimeType']
        
        # 파일 다운로드
        temp_path = self.download_file(file_id, file_name, mime_type)
        if not temp_path:
            return None
        
        try:
            # UnstructuredFileLoader로 파일 파싱
            loader = UnstructuredFileLoader(temp_path)
            documents = loader.load()
            
            if documents:
                # 메타데이터 추가
                doc = documents[0]
                doc.metadata.update({
                    "source": "google_drive",
                    "page_id": f"gdrive_{file_id}",
                    "title": file_name,
                    "file_name": file_name,
                    "file_id": file_id,
                    "mime_type": mime_type,
                    "path": file_info.get('path', ''),
                    "last_modified": file_info.get('modifiedTime', ''),
                    "created_time": file_info.get('createdTime', '')
                })
                return doc
                
        except Exception as e:
            print(f"❌ 파일 파싱 실패 ({file_name}): {e}")
            
        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
        return None
    
    def load_all_documents(self, since: Optional[str] = None, existing_metadata: Optional[Dict[str, Dict[str, Any]]] = None) -> List[Document]:
        """Google Drive의 모든 문서를 로드합니다.
        
        Args:
            since: ISO 8601 형식의 날짜 문자열. 이 시간 이후에 수정된 파일만 가져옵니다.
            existing_metadata: 기존 ChromaDB 메타데이터 딕셔너리. 변경 없으면 다운로드를 스킵합니다.
        """
        if not self.folder_id:
            print("⚠️ GDRIVE_FOLDER_ID가 설정되지 않았습니다.")
            return []
        
        files = self.list_files_in_folder(since=since)
        print(f"🔍 총 {len(files)}개의 파일을 발견했습니다.")
        
        if since and len(files) == 0:
            print(f"📅 {since} 이후에 수정된 파일이 없습니다.")
            return []
        
        # 기존 메타를 file_id 기준으로 빠르게 조회할 수 있게 맵 구축
        file_id_to_meta = {}
        if existing_metadata:
            for _doc_id, _meta in existing_metadata.items():
                fid = _meta.get('file_id')
                if fid and fid not in file_id_to_meta:
                    file_id_to_meta[fid] = _meta
        
        documents = []
        for i, file_info in enumerate(files, 1):
            print(f"\n📄 파일 {i}/{len(files)}: {file_info['name']}")
            
            # 기존 메타데이터 기반 사전 스킵 로직
            if existing_metadata is not None:
                file_id = file_info.get('id')
                prev_last_modified = None
                # 1) doc_id 정합 시도
                doc_id = f"google_drive:gdrive_{file_id}"
                meta = existing_metadata.get(doc_id) or file_id_to_meta.get(file_id)
                if meta:
                    prev_last_modified = meta.get('last_modified') or meta.get('last_updated')
                curr_last_modified = file_info.get('modifiedTime')
                # 1-a) modifiedTime이 동일하면 즉시 스킵
                if prev_last_modified and curr_last_modified and prev_last_modified == curr_last_modified:
                    print(f"⏭️ 변경 없음으로 스킵: {file_info['name']} ({file_id})")
                    continue
                # 1-b) modifiedTime이 제공되지 않은 경우: 동일 file_id 존재 시 보수적으로 스킵
                if meta and not curr_last_modified:
                    print(f"⏭️ 동일 file_id 기존 존재로 스킵(타임스탬프 없음): {file_info['name']} ({file_id})")
                    continue
                # 1-c) 서버 메타로 한 번 더 확인
                try:
                    fresh = self.service.files().get(
                        fileId=file_id,
                        fields="id, modifiedTime"
                    ).execute()
                    fresh_mod = fresh.get('modifiedTime')
                    if prev_last_modified and fresh_mod and prev_last_modified == fresh_mod:
                        print(f"⏭️ 서버 메타 기준 변경 없음으로 스킵: {file_info['name']} ({file_id})")
                        continue
                except Exception:
                    pass
            
            doc = self.process_file(file_info)
            if doc:
                documents.append(doc)
                print(f"  ✅ 문서 로드 완료")
            else:
                print(f"  ⚠️ 문서 로드 실패")
        
        return documents