"""
화자 중심 분석 모듈 (SpeakerAnalyzer)

회의에서 화자별 특성, 기여도, 상호작용을 심층 분석합니다.
- 화자별 발화 패턴 분석
- 아젠다별 화자 기여도 측정
- 화자간 상호작용 패턴 분석
- 의견 분포 및 합의 패턴 분석
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict, Counter
import re

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class SpeakerAnalyzer(BaseAgent):
    """화자 중심 회의 분석 에이전트"""
    
    def __init__(self, llm_client=None):
        super().__init__(
            name="SpeakerAnalyzer",
            description="화자별 발화 패턴, 기여도, 상호작용을 심층 분석하는 에이전트",
            llm_client=llm_client
        )
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """화자 중심 분석 실행"""
        try:
            logger.info(f"🎤 {self.name}: 화자 중심 분석 시작")
            
            # 입력 데이터 검증
            if not self._validate_input(input_data):
                return self._create_empty_result("입력 데이터가 유효하지 않습니다.")
            
            # 화자별 발화 데이터 추출
            speaker_data = self._extract_speaker_data(input_data)
            
            if not speaker_data:
                return self._create_empty_result("화자 데이터를 추출할 수 없습니다.")
            
            # 분석 실행
            analysis_result = {
                "speaker_statistics": self._analyze_speaker_statistics(speaker_data),
                "speaking_patterns": self._analyze_speaking_patterns(speaker_data),
                "interaction_analysis": self._analyze_speaker_interactions(speaker_data),
                "agenda_contributions": await self._analyze_agenda_contributions(speaker_data, input_data),
                "sentiment_analysis": self._analyze_speaker_sentiments(speaker_data),
                "summary": self._generate_speaker_summary(speaker_data)
            }
            
            logger.info(f"✅ {self.name}: 화자 중심 분석 완료 - {len(speaker_data)} 화자")
            
            return {
                "analysis_type": "speaker_centered",
                "total_speakers": len(speaker_data),
                "analysis_timestamp": datetime.now().isoformat(),
                "confidence": 0.85,  # 기본 신뢰도
                **analysis_result
            }
            
        except Exception as e:
            logger.error(f"❌ {self.name} 분석 실패: {str(e)}")
            return self._create_error_result(str(e))
    
    def _validate_input(self, input_data: Dict[str, Any]) -> bool:
        """입력 데이터 유효성 검증"""
        timeline = input_data.get("timeline", [])
        segments = input_data.get("segments", [])
        
        if not timeline and not segments:
            logger.error(f"{self.name}: 타임라인 또는 세그먼트 데이터가 없습니다.")
            return False
        
        return True
    
    def _extract_speaker_data(self, input_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """화자별 발화 데이터 추출"""
        speaker_utterances = defaultdict(list)
        
        # 타임라인에서 데이터 추출
        timeline = input_data.get("timeline", [])
        for item in timeline:
            speaker = item.get("speaker", "Unknown")
            if speaker and speaker != "Unknown":
                utterance = {
                    "text": item.get("text", ""),
                    "start_time": item.get("start", 0),
                    "end_time": item.get("end", 0),
                    "duration": item.get("end", 0) - item.get("start", 0),
                    "timestamp": item.get("timestamp", "")
                }
                speaker_utterances[speaker].append(utterance)
        
        # 세그먼트에서도 데이터 추출 (타임라인이 없는 경우)
        if not speaker_utterances:
            segments = input_data.get("segments", [])
            for seg in segments:
                speaker = self._extract_speaker_from_segment(seg)
                if speaker and speaker != "Unknown":
                    utterance = {
                        "text": self._extract_text_from_segment(seg),
                        "start_time": seg.get("start", 0),
                        "end_time": seg.get("end", 0),
                        "duration": seg.get("duration", 0) or (seg.get("end", 0) - seg.get("start", 0)),
                        "timestamp": seg.get("timestamp", "")
                    }
                    speaker_utterances[speaker].append(utterance)
        
        logger.debug(f"화자별 발화 데이터: {[(spk, len(utts)) for spk, utts in speaker_utterances.items()]}")
        return dict(speaker_utterances)
    
    def _analyze_speaker_statistics(self, speaker_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """화자별 기본 통계 분석"""
        stats = {}
        total_speaking_time = 0
        total_utterances = 0
        total_words = 0
        
        # 각 화자별 통계 계산
        for speaker, utterances in speaker_data.items():
            speaking_time = sum(utt["duration"] for utt in utterances)
            utterance_count = len(utterances)
            word_count = sum(len(utt["text"].split()) for utt in utterances)
            avg_utterance_length = word_count / utterance_count if utterance_count > 0 else 0
            
            stats[speaker] = {
                "utterance_count": utterance_count,
                "total_speaking_time": speaking_time,
                "total_words": word_count,
                "average_utterance_length": round(avg_utterance_length, 1),
                "speaking_rate": round(word_count / (speaking_time / 60), 1) if speaking_time > 0 else 0  # 분당 단어 수
            }
            
            total_speaking_time += speaking_time
            total_utterances += utterance_count
            total_words += word_count
        
        # 비율 계산
        for speaker in stats:
            stats[speaker]["speaking_percentage"] = round(
                (stats[speaker]["total_speaking_time"] / total_speaking_time * 100) if total_speaking_time > 0 else 0, 1
            )
            stats[speaker]["utterance_percentage"] = round(
                (stats[speaker]["utterance_count"] / total_utterances * 100) if total_utterances > 0 else 0, 1
            )
        
        return {
            "individual_stats": stats,
            "summary": {
                "total_speakers": len(speaker_data),
                "total_speaking_time": total_speaking_time,
                "total_utterances": total_utterances,
                "total_words": total_words,
                "most_active_speaker": max(stats.keys(), key=lambda s: stats[s]["total_words"]) if stats else None,
                "most_talkative_speaker": max(stats.keys(), key=lambda s: stats[s]["total_speaking_time"]) if stats else None
            }
        }
    
    def _analyze_speaking_patterns(self, speaker_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """화자별 발화 패턴 분석"""
        patterns = {}
        
        for speaker, utterances in speaker_data.items():
            if not utterances:
                continue
            
            # 발화 길이 분포
            utterance_lengths = [len(utt["text"].split()) for utt in utterances]
            
            # 발화 간격 분석
            intervals = []
            if len(utterances) > 1:
                for i in range(1, len(utterances)):
                    interval = utterances[i]["start_time"] - utterances[i-1]["end_time"]
                    if interval >= 0:  # 유효한 간격만
                        intervals.append(interval)
            
            # 발화 시작 시간 분포 (회의 진행 패턴)
            speaking_times = [utt["start_time"] for utt in utterances]
            
            patterns[speaker] = {
                "utterance_length_stats": {
                    "min": min(utterance_lengths) if utterance_lengths else 0,
                    "max": max(utterance_lengths) if utterance_lengths else 0,
                    "average": round(sum(utterance_lengths) / len(utterance_lengths), 1) if utterance_lengths else 0,
                    "distribution": self._categorize_utterance_lengths(utterance_lengths)
                },
                "speaking_intervals": {
                    "average_interval": round(sum(intervals) / len(intervals), 1) if intervals else 0,
                    "total_pauses": len(intervals),
                    "longest_pause": max(intervals) if intervals else 0
                },
                "temporal_pattern": {
                    "first_speech_time": min(speaking_times) if speaking_times else 0,
                    "last_speech_time": max(speaking_times) if speaking_times else 0,
                    "speaking_distribution": self._analyze_temporal_distribution(speaking_times)
                }
            }
        
        return patterns
    
    def _analyze_speaker_interactions(self, speaker_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """화자간 상호작용 패턴 분석"""
        interactions = {}
        all_utterances = []
        
        # 모든 발화를 시간순으로 정렬
        for speaker, utterances in speaker_data.items():
            for utt in utterances:
                utt_with_speaker = utt.copy()
                utt_with_speaker["speaker"] = speaker
                all_utterances.append(utt_with_speaker)
        
        all_utterances.sort(key=lambda x: x["start_time"])
        
        if len(all_utterances) < 2:
            return {"error": "상호작용 분석을 위한 충분한 데이터가 없습니다."}
        
        # 화자 전환 패턴 분석
        transitions = []
        response_times = []
        
        for i in range(1, len(all_utterances)):
            prev_speaker = all_utterances[i-1]["speaker"]
            curr_speaker = all_utterances[i]["speaker"]
            
            # 화자 전환
            if prev_speaker != curr_speaker:
                transitions.append((prev_speaker, curr_speaker))
                
                # 응답 시간 (이전 발화 종료 ~ 현재 발화 시작)
                response_time = all_utterances[i]["start_time"] - all_utterances[i-1]["end_time"]
                if response_time >= 0:
                    response_times.append(response_time)
        
        # 상호작용 매트릭스
        interaction_matrix = defaultdict(lambda: defaultdict(int))
        for from_speaker, to_speaker in transitions:
            interaction_matrix[from_speaker][to_speaker] += 1
        
        interactions = {
            "speaker_transitions": {
                "total_transitions": len(transitions),
                "transition_matrix": dict(interaction_matrix),
                "most_common_transitions": Counter(transitions).most_common(5)
            },
            "response_patterns": {
                "average_response_time": round(sum(response_times) / len(response_times), 1) if response_times else 0,
                "fastest_response": min(response_times) if response_times else 0,
                "slowest_response": max(response_times) if response_times else 0
            },
            "interaction_metrics": self._calculate_interaction_metrics(speaker_data, interaction_matrix)
        }
        
        return interactions
    
    async def _analyze_agenda_contributions(self, speaker_data: Dict[str, List[Dict]], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """아젠다별 화자 기여도 분석"""
        # 간단한 키워드 기반 토픽 분석 (LLM이 있으면 더 정교한 분석 가능)
        contributions = {}
        
        # 기본 토픽 키워드 (실제로는 아젠다 마이닝 결과를 활용)
        topic_keywords = {
            "프로젝트": ["프로젝트", "개발", "일정", "계획"],
            "예산": ["예산", "비용", "금액", "투자"],
            "인사": ["채용", "인력", "팀", "조직"],
            "기술": ["기술", "시스템", "개발", "구현"],
            "마케팅": ["마케팅", "홍보", "고객", "판매"]
        }
        
        for speaker, utterances in speaker_data.items():
            speaker_contributions = {}
            
            for topic, keywords in topic_keywords.items():
                topic_mentions = 0
                topic_words = 0
                
                for utt in utterances:
                    text_lower = utt["text"].lower()
                    for keyword in keywords:
                        if keyword in text_lower:
                            topic_mentions += 1
                            topic_words += len(utt["text"].split())
                
                speaker_contributions[topic] = {
                    "mentions": topic_mentions,
                    "words": topic_words,
                    "relevance_score": topic_mentions * 0.3 + (topic_words / 100) * 0.7
                }
            
            contributions[speaker] = speaker_contributions
        
        # 토픽별 주요 기여자 식별
        topic_leaders = {}
        for topic in topic_keywords.keys():
            topic_scores = [(spk, contrib[topic]["relevance_score"]) for spk, contrib in contributions.items()]
            topic_scores.sort(key=lambda x: x[1], reverse=True)
            topic_leaders[topic] = topic_scores[0][0] if topic_scores and topic_scores[0][1] > 0 else None
        
        return {
            "individual_contributions": contributions,
            "topic_leadership": topic_leaders,
            "analysis_method": "keyword_based"  # LLM 사용 시 "llm_based"로 변경 가능
        }
    
    def _analyze_speaker_sentiments(self, speaker_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """화자별 감정/어조 분석 (기본적인 키워드 기반)"""
        sentiments = {}
        
        # 감정 키워드 사전 (간단한 버전)
        positive_words = ["좋다", "훌륭", "완벽", "성공", "만족", "긍정", "찬성", "동의"]
        negative_words = ["나쁘다", "문제", "걱정", "우려", "반대", "부정", "실패", "어려움"]
        question_words = ["어떻게", "무엇", "왜", "언제", "어디", "누구", "?"]
        
        for speaker, utterances in speaker_data.items():
            positive_count = 0
            negative_count = 0
            question_count = 0
            total_words = 0
            
            for utt in utterances:
                text = utt["text"]
                words = text.split()
                total_words += len(words)
                
                text_lower = text.lower()
                
                for word in positive_words:
                    if word in text_lower:
                        positive_count += 1
                
                for word in negative_words:
                    if word in text_lower:
                        negative_count += 1
                
                for word in question_words:
                    if word in text_lower or "?" in text:
                        question_count += 1
            
            # 감정 점수 계산
            sentiment_score = (positive_count - negative_count) / max(total_words, 1) * 100
            
            sentiments[speaker] = {
                "positive_indicators": positive_count,
                "negative_indicators": negative_count,
                "questions_asked": question_count,
                "sentiment_score": round(sentiment_score, 2),
                "sentiment_category": self._categorize_sentiment(sentiment_score),
                "engagement_level": self._calculate_engagement_level(question_count, len(utterances))
            }
        
        return sentiments
    
    def _generate_speaker_summary(self, speaker_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """화자별 종합 요약"""
        if not speaker_data:
            return {"summary": "분석할 화자 데이터가 없습니다."}
        
        # 전체 통계
        total_speakers = len(speaker_data)
        total_utterances = sum(len(utts) for utts in speaker_data.values())
        total_words = sum(sum(len(utt["text"].split()) for utt in utts) for utts in speaker_data.values())
        
        # 화자별 기여도 순위
        speaker_rankings = []
        for speaker, utterances in speaker_data.items():
            word_count = sum(len(utt["text"].split()) for utt in utterances)
            speaker_rankings.append({
                "speaker": speaker,
                "utterances": len(utterances),
                "words": word_count,
                "contribution_score": word_count * 0.7 + len(utterances) * 0.3
            })
        
        speaker_rankings.sort(key=lambda x: x["contribution_score"], reverse=True)
        
        return {
            "meeting_overview": {
                "total_speakers": total_speakers,
                "total_utterances": total_utterances,
                "total_words": total_words,
                "average_words_per_speaker": round(total_words / total_speakers, 1)
            },
            "speaker_rankings": speaker_rankings,
            "top_contributors": [spk["speaker"] for spk in speaker_rankings[:3]],
            "participation_balance": self._assess_participation_balance(speaker_rankings),
            "key_insights": self._generate_key_insights(speaker_data, speaker_rankings)
        }
    
    def _categorize_utterance_lengths(self, lengths: List[int]) -> Dict[str, int]:
        """발화 길이별 분포 분류"""
        short = sum(1 for l in lengths if l <= 5)
        medium = sum(1 for l in lengths if 6 <= l <= 15)
        long_ = sum(1 for l in lengths if l > 15)
        
        return {"short": short, "medium": medium, "long": long_}
    
    def _analyze_temporal_distribution(self, speaking_times: List[float]) -> str:
        """시간대별 발화 분포 분석"""
        if not speaking_times:
            return "no_data"
        
        max_time = max(speaking_times)
        early_count = sum(1 for t in speaking_times if t <= max_time * 0.33)
        middle_count = sum(1 for t in speaking_times if max_time * 0.33 < t <= max_time * 0.66)
        late_count = sum(1 for t in speaking_times if t > max_time * 0.66)
        
        if early_count >= middle_count and early_count >= late_count:
            return "early_dominant"
        elif middle_count >= late_count:
            return "middle_dominant" 
        else:
            return "late_dominant"
    
    def _calculate_interaction_metrics(self, speaker_data: Dict, interaction_matrix: Dict) -> Dict[str, Any]:
        """상호작용 메트릭 계산"""
        metrics = {}
        speakers = list(speaker_data.keys())
        
        for speaker in speakers:
            # 이 화자가 얼마나 다른 화자들과 상호작용하는가
            interactions_initiated = sum(interaction_matrix.get(speaker, {}).values())
            interactions_received = sum(interaction_matrix.get(other, {}).get(speaker, 0) for other in speakers)
            
            metrics[speaker] = {
                "interactions_initiated": interactions_initiated,
                "interactions_received": interactions_received,
                "interaction_ratio": round(interactions_initiated / max(interactions_received, 1), 2),
                "interaction_diversity": len(interaction_matrix.get(speaker, {}))  # 몇 명과 상호작용했는가
            }
        
        return metrics
    
    def _categorize_sentiment(self, score: float) -> str:
        """감정 점수를 카테고리로 분류"""
        if score > 1.0:
            return "very_positive"
        elif score > 0.2:
            return "positive"
        elif score > -0.2:
            return "neutral"
        elif score > -1.0:
            return "negative"
        else:
            return "very_negative"
    
    def _calculate_engagement_level(self, questions: int, utterances: int) -> str:
        """참여 수준 계산"""
        if utterances == 0:
            return "no_participation"
        
        question_ratio = questions / utterances
        
        if question_ratio > 0.3:
            return "highly_engaged"
        elif question_ratio > 0.1:
            return "moderately_engaged"
        else:
            return "low_engagement"
    
    def _assess_participation_balance(self, rankings: List[Dict]) -> str:
        """참여 균형도 평가"""
        if len(rankings) < 2:
            return "insufficient_data"
        
        scores = [r["contribution_score"] for r in rankings]
        max_score = max(scores)
        min_score = min(scores)
        
        if max_score == 0:
            return "no_participation"
        
        balance_ratio = min_score / max_score
        
        if balance_ratio > 0.7:
            return "well_balanced"
        elif balance_ratio > 0.3:
            return "moderately_balanced"
        else:
            return "unbalanced"
    
    def _generate_key_insights(self, speaker_data: Dict, rankings: List[Dict]) -> List[str]:
        """주요 인사이트 생성"""
        insights = []
        
        if not rankings:
            return ["분석할 데이터가 부족합니다."]
        
        # 최다 발언자
        top_speaker = rankings[0]
        insights.append(f"{top_speaker['speaker']}가 가장 활발하게 참여했습니다 ({top_speaker['words']}단어, {top_speaker['utterances']}회 발언).")
        
        # 참여도 격차
        if len(rankings) > 1:
            participation_gap = rankings[0]["contribution_score"] / rankings[-1]["contribution_score"] if rankings[-1]["contribution_score"] > 0 else float('inf')
            if participation_gap > 5:
                insights.append("화자간 참여도 격차가 큽니다. 일부 참석자의 더 많은 참여가 필요할 수 있습니다.")
        
        # 화자 수 대비 발언 분포
        total_speakers = len(speaker_data)
        active_speakers = len([r for r in rankings if r["utterances"] > 2])
        if active_speakers / total_speakers < 0.5:
            insights.append("참석자 중 절반 이상이 적극적으로 발언하지 않았습니다.")
        
        return insights
    
    def _extract_text_from_segment(self, seg: Dict[str, Any]) -> str:
        """세그먼트에서 텍스트 추출"""
        text_fields = ["text", "msg", "content", "utterance"]
        for field in text_fields:
            if field in seg and seg[field]:
                return seg[field].strip()
        return ""
    
    def _extract_speaker_from_segment(self, seg: Dict[str, Any]) -> str:
        """세그먼트에서 화자 추출"""
        speaker_fields = ["speaker", "spk"]
        for field in speaker_fields:
            if field in seg and seg[field] is not None:
                speaker_value = seg[field]
                if isinstance(speaker_value, int):
                    return f"Speaker {speaker_value}"
                else:
                    return str(speaker_value)
        return "Unknown"
    
    def _create_empty_result(self, reason: str) -> Dict[str, Any]:
        """빈 결과 생성"""
        return {
            "analysis_type": "speaker_centered",
            "error": reason,
            "total_speakers": 0,
            "analysis_timestamp": datetime.now().isoformat(),
            "confidence": 0.0
        }
    
    def _create_error_result(self, error_msg: str) -> Dict[str, Any]:
        """오류 결과 생성"""
        return {
            "analysis_type": "speaker_centered",
            "error": error_msg,
            "total_speakers": 0,
            "analysis_timestamp": datetime.now().isoformat(),
            "confidence": 0.0
        }