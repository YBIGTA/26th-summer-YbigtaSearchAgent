"""
백엔드 메인 애플리케이션
FastAPI 서버 및 라우트 설정
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import sys
import uuid
from datetime import datetime

# 환경변수 로드 (로컬에서 실행 시)
from dotenv import load_dotenv
load_dotenv()

# 백엔드 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.models import init_db, get_session, MeetingReport
from core.embeddings import AsyncUpstageEmbeddings
from core.settings_sync import settings_sync
from indexers.hybrid_chroma_manager import HybridChromaManager
from integrations.notion_client import NotionClient
from integrations.github_client import GitHubClient
from integrations.drive_client import GoogleDriveClient
from stt.stt_manager import stt_manager
from stt.speaker_diarization import SpeakerDiarizationEngine
from core.update_scheduler import UpdateScheduler
from core.meeting_pipeline import MeetingAnalysisPipeline
from agents.multi_agent_orchestrator import MultiAgentOrchestrator
from llm import create_upstage_client
from nlp.hybrid_retriever import HybridRetriever

# 전역 변수
db_engine = None
chroma_manager = None
embeddings = None
update_scheduler = None
agent_orchestrator = None
hybrid_retriever = None
speaker_diarizer = None
meeting_pipeline = None
analysis_jobs = {}  # 분석 작업 상태 저장


# Pydantic 모델들
class AnalysisRequest(BaseModel):
    transcript_id: int
    analysis_options: Optional[Dict[str, Any]] = None
    priority: Optional[str] = "normal"

class AgentConfig(BaseModel):
    agent_type: str
    enabled: bool = True
    config: Optional[Dict[str, Any]] = None

class STTRequest(BaseModel):
    file_id: int
    engine: Optional[str] = "whisper"
    language: Optional[str] = "ko"
    enable_diarization: Optional[bool] = True

class PipelineRequest(BaseModel):
    audio_file_path: str
    analysis_options: Optional[Dict[str, Any]] = None

class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    search_type: str = "hybrid"  # "hybrid", "semantic", "keyword"
    filters: Optional[Dict[str, Any]] = None
    sources: Optional[List[str]] = None

class SearchResponse(BaseModel):
    query: str
    search_type: str
    results: Dict[str, Any]
    total_found: int
    response_time: float
    search_metadata: Dict[str, Any]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    global db_engine, chroma_manager, embeddings, update_scheduler, agent_orchestrator, hybrid_retriever, speaker_diarizer, meeting_pipeline
    
    # 환경 변수 확인
    upstage_api_key = os.getenv("UPSTAGE_API_KEY")
    if not upstage_api_key:
        print("⚠️ UPSTAGE_API_KEY가 설정되지 않았습니다.")
        print("환경 변수를 확인하거나 .env 파일을 설정해주세요.")
    
    # 시작 시 초기화
    print("🚀 백엔드 서버 초기화 중...")
    
    # 데이터베이스 초기화
    db_engine = init_db()
    print("✅ 데이터베이스 초기화 완료")
    
    # 임베딩 모델 초기화 (조건부)
    try:
        embeddings = AsyncUpstageEmbeddings()
        print("✅ 임베딩 모델 초기화 완료")
    except Exception as e:
        print(f"⚠️ 임베딩 모델 초기화 실패: {e}")
        embeddings = None
    
    # 하이브리드 ChromaDB 시스템 초기화
    chroma_manager = HybridChromaManager(
        unified_db_path="data/unified_chroma_db/unified_chroma_db",
        incremental_db_path="data/indexes/incremental_chroma_db"
    )
    chroma_manager.initialize(embeddings)
    print("✅ 하이브리드 ChromaDB 시스템 초기화 완료")
    
    # 하이브리드 검색 시스템 초기화
    hybrid_retriever = HybridRetriever(
        chroma_manager=chroma_manager,
        embedding_client=embeddings,
        db_session_factory=get_session
    )
    print("✅ 하이브리드 검색 시스템 초기화 완료")
    
    # 화자 분리 시스템 초기화
    speaker_diarizer = SpeakerDiarizationEngine()
    print("✅ 화자 분리 시스템 초기화 완료")
    
    # LLM 클라이언트 초기화
    llm_client = create_upstage_client()
    if llm_client:
        print("✅ Upstage LLM 클라이언트 초기화 완료")
    else:
        print("⚠️ Upstage LLM 클라이언트 초기화 실패 - 에이전트가 제한된 기능으로 동작합니다")
    
    # 멀티에이전트 오케스트레이터 초기화
    if llm_client:
        agent_orchestrator = MultiAgentOrchestrator(
            retriever=hybrid_retriever,
            llm_client=llm_client
        )
        print("✅ 멀티에이전트 오케스트레이터 초기화 완료")
    else:
        agent_orchestrator = None
        print("⚠️ LLM 클라이언트가 없어 에이전트 오케스트레이터를 초기화하지 않습니다.")
    
    # 회의 분석 파이프라인 초기화
    meeting_pipeline = MeetingAnalysisPipeline(
        stt_manager=stt_manager,
        speaker_diarizer=speaker_diarizer,
        agent_orchestrator=agent_orchestrator,
        db_engine=db_engine
    )
    print("✅ 회의 분석 파이프라인 초기화 완료")
    
    # 업데이트 스케줄러 초기화
    update_scheduler = UpdateScheduler(chroma_manager, db_session_factory=get_session, db_engine=db_engine)
    update_scheduler.start()
    print("✅ 문서 업데이트 스케줄러 시작")
    
    print("🎉 모든 컴포넌트 초기화 완료!")
    
    yield
    
    # 종료 시 정리
    print("👋 백엔드 서버 종료 중...")
    if update_scheduler:
        update_scheduler.stop()
    if agent_orchestrator and hasattr(agent_orchestrator, 'cleanup'):
        await agent_orchestrator.cleanup()


# FastAPI 앱 생성
app = FastAPI(
    title="YBIGTA Meeting Analyzer Backend",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정 (프론트엔드-백엔드 통신)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # 개발 서버
        "http://127.0.0.1:3000",
        "http://localhost:8000",  # 자체 서버
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# === 라우트 정의 ===

@app.get("/")
async def root():
    """헬스 체크"""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/api/stats")
async def get_stats():
    """시스템 통계 반환"""
    stats = chroma_manager.get_statistics()
    return stats

@app.get("/api/search/stats")
async def get_search_stats():
    """검색 시스템 통계 반환"""
    try:
        if not hybrid_retriever:
            raise HTTPException(status_code=503, detail="하이브리드 검색 시스템이 초기화되지 않았습니다.")
        
        search_stats = hybrid_retriever.get_search_stats()
        
        # 각 검색 엔진의 상태 확인
        engine_stats = {}
        if hybrid_retriever.semantic_engine:
            engine_stats["semantic"] = hybrid_retriever.semantic_engine.get_search_stats()
        if hybrid_retriever.keyword_engine:
            engine_stats["keyword"] = hybrid_retriever.keyword_engine.get_search_stats()
        
        return {
            "hybrid_retriever": search_stats,
            "engines": engine_stats,
            "chroma_manager": chroma_manager.get_statistics() if chroma_manager else None,
            "embeddings": {
                "available": embeddings is not None,
                "type": "AsyncUpstageEmbeddings" if embeddings else None
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === 설정 관리 ===

@app.post("/api/settings/api-keys")
async def save_api_key(provider: str, key: str, index: int = None):
    """API 키 저장"""
    result = settings_sync.save_api_key(provider, key, index)
    return result


@app.get("/api/settings/api-keys")
async def get_api_keys(provider: str = None):
    """저장된 API 키 목록 반환 (마스킹됨)"""
    keys = settings_sync.get_api_keys(provider)
    return {"keys": keys}


@app.delete("/api/settings/api-keys")
async def remove_api_key(provider: str, index: int = None):
    """API 키 제거"""
    result = settings_sync.remove_api_key(provider, index)
    return result


@app.post("/api/settings/api-keys/test")
async def test_api_key(provider: str, key: str):
    """API 키 유효성 테스트"""
    result = settings_sync.test_api_key(provider, key)
    return result


@app.post("/api/settings/notion-pages")
async def save_notion_pages(page_ids: list):
    """Notion 페이지 ID 저장"""
    result = settings_sync.save_notion_pages(page_ids)
    return result


@app.get("/api/settings/stt-engines")
async def get_stt_engines():
    """사용 가능한 STT 엔진 목록"""
    engines = stt_manager.get_available_engines()
    return {"engines": engines}


@app.post("/api/settings/stt-engines/validate")
async def validate_stt_engine(engine: str):
    """STT 엔진 설정 유효성 검사"""
    result = stt_manager.validate_engine_config(engine)
    return result


# === 오디오 처리 ===

@app.post("/api/audio/upload")
async def upload_audio(file: UploadFile = File(...)):
    """오디오 파일 업로드"""
    # 파일 저장
    os.makedirs("data/audio", exist_ok=True)
    file_path = f"data/audio/{file.filename}"
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # DB에 기록
    session = get_session(db_engine)
    try:
        # TODO: AudioFile 모델에 저장
        return {
            "status": "success",
            "file_id": 1,
            "filename": file.filename,
            "message": "파일이 업로드되었습니다."
        }
    finally:
        session.close()


@app.post("/api/stt/process")
async def process_stt_enhanced(request: STTRequest):
    """고급 STT 처리 (화자 분리 포함)"""
    try:
        # 파일 경로 조회 (TODO: 실제로는 DB에서 조회해야 함)
        # 임시로 업로드된 파일명으로 찾기
        if request.file_id == 1:
            file_path = "data/audio/test_audio.wav"
        else:
            file_path = f"data/audio/sample_{request.file_id}.wav"
        
        print(f"DEBUG: Looking for file at: {file_path}")
        print(f"DEBUG: File exists: {os.path.exists(file_path)}")
        print(f"DEBUG: Current working directory: {os.getcwd()}")
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"오디오 파일을 찾을 수 없습니다: {file_path}")
        
        # STT 처리
        stt_result = stt_manager.transcribe(file_path, request.engine, request.language)
        
        # 화자 분리 활성화 시 처리
        if request.enable_diarization and speaker_diarizer:
            segments_with_speakers = await speaker_diarizer.diarize_audio(
                file_path, 
                stt_result.get("segments", [])
            )
            stt_result["segments"] = segments_with_speakers
            
            # 화자별 통계 추가
            speaker_stats = speaker_diarizer.analyze_speaker_distribution(segments_with_speakers)
            stt_result["speaker_analysis"] = speaker_stats
        
        return {
            "status": "completed",
            "file_id": request.file_id,
            "diarization_enabled": request.enable_diarization,
            "result": stt_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/stt/{file_id}")
async def process_stt_legacy(file_id: int, engine: str = "whisper", language: str = "ko"):
    """기존 STT 처리 (하위 호환성)"""
    request = STTRequest(
        file_id=file_id,
        engine=engine,
        language=language,
        enable_diarization=False
    )
    return await process_stt_enhanced(request)


# === 회의록 관리 ===

@app.get("/api/transcripts")
async def get_transcripts():
    """회의록 목록 조회"""
    session = get_session(db_engine)
    try:
        # TODO: Transcript 모델 조회
        return {
            "transcripts": [
                {
                    "id": 1,
                    "title": "2024년 1월 정기회의",
                    "date": "2024-01-15",
                    "duration": 3600,
                    "speakers": 5
                }
            ]
        }
    finally:
        session.close()


@app.get("/api/transcripts/{transcript_id}")
async def get_transcript(transcript_id: int):
    """특정 회의록 상세 조회"""
    session = get_session(db_engine)
    try:
        # TODO: Transcript 상세 조회
        return {
            "id": transcript_id,
            "title": "2024년 1월 정기회의",
            "utterances": []
        }
    finally:
        session.close()


# === 검색 ===

@app.post("/api/v1/search", response_model=SearchResponse)
async def search_endpoint(request: SearchRequest):
    """통합 검색 API - 하이브리드, 의미적, 키워드 검색 지원"""
    import time
    start_time = time.time()
    
    try:
        if not hybrid_retriever:
            raise HTTPException(status_code=503, detail="하이브리드 검색 시스템이 초기화되지 않았습니다.")
        
        # 검색 실행
        results = await hybrid_retriever.search(
            query=request.query,
            top_k=request.top_k,
            search_type=request.search_type,
            filters=request.filters,
            sources=request.sources
        )
        
        response_time = time.time() - start_time
        
        return SearchResponse(
            query=request.query,
            search_type=request.search_type,
            results=results,
            total_found=len(results.get("results", {}).get("documents", [])),
            response_time=response_time,
            search_metadata=results.get("search_metadata", {})
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 중 오류 발생: {str(e)}")

@app.post("/api/search/hybrid")
async def hybrid_search_endpoint(query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None, sources: Optional[List[str]] = None):
    """고급 하이브리드 검색 (하위 호환성)"""
    try:
        if not hybrid_retriever:
            raise HTTPException(status_code=503, detail="하이브리드 검색 시스템이 초기화되지 않았습니다.")
        
        results = await hybrid_retriever.search(
            query=query, 
            top_k=top_k,
            filters=filters,
            sources=sources
        )
        
        return {
            "query": query,
            "results": results,
            "total_found": len(results.get("results", {}).get("documents", []))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search/vector")
async def vector_search(query: str, top_k: int = 5):
    """벡터 검색만"""
    try:
        if not hybrid_retriever or not hybrid_retriever.semantic_engine:
            # 폴백: 기존 ChromaDB 사용
            if chroma_manager:
                results = chroma_manager.vector_search(query, top_k)
                return {"results": results}
            else:
                raise HTTPException(status_code=503, detail="벡터 검색 시스템이 초기화되지 않았습니다.")
        
        results = await hybrid_retriever.semantic_engine.search(
            query=query,
            top_k=top_k
        )
        return {"results": results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search/keyword")
async def keyword_search(query: str, top_k: int = 5):
    """키워드 검색만"""
    try:
        if not hybrid_retriever or not hybrid_retriever.keyword_engine:
            # 폴백: 메타데이터 검색
            if chroma_manager:
                filter = {"$or": [{"title": {"$contains": query}}, {"source": {"$contains": query}}]}
                results = chroma_manager.metadata_search(filter, top_k)
                return {"results": results}
            else:
                raise HTTPException(status_code=503, detail="키워드 검색 시스템이 초기화되지 않았습니다.")
        
                results = await hybrid_retriever.keyword_engine.search(
            query=query,
            top_k=top_k
        )
        return {"results": results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search/text")
async def text_search(query: str, top_k: int = 5):
    """텍스트 검색 (하위 호환성)"""
    return await keyword_search(query, top_k)

@app.post("/api/search/config")
async def update_search_config(config: Dict[str, Any]):
    """검색 시스템 설정 업데이트"""
    try:
        if not hybrid_retriever:
            raise HTTPException(status_code=503, detail="하이브리드 검색 시스템이 초기화되지 않았습니다.")
        
        success = await hybrid_retriever.update_configuration(config)
        
        if success:
            return {
                "status": "success",
                "message": "검색 시스템 설정이 업데이트되었습니다.",
                "updated_config": config
            }
        else:
            raise HTTPException(status_code=400, detail="설정 업데이트 실패")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === 지식베이스 동기화 ===

@app.post("/api/sync/notion")
async def sync_notion():
    """Notion 문서 동기화"""
    try:
        client = NotionClient()
        docs = await client.load_all_pages()
        chroma_manager.sync_source("notion", docs)
        return {
            "status": "success",
            "documents_synced": len(docs),
            "message": f"{len(docs)}개의 Notion 문서가 동기화되었습니다."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sync/github")
async def sync_github():
    """GitHub 리포지토리 동기화"""
    try:
        client = GitHubClient()
        docs = client.load_all_repos()
        chroma_manager.sync_source("github", docs)
        return {
            "status": "success",
            "documents_synced": len(docs),
            "message": f"{len(docs)}개의 GitHub 문서가 동기화되었습니다."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sync/drive")
async def sync_drive():
    """Google Drive 문서 동기화"""
    try:
        client = GoogleDriveClient()
        docs = client.load_all_documents()
        chroma_manager.sync_source("google_drive", docs)
        return {
            "status": "success",
            "documents_synced": len(docs),
            "message": f"{len(docs)}개의 Drive 문서가 동기화되었습니다."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === 동기화 상태 ===

@app.get("/api/sync/status")
async def get_sync_status():
    """모든 소스의 동기화 상태를 반환합니다."""
    if not update_scheduler:
        return {"error": "스케줄러가 초기화되지 않았습니다."}
    
    return update_scheduler.get_sync_status()


@app.post("/api/sync/force/{source}")
async def force_sync_source(source: str):
    """특정 소스를 강제로 동기화합니다."""
    if not update_scheduler:
        raise HTTPException(status_code=503, detail="스케줄러가 초기화되지 않았습니다.")
    
    valid_sources = ['notion', 'github', 'google_drive']
    if source not in valid_sources:
        raise HTTPException(status_code=400, detail=f"유효하지 않은 소스입니다. 가능한 값: {valid_sources}")
    
    try:
        await update_scheduler.force_sync(source)
        return {
            "status": "success",
            "message": f"{source} 동기화를 시작했습니다."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === 멀티에이전트 분석 시스템 ===

@app.post("/api/agents/analyze")
async def start_multi_agent_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """멀티에이전트 회의 분석 시작"""
    try:
        if not agent_orchestrator:
            raise HTTPException(status_code=503, detail="멀티에이전트 시스템이 초기화되지 않았습니다.")
        
        # 고유한 작업 ID 생성
        job_id = f"analysis_{uuid.uuid4().hex[:8]}"
        
        # 작업 상태 초기화
        analysis_jobs[job_id] = {
            "status": "initializing",
            "transcript_id": request.transcript_id,
            "progress": 0,
            "started_at": None,
            "completed_at": None,
            "error": None,
            "results": None
        }
        
        # 백그라운드에서 분석 시작
        background_tasks.add_task(
            execute_multi_agent_analysis,
            job_id,
            request.transcript_id,
            request.analysis_options or {}
        )
        
        return {
            "status": "started",
            "job_id": job_id,
            "transcript_id": request.transcript_id,
            "message": "멀티에이전트 분석을 시작했습니다."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def execute_multi_agent_analysis(job_id: str, transcript_id: int, options: Dict[str, Any]):
    """실제 멀티에이전트 분석 실행 (백그라운드 작업)"""
    try:
        # 작업 상태 업데이트
        analysis_jobs[job_id]["status"] = "running"
        analysis_jobs[job_id]["started_at"] = "2024-01-01T00:00:00Z"  # TODO: 실제 시간
        analysis_jobs[job_id]["progress"] = 10
        
        # 회의록 데이터 조회 (TODO: 실제 DB 조회)
        transcript_data = {
            "id": transcript_id,
            "title": f"Meeting {transcript_id}",
            "content": "Sample meeting transcript content...",
            "segments": []
        }
        
        # 멀티에이전트 분석 실행
        analysis_jobs[job_id]["progress"] = 30
        results = await agent_orchestrator.analyze_meeting(transcript_data, options)
        
        # 결과 저장
        analysis_jobs[job_id]["status"] = "completed"
        analysis_jobs[job_id]["progress"] = 100
        analysis_jobs[job_id]["completed_at"] = "2024-01-01T01:00:00Z"  # TODO: 실제 시간
        analysis_jobs[job_id]["results"] = results
        
    except Exception as e:
        # 오류 상태 업데이트
        analysis_jobs[job_id]["status"] = "failed"
        analysis_jobs[job_id]["error"] = str(e)
        print(f"멀티에이전트 분석 실패 (job_id: {job_id}): {str(e)}")


@app.get("/api/agents/status/{job_id}")
async def get_analysis_status(job_id: str):
    """분석 작업 상태 조회"""
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="분석 작업을 찾을 수 없습니다.")
    
    return analysis_jobs[job_id]


@app.get("/api/agents/results/{job_id}")
async def get_analysis_results(job_id: str):
    """분석 결과 조회"""
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="분석 작업을 찾을 수 없습니다.")
    
    job = analysis_jobs[job_id]
    
    if job["status"] == "failed":
        raise HTTPException(status_code=500, detail=f"분석 실패: {job['error']}")
    
    if job["status"] != "completed":
        raise HTTPException(status_code=202, detail="분석이 아직 완료되지 않았습니다.")
    
    return {
        "job_id": job_id,
        "status": job["status"],
        "transcript_id": job["transcript_id"],
        "results": job["results"],
        "completed_at": job["completed_at"]
    }


@app.get("/api/agents/jobs")
async def list_analysis_jobs():
    """모든 분석 작업 목록"""
    return {
        "jobs": [
            {
                "job_id": job_id,
                "status": job["status"],
                "transcript_id": job["transcript_id"],
                "progress": job["progress"],
                "started_at": job["started_at"]
            }
            for job_id, job in analysis_jobs.items()
        ]
    }


@app.delete("/api/agents/jobs/{job_id}")
async def cancel_analysis_job(job_id: str):
    """분석 작업 취소"""
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="분석 작업을 찾을 수 없습니다.")
    
    job = analysis_jobs[job_id]
    
    if job["status"] in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail="이미 완료된 작업은 취소할 수 없습니다.")
    
    # 작업 취소
    analysis_jobs[job_id]["status"] = "cancelled"
    
    return {
        "message": f"분석 작업 {job_id}가 취소되었습니다."
    }


# === 개별 에이전트 엔드포인트 ===

@app.post("/api/agents/agenda-miner")
async def run_agenda_miner(transcript_id: int):
    """안건 추출 에이전트 실행"""
    try:
        if not agent_orchestrator:
            raise HTTPException(status_code=503, detail="에이전트 시스템이 초기화되지 않았습니다.")
        
        # TODO: 실제 transcript 데이터 조회
        transcript_data = f"Meeting transcript {transcript_id}"
        
        result = await agent_orchestrator.agenda_miner.analyze(transcript_data)
        
        return {
            "agent": "agenda_miner",
            "transcript_id": transcript_id,
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/claim-checker")
async def run_claim_checker(transcript_id: int):
    """주장 검증 에이전트 실행"""
    try:
        if not agent_orchestrator:
            raise HTTPException(status_code=503, detail="에이전트 시스템이 초기화되지 않았습니다.")
        
        transcript_data = f"Meeting transcript {transcript_id}"
        result = await agent_orchestrator.claim_checker.analyze(transcript_data)
        
        return {
            "agent": "claim_checker",
            "transcript_id": transcript_id,
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/counter-arguer")
async def run_counter_arguer(transcript_id: int):
    """반박 생성 에이전트 실행"""
    try:
        if not agent_orchestrator:
            raise HTTPException(status_code=503, detail="에이전트 시스템이 초기화되지 않았습니다.")
        
        transcript_data = f"Meeting transcript {transcript_id}"
        result = await agent_orchestrator.counter_arguer.analyze(transcript_data)
        
        return {
            "agent": "counter_arguer",
            "transcript_id": transcript_id,
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/evidence-hunter")
async def run_evidence_hunter(transcript_id: int, query: Optional[str] = None):
    """증거 수집 에이전트 실행"""
    try:
        if not agent_orchestrator:
            raise HTTPException(status_code=503, detail="에이전트 시스템이 초기화되지 않았습니다.")
        
        transcript_data = f"Meeting transcript {transcript_id}"
        search_query = query or f"Evidence for meeting {transcript_id}"
        
        result = await agent_orchestrator.evidence_hunter.search_and_verify(search_query, transcript_data)
        
        return {
            "agent": "evidence_hunter",
            "transcript_id": transcript_id,
            "query": search_query,
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/summarizer")
async def run_summarizer(transcript_id: int):
    """요약 에이전트 실행"""
    try:
        if not agent_orchestrator:
            raise HTTPException(status_code=503, detail="에이전트 시스템이 초기화되지 않았습니다.")
        
        # TODO: 다른 에이전트들의 결과를 수집
        agent_results = {
            "agendas": ["Sample agenda 1", "Sample agenda 2"],
            "claims": ["Sample claim verification"],
            "counter_arguments": ["Sample counter argument"],
            "evidence": ["Sample evidence"]
        }
        
        result = await agent_orchestrator.summarizer.generate_report(agent_results)
        
        return {
            "agent": "summarizer",
            "transcript_id": transcript_id,
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/config")
async def get_agent_config():
    """에이전트 설정 조회"""
    if not agent_orchestrator:
        raise HTTPException(status_code=503, detail="에이전트 시스템이 초기화되지 않았습니다.")
    
    return {
        "agents": {
            "agenda_miner": {"enabled": True, "type": "analysis"},
            "claim_checker": {"enabled": True, "type": "verification"},
            "counter_arguer": {"enabled": True, "type": "generation"},
            "evidence_hunter": {"enabled": True, "type": "retrieval"},
            "summarizer": {"enabled": True, "type": "synthesis"}
        },
        "orchestrator_config": {
            "max_concurrent_agents": 3,
            "timeout_minutes": 30,
            "retry_attempts": 2
        }
    }


@app.post("/api/agents/config")
async def update_agent_config(config: AgentConfig):
    """에이전트 설정 업데이트"""
    try:
        if not agent_orchestrator:
            raise HTTPException(status_code=503, detail="에이전트 시스템이 초기화되지 않았습니다.")
        
        # TODO: 설정 적용
        success = await agent_orchestrator.update_agent_config(
            config.agent_type, 
            config.enabled, 
            config.config or {}
        )
        
        if success:
            return {"message": f"{config.agent_type} 설정이 업데이트되었습니다."}
        else:
            raise HTTPException(status_code=400, detail="설정 업데이트 실패")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === 통합 회의 분석 파이프라인 ===

@app.post("/api/pipeline/analyze")
async def start_meeting_analysis_pipeline(request: PipelineRequest):
    """통합 회의 분석 파이프라인 시작"""
    try:
        if not meeting_pipeline:
            raise HTTPException(status_code=503, detail="회의 분석 파이프라인이 초기화되지 않았습니다.")
        
        # 파일 경로 검증
        if not os.path.exists(request.audio_file_path):
            raise HTTPException(status_code=404, detail="오디오 파일을 찾을 수 없습니다.")
        
        # 파이프라인 시작
        job_id = await meeting_pipeline.start_analysis(
            request.audio_file_path,
            request.analysis_options
        )
        
        return {
            "status": "started",
            "job_id": job_id,
            "audio_file": request.audio_file_path,
            "message": "통합 회의 분석 파이프라인을 시작했습니다."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pipeline/status/{job_id}")
async def get_pipeline_status(job_id: str):
    """파이프라인 작업 상태 조회"""
    if not meeting_pipeline:
        raise HTTPException(status_code=503, detail="회의 분석 파이프라인이 초기화되지 않았습니다.")
    
    job_status = meeting_pipeline.get_job_status(job_id)
    
    if not job_status:
        raise HTTPException(status_code=404, detail="파이프라인 작업을 찾을 수 없습니다.")
    
    return {
        "job_id": job_id,
        "status": job_status["status"],
        "current_stage": job_status.get("current_stage"),
        "progress": job_status["progress"],
        "started_at": job_status["started_at"],
        "completed_at": job_status.get("completed_at"),
        "error": job_status.get("error")
    }


@app.get("/api/pipeline/results/{job_id}")
async def get_pipeline_results(job_id: str):
    """파이프라인 분석 결과 조회"""
    if not meeting_pipeline:
        raise HTTPException(status_code=503, detail="회의 분석 파이프라인이 초기화되지 않았습니다.")
    
    job_status = meeting_pipeline.get_job_status(job_id)
    
    if not job_status:
        raise HTTPException(status_code=404, detail="파이프라인 작업을 찾을 수 없습니다.")
    
    if job_status["status"] == "failed":
        raise HTTPException(status_code=500, detail=f"파이프라인 실행 실패: {job_status['error']}")
    
    if job_status["status"] != "completed":
        raise HTTPException(status_code=202, detail="파이프라인이 아직 완료되지 않았습니다.")
    
    results = meeting_pipeline.get_job_results(job_id)
    
    return {
        "job_id": job_id,
        "status": job_status["status"],
        "completed_at": job_status["completed_at"],
        "results": results
    }


@app.delete("/api/pipeline/jobs/{job_id}")
async def cancel_pipeline_job(job_id: str):
    """파이프라인 작업 취소"""
    if not meeting_pipeline:
        raise HTTPException(status_code=503, detail="회의 분석 파이프라인이 초기화되지 않았습니다.")
    
    success = meeting_pipeline.cancel_job(job_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="작업을 취소할 수 없습니다. (이미 완료되었거나 존재하지 않는 작업)")
    
    return {"message": f"파이프라인 작업 {job_id}가 취소되었습니다."}


@app.get("/api/pipeline/jobs")
async def list_pipeline_jobs():
    """모든 파이프라인 작업 목록"""
    if not meeting_pipeline:
        raise HTTPException(status_code=503, detail="회의 분석 파이프라인이 초기화되지 않았습니다.")
    
    jobs = []
    for job_id, job_data in meeting_pipeline.pipeline_jobs.items():
        jobs.append({
            "job_id": job_id,
            "status": job_data["status"],
            "current_stage": job_data.get("current_stage"),
            "progress": job_data["progress"],
            "audio_file": job_data["audio_file"],
            "started_at": job_data["started_at"],
            "completed_at": job_data.get("completed_at")
        })
    
    return {"jobs": jobs}


@app.post("/api/pipeline/cleanup")
async def cleanup_pipeline_jobs(max_age_hours: int = 24):
    """완료된 파이프라인 작업 정리"""
    if not meeting_pipeline:
        raise HTTPException(status_code=503, detail="회의 분석 파이프라인이 초기화되지 않았습니다.")
    
    cleaned_count = meeting_pipeline.cleanup_completed_jobs(max_age_hours)
    
    return {
        "message": f"{cleaned_count}개의 완료된 작업을 정리했습니다.",
        "cleaned_jobs": cleaned_count
    }


# === 원클릭 회의 분석 (파일 업로드 → 전체 파이프라인) ===

# 지원하는 오디오/비디오 포맷
SUPPORTED_AUDIO_FORMATS = {
    '.mp3', '.wav', '.m4a', '.flac', '.ogg', '.opus', '.webm',
    '.aac', '.wma', '.amr', '.ac3', '.aiff', '.au', '.oga',
    '.mp2', '.weba', '.3gp', '.spx', '.ape', '.mka'
}

SUPPORTED_VIDEO_FORMATS = {
    '.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv',
    '.mpg', '.mpeg', '.m4v', '.ogv', '.mts', '.ts', '.vob',
    '.3gp', '.3g2', '.divx', '.xvid', '.asf', '.rm', '.rmvb'
}

SUPPORTED_FORMATS = SUPPORTED_AUDIO_FORMATS | SUPPORTED_VIDEO_FORMATS


@app.post("/api/meetings/analyze-upload")
async def analyze_uploaded_meeting(file: UploadFile = File(...)):
    """파일 업로드 + 즉시 전체 분석 파이프라인 실행"""
    print(f"\n🚀 === 파일 업로드 요청 수신 === {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        if not meeting_pipeline:
            raise HTTPException(status_code=503, detail="회의 분석 파이프라인이 초기화되지 않았습니다.")
        
        # 파일 확장자 검증
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        # 디버깅 정보 로깅
        print(f"📁 업로드 파일: {file.filename}")
        print(f"📋 MIME 타입: {file.content_type}")
        print(f"🔤 확장자: {file_ext}")
        print(f"📊 파일 크기: {file.size if hasattr(file, 'size') else 'unknown'}")
        
        # 확장자 기반 검증 (MIME 타입 무시)
        if file_ext not in SUPPORTED_FORMATS:
            supported_list = sorted(SUPPORTED_FORMATS)
            raise HTTPException(
                status_code=400, 
                detail=f"지원하지 않는 파일 형식: {file_ext}. 지원 형식: {', '.join(supported_list[:10])}..."
            )
        
        # 파일명 처리
        filename_without_ext = os.path.splitext(file.filename)[0]
        
        # 파일 저장 (안전한 파일명 생성)
        os.makedirs("data/meetings", exist_ok=True)
        safe_filename = f"{uuid.uuid4()}_{file.filename.replace(' ', '_')}"
        file_path = f"data/meetings/{safe_filename}"
        
        # 파일 크기 계산
        file_content = await file.read()
        file_size = len(file_content)
        
        # 파일을 다시 시작점으로 리셋
        await file.seek(0)
        
        # 청크 단위로 파일 저장 (대용량 파일 지원)
        chunk_size = 1024 * 1024  # 1MB
        with open(file_path, "wb") as f:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
        
        print(f"파일 저장 완료: {file_path}")
        
        # 즉시 파이프라인 시작
        print(f"회의 분석 파이프라인 시작 중...")
        start_time = datetime.now()
        
        # 파일 정보를 포함한 옵션 전달
        analysis_options = {
            "title": filename_without_ext,
            "original_filename": file.filename,
            "file_size": file_size
        }
        
        job_id = await meeting_pipeline.start_analysis(file_path, analysis_options)
        pipeline_start_time = (datetime.now() - start_time).total_seconds()
        print(f"파이프라인 시작 완료: job_id={job_id}, 소요시간={pipeline_start_time:.2f}초")
        
        response = {
            "status": "started",
            "job_id": job_id,
            "filename": file.filename,
            "file_path": file_path,
            "format": file_ext,
            "message": "파일 업로드 후 회의 분석을 시작했습니다."
        }
        
        print(f"📤 응답 반환: {response}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 업로드 처리 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/meetings/{job_id}/status")
async def get_pipeline_status(job_id: str):
    """파이프라인 작업 상태 조회"""
    if not meeting_pipeline:
        raise HTTPException(status_code=503, detail="회의 분석 파이프라인이 초기화되지 않았습니다.")
    
    status = meeting_pipeline.get_job_status(job_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    
    return {
        "job_id": job_id,
        "status": status["status"],
        "progress": status.get("progress", 0),
        "current_stage": status.get("current_stage"),
        "started_at": status.get("started_at"),
        "completed_at": status.get("completed_at"),
        "error": status.get("error"),
        "estimated_remaining": meeting_pipeline.get_estimated_remaining_time(job_id)
    }


@app.get("/api/meetings/{job_id}/report")
async def get_meeting_report(job_id: str, format: str = "json"):
    """회의 분석 최종 보고서 조회"""
    if not meeting_pipeline:
        raise HTTPException(status_code=503, detail="회의 분석 파이프라인이 초기화되지 않았습니다.")
    
    results = meeting_pipeline.get_job_results(job_id)
    
    if not results:
        raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")
    
    if "final_report" not in results:
        raise HTTPException(status_code=202, detail="보고서가 아직 생성되지 않았습니다.")
    
    report = results["final_report"]
    
    if format.lower() == "summary":
        # 요약된 보고서만 반환
        return {
            "job_id": job_id,
            "summary": report.get("executive_summary", {}),
            "generated_at": report.get("generated_at")
        }
    
    # 전체 보고서 반환
    return {
        "job_id": job_id,
        "report": report
    }


# === 보고서 저장/조회 ===

@app.post("/api/reports/save")
async def save_meeting_report(request: dict):
    """회의 분석 보고서 저장"""
    session = get_session(db_engine)
    try:
        job_id = request.get("job_id")
        if not job_id:
            raise HTTPException(status_code=400, detail="job_id가 필요합니다.")
        
        # 기존 보고서가 있는지 확인
        existing_report = session.query(MeetingReport).filter_by(job_id=job_id).first()
        
        if existing_report:
            # 기존 보고서 업데이트
            meeting_report = existing_report
        else:
            # 새 보고서 생성
            meeting_report = MeetingReport(job_id=job_id)
            session.add(meeting_report)
        
        # 필드 업데이트
        meeting_report.title = request.get("title", meeting_report.title)
        meeting_report.original_filename = request.get("original_filename", meeting_report.original_filename)
        meeting_report.file_size = request.get("file_size", meeting_report.file_size)
        meeting_report.duration_seconds = request.get("duration_seconds", meeting_report.duration_seconds)
        meeting_report.num_speakers = request.get("num_speakers", meeting_report.num_speakers)
        meeting_report.raw_results = request.get("raw_results", meeting_report.raw_results)
        meeting_report.executive_summary = request.get("executive_summary", meeting_report.executive_summary)
        meeting_report.agendas = request.get("agendas", meeting_report.agendas)
        meeting_report.claims = request.get("claims", meeting_report.claims)
        meeting_report.counter_arguments = request.get("counter_arguments", meeting_report.counter_arguments)
        meeting_report.evidence = request.get("evidence", meeting_report.evidence)
        meeting_report.final_report = request.get("final_report", meeting_report.final_report)
        meeting_report.status = request.get("status", meeting_report.status)
        meeting_report.progress = request.get("progress", meeting_report.progress)
        meeting_report.current_stage = request.get("current_stage", meeting_report.current_stage)
        meeting_report.error_message = request.get("error_message", meeting_report.error_message)
        
        if request.get("status") == "completed" and not meeting_report.completed_at:
            meeting_report.completed_at = datetime.now()
        
        meeting_report.updated_at = datetime.now()
        
        session.commit()
        
        return {
            "status": "success",
            "message": "보고서가 저장되었습니다.",
            "report_id": meeting_report.id
        }
        
    except Exception as e:
        session.rollback()
        print(f"❌ 보고서 저장 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@app.get("/api/reports")
async def get_all_reports(limit: int = 50, offset: int = 0, status: str = None):
    """저장된 모든 보고서 목록 조회"""
    session = get_session(db_engine)
    try:
        query = session.query(MeetingReport)
        
        if status:
            query = query.filter(MeetingReport.status == status)
        
        reports = query.order_by(MeetingReport.created_at.desc()).offset(offset).limit(limit).all()
        
        report_list = []
        for report in reports:
            report_list.append({
                "id": report.id,
                "job_id": report.job_id,
                "title": report.title,
                "original_filename": report.original_filename,
                "file_size": report.file_size,
                "duration_seconds": report.duration_seconds,
                "num_speakers": report.num_speakers,
                "status": report.status,
                "progress": report.progress,
                "current_stage": report.current_stage,
                "error_message": report.error_message,
                "created_at": report.created_at.isoformat() if report.created_at else None,
                "completed_at": report.completed_at.isoformat() if report.completed_at else None,
                "updated_at": report.updated_at.isoformat() if report.updated_at else None
            })
        
        return {
            "reports": report_list,
            "total": len(report_list),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        print(f"❌ 보고서 목록 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@app.get("/api/reports/{job_id}")
async def get_report_by_job_id(job_id: str):
    """특정 job_id로 보고서 조회"""
    session = get_session(db_engine)
    try:
        report = session.query(MeetingReport).filter_by(job_id=job_id).first()
        
        if not report:
            raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다.")
        
        return {
            "id": report.id,
            "job_id": report.job_id,
            "title": report.title,
            "original_filename": report.original_filename,
            "file_size": report.file_size,
            "duration_seconds": report.duration_seconds,
            "num_speakers": report.num_speakers,
            "raw_results": report.raw_results,
            "executive_summary": report.executive_summary,
            "agendas": report.agendas,
            "claims": report.claims,
            "counter_arguments": report.counter_arguments,
            "evidence": report.evidence,
            "final_report": report.final_report,
            "status": report.status,
            "progress": report.progress,
            "current_stage": report.current_stage,
            "error_message": report.error_message,
            "created_at": report.created_at.isoformat() if report.created_at else None,
            "completed_at": report.completed_at.isoformat() if report.completed_at else None,
            "updated_at": report.updated_at.isoformat() if report.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 보고서 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@app.delete("/api/reports/{job_id}")
async def delete_report(job_id: str):
    """보고서 삭제"""
    session = get_session(db_engine)
    try:
        report = session.query(MeetingReport).filter_by(job_id=job_id).first()
        
        if not report:
            raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다.")
        
        session.delete(report)
        session.commit()
        
        return {
            "status": "success",
            "message": "보고서가 삭제되었습니다."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        print(f"❌ 보고서 삭제 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@app.get("/api/health")
async def health_check():
    """시스템 상태 확인"""
    status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "database": "ok" if db_engine else "error",
            "embeddings": "ok" if embeddings else "error", 
            "hybrid_chroma_db": "ok" if chroma_manager and chroma_manager.available else "error",
            "unified_chroma_db": "ok" if chroma_manager and hasattr(chroma_manager, 'unified_adapter') and chroma_manager.unified_adapter.available else "degraded",
            "incremental_chroma_db": "ok" if chroma_manager and hasattr(chroma_manager, 'incremental_manager') and chroma_manager.incremental_manager.available else "degraded",
            "meeting_pipeline": "ok" if meeting_pipeline else "error",
            "update_scheduler": "ok" if update_scheduler else "error"
        }
    }
    
    # 컴포넌트 중 하나라도 오류가 있으면 degraded 상태
    if "error" in status["components"].values():
        status["status"] = "degraded"
    
    # 활성 작업 수 추가
    if meeting_pipeline:
        active_jobs = len([job for job in meeting_pipeline.pipeline_jobs.values() 
                          if job.get("status") in ["running", "initializing"]])
        status["active_jobs"] = active_jobs
    
    return status


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)