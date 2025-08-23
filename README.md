# YBIGTA 맞춤형 RAG AI Agent 🤖

## 개발해야 할 목록

1. ✅ YBIGTA Notion을 데이터베이스화하여 API와 연동한 뒤 .Env에 notion api key와 database key 저장
2. ✅ 로봇 계정 만들고 gdrive-credentials.json 받기
3. ✅ .env에 드라이브 폴더 id 저장

## 환경 변수 설정

`.env` 파일에 다음 환경 변수들을 설정해야 합니다:

```bash
# Upstage API 설정
UPSTAGE_API_KEY=your_upstage_api_key_here

# Notion API 설정 (페이지 기반)
NOTION_API_KEY=your_notion_integration_token_here
NOTION_PAGE_ID_1=your_first_notion_page_id_here
NOTION_PAGE_ID_2=your_second_notion_page_id_here  # 선택사항
NOTION_PAGE_ID_3=your_third_notion_page_id_here   # 선택사항
# 필요한 만큼 계속 추가 가능: NOTION_PAGE_ID_4, NOTION_PAGE_ID_5, ...

# GitHub 설정
GITHUB_PERSONAL_ACCESS_TOKEN=your_github_personal_access_token_here
```

## Upstage API 키 설정

1. [Upstage AI](https://upstage.ai/)에서 API 키를 발급받습니다.
2. `.env` 파일에 `UPSTAGE_API_KEY`를 설정합니다.
3. 예시: `UPSTAGE_API_KEY=up_9VGq6BcaLnASRYYs5JFflMN83psE9`

## Notion 페이지 ID 찾는 방법

1. Notion 페이지를 열고 URL을 확인
2. URL 형식: `https://www.notion.so/페이지이름-페이지ID`
3. 페이지 ID는 32자리 문자열 (예: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`)

## 여러 페이지 추가 방법

코드가 자동으로 `NOTION_PAGE_ID_1`, `NOTION_PAGE_ID_2`, `NOTION_PAGE_ID_3`... 순서로 환경 변수를 찾아서 모든 페이지를 로드합니다.

예시:
```bash
# .env 파일에 추가
NOTION_PAGE_ID_1=page_id_1_here
NOTION_PAGE_ID_2=page_id_2_here
NOTION_PAGE_ID_3=page_id_3_here
NOTION_PAGE_ID_4=page_id_4_here
# ... 계속 추가 가능
```

## 검색 방법

### 1. FAISS 텍스트 검색

FAISS 인덱스에서 글자 기반 검색을 수행할 수 있습니다:

```python
from text_search_from_faiss import FAISSTextSearcher

# 검색기 초기화
searcher = FAISSTextSearcher("notion_faiss_index")

# 1. 정확한 텍스트 검색
results = searcher.search_by_text("YBIGTA", top_k=5)

# 2. 정규표현식 검색
results = searcher.search_by_regex(r"\b[A-Z]{2,}\b", top_k=5)

# 3. 키워드 검색
results = searcher.search_by_keywords(["프로젝트", "개발", "AI"], operator="OR")
```

### 2. Elasticsearch 변환

FAISS 인덱스를 Elasticsearch로 변환하여 더 강력한 검색 기능을 사용할 수 있습니다:

```python
from faiss_to_elasticsearch import FAISSToElasticsearchConverter

# 변환기 초기화
converter = FAISSToElasticsearchConverter("notion_faiss_index")

# Elasticsearch로 변환
converter.convert_to_elasticsearch()

# 검색 수행
results = converter.search_by_text("YBIGTA", top_k=5)
results = converter.search_by_vector(query_vector, top_k=5)
results = converter.hybrid_search("YBIGTA", query_vector, top_k=5)
```

### 3. Elasticsearch 설치 및 설정

```bash
# Docker로 Elasticsearch 실행
docker run -d \
  --name elasticsearch \
  -p 9200:9200 \
  -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  elasticsearch:8.17.0

# 또는 Docker Compose 사용
docker-compose up -d elasticsearch
```

## 주요 변경사항

- **Upstage API 임베딩**: OpenAI 대신 Upstage Solar 임베딩 모델 사용
- **직접 Notion API 호출**: NotionAPILoader 대신 직접 Notion API를 호출하여 페이지 내용 로드
- **전체 내용 로드**: 페이지의 모든 블록과 내용을 포함하여 로드 (제목, 단락, 목록, 인용구, 코드 등)
- **다중 페이지 지원**: 여러 페이지를 동시에 로드 가능
- **동적 페이지 ID**: 환경 변수에서 자동으로 모든 페이지 ID를 찾아서 로드
- **향상된 텍스트 추출**: 다양한 Notion 블록 타입 지원 (제목, 단락, 목록, 인용구, 코드 등)
- **재귀적 블록 탐색**: 모든 하위 블록을 자동으로 탐색하여 완전한 내용 추출
- **텍스트 기반 검색**: FAISS 인덱스에서 글자 기반 검색 지원
- **Elasticsearch 변환**: FAISS를 Elasticsearch로 변환하여 하이브리드 검색 지원