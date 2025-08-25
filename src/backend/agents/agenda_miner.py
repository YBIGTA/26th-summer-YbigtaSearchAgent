"""
아젠다 마이너 (AgendaMiner)

회의 발화를 분석하여 핵심 아젠다를 추출합니다.
- 토픽 클러스터링
- 중요도 분석
- 논의 구조 파악
"""

import json
import logging
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class AgendaMiner(BaseAgent):
    """아젠다 추출 전문 에이전트"""
    
    def __init__(self, llm_client=None):
        super().__init__(
            name="AgendaMiner",
            description="회의 발화를 클러스터링하여 핵심 아젠다를 추출하는 전문가",
            llm_client=llm_client
        )
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        회의록에서 아젠다 추출
        
        Args:
            input_data: {
                "transcript": str,  # 회의록 전문
                "speakers": List[str],  # 발화자 목록
                "timeline": List[Dict],  # 타임라인 정보
                "metadata": Dict  # 회의 메타데이터
            }
            
        Returns:
            {
                "agendas": List[Dict],  # 추출된 아젠다들
                "topics": List[Dict],   # 토픽 분석
                "structure": Dict,      # 논의 구조
                "confidence": float     # 신뢰도
            }
        """
        logger.info("AgendaMiner: 아젠다 추출 시작")
        
        try:
            transcript = input_data.get("transcript", "")
            speakers = input_data.get("speakers", [])
            timeline = input_data.get("timeline", [])
            
            if not transcript:
                return {
                    "error": "회의록이 제공되지 않았습니다.",
                    "agendas": [],
                    "topics": [],
                    "structure": {},
                    "confidence": 0.0
                }
            
            # 1. 토픽 클러스터링 수행
            topics = await self._extract_topics(transcript, timeline)
            
            # 2. 아젠다 식별
            agendas = await self._identify_agendas(topics, speakers, timeline)
            
            # 3. 논의 구조 분석
            structure = await self._analyze_structure(agendas, timeline)
            
            # 4. 신뢰도 계산
            confidence = self._calculate_confidence(agendas, topics)
            
            result = {
                "agendas": agendas,
                "topics": topics,
                "structure": structure,
                "confidence": confidence,
                "agent": self.name,
                "timestamp": input_data.get("timestamp")
            }
            
            logger.info(f"AgendaMiner: {len(agendas)}개 아젠다 추출 완료")
            return result
            
        except Exception as e:
            logger.error(f"AgendaMiner 처리 오류: {str(e)}")
            return {
                "error": str(e),
                "agendas": [],
                "topics": [],
                "structure": {},
                "confidence": 0.0
            }
    
    async def _extract_topics(self, transcript: str, timeline: List[Dict]) -> List[Dict]:
        """토픽 클러스터링"""
        
        context = f"""
회의록:
{transcript[:2000]}...

타임라인 정보:
{json.dumps(timeline[:10], ensure_ascii=False, indent=2) if timeline else "없음"}
"""
        
        question = "이 회의록에서 논의된 주요 토픽들을 추출하여 JSON 형식으로 반환하세요. 중요한 토픽일수록 높은 importance_score를 주세요 (0.0-1.0)."
        
        # 기대하는 형식 정의
        expected_format = {
            "topics": [
                {
                    "id": 1,
                    "title": "토픽 제목",
                    "keywords": ["키워드1", "키워드2", "키워드3"],
                    "description": "토픽 설명",
                    "importance_score": 0.8,
                    "time_segments": [{"start": "00:05:30", "end": "00:12:15"}]
                }
            ]
        }
        
        # 기본 fallback 결과
        fallback_topics = [{
            "id": 1,
            "title": "회의 주요 내용",
            "keywords": ["논의", "결정", "계획"],
            "description": "회의의 전반적인 논의 내용",
            "importance_score": 0.7,
            "time_segments": []
        }]
        
        try:
            result = await self.think_structured(context, question, expected_format)
            topics = result.get("topics", fallback_topics)
            
            # 결과 검증 및 보정
            validated_topics = []
            for i, topic in enumerate(topics):
                if isinstance(topic, dict):
                    validated_topic = {
                        "id": topic.get("id", i + 1),
                        "title": str(topic.get("title", f"토픽 {i + 1}")).strip(),
                        "keywords": topic.get("keywords", [])[:5],  # 최대 5개
                        "description": str(topic.get("description", "")).strip(),
                        "importance_score": max(0.0, min(1.0, float(topic.get("importance_score", 0.5)))),
                        "time_segments": topic.get("time_segments", [])
                    }
                    validated_topics.append(validated_topic)
            
            return validated_topics if validated_topics else fallback_topics
            
        except Exception as e:
            logger.warning(f"AgendaMiner: 토픽 추출 오류 - {str(e)}")
            return fallback_topics
    
    async def _identify_agendas(self, topics: List[Dict], speakers: List[str], timeline: List[Dict]) -> List[Dict]:
        """아젠다 식별"""
        
        topics_str = json.dumps(topics, ensure_ascii=False, indent=2)
        speakers_str = ", ".join(speakers) if speakers else "정보 없음"
        
        context = f"""
