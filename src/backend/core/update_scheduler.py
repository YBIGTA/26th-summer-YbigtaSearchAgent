"""
문서 업데이트 스케줄러
주기적으로 외부 소스의 문서 변경사항을 확인하고 동기화
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from integrations.notion_client import NotionClient
from integrations.github_client import GitHubClient
from integrations.drive_client import GoogleDriveClient
from indexers.chroma_index import ChromaIndexManager
from db.models import UserSetting


class UpdateScheduler:
    def __init__(self, chroma_manager: ChromaIndexManager, db_session_factory: Optional[Callable] = None, db_engine=None):
        self.chroma_manager = chroma_manager
        self.db_session_factory = db_session_factory
        self.db_engine = db_engine
        self.scheduler = AsyncIOScheduler()
        self.last_sync_times = {}
        self.sync_status = {}
        
        # 동기화 간격 설정 (환경변수로 설정 가능)
        self.sync_intervals = {
            'notion': int(os.getenv('NOTION_SYNC_INTERVAL', '3600')),  # 1시간
            'github': int(os.getenv('GITHUB_SYNC_INTERVAL', '7200')),  # 2시간
            'google_drive': int(os.getenv('GDRIVE_SYNC_INTERVAL', '3600'))  # 1시간
        }
    
    def _get_last_sync_time(self, source: str) -> Optional[datetime]:
        """데이터베이스에서 특정 소스의 마지막 동기화 시간을 읽어옵니다."""
        if not self.db_session_factory or not self.db_engine:
            print(f"⚠️ 데이터베이스 세션 팩토리나 엔진이 설정되지 않았습니다. {source} 마지막 동기화 시간을 메모리에서 읽습니다.")
            return self.last_sync_times.get(source)
        
        try:
            session = self.db_session_factory(self.db_engine)
            setting_key = f"last_sync_{source}"
            
            # UserSetting 테이블에서 마지막 동기화 시간 조회
            setting = session.query(UserSetting).filter(
                UserSetting.key == setting_key
            ).first()
            
            if setting and setting.value:
                # ISO 8601 형식의 문자열을 datetime 객체로 변환
                last_sync_time = datetime.fromisoformat(setting.value)
                print(f"📅 {source} 마지막 동기화 시간: {last_sync_time}")
                return last_sync_time
            else:
                print(f"📅 {source} 마지막 동기화 시간이 데이터베이스에 없습니다.")
                return None
                
        except Exception as e:
            print(f"❌ {source} 마지막 동기화 시간 조회 실패: {e}")
            return self.last_sync_times.get(source)
        finally:
            if 'session' in locals():
                session.close()
    
    def _set_last_sync_time(self, source: str, sync_time: datetime = None) -> bool:
        """데이터베이스에 특정 소스의 마지막 동기화 시간을 저장합니다."""
        if not self.db_session_factory or not self.db_engine:
            print(f"⚠️ 데이터베이스 세션 팩토리나 엔진이 설정되지 않았습니다. {source} 마지막 동기화 시간을 메모리에만 저장합니다.")
            self.last_sync_times[source] = sync_time or datetime.now()
            return False
        
        try:
            session = self.db_session_factory(self.db_engine)
            setting_key = f"last_sync_{source}"
            current_time = sync_time or datetime.now()
            
            # UserSetting 테이블에서 기존 설정 조회
            setting = session.query(UserSetting).filter(
                UserSetting.key == setting_key
            ).first()
            
            if setting:
                # 기존 설정 업데이트
                setting.value = current_time.isoformat()
                setting.updated_at = datetime.utcnow()
            else:
                # 새 설정 생성 (user_id는 1로 가정, 실제로는 적절한 사용자 ID 사용)
                setting = UserSetting(
                    user_id=1,  # 기본 사용자 ID
                    key=setting_key,
                    value=current_time.isoformat()
                )
                session.add(setting)
            
            session.commit()
            print(f"✅ {source} 마지막 동기화 시간 저장 완료: {current_time}")
            
            # 메모리에도 저장
            self.last_sync_times[source] = current_time
            return True
            
        except Exception as e:
            print(f"❌ {source} 마지막 동기화 시간 저장 실패: {e}")
            if 'session' in locals():
                session.rollback()
            # 메모리에만 저장
            self.last_sync_times[source] = sync_time or datetime.now()
            return False
        finally:
            if 'session' in locals():
                session.close()
    
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
            
            # 마지막 동기화 시간 조회
            last_sync_time = self._get_last_sync_time(source)
            if last_sync_time:
                print(f"📅 Notion 마지막 동기화 시간: {last_sync_time}")
            
            # Notion 클라이언트 초기화 (마지막 동기화 시간 전달)
            client = NotionClient()
            
            # 모든 페이지 로드 (마지막 동기화 시간 이후 변경사항만 가져오기)
            since_str = last_sync_time.isoformat() if last_sync_time else None
            documents = await client.load_all_pages(since=since_str)
            
            if documents:
                # ChromaDB에 동기화 (증분 업데이트)
                self.chroma_manager.sync_source(source, documents)
                
                # 통계 업데이트
                self._set_last_sync_time(source)
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
            
            # 마지막 동기화 시간 조회
            last_sync_time = self._get_last_sync_time(source)
            if last_sync_time:
                print(f"📅 GitHub 마지막 동기화 시간: {last_sync_time}")
            
            # GitHub 클라이언트 초기화 (마지막 동기화 시간 전달)
            client = GitHubClient()
            
            # 모든 리포지토리 로드 (마지막 동기화 시간 이후 변경사항만 가져오기)
            since_str = last_sync_time.isoformat() if last_sync_time else None
            documents = await asyncio.get_event_loop().run_in_executor(None, client.load_all_repos, since_str)
            
            if documents:
                # ChromaDB에 동기화 (증분 업데이트)
                self.chroma_manager.sync_source(source, documents)
                
                # 통계 업데이트
                self._set_last_sync_time(source)
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
            
            # 마지막 동기화 시간 조회
            last_sync_time = self._get_last_sync_time(source)
            if last_sync_time:
                print(f"📅 Google Drive 마지막 동기화 시간: {last_sync_time}")
            
            # Google Drive 클라이언트 초기화 (마지막 동기화 시간 전달)
            client = GoogleDriveClient()
            
            # 모든 문서 로드 (마지막 동기화 시간 이후 변경사항만 가져오기)
            since_str = last_sync_time.isoformat() if last_sync_time else None
            documents = await asyncio.get_event_loop().run_in_executor(None, client.load_all_documents, since_str)
            
            if documents:
                # ChromaDB에 동기화 (증분 업데이트)
                self.chroma_manager.sync_source(source, documents)
                
                # 통계 업데이트
                self._set_last_sync_time(source)
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
                'last_sync': self._get_last_sync_time(source),
                'next_sync': self._get_next_sync_time(source),
                'interval': self.sync_intervals.get(source)
            }
        
        # ChromaDB 통계 추가
        status['database'] = self.chroma_manager.get_statistics()
        status['update_status'] = self.chroma_manager.get_update_status()
        
        return status
    
    def _get_next_sync_time(self, source: str) -> datetime:
        """다음 동기화 예정 시간을 계산합니다."""
        last_sync = self._get_last_sync_time(source)
        if last_sync is None:
            return datetime.now()
        
        interval = self.sync_intervals.get(source, 3600)
        return last_sync + timedelta(seconds=interval)