"""
회의 분석 파이프라인 (MeetingAnalysisPipeline)

오디오 → STT → 화자분리 → 멀티에이전트 분석 → 보고서 생성의 
전체 워크플로우를 관리합니다.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)

# 지연 import를 위한 전역 변수
SpeakerAnalyzer = None



class MeetingAnalysisPipeline:
    """회의 분석 전체 파이프라인"""
    
    def __init__(self, 
                 stt_manager=None,
                 speaker_diarizer=None, 
                 llm_client=None,
                 chroma_manager=None,
                 embedding_client=None,
                 db_engine=None):
        self.stt_manager = stt_manager
        self.speaker_diarizer = speaker_diarizer
        self.llm_client = llm_client  # agent_orchestrator 대신 llm_client 직접 사용
        self.chroma_manager = chroma_manager  # ChromaDB 매니저 직접 전달
        self.embedding_client = embedding_client
        self.db_engine = db_engine
        
        # 파이프라인 상태 관리
        self.pipeline_jobs = {}
        
        # 파이프라인 단계 정의
        self.pipeline_stages = [
            "file_validation",
            "stt_processing", 
            "speaker_diarization",
            "transcript_processing",
            "speaker_analysis",  # 새로운 화자 중심 분석 단계
            "simple_analysis",  # 단순 2단계 분석
            "report_generation",
            "result_storage"
        ]
        
        # 각 단계별 가중치 (진행률 계산용)
        self.stage_weights = {
            "file_validation": 5,
            "stt_processing": 20,
            "speaker_diarization": 10,
            "transcript_processing": 8,
            "speaker_analysis": 12,  # 새로운 단계
            "simple_analysis": 30,  # 단순 2단계 분석
            "report_generation": 12,
            "result_storage": 3
        }
        
        # 화자 분석기 초기화 (지연 로딩)
        self.speaker_analyzer = None
    
    async def start_analysis(self, 
                           audio_file_path: str,
                           options: Optional[Dict[str, Any]] = None,
                           progress_callback: Optional[Callable] = None) -> str:
        """회의 분석 파이프라인 시작"""
        
        # 작업 ID 생성
        job_id = f"pipeline_{uuid.uuid4().hex[:8]}"
        
        # 기본 옵션 설정
        default_options = {
            "stt_engine": "returnzero",
            "language": "ko", 
            "enable_diarization": True,
            "enable_agents": True,
            "agent_config": {
                "agenda_miner": True,
                "claim_checker": True,
                "counter_arguer": True,
                "evidence_hunter": True,
                "summarizer": True
            }
        }
        pipeline_options = {**default_options, **(options or {})}
        
        # 작업 상태 초기화
        self.pipeline_jobs[job_id] = {
            "status": "initializing",
            "audio_file": audio_file_path,
            "options": pipeline_options,
            "progress": 0,
            "current_stage": None,
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "error": None,
            "results": {},
            "progress_callback": progress_callback,
            # 파일 메타데이터 추가
            "title": pipeline_options.get("title", f"Meeting_{job_id[:8]}"),
            "original_filename": pipeline_options.get("original_filename", "unknown.wav"),
            "file_size": pipeline_options.get("file_size", 0)
        }
        
        # 백그라운드에서 파이프라인 실행 (오류 처리 강화)
        logger.info(f"=== 파이프라인 시작: {job_id} ===")
        logger.info(f"오디오 파일: {audio_file_path}")
        logger.info(f"옵션: {pipeline_options}")
        
        task = asyncio.create_task(self._execute_pipeline(job_id))
        
        # 태스크 오류 처리를 위한 콜백 추가
        def task_done_callback(task):
            if task.exception():
                logger.error(f"파이프라인 태스크 오류 ({job_id}): {task.exception()}")
                import traceback
                logger.error(f"스택 트레이스:\n{traceback.format_exception(type(task.exception()), task.exception(), task.exception().__traceback__)}")
                
                # 작업 상태를 실패로 업데이트
                if job_id in self.pipeline_jobs:
                    self.pipeline_jobs[job_id]["status"] = "failed"
                    self.pipeline_jobs[job_id]["error"] = str(task.exception())
                    self.pipeline_jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()
            else:
                logger.info(f"파이프라인 태스크 완료 ({job_id})")
        
        task.add_done_callback(task_done_callback)
        
        logger.info(f"회의 분석 파이프라인 시작: {job_id}")
        return job_id
    
    async def _execute_pipeline(self, job_id: str):
        """단순화된 파이프라인 실행"""
        logger.info(f"파이프라인 시작: {job_id}")
        
        job = self.pipeline_jobs[job_id]
        
        try:
            job["status"] = "running"
            
            # 1. 파일 검증 (5%)
            await self._update_progress(job_id, "file_validation", 5)
            validation_result = await self._validate_audio_file(job["audio_file"])
            if not validation_result["valid"]:
                raise Exception(f"파일 검증 실패: {validation_result['error']}")
            
            # 2. STT 처리 (50%)
            await self._update_progress(job_id, "stt_processing", 20)
            stt_result = await self._process_stt(job["audio_file"], job["options"])
            await self._update_progress(job_id, "stt_processing", 50)
            
            # 3. 간단한 전사본 구성 (60%)
            await self._update_progress(job_id, "transcript_processing", 60)
            transcript = {
                "full_text": stt_result.get("full_text", ""),  # STT 결과 직접 사용
                "segments": stt_result.get("segments", []),
                "metadata": {
                    "total_duration": stt_result.get("duration", 0.0),
                    "total_segments": len(stt_result.get("segments", [])),
                    "language": stt_result.get("language", "ko"),
                    "confidence": stt_result.get("confidence", 0.0)
                }
            }
            
            logger.info(f"전사 완료: {len(transcript['full_text'])}자, {len(transcript['segments'])}개 세그먼트")
            
            # 4. 통합 분석 (85%) - 간소화된 2단계 분석
            agent_results = {"skipped": True}
            if job["options"]["enable_agents"]:
                await self._update_progress(job_id, "simple_analysis", 65)
                logger.info("🔍 단순 회의 분석 시작 (2단계 프로세스: 요약 + RAG 분석)")
                
                try:
                    # 단순 분석기 초기화
                    simple_analyzer = self._get_simple_analyzer()
                    
                    if simple_analyzer:
                        await self._update_progress(job_id, "simple_analysis", 70)
                        logger.info(f"분석 입력: 텍스트 {len(transcript['full_text'])}자, 세그먼트 {len(transcript['segments'])}개")
                        
                        # 단순 분석 실행
                        agent_results = await simple_analyzer.analyze_meeting(
                            transcript_text=transcript["full_text"],
                            segments=transcript["segments"]
                        )
                        await self._update_progress(job_id, "simple_analysis", 85)
                        
                        # 분석 결과 로깅
                        if agent_results:
                            logger.info(f"✅ 통합 분석 완료: 신뢰도 {agent_results.get('confidence', 0):.2f}")
                            
                            # 주요 결과 요약 로깅
                            exec_summary = agent_results.get("executive_summary", {})
                            agenda_count = len(exec_summary.get("agenda_items", []))
                            action_count = len(exec_summary.get("action_items", []))
                            insights_count = len(exec_summary.get("insights", []))
                            
                            logger.info(f"📋 식별된 아젠다: {agenda_count}개")
                            logger.info(f"📝 액션 아이템: {action_count}개")
                            logger.info(f"💡 인사이트: {insights_count}개")
                            
                            if agent_results.get("related_context"):
                                context_count = len(agent_results["related_context"])
                                logger.info(f"🔗 관련 문서: {context_count}개")
                        else:
                            logger.warning("⚠️ 통합 분석 결과가 None임")
                    else:
                        logger.warning("⚠️ 통합 분석기를 초기화할 수 없음")
                        agent_results = self._create_simple_fallback_results(transcript)
                        
                except Exception as e:
                    logger.error(f"❌ 통합 분석 실패: {str(e)}")
                    logger.error(f"에러 타입: {type(e)}")
                    import traceback
                    logger.error(f"스택 트레이스: {traceback.format_exc()}")
                    agent_results = self._create_simple_fallback_results(transcript)
                    await self._update_progress(job_id, "simple_analysis", 80)
                    logger.info("🔄 Fallback 결과로 대체됨")
            else:
                logger.info("⏩ 분석 비활성화됨 - 기본 결과 생성")
                agent_results = self._create_simple_fallback_results(transcript)
            
            # 5. 보고서 생성 (95%)
            await self._update_progress(job_id, "report_generation", 90)
            logger.info("📊 최종 보고서 생성 시작")
            report = await self._generate_simple_report(transcript, agent_results)
            
            if report:
                logger.info(f"✅ 보고서 생성 완료: {type(report)} 타입")
                if isinstance(report, dict):
                    logger.info(f"보고서 키: {list(report.keys())}")
            else:
                logger.warning("⚠️ 보고서 생성 결과가 None임")
            
            # 6. 결과 저장 (100%)
            await self._update_progress(job_id, "result_storage", 95)
            job["results"] = {
                "stt": stt_result,
                "transcript": transcript,
                "agent_analysis": agent_results,
                "final_report": report
            }
            
            logger.info("💾 최종 결과를 데이터베이스에 저장 중")
            storage_result = await self._store_results(job_id, job["results"])
            
            if storage_result.get("saved"):
                logger.info(f"✅ DB 저장 성공: report_id={storage_result.get('report_id')}")
            else:
                logger.error(f"❌ DB 저장 실패: {storage_result.get('error')}")
            
            # 완료
            job["status"] = "completed"
            job["completed_at"] = datetime.utcnow().isoformat()
            await self._update_progress(job_id, "completed", 100)
            
            logger.info(f"파이프라인 완료: {job_id}")
            
        except Exception as e:
            job["status"] = "failed"
            job["error"] = str(e)
            job["completed_at"] = datetime.utcnow().isoformat()
            logger.error(f"파이프라인 실패: {job_id} - {e}")
            
            if job.get("progress_callback"):
                await job["progress_callback"](job_id, "failed", 0, str(e))
    
    async def _validate_audio_file(self, file_path: str) -> Dict[str, Any]:
        """오디오 파일 검증"""
        try:
            path = Path(file_path)
            
            if not path.exists():
                return {"valid": False, "error": "파일이 존재하지 않습니다."}
            
            if path.stat().st_size == 0:
                return {"valid": False, "error": "파일이 비어있습니다."}
            
            # 파일 확장자 확인
            valid_extensions = ['.wav', '.mp3', '.mp4', '.m4a', '.flac', '.ogg']
            if path.suffix.lower() not in valid_extensions:
                return {"valid": False, "error": f"지원되지 않는 파일 형식: {path.suffix}"}
            
            return {
                "valid": True,
                "file_size": path.stat().st_size,
                "file_format": path.suffix,
                "file_name": path.name
            }
            
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    async def _process_stt(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """STT 처리"""
        if not self.stt_manager:
            raise Exception("STT 매니저가 설정되지 않았습니다.")
        
        try:
            result = self.stt_manager.transcribe(
                file_path, 
                options.get("stt_engine", "returnzero"),
                options.get("language", "ko")
            )
            
            return {
                "engine_used": options.get("stt_engine", "returnzero"),
                "language": options.get("language", "ko"),
                "segments": result.get("segments", []),
                "full_text": result.get("text", ""),
                "confidence": result.get("confidence", 0.0),
                "duration": result.get("duration", 0.0)
            }
            
        except Exception as e:
            raise Exception(f"STT 처리 실패: {str(e)}")
    
    async def _process_diarization(self, file_path: str, stt_segments: List[Dict]) -> Dict[str, Any]:
        """화자 분리 처리"""
        if not self.speaker_diarizer:
            raise Exception("화자 분리 시스템이 설정되지 않았습니다.")
        
        try:
            segments_with_speakers = await self.speaker_diarizer.diarize_audio(
                file_path, stt_segments
            )
            
            speaker_stats = self.speaker_diarizer.analyze_speaker_distribution(
                segments_with_speakers
            )
            
            return {
                "segments": segments_with_speakers,
                "speaker_statistics": speaker_stats,
                "total_speakers": speaker_stats.get("total_speakers", 0),
                "diarization_stats": self.speaker_diarizer.get_stats()
            }
            
        except Exception as e:
            raise Exception(f"화자 분리 실패: {str(e)}")
    
    async def _generate_simple_report(self, transcript: Dict[str, Any], agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """단순화된 보고서 생성 - SimpleMeetingAnalyzer 출력과 기존 필드 매핑"""
        try:
            full_text = transcript.get("full_text", "")
            metadata = transcript.get("metadata", {})
            
            # 기본 통계
            duration = metadata.get("total_duration", 0)
            word_count = len(full_text.split()) if full_text else 0
            
            # SimpleMeetingAnalyzer 결과를 기존 필드 구조에 매핑
            executive_summary = {}
            agendas = []
            claims = []
            evidence = []
            final_report_text = ""
            
            if agent_results and not agent_results.get("skipped"):
                # SimpleMeetingAnalyzer 출력 구조 매핑
                executive_summary = {
                    "overview": agent_results.get("overview", "분석 요약이 없습니다."),
                    "key_points": agent_results.get("key_points", []),
                    "main_topics": agent_results.get("main_topics", []),
                    "decisions": agent_results.get("decisions", []),
                    "action_items": agent_results.get("action_items", []),
                    "insights": agent_results.get("insights", []),
                    "recommendations": agent_results.get("recommendations", []),
                    "processing_method": agent_results.get("processing_method", "simple_2step_analysis")
                }
                
                # 기존 필드와 매핑
                agendas = agent_results.get("main_topics", [])
                claims = agent_results.get("key_points", [])
                evidence = agent_results.get("insights", [])
                
                # 최종 보고서 텍스트 생성
                final_report_parts = []
                if agent_results.get("overview"):
                    final_report_parts.append(f"**개요**: {agent_results['overview']}")
                if agent_results.get("key_points"):
                    final_report_parts.append(f"**핵심 포인트**: {', '.join(agent_results['key_points'][:3])}")
                if agent_results.get("recommendations"):
                    final_report_parts.append(f"**권장사항**: {', '.join(agent_results['recommendations'][:3])}")
                
                final_report_text = "\n\n".join(final_report_parts) if final_report_parts else "분석 내용이 없습니다."
            
            report = {
                "title": "회의 분석 보고서",
                "generated_at": datetime.utcnow().isoformat(),
                "summary": {
                    "duration_seconds": duration,
                    "word_count": word_count,
                    "character_count": len(full_text),
                    "language": metadata.get("language", "ko")
                },
                "transcript": full_text,
                "agent_analysis": agent_results,
                "executive_summary": executive_summary,
                "agendas": agendas,
                "claims": claims,
                "evidence": evidence,
                "final_report": final_report_text
            }
            
            return report
            
        except Exception as e:
            logger.error(f"보고서 생성 실패: {e}")
            return {
                "title": "회의 분석 보고서 (오류)",
                "generated_at": datetime.utcnow().isoformat(),
                "error": str(e),
                "transcript": transcript.get("full_text", ""),
                "executive_summary": {},
                "agendas": [],
                "claims": [],
                "evidence": [],
                "final_report": f"보고서 생성 중 오류 발생: {str(e)}"
            }
    
    
    
    
    async def _store_results(self, job_id: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """결과 저장 - 단순화된 내용만 저장"""
        if not self.db_engine:
            return {"saved": False, "error": "DB 엔진 없음"}
            
        try:
            # Import database models inside function
            try:
                from db.models import get_session, MeetingReport
            except ImportError as e:
                logger.error(f"❌ 데이터베이스 모델을 import할 수 없습니다: {e}")
                return {"saved": False, "error": "데이터베이스 모델 import 실패"}
            
            job = self.pipeline_jobs.get(job_id, {})
            
            # 세션 생성
            session = get_session(self.db_engine)
            
            try:
                # 기존 보고서가 있는지 확인
                existing_report = session.query(MeetingReport).filter_by(job_id=job_id).first()
                
                if existing_report:
                    # 기존 보고서 업데이트
                    meeting_report = existing_report
                else:
                    # 새 보고서 생성
                    meeting_report = MeetingReport(job_id=job_id)
                    session.add(meeting_report)
                
                # 보고서 필드 업데이트
                meeting_report.title = job.get("title", f"Meeting_{job_id[:8]}")
                meeting_report.original_filename = job.get("original_filename", "unknown.wav")
                meeting_report.file_size = job.get("file_size", 0)
                meeting_report.duration_seconds = results.get("stt", {}).get("duration", 0)
                meeting_report.num_speakers = len(results.get("diarization", {}).get("speakers", []))
                meeting_report.raw_results = results
                # SimpleMeetingAnalyzer 결과를 기존 DB 스키마에 매핑
                final_report = results.get("final_report", {})
                agent_analysis = results.get("agent_analysis", {})
                
                meeting_report.executive_summary = final_report.get("executive_summary", {})
                meeting_report.agendas = final_report.get("agendas", [])  # main_topics 매핑됨
                meeting_report.claims = final_report.get("claims", [])    # key_points 매핑됨  
                meeting_report.counter_arguments = []  # SimpleMeetingAnalyzer에서는 사용하지 않음
                meeting_report.evidence = final_report.get("evidence", [])  # insights 매핑됨
                meeting_report.final_report = results.get("final_report", {})
                meeting_report.status = "completed"
                meeting_report.progress = 100
                meeting_report.current_stage = "completed"
                meeting_report.completed_at = datetime.now()
                meeting_report.updated_at = datetime.now()
                
                session.commit()
                
                logger.info(f"✅ 보고서가 성공적으로 데이터베이스에 저장되었습니다: {job_id}")
                return {
                    "saved": True,
                    "report_id": meeting_report.id,
                    "job_id": job_id
                }
                
            finally:
                session.close()
            
        except Exception as e:
            logger.error(f"❌ 데이터베이스 저장 중 오류: {str(e)}")
            return {"saved": False, "error": str(e)}
    
    async def _update_progress_in_db(self, job_id: str, stage: str, progress: int):
        """DB에 진행률 업데이트"""
        if not self.db_engine:
            logger.warning("DB 엔진이 없어서 진행률을 저장할 수 없습니다")
            return
            
        try:
            # Import database models inside function
            from db.models import get_session, MeetingReport
            
            job = self.pipeline_jobs.get(job_id, {})
            
            # 세션 생성
            session = get_session(self.db_engine)
            
            try:
                # 기존 보고서가 있는지 확인
                existing_report = session.query(MeetingReport).filter_by(job_id=job_id).first()
                
                if existing_report:
                    # 기존 보고서 업데이트
                    meeting_report = existing_report
                else:
                    # 새 보고서 생성
                    meeting_report = MeetingReport(job_id=job_id)
                    session.add(meeting_report)
                    
                    # 초기 메타데이터 설정
                    meeting_report.title = job.get("title", f"Meeting_{job_id[:8]}")
                    meeting_report.original_filename = job.get("original_filename", "unknown.wav")
                    meeting_report.file_size = job.get("file_size", 0)
                
                # 진행률 정보 업데이트
                meeting_report.status = "processing"
                meeting_report.progress = progress
                meeting_report.current_stage = stage
                meeting_report.updated_at = datetime.now()
                
                session.commit()
                logger.debug(f"✅ DB 진행률 업데이트 완료: {job_id} - {stage} ({progress}%)")
                
            finally:
                session.close()
            
        except Exception as e:
            logger.error(f"❌ DB 진행률 업데이트 실패: {str(e)}")
            # DB 오류가 발생해도 파이프라인은 계속 진행
    
    
    
    
    
    
    
    
    async def _update_progress(self, job_id: str, stage: str, progress: int):
        """진행률 업데이트 - 메모리와 DB에 모두 저장"""
        job = self.pipeline_jobs[job_id]
        job["current_stage"] = stage
        job["progress"] = progress
        
        logger.info(f"📊 진행률 업데이트: {job_id} - {stage} ({progress}%)")
        
        # DB에도 진행률 업데이트 저장
        await self._update_progress_in_db(job_id, stage, progress)
        
        # 콜백 호출
        if job.get("progress_callback"):
            await job["progress_callback"](job_id, stage, progress, None)
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """작업 상태 조회"""
        return self.pipeline_jobs.get(job_id)
    
    def get_job_results(self, job_id: str) -> Optional[Dict[str, Any]]:
        """작업 결과 조회"""
        job = self.pipeline_jobs.get(job_id)
        return job.get("results") if job else None
    
    def get_estimated_remaining_time(self, job_id: str) -> Optional[int]:
        """예상 남은 시간 계산 (초 단위)"""
        job = self.pipeline_jobs.get(job_id)
        if not job:
            return None
        
        progress = job.get("progress", 0)
        if progress <= 0:
            return None
        
        # 시작 시간부터 현재까지 경과 시간 계산
        started_at = job.get("started_at")
        if not started_at:
            return None
        
        try:
            start_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            elapsed_seconds = (datetime.utcnow() - start_time.replace(tzinfo=None)).total_seconds()
            
            # 진행률 기반으로 예상 총 시간 계산
            if progress > 0:
                estimated_total_time = elapsed_seconds / (progress / 100)
                remaining_time = estimated_total_time - elapsed_seconds
                return max(0, int(remaining_time))
        except:
            pass
        
        return None
    
    def cancel_job(self, job_id: str) -> bool:
        """작업 취소"""
        if job_id in self.pipeline_jobs:
            job = self.pipeline_jobs[job_id]
            if job["status"] in ["running", "initializing"]:
                job["status"] = "cancelled"
                job["completed_at"] = datetime.utcnow().isoformat()
                return True
        return False
    
    def cleanup_completed_jobs(self, max_age_hours: int = 24):
        """완료된 작업 정리"""
        current_time = datetime.utcnow()
        jobs_to_remove = []
        
        for job_id, job in self.pipeline_jobs.items():
            if job["status"] in ["completed", "failed", "cancelled"]:
                completed_at = datetime.fromisoformat(job["completed_at"])
                age_hours = (current_time - completed_at).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.pipeline_jobs[job_id]
        
        return len(jobs_to_remove)
    
    def _get_simple_analyzer(self):
        """단순 분석기 인스턴스 생성"""
        try:
            from agents.simple_analyzer import SimpleMeetingAnalyzer
            
            # LLM 클라이언트 직접 사용
            llm_client = self.llm_client
            
            # ChromaDB 매니저 직접 사용
            chroma_manager = self.chroma_manager
            
            analyzer = SimpleMeetingAnalyzer(
                llm_client=llm_client,
                chroma_manager=chroma_manager,
                embedding_client=self.embedding_client
            )
            
            logger.info(f"✅ 단순 분석기 초기화 완료 (LLM: {'있음' if llm_client else '없음'}, ChromaDB: {'있음' if chroma_manager else '없음'})")
            return analyzer
            
        except Exception as e:
            logger.error(f"❌ 단순 분석기 초기화 실패: {str(e)}")
            return None
    
    def _create_simple_fallback_results(self, transcript: Dict[str, Any]) -> Dict[str, Any]:
        """간단한 기본 분석 결과 - 개선된 버전"""
        full_text = transcript.get("full_text", "")
        segments = transcript.get("segments", [])
        
        # 기본 통계 분석
        word_count = len(full_text.split()) if full_text else 0
        char_count = len(full_text)
        segment_count = len(segments)
        
        # 간단한 키워드 추출 (공백/특수문자로 분리된 단어 중 길이 3 이상)
        import re
        words = re.findall(r'\b\w{3,}\b', full_text) if full_text else []
        unique_words = list(set(words))[:10]  # 상위 10개 고유 단어
        
        return {
            "executive_summary": {
                "overview": f"총 {char_count}자, {word_count}단어로 구성된 회의 내용을 기본 분석했습니다.",
                "key_points": [
                    f"회의 길이: {char_count}자 ({word_count}단어)",
                    f"발화 세그먼트: {segment_count}개",
                    f"주요 키워드: {', '.join(unique_words[:5])}" if unique_words else "키워드 없음"
                ]
            },
            "detailed_analysis": {
                "findings": [
                    f"전체 텍스트 길이: {char_count}자",
                    f"단어 수: {word_count}개",
                    f"발화 세그먼트: {segment_count}개"
                ],
                "insights": [
                    "AI 에이전트 분석은 수행되지 않았으나 기본 통계 분석은 완료됨",
                    "추가 분석을 원할 경우 다시 시도하거나 더 상세한 회의록 제공 권장"
                ]
            },
            "detailed_results": {
                "agenda_analysis": {
                    "agendas": [],
                    "processing_note": "에이전트 분석 실패로 아젠다 추출되지 않음"
                },
                "claim_analysis": {
                    "claims": [],
                    "processing_note": "에이전트 분석 실패로 주장 분석되지 않음"
                }
            },
            "confidence": 0.4,
            "processing_method": "fallback_analysis",
            "processing_note": "에이전트 분석 실패로 기본 결과 생성"
        }