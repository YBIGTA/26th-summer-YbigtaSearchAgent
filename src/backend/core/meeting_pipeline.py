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



class MeetingAnalysisPipeline:
    """회의 분석 전체 파이프라인"""
    
    def __init__(self, 
                 stt_manager=None,
                 speaker_diarizer=None, 
                 agent_orchestrator=None,
                 db_engine=None):
        self.stt_manager = stt_manager
        self.speaker_diarizer = speaker_diarizer
        self.agent_orchestrator = agent_orchestrator
        self.db_engine = db_engine
        
        # 파이프라인 상태 관리
        self.pipeline_jobs = {}
        
        # 파이프라인 단계 정의
        self.pipeline_stages = [
            "file_validation",
            "stt_processing", 
            "speaker_diarization",
            "transcript_processing",
            "agent_analysis",
            "report_generation",
            "result_storage"
        ]
        
        # 각 단계별 가중치 (진행률 계산용)
        self.stage_weights = {
            "file_validation": 5,
            "stt_processing": 25,
            "speaker_diarization": 15,
            "transcript_processing": 10,
            "agent_analysis": 35,
            "report_generation": 8,
            "result_storage": 2
        }
    
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
        
        # 백그라운드에서 파이프라인 실행
        asyncio.create_task(self._execute_pipeline(job_id))
        
        logger.info(f"회의 분석 파이프라인 시작: {job_id}")
        return job_id
    
    async def _execute_pipeline(self, job_id: str):
        """파이프라인 실제 실행"""
        job = self.pipeline_jobs[job_id]
        
        try:
            job["status"] = "running"
            
            # 1. 파일 검증
            await self._update_progress(job_id, "file_validation", 0)
            validation_result = await self._validate_audio_file(job["audio_file"])
            job["results"]["validation"] = validation_result
            
            if not validation_result["valid"]:
                raise Exception(f"오디오 파일 검증 실패: {validation_result['error']}")
            
            # 2. STT 처리
            await self._update_progress(job_id, "stt_processing", 20)
            stt_result = await self._process_stt(job["audio_file"], job["options"])
            job["results"]["stt"] = stt_result
            
            # 3. 화자 분리
            if job["options"]["enable_diarization"]:
                await self._update_progress(job_id, "speaker_diarization", 40)
                diarization_result = await self._process_diarization(
                    job["audio_file"], 
                    stt_result.get("segments", [])
                )
                job["results"]["diarization"] = diarization_result
            else:
                job["results"]["diarization"] = {"skipped": True}
            
            # 4. 회의록 후처리
            await self._update_progress(job_id, "transcript_processing", 55)
            transcript = await self._process_transcript(job["results"])
            job["results"]["transcript"] = transcript
            
            # 5. 멀티에이전트 분석
            if job["options"]["enable_agents"]:
                await self._update_progress(job_id, "agent_analysis", 65)
                logger.info(f"멀티에이전트 분석 시작: {job_id}")
                logger.debug(f"전사 결과 요약: 텍스트 길이={len(transcript.get('full_text', ''))}, 세그먼트 수={len(transcript.get('segments', []))}")
                
                agent_results = await self._process_agents(transcript, job["options"]["agent_config"])
                job["results"]["agent_analysis"] = agent_results
                
                logger.info(f"멀티에이전트 분석 완료: {job_id}")
                logger.debug(f"에이전트 결과 키: {list(agent_results.keys()) if agent_results else 'None'}")
            else:
                job["results"]["agent_analysis"] = {"skipped": True}
                logger.info(f"에이전트 분석 스킵됨: {job_id}")
            
            # 6. 보고서 생성
            await self._update_progress(job_id, "report_generation", 92)
            logger.info(f"보고서 생성 시작: {job_id}")
            logger.debug(f"보고서 생성 입력 데이터: {list(job['results'].keys())}")
            
            report = await self._generate_report(job["results"])
            job["results"]["final_report"] = report
            
            logger.info(f"보고서 생성 완료: {job_id}")
            logger.debug(f"보고서 구조: {list(report.keys()) if report else 'None'}")
            
            # 7. 결과 저장
            await self._update_progress(job_id, "result_storage", 98)
            storage_result = await self._store_results(job_id, job["results"])
            job["results"]["storage"] = storage_result
            
            # 완료 처리
            job["status"] = "completed"
            job["completed_at"] = datetime.utcnow().isoformat()
            await self._update_progress(job_id, "completed", 100)
            
            logger.info(f"회의 분석 파이프라인 완료: {job_id}")
            
        except Exception as e:
            # 오류 처리
            job["status"] = "failed"
            job["error"] = str(e)
            job["completed_at"] = datetime.utcnow().isoformat()
            
            logger.error(f"파이프라인 실행 실패 (job_id: {job_id}): {str(e)}")
            
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
    
    async def _process_transcript(self, pipeline_results: Dict[str, Any]) -> Dict[str, Any]:
        """회의록 후처리"""
        try:
            stt_result = pipeline_results.get("stt", {})
            diarization_result = pipeline_results.get("diarization", {})
            
            # 화자 분리 결과가 있으면 사용, 없으면 STT 결과만 사용
            if not diarization_result.get("skipped", False):
                segments = diarization_result.get("segments", [])
            else:
                segments = stt_result.get("segments", [])
            
            # 회의록 메타데이터 생성
            transcript = {
                "segments": segments,
                "metadata": {
                    "total_duration": stt_result.get("duration", 0.0),
                    "total_segments": len(segments),
                    "speakers_detected": diarization_result.get("total_speakers", 1),
                    "average_confidence": stt_result.get("confidence", 0.0),
                    "language": stt_result.get("language", "ko"),
                    "processing_timestamp": datetime.utcnow().isoformat()
                },
                "full_text": self._generate_full_text(segments),
                "speaker_summary": self._generate_speaker_summary(segments)
            }
            
            return transcript
            
        except Exception as e:
            raise Exception(f"회의록 처리 실패: {str(e)}")
    
    async def _process_agents(self, transcript: Dict[str, Any], agent_config: Dict[str, bool]) -> Dict[str, Any]:
        """멀티에이전트 분석"""
        if not self.agent_orchestrator:
            logger.warning("에이전트 오케스트레이터가 설정되지 않았습니다. 기본 분석 결과를 반환합니다.")
            return self._create_fallback_agent_results(transcript)
        
        try:
            # 에이전트별 활성화 상태에 따라 분석 실행
            agent_results = {}
            
            meeting_data = {
                "transcript": transcript.get("full_text", ""),
                "speakers": transcript.get("speakers", []),
                "timeline": transcript.get("segments", []),
                "metadata": transcript.get("metadata", {}),
                "content": transcript.get("full_text", "")
            }
            
            logger.info(f"에이전트 분석 입력 데이터 준비 완료: 텍스트 {len(meeting_data['transcript'])}자, 세그먼트 {len(meeting_data['timeline'])}개")
            
            # 각 에이전트 순차 실행 (실제로는 병렬 실행 가능)
            if agent_config.get("agenda_miner", True):
                logger.info("AgendaMiner 실행 중...")
                try:
                    agent_results["agendas"] = await self.agent_orchestrator.agenda_miner.analyze(
                        meeting_data
                    )
                    logger.info("AgendaMiner 완료")
                except Exception as e:
                    logger.error(f"AgendaMiner 실패: {str(e)}")
                    agent_results["agendas"] = {"error": str(e), "agendas": []}
            
            if agent_config.get("claim_checker", True):
                logger.info("ClaimChecker 실행 중...")
                try:
                    agent_results["claims"] = await self.agent_orchestrator.claim_checker.analyze(
                        meeting_data
                    )
                    logger.info("ClaimChecker 완료")
                except Exception as e:
                    logger.error(f"ClaimChecker 실패: {str(e)}")
                    agent_results["claims"] = {"error": str(e), "claims": []}
            
            if agent_config.get("counter_arguer", True):
                logger.info("CounterArguer 실행 중...")
                try:
                    agent_results["counter_arguments"] = await self.agent_orchestrator.counter_arguer.analyze(
                        meeting_data
                    )
                    logger.info("CounterArguer 완료")
                except Exception as e:
                    logger.error(f"CounterArguer 실패: {str(e)}")
                    agent_results["counter_arguments"] = {"error": str(e), "counter_arguments": []}
            
            if agent_config.get("evidence_hunter", True):
                logger.info("EvidenceHunter 실행 중...")
                try:
                    agent_results["evidence"] = await self.agent_orchestrator.evidence_hunter.search_and_verify(
                        meeting_data["content"], meeting_data
                    )
                    logger.info("EvidenceHunter 완료")
                except Exception as e:
                    logger.error(f"EvidenceHunter 실패: {str(e)}")
                    agent_results["evidence"] = {"error": str(e), "evidence_found": []}
            
            if agent_config.get("summarizer", True):
                logger.info("Summarizer 실행 중...")
                try:
                    agent_results["summary"] = await self.agent_orchestrator.summarizer.generate_report(
                        agent_results
                    )
                    logger.info("Summarizer 완료")
                except Exception as e:
                    logger.error(f"Summarizer 실패: {str(e)}")
                    agent_results["summary"] = {"error": str(e), "action_items": [], "executive_summary": {}}
            
            logger.info(f"모든 에이전트 실행 완료. 결과 키: {list(agent_results.keys())}")
            return agent_results
            
        except Exception as e:
            logger.error(f"에이전트 분석 전체 실패: {str(e)}")
            raise Exception(f"에이전트 분석 실패: {str(e)}")
    
    async def _generate_report(self, pipeline_results: Dict[str, Any]) -> Dict[str, Any]:
        """최종 보고서 생성"""
        try:
            transcript = pipeline_results.get("transcript", {})
            agent_results = pipeline_results.get("agent_analysis", {})
            
            logger.info(f"보고서 생성 - 입력 체크:")
            logger.info(f"  - transcript 키: {list(transcript.keys()) if transcript else 'None'}")
            logger.info(f"  - agent_results 키: {list(agent_results.keys()) if agent_results else 'None'}")
            
            # 각 단계별 데이터 추출
            meeting_overview = self._generate_meeting_overview(transcript)
            logger.debug(f"meeting_overview: {meeting_overview}")
            
            key_findings = self._extract_key_findings(agent_results)
            logger.debug(f"key_findings: {len(key_findings)}개")
            
            action_items = self._extract_action_items(agent_results)
            logger.debug(f"action_items: {len(action_items)}개")
            
            recommendations = self._generate_recommendations(agent_results)
            logger.debug(f"recommendations: {len(recommendations)}개")
            
            report = {
                "executive_summary": {
                    "meeting_overview": meeting_overview,
                    "key_findings": key_findings,
                    "action_items": action_items,
                    "recommendations": recommendations
                },
                "detailed_analysis": {
                    "transcript_analysis": transcript.get("metadata", {}),
                    "speaker_analysis": transcript.get("speaker_summary", {}),
                    "content_analysis": agent_results
                },
                "technical_details": {
                    "processing_pipeline": {
                        "stt_engine": pipeline_results.get("stt", {}).get("engine_used"),
                        "diarization_enabled": not pipeline_results.get("diarization", {}).get("skipped", True),
                        "agents_used": list(agent_results.keys()) if agent_results else []
                    },
                    "quality_metrics": {
                        "stt_confidence": pipeline_results.get("stt", {}).get("confidence", 0.0),
                        "speakers_detected": transcript.get("metadata", {}).get("speakers_detected", 1),
                        "processing_time": None  # TODO: 실제 처리 시간 계산
                    }
                },
                "generated_at": datetime.utcnow().isoformat(),
                "format_version": "1.0"
            }
            
            logger.info("보고서 생성 완료")
            logger.debug(f"최종 보고서 키: {list(report.keys())}")
            return report
            
        except Exception as e:
            logger.error(f"보고서 생성 실패 상세: {str(e)}")
            logger.exception("보고서 생성 예외 상세:")
            raise Exception(f"보고서 생성 실패: {str(e)}")
    
    async def _store_results(self, job_id: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """결과 저장 - 직접 데이터베이스에 저장"""
        print(f"🔄 _store_results 호출됨: job_id={job_id}")
        logger.info(f"🔄 _store_results 호출됨: job_id={job_id}")
        
        if not self.db_engine:
            print("❌ 데이터베이스 엔진이 없습니다")
            logger.warning("데이터베이스 엔진이 설정되지 않아 저장을 건너뜁니다.")
            return {"saved": False, "error": "데이터베이스 엔진이 없음"}
            
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
                meeting_report.executive_summary = results.get("final_report", {}).get("executive_summary", {})
                meeting_report.agendas = results.get("agent_analysis", {}).get("agendas", {})
                meeting_report.claims = results.get("agent_analysis", {}).get("claims", {})
                meeting_report.counter_arguments = results.get("agent_analysis", {}).get("counter_arguments", {})
                meeting_report.evidence = results.get("agent_analysis", {}).get("evidence", {})
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
    
    def _generate_full_text(self, segments: List[Dict[str, Any]]) -> str:
        """세그먼트에서 전체 텍스트 생성"""
        return " ".join([
            seg.get("text", "") for seg in segments 
            if seg.get("text", "").strip()
        ])
    
    def _generate_speaker_summary(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """화자별 요약 생성"""
        speaker_data = {}
        
        for seg in segments:
            speaker = seg.get("speaker", "Unknown")
            if speaker not in speaker_data:
                speaker_data[speaker] = {
                    "utterance_count": 0,
                    "total_words": 0,
                    "total_duration": 0.0
                }
            
            speaker_data[speaker]["utterance_count"] += 1
            speaker_data[speaker]["total_words"] += len(seg.get("text", "").split())
            speaker_data[speaker]["total_duration"] += seg.get("duration", 0.0)
        
        return speaker_data
    
    def _generate_meeting_overview(self, transcript: Dict[str, Any]) -> str:
        """회의 개요 생성"""
        metadata = transcript.get("metadata", {})
        duration = metadata.get("total_duration", 0)
        speakers = metadata.get("speakers_detected", 1)
        
        return f"총 {duration:.1f}초 길이의 회의에서 {speakers}명의 화자가 참여했습니다."
    
    def _extract_key_findings(self, agent_results: Dict[str, Any]) -> List[str]:
        """주요 발견사항 추출"""
        findings = []
        
        if "agendas" in agent_results:
            agendas = agent_results["agendas"].get("agendas", [])
            findings.extend([f"주요 안건: {agenda}" for agenda in agendas[:3]])
        
        if "claims" in agent_results:
            claims = agent_results["claims"].get("verified_claims", [])
            findings.extend([f"검증된 주장: {claim}" for claim in claims[:2]])
        
        return findings or ["분석 결과가 없습니다."]
    
    def _extract_action_items(self, agent_results: Dict[str, Any]) -> List[str]:
        """액션 아이템 추출"""
        if "summary" in agent_results:
            return agent_results["summary"].get("action_items", [])
        return ["액션 아이템이 식별되지 않았습니다."]
    
    def _generate_recommendations(self, agent_results: Dict[str, Any]) -> List[str]:
        """권장사항 생성"""
        recommendations = []
        
        if "counter_arguments" in agent_results:
            counter_args = agent_results["counter_arguments"].get("counter_arguments", [])
            if counter_args:
                recommendations.append("제시된 반박 의견들을 검토해보시기 바랍니다.")
        
        if "evidence" in agent_results:
            evidence = agent_results["evidence"].get("evidence_found", [])
            if evidence:
                recommendations.append("추가 증거 자료를 참고하여 의사결정하시기 바랍니다.")
        
        return recommendations or ["특별한 권장사항이 없습니다."]
    
    async def _update_progress(self, job_id: str, stage: str, progress: int):
        """진행률 업데이트"""
        job = self.pipeline_jobs[job_id]
        job["current_stage"] = stage
        job["progress"] = progress
        
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
    
    def _create_fallback_agent_results(self, transcript: Dict[str, Any]) -> Dict[str, Any]:
        """LLM 없이 기본 분석 결과 생성"""
        logger.info("기본 분석 결과 생성 중...")
        
        full_text = transcript.get("full_text", "")
        segments = transcript.get("segments", [])
        speakers = transcript.get("speaker_summary", {})
        
        # 기본 아젠다
        basic_agenda = {
            "id": 1,
            "title": "회의 주요 내용",
            "description": f"총 {len(full_text)}자의 회의록이 분석되었습니다.",
            "category": "discussion",
            "priority": "medium",
            "related_topics": [],
            "outcomes": [],
            "action_items": [],
            "discussion_points": ["회의 내용 요약이 필요합니다."]
        }
        
        # 기본 주장 분석
        basic_claim = {
            "id": 1,
            "speaker": "알 수 없음",
            "claim": "주요 논의 사항이 있었습니다.",
            "type": "opinion",
            "confidence_level": "low",
            "evidence": [],
            "context": "전체 회의 맥락",
            "implications": [],
            "related_claims": [],
            "time_reference": "회의 전반"
        }
        
        return {
            "agendas": {
                "agendas": [basic_agenda],
                "confidence": 0.3,
                "processing_note": "LLM 분석 없이 기본 결과 생성됨"
            },
            "claims": {
                "claims": [basic_claim],
                "confidence": 0.3,
                "processing_note": "LLM 분석 없이 기본 결과 생성됨"
            },
            "counter_arguments": {
                "counter_arguments": [],
                "confidence": 0.0,
                "processing_note": "LLM 분석 없이 기본 결과 생성됨"
            },
            "evidence": {
                "evidence_found": [],
                "confidence": 0.0,
                "processing_note": "LLM 분석 없이 기본 결과 생성됨"
            },
            "summary": {
                "executive_summary": {
                    "overview": f"총 {len(segments)}개 발화가 포함된 회의가 분석되었습니다.",
                    "participants": len(speakers),
                    "duration": transcript.get("metadata", {}).get("total_duration", 0)
                },
                "action_items": [],
                "key_decisions": [],
                "next_steps": [],
                "confidence": 0.3,
                "processing_note": "LLM 분석 없이 기본 결과 생성됨"
            }
        }