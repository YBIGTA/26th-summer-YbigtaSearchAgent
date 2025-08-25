"""
텍스트 처리기 (TextProcessor)

텍스트 정제, 토큰화, 키워드 추출 등의 기본적인 NLP 처리를 제공합니다.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import Counter
import asyncio

logger = logging.getLogger(__name__)


class TextProcessor:
    """텍스트 처리 유틸리티 클래스"""
    
    def __init__(self):
        # 한국어 불용어
        self.korean_stopwords = {
            "은", "는", "이", "가", "을", "를", "에", "의", "와", "과", "도", "만", 
            "에서", "로", "으로", "부터", "까지", "에게", "께서", "에서부터", "까지", 
            "하고", "하며", "하면서", "그리고", "그런데", "하지만", "그러나", "또한",
            "또", "및", "등", "즉", "이런", "그런", "이러한", "그러한", "같은",
            "있다", "없다", "이다", "아니다", "되다", "하다", "주다", "받다",
            "것", "수", "때", "곳", "사람", "경우", "문제", "방법", "상태", "결과"
        }
        
        # 영어 불용어
        self.english_stopwords = {
            "a", "an", "and", "are", "as", "at", "be", "been", "by", "for", 
            "from", "has", "he", "in", "is", "it", "its", "of", "on", "that", 
            "the", "to", "was", "will", "with", "would", "could", "should",
            "this", "these", "those", "they", "them", "their", "there", "where",
            "when", "what", "who", "why", "how", "can", "may", "might", "must",
            "shall", "do", "does", "did", "have", "had", "having"
        }
        
        # 전체 불용어 집합
        self.stopwords = self.korean_stopwords | self.english_stopwords
        
        # 정규식 패턴
        self.patterns = {
            "korean": re.compile(r'[가-힣]+'),
            "english": re.compile(r'[a-zA-Z]+'),
            "number": re.compile(r'\d+'),
            "special": re.compile(r'[^\w\s가-힣]'),
            "whitespace": re.compile(r'\s+'),
            "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            "url": re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'),
            "phone": re.compile(r'(?:\d{2,3}-\d{3,4}-\d{4}|\d{10,11})')
        }
    
    def clean_text(self, text: str, options: Optional[Dict[str, bool]] = None) -> str:
        """
        텍스트 정제
        
        Args:
            text: 정제할 텍스트
            options: 정제 옵션
                - remove_special: 특수문자 제거 (기본: True)
                - remove_numbers: 숫자 제거 (기본: False)
                - remove_urls: URL 제거 (기본: True)
                - remove_emails: 이메일 제거 (기본: True)
                - normalize_whitespace: 공백 정규화 (기본: True)
                - lowercase: 소문자 변환 (기본: False)
        """
        if not text:
            return ""
        
        # 기본 옵션
        default_options = {
            "remove_special": True,
            "remove_numbers": False,
            "remove_urls": True,
            "remove_emails": True,
            "normalize_whitespace": True,
            "lowercase": False
        }
        
        if options:
            default_options.update(options)
        
        cleaned = text
        
        # URL 제거
        if default_options["remove_urls"]:
            cleaned = self.patterns["url"].sub(" ", cleaned)
        
        # 이메일 제거
        if default_options["remove_emails"]:
            cleaned = self.patterns["email"].sub(" ", cleaned)
        
        # 전화번호 제거
        cleaned = self.patterns["phone"].sub(" ", cleaned)
        
        # 특수문자 제거
        if default_options["remove_special"]:
            cleaned = self.patterns["special"].sub(" ", cleaned)
        
        # 숫자 제거
        if default_options["remove_numbers"]:
            cleaned = self.patterns["number"].sub(" ", cleaned)
        
        # 공백 정규화
        if default_options["normalize_whitespace"]:
            cleaned = self.patterns["whitespace"].sub(" ", cleaned).strip()
        
        # 소문자 변환
        if default_options["lowercase"]:
            cleaned = cleaned.lower()
        
        return cleaned
    
    def tokenize(self, text: str, min_length: int = 2, max_length: int = 50) -> List[str]:
        """
        텍스트 토큰화
        
        Args:
            text: 토큰화할 텍스트
            min_length: 최소 토큰 길이
            max_length: 최대 토큰 길이
        """
        if not text:
            return []
        
        # 기본 공백 기반 토큰화
        tokens = text.split()
        
        # 길이 필터링
        filtered_tokens = [
            token for token in tokens 
            if min_length <= len(token) <= max_length
        ]
        
        # 불용어 제거
        meaningful_tokens = [
            token for token in filtered_tokens 
            if token.lower() not in self.stopwords
        ]
        
        return meaningful_tokens
    
    def extract_keywords(self, text: str, top_k: int = 10, method: str = "frequency") -> List[str]:
        """
        키워드 추출
        
        Args:
            text: 키워드를 추출할 텍스트
            top_k: 추출할 키워드 수
            method: 추출 방법 ("frequency", "tfidf", "combined")
        """
        if not text:
            return []
        
        # 텍스트 정제 및 토큰화
        cleaned_text = self.clean_text(text, {"lowercase": True})
        tokens = self.tokenize(cleaned_text)
        
        if not tokens:
            return []
        
        if method == "frequency":
            return self._extract_by_frequency(tokens, top_k)
        elif method == "tfidf":
            return self._extract_by_tfidf(tokens, top_k)
        elif method == "combined":
            return self._extract_by_combined_method(tokens, top_k)
        else:
            logger.warning(f"알 수 없는 키워드 추출 방법: {method}")
            return self._extract_by_frequency(tokens, top_k)
    
    def _extract_by_frequency(self, tokens: List[str], top_k: int) -> List[str]:
        """빈도 기반 키워드 추출"""
        
        counter = Counter(tokens)
        return [word for word, count in counter.most_common(top_k)]
    
    def _extract_by_tfidf(self, tokens: List[str], top_k: int) -> List[str]:
        """TF-IDF 기반 키워드 추출 (간단 구현)"""
        
        # 단일 문서이므로 TF만 고려
        counter = Counter(tokens)
        total_tokens = len(tokens)
        
        # TF 점수 계산
        tf_scores = {}
        for word, count in counter.items():
            tf_scores[word] = count / total_tokens
        
        # 점수순 정렬
        sorted_words = sorted(tf_scores.items(), key=lambda x: x[1], reverse=True)
        return [word for word, score in sorted_words[:top_k]]
    
    def _extract_by_combined_method(self, tokens: List[str], top_k: int) -> List[str]:
        """복합적 방법으로 키워드 추출"""
        
        # 빈도와 길이를 고려한 점수
        counter = Counter(tokens)
        combined_scores = {}
        
        for word, count in counter.items():
            # 빈도 점수 (정규화)
            freq_score = count / len(tokens)
            
            # 길이 점수 (긴 단어에 가점)
            length_score = min(len(word) / 10, 1.0)  # 최대 1.0
            
            # 언어별 가중치
            lang_weight = 1.0
            if self.patterns["korean"].match(word):
                lang_weight = 1.2  # 한국어 단어 가점
            elif self.patterns["english"].match(word):
                lang_weight = 1.0
            
            # 복합 점수
            combined_scores[word] = (freq_score * 0.6) + (length_score * 0.3) + (lang_weight * 0.1)
        
        # 점수순 정렬
        sorted_words = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        return [word for word, score in sorted_words[:top_k]]
    
    async def expand_query(self, query: str) -> str:
        """
        쿼리 확장 (동의어, 관련어 추가)
        
        Args:
            query: 확장할 쿼리
        """
        if not query:
            return query
        
        # 기본 쿼리 반환 (실제로는 동의어 사전이나 임베딩 기반 유사어 찾기)
        expanded_terms = []
        
        # 키워드 추출
        keywords = self.extract_keywords(query, top_k=5)
        
        # 각 키워드에 대해 유사어 추가 (더미 구현)
        for keyword in keywords:
            expanded_terms.append(keyword)
            
            # 간단한 동의어 매핑 (실제로는 외부 사전 활용)
            synonyms = self._get_simple_synonyms(keyword)
            expanded_terms.extend(synonyms[:2])  # 최대 2개 동의어
        
        # 중복 제거하고 원본 쿼리에 추가
        unique_terms = list(set(expanded_terms))
        if len(unique_terms) > len(keywords):
            return query + " " + " ".join(unique_terms[len(keywords):])
        
        return query
    
    def _get_simple_synonyms(self, word: str) -> List[str]:
        """간단한 동의어 매핑"""
        
        synonym_map = {
            "회의": ["미팅", "모임", "협의"],
            "분석": ["검토", "조사", "해석"],
            "문서": ["자료", "파일", "문헌"],
            "프로젝트": ["사업", "과제", "업무"],
            "계획": ["방안", "전략", "안"],
            "결과": ["성과", "산출물", "outcome"],
            "meeting": ["conference", "discussion", "session"],
            "project": ["initiative", "program", "task"],
            "analysis": ["review", "study", "examination"],
            "plan": ["strategy", "scheme", "proposal"],
            "result": ["outcome", "finding", "conclusion"]
        }
        
        return synonym_map.get(word.lower(), [])
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        개체명 추출 (간단한 규칙 기반)
        
        Args:
            text: 개체명을 추출할 텍스트
            
        Returns:
            개체 유형별 리스트
        """
        entities = {
            "dates": [],
            "numbers": [],
            "emails": [],
            "urls": [],
            "phones": [],
            "organizations": [],
            "persons": []
        }
        
        # 날짜 패턴
        date_patterns = [
            r'\d{4}[-./]\d{1,2}[-./]\d{1,2}',  # 2024-01-15
            r'\d{1,2}[-./]\d{1,2}[-./]\d{4}',  # 15-01-2024
            r'\d{4}년\s*\d{1,2}월\s*\d{1,2}일',  # 2024년 1월 15일
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            entities["dates"].extend(matches)
        
        # 숫자
        numbers = self.patterns["number"].findall(text)
        entities["numbers"] = [num for num in numbers if len(num) > 1]  # 한 자리 숫자 제외
        
        # 이메일
        emails = self.patterns["email"].findall(text)
        entities["emails"] = emails
        
        # URL
        urls = self.patterns["url"].findall(text)
        entities["urls"] = urls
        
        # 전화번호
        phones = self.patterns["phone"].findall(text)
        entities["phones"] = phones
        
        # 조직명 추출 (간단한 패턴)
        org_patterns = [
            r'[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*(?:\s+(?:Inc|Corp|Ltd|Co|Company)\.?)',  # 영문 회사명
            r'[가-힣]+(?:회사|기업|그룹|법인|재단|협회|조합|연구소|대학교|센터)',  # 한글 조직명
        ]
        
        for pattern in org_patterns:
            matches = re.findall(pattern, text)
            entities["organizations"].extend(matches)
        
        # 인명 추출 (매우 간단한 패턴)
        person_patterns = [
            r'[A-Z][a-z]+\s+[A-Z][a-z]+',  # John Smith
            r'[가-힣]{2,4}(?:\s+[가-힣]{1,2})?(?=님|씨|교수|대표|이사|부장|과장|팀장)',  # 한글 이름 + 직책
        ]
        
        for pattern in person_patterns:
            matches = re.findall(pattern, text)
            entities["persons"].extend(matches)
        
        # 중복 제거
        for entity_type in entities:
            entities[entity_type] = list(set(entities[entity_type]))
        
        return entities
    
    def calculate_similarity(self, text1: str, text2: str, method: str = "jaccard") -> float:
        """
        텍스트 유사도 계산
        
        Args:
            text1, text2: 비교할 텍스트들
            method: 유사도 계산 방법 ("jaccard", "cosine", "levenshtein")
        """
        if not text1 or not text2:
            return 0.0
        
        if method == "jaccard":
            return self._jaccard_similarity(text1, text2)
        elif method == "cosine":
            return self._cosine_similarity(text1, text2)
        elif method == "levenshtein":
            return self._levenshtein_similarity(text1, text2)
        else:
            logger.warning(f"알 수 없는 유사도 계산 방법: {method}")
            return self._jaccard_similarity(text1, text2)
    
    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """Jaccard 유사도 계산"""
        
        tokens1 = set(self.tokenize(self.clean_text(text1, {"lowercase": True})))
        tokens2 = set(self.tokenize(self.clean_text(text2, {"lowercase": True})))
        
        if not tokens1 and not tokens2:
            return 1.0
        
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        
        return intersection / union if union > 0 else 0.0
    
    def _cosine_similarity(self, text1: str, text2: str) -> float:
        """코사인 유사도 계산 (간단 구현)"""
        
        tokens1 = self.tokenize(self.clean_text(text1, {"lowercase": True}))
        tokens2 = self.tokenize(self.clean_text(text2, {"lowercase": True}))
        
        # 용어 빈도 벡터 생성
        all_tokens = set(tokens1 + tokens2)
        
        if not all_tokens:
            return 0.0
        
        vector1 = [tokens1.count(token) for token in all_tokens]
        vector2 = [tokens2.count(token) for token in all_tokens]
        
        # 코사인 유사도 계산
        dot_product = sum(a * b for a, b in zip(vector1, vector2))
        magnitude1 = (sum(a * a for a in vector1)) ** 0.5
        magnitude2 = (sum(b * b for b in vector2)) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def _levenshtein_similarity(self, text1: str, text2: str) -> float:
        """레벤슈타인 거리 기반 유사도"""
        
        def levenshtein_distance(s1: str, s2: str) -> int:
            if len(s1) < len(s2):
                return levenshtein_distance(s2, s1)
            
            if len(s2) == 0:
                return len(s1)
            
            previous_row = list(range(len(s2) + 1))
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            
            return previous_row[-1]
        
        distance = levenshtein_distance(text1.lower(), text2.lower())
        max_length = max(len(text1), len(text2))
        
        if max_length == 0:
            return 1.0
        
        return 1.0 - (distance / max_length)
    
    def get_text_stats(self, text: str) -> Dict[str, Any]:
        """텍스트 통계 정보 반환"""
        
        if not text:
            return {
                "char_count": 0,
                "word_count": 0,
                "sentence_count": 0,
                "paragraph_count": 0,
                "avg_word_length": 0.0,
                "language_distribution": {}
            }
        
        # 기본 통계
        char_count = len(text)
        words = self.tokenize(text)
        word_count = len(words)
        sentence_count = len(re.split(r'[.!?]+', text))
        paragraph_count = len(text.split('\n\n'))
        
        # 평균 단어 길이
        avg_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0.0
        
        # 언어 분포
        korean_chars = len(self.patterns["korean"].findall(text))
        english_chars = len(self.patterns["english"].findall(text))
        number_chars = len(self.patterns["number"].findall(text))
        
        total_meaningful_chars = korean_chars + english_chars + number_chars
        
        language_distribution = {}
        if total_meaningful_chars > 0:
            language_distribution = {
                "korean": korean_chars / total_meaningful_chars,
                "english": english_chars / total_meaningful_chars,
                "numbers": number_chars / total_meaningful_chars
            }
        
        return {
            "char_count": char_count,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "paragraph_count": paragraph_count,
            "avg_word_length": round(avg_word_length, 2),
            "language_distribution": language_distribution
        }