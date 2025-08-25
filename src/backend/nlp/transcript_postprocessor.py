"""
전사 후처리 (Transcript Post-processor)

STT 결과의 품질을 개선하는 후처리 로직들입니다.
- 한국어 특화 텍스트 정제
- 발음 유사성 기반 오류 교정
- 문맥적 단어 교정
- 음성학적 오류 수정
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CorrectionRule:
    """교정 규칙 데이터 클래스"""
    pattern: str
    replacement: str
    context: Optional[str] = None
    confidence: float = 1.0


class TranscriptPostProcessor:
    """전사 결과 후처리 전문 클래스"""
    
    def __init__(self):
        self.korean_correction_rules = self._load_korean_correction_rules()
        self.phonetic_correction_rules = self._load_phonetic_correction_rules()
        self.context_correction_rules = self._load_context_correction_rules()
        
    def process(self, transcript_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        전사 결과를 후처리합니다.
        
        Args:
            transcript_data: STT 결과 데이터
            
        Returns:
            개선된 전사 결과
        """
        logger.info("전사 후처리 시작")
        
        try:
            processed_data = transcript_data.copy()
            
            # 1. 기본 텍스트 정제
            if "text" in processed_data:
                processed_data["text"] = self._clean_text(processed_data["text"])
                processed_data["text"] = self._apply_correction_rules(processed_data["text"])
            
            # 2. 세그먼트별 후처리
            if "segments" in processed_data:
                processed_segments = []
                for segment in processed_data["segments"]:
                    processed_segment = segment.copy()
                    
                    if "text" in processed_segment:
                        original_text = processed_segment["text"]
                        
                        # 텍스트 정제 및 교정
                        cleaned_text = self._clean_text(original_text)
                        corrected_text = self._apply_correction_rules(cleaned_text)
                        
                        processed_segment["text"] = corrected_text
                        processed_segment["original_text"] = original_text
                        
                        # 교정 점수 계산
                        correction_score = self._calculate_correction_score(original_text, corrected_text)
                        processed_segment["correction_confidence"] = correction_score
                    
                    processed_segments.append(processed_segment)
                
                processed_data["segments"] = processed_segments
            
            # 3. 전체 텍스트 재구성
            if processed_data.get("segments"):
                full_corrected_text = " ".join([
                    seg["text"] for seg in processed_data["segments"] 
                    if seg.get("text", "").strip()
                ])
                processed_data["text"] = full_corrected_text
            
            # 4. 메타데이터 추가
            processed_data["postprocessing"] = {
                "applied": True,
                "timestamp": self._get_timestamp(),
                "corrections_applied": len(self.korean_correction_rules) + len(self.phonetic_correction_rules),
                "quality_score": self._calculate_overall_quality_score(processed_data)
            }
            
            logger.info("전사 후처리 완료")
            return processed_data
            
        except Exception as e:
            logger.error(f"전사 후처리 오류: {str(e)}")
            return transcript_data
    
    def _clean_text(self, text: str) -> str:
        """기본 텍스트 정제"""
        if not text:
            return ""
        
        # 1. 연속된 공백 정리
        text = re.sub(r'\s+', ' ', text)
        
        # 2. 특수문자 정리
        text = re.sub(r'[^\w\s가-힣.,!?-]', '', text)
        
        # 3. 문장 부호 정리
        text = re.sub(r'([.!?])\s*([.!?])+', r'\1', text)  # 연속된 문장부호
        text = re.sub(r'([,])\s*([,])+', r'\1', text)  # 연속된 쉼표
        
        # 4. 앞뒤 공백 제거
        text = text.strip()
        
        return text
    
    def _apply_correction_rules(self, text: str) -> str:
        """교정 규칙 적용"""
        if not text:
            return ""
        
        corrected_text = text
        
        # 1. 한국어 특화 교정
        for rule in self.korean_correction_rules:
            corrected_text = re.sub(rule.pattern, rule.replacement, corrected_text, flags=re.IGNORECASE)
        
        # 2. 음성학적 교정
        for rule in self.phonetic_correction_rules:
            corrected_text = re.sub(rule.pattern, rule.replacement, corrected_text, flags=re.IGNORECASE)
        
        # 3. 문맥적 교정
        corrected_text = self._apply_contextual_corrections(corrected_text)
        
        return corrected_text
    
    def _apply_contextual_corrections(self, text: str) -> str:
        """문맥적 교정 적용"""
        corrected_text = text
        
        # 회의 관련 용어 교정
        meeting_terms = {
            r'\b맨 투 맨\b': '1:1',
            r'\b맨투맨\b': '1:1',
            r'\b맨 투밑\b': '1:1',
            r'\b맨투밑\b': '1:1',
            r'\b월파\b': '월요일',
            r'\b화파\b': '화요일',
            r'\b수파\b': '수요일',
            r'\b목파\b': '목요일',
            r'\b금파\b': '금요일',
            r'\b토파\b': '토요일',
            r'\b일파\b': '일요일',
            r'\b나섯 시\b': '다섯 시',
            r'\b나섯시\b': '다섯시',
            r'\b나 섯 시\b': '다섯 시',
            r'\b동섯 시\b': '다섯 시',
            r'\b동섯시\b': '다섯시',
            r'\b모요일\b': '월요일',
            r'\b출가해라\b': '죄송해요',
            r'\b날칭\b': '날짜',
            r'\b프리하\b': '프리한',
            r'\b길기어\b': '그리고',
            r'\b가은다\b': '간다',
            r'\b봤자\b': '봐도',
        }
        
        for pattern, replacement in meeting_terms.items():
            corrected_text = re.sub(pattern, replacement, corrected_text, flags=re.IGNORECASE)
        
        return corrected_text
    
    def _load_korean_correction_rules(self) -> List[CorrectionRule]:
        """한국어 교정 규칙 로드"""
        rules = [
            # 숫자 관련
            CorrectionRule(r'\b하나\b', '1', confidence=0.9),
            CorrectionRule(r'\b둘\b', '2', confidence=0.9),
            CorrectionRule(r'\b셋\b', '3', confidence=0.9),
            CorrectionRule(r'\b넷\b', '4', confidence=0.9),
            CorrectionRule(r'\b다섯\b', '5', confidence=0.9),
            CorrectionRule(r'\b여섯\b', '6', confidence=0.9),
            CorrectionRule(r'\b일곱\b', '7', confidence=0.9),
            CorrectionRule(r'\b여덟\b', '8', confidence=0.9),
            CorrectionRule(r'\b아홉\b', '9', confidence=0.9),
            CorrectionRule(r'\b열\b', '10', confidence=0.9),
            
            # 시간 관련
            CorrectionRule(r'\b([0-9]+)\s*시\b', r'\1시', confidence=0.95),
            CorrectionRule(r'\b([0-9]+)\s*분\b', r'\1분', confidence=0.95),
            CorrectionRule(r'\b([0-9]+)\s*초\b', r'\1초', confidence=0.95),
            
            # 일반적인 오타
            CorrectionRule(r'\b그랫\b', '그래서', confidence=0.8),
            CorrectionRule(r'\b그럼\b', '그러면', confidence=0.7),
            CorrectionRule(r'\b뭐냐\b', '뭔가', confidence=0.7),
            CorrectionRule(r'\b어떻냐\b', '어떤가', confidence=0.7),
            CorrectionRule(r'\b됀\b', '된', confidence=0.9),
            CorrectionRule(r'\b할 일\b', '할일', confidence=0.8),
            
            # 존댓말 정제
            CorrectionRule(r'\b해요\s+해요\b', '해요', confidence=0.9),
            CorrectionRule(r'\b습니다\s+습니다\b', '습니다', confidence=0.9),
        ]
        return rules
    
    def _load_phonetic_correction_rules(self) -> List[CorrectionRule]:
        """음성학적 교정 규칙 로드"""
        rules = [
            # ㄴ/ㄹ 혼동
            CorrectionRule(r'\b는데\b', '는데', confidence=0.8),
            CorrectionRule(r'\b니까\b', '니까', confidence=0.8),
            
            # ㅓ/ㅏ 혼동
            CorrectionRule(r'\b머냐\b', '뭐냐', confidence=0.8),
            CorrectionRule(r'\b머지\b', '뭐지', confidence=0.8),
            
            # 종성 탈락
            CorrectionRule(r'\b안녕하세요\b', '안녕하세요', confidence=0.9),
            CorrectionRule(r'\b감사합니다\b', '감사합니다', confidence=0.9),
            
            # 연음 현상
            CorrectionRule(r'\b이거\s*는\b', '이것은', confidence=0.7),
            CorrectionRule(r'\b그거\s*는\b', '그것은', confidence=0.7),
            CorrectionRule(r'\b저거\s*는\b', '저것은', confidence=0.7),
        ]
        return rules
    
    def _load_context_correction_rules(self) -> List[CorrectionRule]:
        """문맥 교정 규칙 로드"""
        rules = [
            # 회의 맥락
            CorrectionRule(r'\b회의\s*를\b', '회의를', confidence=0.9),
            CorrectionRule(r'\b안건\s*이\b', '안건이', confidence=0.9),
            CorrectionRule(r'\b논의\s*해\b', '논의해', confidence=0.9),
            CorrectionRule(r'\b결정\s*해\b', '결정해', confidence=0.9),
            
            # 업무 맥락
            CorrectionRule(r'\b프로젝트\s*를\b', '프로젝트를', confidence=0.9),
            CorrectionRule(r'\b작업\s*을\b', '작업을', confidence=0.9),
            CorrectionRule(r'\b계획\s*을\b', '계획을', confidence=0.9),
        ]
        return rules
    
    def _calculate_correction_score(self, original: str, corrected: str) -> float:
        """교정 신뢰도 점수 계산"""
        if original == corrected:
            return 1.0
        
        # 글자 단위 유사도
        original_chars = set(original)
        corrected_chars = set(corrected)
        
        if len(original_chars) == 0 and len(corrected_chars) == 0:
            return 1.0
        
        intersection = len(original_chars.intersection(corrected_chars))
        union = len(original_chars.union(corrected_chars))
        
        similarity = intersection / union if union > 0 else 0
        
        # 길이 차이 페널티
        length_penalty = 1 - abs(len(original) - len(corrected)) / max(len(original), len(corrected), 1)
        
        return (similarity * 0.7 + length_penalty * 0.3)
    
    def _calculate_overall_quality_score(self, processed_data: Dict[str, Any]) -> float:
        """전체 품질 점수 계산"""
        if not processed_data.get("segments"):
            return 0.5
        
        scores = []
        for segment in processed_data["segments"]:
            confidence = segment.get("correction_confidence", 0.5)
            scores.append(confidence)
        
        return sum(scores) / len(scores) if scores else 0.5
    
    def _get_timestamp(self) -> str:
        """현재 타임스탬프 반환"""
        from datetime import datetime
        return datetime.now().isoformat()


# 편의 함수
def postprocess_transcript(transcript_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    전사 결과를 후처리합니다.
    
    Args:
        transcript_data: STT 결과 데이터
        
    Returns:
        개선된 전사 결과
    """
    processor = TranscriptPostProcessor()
    return processor.process(transcript_data)