"""
문서 업데이트 스케줄러
주기적으로 외부 소스의 문서 변경사항을 확인하고 동기화
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from integrations.notion_client import NotionClient
from integrations.github_client import GitHubClient
from integrations.drive_client import GoogleDriveClient
from indexers.chroma_index import ChromaIndexManager


class UpdateScheduler:
    def __init__(self, chroma_manager: ChromaIndexManager):
        self.chroma_manager = chroma_manager
        self.scheduler = AsyncIOScheduler()
        self.last_sync_times = {}
        self.sync_status = {}
        
        # 동기화 간격 설정 (환경변수로 설정 가능)
        self.sync_intervals = {
            'notion': int(os.getenv('NOTION_SYNC_INTERVAL', '3600')),  # 1시간
            'github': int(os.getenv('GITHUB_SYNC_INTERVAL', '7200')),  # 2시간
            'google_drive': int(os.getenv('GDRIVE_SYNC_INTERVAL', '3600'))  # 1시간
        }
    
    def start(self):
        """스케줄러를 시작합니다."""
        print("🚀 문서 업데이트 스케줄러 시작")
        
        # 각 소스별 동기화 작업 등록
        if os.getenv('NOTION_API_KEY'):
            self.scheduler.add_job(
                self.sync_notion,
                IntervalTrigger(seconds=self.sync_intervals['notion']),
                id='sync_notion',
                name='Notion 동기화',
                replace_existing=True
            )
            print(f"📅 Notion 동기화 스케줄 등록 (매 {self.sync_intervals['notion']}초)")
        
        if os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN'):
            self.scheduler.add_job(
                self.sync_github,
                IntervalTrigger(seconds=self.sync_intervals['github']),
                id='sync_github',
                name='GitHub 동기화',
                replace_existing=True
            )
            print(f"📅 GitHub 동기화 스케줄 등록 (매 {self.sync_intervals['github']}초)")
        
        if os.getenv('GDRIVE_FOLDER_ID'):
            self.scheduler.add_job(
                self.sync_google_drive,
                IntervalTrigger(seconds=self.sync_intervals['google_drive']),
                id='sync_google_drive',
                name='Google Drive 동기화',
                replace_existing=True
            )
            print(f"📅 Google Drive 동기화 스케줄 등록 (매 {self.sync_intervals['google_drive']}초)")
        
        # 스케줄러 시작
        self.scheduler.start()
        
        # 초기 동기화 실행
        asyncio.create_task(self.initial_sync())
    
    def stop(self):
        """스케줄러를 중지합니다."""
        print("🛑 문서 업데이트 스케줄러 중지")
        self.scheduler.shutdown()
    
    async def initial_sync(self):
        """초기 동기화를 수행합니다."""
        print("🔄 초기 동기화 시작...")
        
        tasks = []
        if os.getenv('NOTION_API_KEY'):
            tasks.append(self.sync_notion())
        if os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN'):
            tasks.append(self.sync_github())
        if os.getenv('GDRIVE_FOLDER_ID'):
            tasks.append(self.sync_google_drive())
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        print("✅ 초기 동기화 완료")
    
    async def sync_notion(self):
        """Notion 문서를 동기화합니다."""
        source = 'notion'
        print(f"\n🔄 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Notion 동기화 시작")
        
        try:
            self.sync_status[source] = 'syncing'
            start_time = datetime.now()
            
            # Notion 클라이언트 초기화
            client = NotionClient()
            
            # 모든 페이지 로드
            documents = await client.load_all_pages()
            
            if documents:
                # ChromaDB에 동기화 (증분 업데이트)
                self.chroma_manager.sync_source(source, documents)
                
                # 통계 업데이트
                self.last_sync_times[source] = datetime.now()
                self.sync_status[source] = 'completed'
                
                duration = (datetime.now() - start_time).seconds
                print(f"✅ Notion 동기화 완료: {len(documents)}개 문서, {duration}초 소요")
            else:
                print("⚠️ Notion에서 문서를 찾을 수 없습니다.")
                self.sync_status[source] = 'no_documents'
                
        except Exception as e:
            print(f"❌ Notion 동기화 실패: {e}")
            self.sync_status[source] = 'error'
    
    async def sync_github(self):
        """GitHub 리포지토리를 동기화합니다."""
        source = 'github'
        print(f"\n🔄 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - GitHub 동기화 시작")
        
        try:
            self.sync_status[source] = 'syncing'
            start_time = datetime.now()
            
            # GitHub 클라이언트 초기화
            client = GitHubClient()
            
            # 모든 리포지토리 로드
            documents = await asyncio.get_event_loop().run_in_executor(None, client.load_all_repos)
            
            if documents:
                # ChromaDB에 동기화 (증분 업데이트)
                self.chroma_manager.sync_source(source, documents)
                
                # 통계 업데이트
                self.last_sync_times[source] = datetime.now()
                self.sync_status[source] = 'completed'
                
                duration = (datetime.now() - start_time).seconds
                print(f"✅ GitHub 동기화 완료: {len(documents)}개 리포지토리, {duration}초 소요")
            else:
                print("⚠️ GitHub에서 리포지토리를 찾을 수 없습니다.")
                self.sync_status[source] = 'no_documents'
                
        except Exception as e:
            print(f"❌ GitHub 동기화 실패: {e}")
            self.sync_status[source] = 'error'
    
    async def sync_google_drive(self):
        """Google Drive 문서를 동기화합니다."""
        source = 'google_drive'
        print(f"\n🔄 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Google Drive 동기화 시작")
        
        try:
            self.sync_status[source] = 'syncing'
            start_time = datetime.now()
            
            # Google Drive 클라이언트 초기화
            client = GoogleDriveClient()
            
            # 모든 문서 로드
            documents = await asyncio.get_event_loop().run_in_executor(None, client.load_all_documents)
            
            if documents:
                # ChromaDB에 동기화 (증분 업데이트)
                self.chroma_manager.sync_source(source, documents)
                
                # 통계 업데이트
                self.last_sync_times[source] = datetime.now()
                self.sync_status[source] = 'completed'
                
                duration = (datetime.now() - start_time).seconds
                print(f"✅ Google Drive 동기화 완료: {len(documents)}개 문서, {duration}초 소요")
            else:
                print("⚠️ Google Drive에서 문서를 찾을 수 없습니다.")
                self.sync_status[source] = 'no_documents'
                
        except Exception as e:
            print(f"❌ Google Drive 동기화 실패: {e}")
            self.sync_status[source] = 'error'
    
    async def force_sync(self, source: str = None):
        """특정 소스 또는 모든 소스를 강제로 동기화합니다."""
        if source:
            if source == 'notion':
                await self.sync_notion()
            elif source == 'github':
                await self.sync_github()
            elif source == 'google_drive':
                await self.sync_google_drive()
            else:
                raise ValueError(f"알 수 없는 소스: {source}")
        else:
            # 모든 소스 동기화
            await self.initial_sync()
    
    def get_sync_status(self) -> Dict[str, Any]:
        """동기화 상태를 반환합니다."""
        status = {}
        
        for source in ['notion', 'github', 'google_drive']:
            status[source] = {
                'status': self.sync_status.get(source, 'not_started'),
                'last_sync': self.last_sync_times.get(source),
                'next_sync': self._get_next_sync_time(source),
                'interval': self.sync_intervals.get(source)
            }
        
        # ChromaDB 통계 추가
        status['database'] = self.chroma_manager.get_statistics()
        status['update_status'] = self.chroma_manager.get_update_status()
        
        return status
    
    def _get_next_sync_time(self, source: str) -> datetime:
        """다음 동기화 예정 시간을 계산합니다."""
        if source not in self.last_sync_times:
            return datetime.now()
        
        last_sync = self.last_sync_times[source]
        interval = self.sync_intervals.get(source, 3600)
        return last_sync + timedelta(seconds=interval)