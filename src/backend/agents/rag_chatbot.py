"""
RAG 챗봇 서비스
하이브리드 검색과 LLM을 결합하여 질문에 답변
"""

import os
import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from sqlalchemy.orm import Session

from nlp.hybrid_retriever import HybridRetriever
from llm.upstage_client import UpstageClient
from db.models import ChatSession, ChatMessage, ChatMessageSource, ChatbotSetting, get_session

logger = logging.getLogger(__name__)


class RAGChatbot:
    """RAG 기반 챗봇"""
    
    def __init__(self, hybrid_retriever: HybridRetriever, llm_client: UpstageClient, db_engine=None):
        self.hybrid_retriever = hybrid_retriever
        self.llm_client = llm_client
        self.db_engine = db_engine
        
        # 시스템 프롬프트
        self.system_prompt = """당신은 YBIGTA의 지식베이스를 기반으로 한 AI 어시스턴트입니다.

주어진 컨텍스트를 바탕으로 질문에 정확하고 도움이 되는 답변을 제공하세요.

답변 규칙:
1. 컨텍스트에 있는 정보만을 사용하여 답변하세요
2. 정보가 부족하면 솔직히 말하고, 추측하지 마세요
3. 답변은 한국어로 제공하세요
4. 구조적이고 읽기 쉽게 답변하세요
5. 필요시 관련 문서나 소스를 언급하세요

컨텍스트:
{context}

질문: {question}"""
    
    async def chat(self, 
                  question: str, 
                  session_id: str = None,
                  user_id: int = None,
                  chat_history: List[Dict[str, str]] = None,
                  top_k: int = 5,
                  search_type: str = "hybrid") -> Dict[str, Any]:
        """
        RAG 챗봇 대화
        
        Args:
            question: 사용자 질문
            session_id: 대화 세션 ID
            user_id: 사용자 ID
            chat_history: 이전 대화 기록
            top_k: 검색할 문서 수
            search_type: 검색 타입 (hybrid, semantic, keyword)
        
        Returns:
            답변과 메타데이터
        """
        try:
            start_time = datetime.now()
            
            # 1. 세션 생성 또는 가져오기
            if not session_id:
                session_id = str(uuid.uuid4())
            
            db_session = get_session(self.db_engine) if self.db_engine else None
            
            # 2. 관련 문서 검색
            logger.info(f"🔍 질문 검색 시작: {question}")
            search_results = await self.hybrid_retriever.search(
                query=question,
                top_k=top_k,
                search_type=search_type
            )
            
            # 3. 컨텍스트 구성
            context = self._build_context(search_results)
            
            # 4. 대화 기록 구성
            messages = self._build_messages(question, context, chat_history)
            
            # 5. LLM 호출
            logger.info("🤖 LLM 답변 생성 중...")
            response = await self.llm_client.invoke_async(messages)
            
            # 6. 응답 구성
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # 7. DB에 대화 기록 저장
            if db_session:
                await self._save_chat_to_db(
                    db_session, session_id, user_id, question, response, 
                    search_results, processing_time, search_type, top_k
                )
            
            result = {
                "answer": response,
                "question": question,
                "session_id": session_id,
                "context": context,
                "sources": self._extract_sources(search_results),
                "search_results": search_results,
                "processing_time": processing_time,
                "timestamp": end_time.isoformat()
            }
            
            logger.info(f"✅ 챗봇 응답 완료 ({processing_time:.2f}초)")
            return result
            
        except Exception as e:
            logger.error(f"❌ 챗봇 오류: {e}")
            return {
                "answer": f"죄송합니다. 오류가 발생했습니다: {str(e)}",
                "question": question,
                "session_id": session_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _save_chat_to_db(self, db_session: Session, session_id: str, user_id: int,
                              question: str, answer: str, search_results: Dict[str, Any],
                              processing_time: float, search_type: str, top_k: int):
        """대화를 DB에 저장"""
        try:
            # 1. 세션 생성 또는 가져오기
            chat_session = db_session.query(ChatSession).filter_by(session_id=session_id).first()
            if not chat_session:
                chat_session = ChatSession(
                    session_id=session_id,
                    user_id=user_id,
                    title=question[:50] + "..." if len(question) > 50 else question
                )
                db_session.add(chat_session)
                db_session.flush()  # ID 생성
            
            # 2. 사용자 메시지 저장
            user_message = ChatMessage(
                session_id=chat_session.id,
                role="user",
                content=question,
                created_at=datetime.now()
            )
            db_session.add(user_message)
            db_session.flush()
            
            # 3. 어시스턴트 메시지 저장
            assistant_message = ChatMessage(
                session_id=chat_session.id,
                role="assistant",
                content=answer,
                processing_time=processing_time,
                search_type=search_type,
                top_k=top_k,
                sources_count=len(self._extract_sources(search_results)),
                created_at=datetime.now()
            )
            db_session.add(assistant_message)
            db_session.flush()
            
            # 4. 소스 정보 저장
            sources = self._extract_sources(search_results)
            for source in sources:
                source_record = ChatMessageSource(
                    message_id=assistant_message.id,
                    source_type=source.get("source_type", "unknown"),
                    source_id=source.get("source_id", ""),
                    title=source.get("title", ""),
                    content_preview=source.get("content_preview", ""),
                    relevance_score=source.get("relevance_score", 0.0),
                    created_at=datetime.now()
                )
                db_session.add(source_record)
            
            # 5. 세션 업데이트
            chat_session.updated_at = datetime.now()
            
            db_session.commit()
            logger.info(f"💾 대화 기록 저장 완료 (session_id: {session_id})")
            
        except Exception as e:
            db_session.rollback()
            logger.error(f"❌ 대화 기록 저장 실패: {e}")
    
    def get_chat_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """대화 기록 조회"""
        if not self.db_engine:
            return []
        
        try:
            db_session = get_session(self.db_engine)
            messages = db_session.query(ChatMessage).join(ChatSession).filter(
                ChatSession.session_id == session_id
            ).order_by(ChatMessage.created_at.desc()).limit(limit).all()
            
            history = []
            for msg in reversed(messages):  # 시간순 정렬
                history.append({
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat(),
                    "processing_time": msg.processing_time
                })
            
            return history
            
        except Exception as e:
            logger.error(f"❌ 대화 기록 조회 실패: {e}")
            return []
    
    def get_user_sessions(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """사용자의 대화 세션 목록"""
        if not self.db_engine:
            return []
        
        try:
            db_session = get_session(self.db_engine)
            sessions = db_session.query(ChatSession).filter(
                ChatSession.user_id == user_id
            ).order_by(ChatSession.updated_at.desc()).limit(limit).all()
            
            return [{
                "session_id": session.session_id,
                "title": session.title,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "message_count": len(session.messages)
            } for session in sessions]
            
        except Exception as e:
            logger.error(f"❌ 세션 목록 조회 실패: {e}")
            return []
    
    def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """사용자 챗봇 설정 조회"""
        if not self.db_engine:
            return self._get_default_settings()
        
        try:
            db_session = get_session(self.db_engine)
            settings = db_session.query(ChatbotSetting).filter(
                ChatbotSetting.user_id == user_id
            ).first()
            
            if settings:
                return {
                    "default_search_type": settings.default_search_type,
                    "default_top_k": settings.default_top_k,
                    "enable_suggestions": settings.enable_suggestions,
                    "enable_source_citation": settings.enable_source_citation,
                    "language": settings.language
                }
            else:
                return self._get_default_settings()
                
        except Exception as e:
            logger.error(f"❌ 사용자 설정 조회 실패: {e}")
            return self._get_default_settings()
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """기본 설정"""
        return {
            "default_search_type": "hybrid",
            "default_top_k": 5,
            "enable_suggestions": True,
            "enable_source_citation": True,
            "language": "ko"
        }
    
    def _build_context(self, search_results: Dict[str, Any]) -> str:
        """검색 결과로부터 컨텍스트 구성"""
        context_parts = []
        
        # search_results가 문자열이거나 None인 경우 처리
        if not search_results or not isinstance(search_results, dict):
            logger.warning(f"검색 결과가 유효하지 않습니다: {type(search_results)}")
            return "관련 문서를 찾을 수 없습니다."
        
        # results 키가 있는지 확인
        if "results" not in search_results:
            logger.warning("검색 결과에 'results' 키가 없습니다.")
            return "관련 문서를 찾을 수 없습니다."
        
        results = search_results["results"]
        if not isinstance(results, dict):
            logger.warning(f"results가 딕셔너리가 아닙니다: {type(results)}")
            return "관련 문서를 찾을 수 없습니다."
        
        # documents 키가 있는지 확인
        if "documents" not in results:
            logger.warning("results에 'documents' 키가 없습니다.")
            return "관련 문서를 찾을 수 없습니다."
        
        documents = results["documents"]
        if not isinstance(documents, list):
            logger.warning(f"documents가 리스트가 아닙니다: {type(documents)}")
            return "관련 문서를 찾을 수 없습니다."
        
        # 문서 처리
        for i, doc in enumerate(documents[:5], 1):  # 상위 5개만 사용
            if isinstance(doc, dict):
                content = doc.get("content", "")
                metadata = doc.get("metadata", {})
            elif isinstance(doc, str):
                content = doc
                metadata = {}
            else:
                logger.warning(f"문서가 예상된 형식이 아닙니다: {type(doc)}")
                continue
            
            source = metadata.get("source", "Unknown") if isinstance(metadata, dict) else "Unknown"
            title = metadata.get("title", "Unknown") if isinstance(metadata, dict) else "Unknown"
            
            context_parts.append(f"[문서 {i}] {title} ({source})\n{content}\n")
        
        if not context_parts:
            return "관련 문서를 찾을 수 없습니다."
        
        return "\n".join(context_parts)
    
    def _build_messages(self, 
                       question: str, 
                       context: str, 
                       chat_history: List[Dict[str, str]] = None) -> List[Dict[str, str]]:
        """LLM 호출용 메시지 구성"""
        messages = []
        
        # 시스템 메시지
        system_content = self.system_prompt.format(
            context=context,
            question=question
        )
        messages.append({
            "role": "system",
            "content": system_content
        })
        
        # 대화 기록 추가
        if chat_history:
            for msg in chat_history[-6:]:  # 최근 6개 메시지만 사용
                if msg.get("role") in ["user", "assistant"]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
        
        # 현재 질문 추가
        messages.append({
            "role": "user",
            "content": question
        })
        
        return messages
    
    def _extract_sources(self, search_results: Dict[str, Any]) -> List[Dict[str, str]]:
        """검색 결과에서 소스 정보 추출"""
        sources = []
        
        # search_results가 문자열이거나 None인 경우 처리
        if not search_results or not isinstance(search_results, dict):
            logger.warning(f"검색 결과가 유효하지 않습니다: {type(search_results)}")
            return []
        
        # results 키가 있는지 확인
        if "results" not in search_results:
            logger.warning("검색 결과에 'results' 키가 없습니다.")
            return []
        
        results = search_results["results"]
        if not isinstance(results, dict):
            logger.warning(f"results가 딕셔너리가 아닙니다: {type(results)}")
            return []
        
        # documents 키가 있는지 확인
        if "documents" not in results:
            logger.warning("results에 'documents' 키가 없습니다.")
            return []
        
        documents = results["documents"]
        if not isinstance(documents, list):
            logger.warning(f"documents가 리스트가 아닙니다: {type(documents)}")
            return []
        
        # 문서 처리
        for doc in documents[:3]:  # 상위 3개 소스만
            if isinstance(doc, dict):
                metadata = doc.get("metadata", {})
                content = doc.get("content", "")
                score = doc.get("score", 0.0)
            elif isinstance(doc, str):
                metadata = {}
                content = doc
                score = 0.0
            else:
                logger.warning(f"문서가 예상된 형식이 아닙니다: {type(doc)}")
                continue
            
            if isinstance(metadata, dict):
                sources.append({
                    "title": metadata.get("title", "Unknown"),
                    "source": metadata.get("source", "Unknown"),
                    "source_type": metadata.get("source_type", "unknown"),
                    "source_id": metadata.get("source_id", ""),
                    "content_preview": content[:200] + "..." if len(content) > 200 else content,
                    "relevance_score": score
                })
            else:
                sources.append({
                    "title": "Unknown",
                    "source": "Unknown",
                    "source_type": "unknown",
                    "source_id": "",
                    "content_preview": content[:200] + "..." if len(content) > 200 else content,
                    "relevance_score": score
                })
        
        return sources
    
    async def get_chat_suggestions(self, question: str) -> List[str]:
        """질문에 대한 제안 질문들 생성"""
        try:
            suggestions_prompt = f"""다음 질문과 관련된 추가 질문 3개를 한국어로 제안해주세요:

원본 질문: {question}

제안 질문들은:
1. 원본 질문을 더 구체화한 것
2. 관련된 다른 관점의 질문
3. 실용적인 후속 질문

형식: 각 질문을 새 줄로 구분하여 답변하세요."""

            messages = [{
                "role": "system",
                "content": suggestions_prompt
            }]
            
            response = await self.llm_client.invoke_async(messages)
            
            # 응답을 줄바꿈으로 분리
            suggestions = [s.strip() for s in response.split('\n') if s.strip()]
            
            return suggestions[:3]  # 최대 3개만 반환
            
        except Exception as e:
            logger.error(f"❌ 제안 질문 생성 오류: {e}")
            return []
    
    def get_chat_stats(self) -> Dict[str, Any]:
        """챗봇 통계 정보"""
        return {
            "search_engine": "hybrid_retriever",
            "llm_model": self.llm_client.model,
            "available_sources": ["notion", "gdrive", "github"],
            "system_prompt_length": len(self.system_prompt),
            "database_connected": self.db_engine is not None
        } 