추출된 토픽들:
{topics_str}

참석자: {speakers_str}
"""
        
        question = "추출된 토픽들을 바탕으로 회의의 공식 아젠다를 구성하여 JSON 형식으로 반환하세요."
        
        # 기대하는 형식 정의
        expected_format = {
            "agendas": [
                {
                    "id": 1,
                    "title": "아젠다 제목",
                    "description": "아젠다 상세 설명",
                    "category": "discussion",
                    "priority": "high",
                    "related_topics": [1, 2],
                    "outcomes": ["결과1", "결과2"],
                    "action_items": [
                        {
                            "task": "할 일",
                            "assignee": "담당자",
                            "deadline": "마감일"
                        }
                    ],
                    "discussion_points": ["논의점1", "논의점2"]
                }
            ]
        }
        
        # 기본 fallback 결과
        fallback_agendas = [{
            "id": 1,
            "title": "주요 논의사항",
            "description": "회의에서 논의된 주요 안건들",
            "category": "discussion",
            "priority": "high",
            "related_topics": [t["id"] for t in topics[:3]] if topics else [],
            "outcomes": [],
            "action_items": [],
            "discussion_points": []
        }]
        
        try:
            result = await self.think_structured(context, question, expected_format)
            agendas = result.get("agendas", fallback_agendas)
            
            # 결과 검증 및 보정
            validated_agendas = []
            valid_categories = ["discussion", "decision", "information", "planning"]
            valid_priorities = ["high", "medium", "low"]
            
            for i, agenda in enumerate(agendas):
                if isinstance(agenda, dict):
                    validated_agenda = {
                        "id": agenda.get("id", i + 1),
                        "title": str(agenda.get("title", f"아젠다 {i + 1}")).strip(),
                        "description": str(agenda.get("description", "")).strip(),
                        "category": agenda.get("category", "discussion") if agenda.get("category") in valid_categories else "discussion",
                        "priority": agenda.get("priority", "medium") if agenda.get("priority") in valid_priorities else "medium",
                        "related_topics": agenda.get("related_topics", [])[:5],  # 최대 5개
                        "outcomes": agenda.get("outcomes", [])[:10],  # 최대 10개
                        "action_items": agenda.get("action_items", [])[:10],  # 최대 10개
                        "discussion_points": agenda.get("discussion_points", [])[:10]  # 최대 10개
                    }
                    validated_agendas.append(validated_agenda)
            
            return validated_agendas if validated_agendas else fallback_agendas
            
        except Exception as e:
            logger.warning(f"AgendaMiner: 아젠다 식별 오류 - {str(e)}")
            return fallback_agendas
    
    async def _analyze_structure(self, agendas: List[Dict], timeline: List[Dict]) -> Dict[str, Any]:
        """논의 구조 분석"""
        
        return {
            "total_agendas": len(agendas),
            "high_priority_count": len([a for a in agendas if a.get("priority") == "high"]),
            "categories": list(set(a.get("category", "unknown") for a in agendas)),
            "estimated_duration": {
                "total_minutes": len(timeline) if timeline else 0,
                "per_agenda": len(timeline) // len(agendas) if agendas and timeline else 0
            },
            "flow": [
                {
                    "sequence": i + 1,
                    "agenda_id": agenda["id"],
                    "title": agenda["title"],
                    "type": agenda.get("category", "discussion")
                }
                for i, agenda in enumerate(agendas)
            ]
        }
    
    def _calculate_confidence(self, agendas: List[Dict], topics: List[Dict]) -> float:
        """신뢰도 계산"""
        
        if not agendas or not topics:
            return 0.0
        
        # 기본 신뢰도
        confidence = 0.5
        
        # 아젠다 수에 따른 보정
        if len(agendas) >= 2:
            confidence += 0.2
            
        # 토픽 중요도 평균에 따른 보정
        avg_importance = sum(t.get("importance_score", 0) for t in topics) / len(topics)
        confidence += avg_importance * 0.3
        
        # 액션 아이템 존재 여부
        if any(a.get("action_items") for a in agendas):
            confidence += 0.1
            
        return min(confidence, 1.0)