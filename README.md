# YBIGTA Meeting AI 🎙️🤖

스마트 회의 분석 데스크톱 애플리케이션 - 오디오 파일을 STT로 변환하고 AI 에이전트를 통해 회의록을 분석합니다.

## 🚀 빠른 시작 (Docker 사용 - 권장)

### 사전 요구사항
- Docker & Docker Compose 설치
- API 키 (OpenAI, Upstage 등)

### 1. 환경 설정 및 실행
```bash
# Windows
run-docker.bat

# Linux/Mac  
./run-docker.sh
```

### 2. API 키 설정
생성된 `.env` 파일을 편집하고 API 키를 입력:
```env
OPENAI_API_KEY=your_key_here
UPSTAGE_API_KEY1=your_key_here
NOTION_API_KEY=your_key_here  # (선택사항)
```

### 3. 접속
- **Backend API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs  
- **Frontend**: http://localhost:3000

## 🐳 Docker 장점
- ✅ **의존성 문제 해결**: UV 패키지 매니저로 빠르고 정확한 설치
- ✅ **일관된 환경**: 모든 플랫폼에서 동일한 실행 환경
- ✅ **쉬운 배포**: 한 번 빌드하면 어디서든 실행
- ✅ **격리된 환경**: 호스트 시스템에 영향 없음

## 🎯 주요 기능

### 1. 음성 회의 분석 파이프라인
- **음성 파일 업로드** → **STT 변환**(Whisper/ReturnZero) → **화자 분리**(pyannote) → **로컬 DB 저장**
- **Slack 스타일 UI**에서 검색/열람 및 타임라인 기반 화자별 발화 분석

### 2. 멀티에이전트 토론 시스템
- **아젠다 자동 추출** 및 논리 구조 분석
- **5가지 전문 에이전트**가 협력하여 심층 토론 수행:
  - 🔍 **AgendaMiner**: 핵심 아젠다 추출
  - ✅ **ClaimChecker**: 주장-근거 구조 분석
  - 🔄 **CounterArguer**: 반박 논리 제시
  - 📚 **EvidenceHunter**: 증거 수집 (RAG)
  - 📝 **Summarizer**: 결론 및 보고서 작성

### 3. 지식베이스 통합 (YBIGTA Module)
- **Notion** 페이지/데이터베이스 동기화
- **GitHub** 리포지토리 문서 크롤링
- **Google Drive** 문서 수집
- **하이브리드 검색**: FAISS 벡터 + 키워드 검색 (RRF)

### 4. 인사이트 보고서 생성
- **템플릿 기반** 보고서 (PDF/MD/HTML)
- **자동 인용** 및 근거 링크
- **액션 아이템** 추출 및 담당자 배정

## 🏗️ 시스템 아키텍처

```
[데스크톱 앱 (.exe)]
├─ [UI Layer] Electron + React + TypeScript
│  ├─ 왼쪽 사이드바
│  │  ├─ 회의록 목록 (최근/즐겨찾기/태그)
│  │  ├─ 검색 필터
│  │  └─ 개인 설정 메뉴
│  ├─ 메인 콘텐츠 영역
│  │  ├─ 회의록 뷰어/편집기
│  │  ├─ 타임라인 & 화자 분리 뷰
│  │  ├─ 멀티에이전트 토론 창
│  │  └─ 인사이트 보고서
│  └─ 상단 툴바 (업로드/내보내기/설정)
│
├─ [백엔드 프로세스] Python FastAPI (내장)
│  ├─ STT 엔진 (Whisper/ReturnZero)
│  ├─ 화자 분리 (pyannote)
│  ├─ 멀티에이전트 (LangGraph)
│  ├─ 하이브리드 RAG (FAISS + SQLite FTS)
│  └─ 보고서 생성
│
├─ [로컬 저장소]
│  ├─ SQLite: 메타데이터/회의록/설정
│  ├─ FAISS 인덱스: ./data/indexes/
│  ├─ 오디오 파일: ./data/audio/
│  └─ 캐시: ./data/cache/
│
└─ [외부 연동] (API 키 필요)
   ├─ Upstage/OpenAI (임베딩/LLM)
   ├─ Notion API (문서 동기화)
   ├─ GitHub API (리포지토리 크롤링)
   └─ Google Drive API (문서 수집)
```

## ⚙️ 환경 변수 설정

`.env` 파일에 다음 환경 변수들을 설정해야 합니다:

### 🤖 AI API 설정
```bash
# Upstage API (다중 키로 로드 밸런싱)
UPSTAGE_API_KEY1=your_upstage_api_key_1
UPSTAGE_API_KEY2=your_upstage_api_key_2
UPSTAGE_API_KEY3=your_upstage_api_key_3
# ... 최대 8개까지 설정 가능

# OpenAI API (Whisper STT용)
OPENAI_API_KEY=your_openai_api_key

# ReturnZero API (한국어 STT 특화)
RETURNZERO_API_KEY=your_returnzero_api_key
```

### 📝 지식베이스 연동
```bash
# Notion API 설정
NOTION_API_KEY=your_notion_integration_token
NOTION_PAGE_ID_1=your_first_notion_page_id
NOTION_PAGE_ID_2=your_second_notion_page_id
# 필요한 만큼 추가 가능

# GitHub 설정
GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token

# Google Drive 설정  
GDRIVE_FOLDER_ID=your_drive_folder_id
```

### 🗄️ 로컬 저장소 설정
```bash
# 애플리케이션 데이터 경로 (자동 생성)
WINDOWS: %APPDATA%/YBIGTA-Meeting-Analyzer/
MACOS: ~/Library/Application Support/YBIGTA-Meeting-Analyzer/
LINUX: ~/.config/YBIGTA-Meeting-Analyzer/

# 사용자 설정 파일
config.json: API 키 및 환경 설정 (암호화 저장)
settings.db: SQLite 데이터베이스
```

## 🚀 빠른 시작

### 방법 1: 설치 프로그램 사용 (권장)
```bash
# Windows
YBIGTA-Meeting-Analyzer-Setup-1.0.0.exe 실행

# macOS  
YBIGTA-Meeting-Analyzer-1.0.0.dmg 실행

# Linux
sudo dpkg -i ybigta-meeting-analyzer_1.0.0_amd64.deb
```

### 방법 2: 개발자 모드
```bash
# 저장소 클론
git clone https://github.com/your-repo/ybigta-meeting-analyzer.git
cd ybigta-meeting-analyzer

# 의존성 설치
pip install -r requirements.txt
npm install

# 개발 모드 실행
npm run dev

# 프로덕션 빌드
npm run build
npm run dist  # 실행 파일 생성
```

### 첫 실행 시
1. **개인 설정** 탭으로 이동 (왼쪽 사이드바 하단 ⚙️ 아이콘)
2. **API 키 입력**:
   - Upstage/OpenAI API 키 (필수)
   - Notion Integration Token (선택)
   - GitHub Personal Access Token (선택)
   - Google Service Account 키 업로드 (선택)
3. **저장** 후 앱 재시작

## 📁 프로젝트 구조

```
ybigta-meeting-analyzer/
├─ electron/                  # Electron 메인 프로세스
│  ├─ main.js                 # 메인 윈도우 관리
│  ├─ preload.js              # IPC 브릿지
│  └─ menu.js                 # 네이티브 메뉴
├─ src/                       # React 프론트엔드
│  ├─ components/
│  │  ├─ Layout/
│  │  │  ├─ Sidebar.tsx       # 왼쪽 사이드바
│  │  │  ├─ MainContent.tsx   # 메인 콘텐츠 영역
│  │  │  └─ Toolbar.tsx       # 상단 툴바
│  │  ├─ Meetings/
│  │  │  ├─ MeetingList.tsx   # 회의록 목록
│  │  │  ├─ MeetingViewer.tsx # 회의록 뷰어
│  │  │  └─ Timeline.tsx      # 타임라인 뷰
│  │  ├─ Agents/
│  │  │  ├─ AgentChat.tsx     # 에이전트 토론 UI
│  │  │  └─ AgentResults.tsx  # 분석 결과
│  │  └─ Settings/
│  │     ├─ ApiKeyManager.tsx # API 키 관리
│  │     └─ Preferences.tsx   # 환경 설정
│  ├─ pages/
│  │  ├─ Dashboard.tsx        # 메인 대시보드
│  │  ├─ MeetingDetail.tsx    # 회의 상세
│  │  └─ Settings.tsx         # 설정 페이지
│  └─ styles/
│     └─ slack-theme.css      # Slack 스타일 테마
├─ backend/                   # Python 백엔드 (내장)
│  ├─ api/                    # FastAPI 엔드포인트
│  ├─ core/                   # 핵심 비즈니스 로직
│  ├─ db/                     # SQLite 모델
│  ├─ stt/                    # STT 엔진
│  ├─ agents/                 # 멀티에이전트
│  └─ integrations/           # 외부 API 연동
├─ build/                     # 빌드 설정
│  ├─ icon.ico                # Windows 아이콘
│  ├─ icon.icns               # macOS 아이콘
│  └─ electron-builder.yml    # 빌드 설정
└─ data/                      # 런타임 데이터 (gitignore)
   ├─ db/                     # SQLite 데이터베이스
   ├─ indexes/                # FAISS 인덱스
   ├─ audio/                  # 오디오 파일
   └─ cache/                  # 임시 캐시
```

## 🧠 멀티에이전트 시스템

### 에이전트 역할

1. **🔍 AgendaMiner**: 회의 발화를 클러스터링하여 핵심 아젠다 추출
2. **✅ ClaimChecker**: 주장-근거-반례 구조 분석 및 논리 오류 탐지  
3. **🔄 CounterArguer**: 반대 논거 및 대안 시나리오 제시
4. **📚 EvidenceHunter**: RAG 기반 증거 수집 및 출처 검증
5. **📝 Summarizer**: 토론 결과 요약 및 보고서 생성

### 토론 프로세스
```
[증거 수집] → [주장/반박] → [합의/쟁점 도출] → [액션 아이템 추출]
```

## 🔍 하이브리드 검색 시스템

### 검색 방식
- **벡터 검색**: FAISS 기반 의미적 유사도
- **키워드 검색**: PostgreSQL FTS 기반 전문 검색
- **RRF 융합**: Reciprocal Rank Fusion으로 결과 병합
- **재순위화**: LLM 기반 문맥적 재순위화

### 사용 예시
```python
from backend.nlp.retriever import HybridRetriever

retriever = HybridRetriever()

# 하이브리드 검색
results = retriever.search(
    query="YBIGTA 프로젝트 관련 회의 내용",
    filters={
        "date_range": ("2024-01-01", "2024-12-31"),
        "sources": ["notion", "meetings"],
        "speakers": ["김철수", "이영희"]
    },
    top_k=10
)
```

## 💬 Slack 스타일 UI/UX

### 레이아웃 구성
```
┌─────────────────────────────────────────────────────────┐
│  🎙️ YBIGTA Meeting Analyzer  [－][□][✕]                 │
├─────────────────┬───────────────────────────────────────┤
│                 │                                       │
│  📁 회의록      │     [🔍 검색] [⬆️ 업로드] [📤 내보내기]  │
│  ├─ 📅 최근    │  ┌─────────────────────────────────┐  │
│  ├─ ⭐ 즐겨찾기 │  │  2024년 1월 정기회의           │  │
│  └─ 🏷️ 태그별  │  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━  │  │
│                 │  │  👤 김철수 (00:00-05:23)       │  │
│  🔍 스마트 검색  │  │  "이번 프로젝트의 목표는..."    │  │
│  ├─ 벡터 검색   │  │                               │  │
│  └─ 키워드 검색 │  │  👤 이영희 (05:24-08:15)       │  │
│                 │  │  "데이터 파이프라인 구성은..."  │  │
│  📊 분석 도구   │  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━  │  │
│  ├─ 아젠다 추출 │  │                               │  │
│  ├─ 에이전트 토론│  │  [아젠다] [토론] [보고서]      │  │
│  └─ 인사이트   │  └─────────────────────────────────┘  │
│                 │                                       │
│  ⚙️ 개인 설정   │     💡 Tip: 드래그&드롭으로 파일 업로드 │
│                 │                                       │
└─────────────────┴───────────────────────────────────────┘
```

### 주요 UI 특징
- **왼쪽 사이드바**: 
  - 회의록 목록 및 폴더 구조
  - 스마트 검색 도구
  - 분석 도구 바로가기
  - 하단 개인 설정 진입점

- **메인 콘텐츠 영역**:
  - 회의록 타임라인 뷰
  - 화자별 발화 블록 (Slack 메시지 스타일)
  - 하단 탭: 아젠다/토론/보고서

- **상단 툴바**:
  - 전역 검색
  - 파일 업로드 (드래그&드롭 지원)
  - 내보내기 (PDF/MD/DOCX)

### 개인 설정 페이지
```
┌─ 개인 설정 ────────────────────────────────────┐
│                                              │
│  🔑 API 키 관리                              │
│  ┌────────────────────────────────────────┐ │
│  │ Upstage API Key 1: ••••••••••••••••••• │ │
│  │ Upstage API Key 2: ••••••••••••••••••• │ │
│  │ + API 키 추가 (최대 8개)               │ │
│  └────────────────────────────────────────┘ │
│                                              │
│  📝 외부 서비스 연동                          │
│  ┌────────────────────────────────────────┐ │
│  │ ✅ Notion    [토큰 입력] [페이지 선택] │ │
│  │ ✅ GitHub    [토큰 입력] [리포 선택]   │ │
│  │ ☐ G Drive   [계정 연결] [폴더 선택]   │ │
│  └────────────────────────────────────────┘ │
│                                              │
│  🎙️ STT 엔진 설정                            │
│  ○ OpenAI Whisper  ● ReturnZero (한국어)    │
│                                              │
│  💾 저장  ↻ 초기화                           │
└──────────────────────────────────────────────┘
```

## 📝 보고서 템플릿

### 기본 템플릿
- **📋 회의 요약**: 참석자, 시간, 주요 결론
- **🎯 아젠다별 분석**: 토론 내용, 찬반 의견, 근거
- **✅ 액션 아이템**: 담당자, 기한, 우선순위  
- **📚 참고 자료**: 관련 문서, 이전 회의 링크

### 커스터마이징
```python
from backend.api.routers.reports import ReportGenerator

generator = ReportGenerator()

report = generator.generate(
    agenda_id=123,
    template="executive_summary",
    sections=["conclusions", "action_items", "evidence"],
    format="pdf"
)
```

## 🔐 보안 및 권한

### 데이터 보호
- **🔒 암호화**: API 키는 서버측 KMS로 암호화 저장
- **🛡️ 접근 제어**: 사용자/팀별 권한 관리
- **📋 감사 로그**: 모든 접근/수정 기록 추적
- **🎭 민감정보 마스킹**: 개인정보 자동 탐지/마스킹

### 개인정보 설정
- **⏰ 데이터 보관**: 사용자 정의 보관/삭제 정책
- **🔍 접근 범위**: 개인/팀/프로젝트별 데이터 분리
- **📊 사용량 제한**: API 호출/비용 상한 설정

## 📈 성능 최적화

### 병렬 처리
- **⚡ 비동기 STT**: 다중 엔진 동시 실행
- **🔄 API 로드 밸런싱**: 8개 Upstage API 키 순환
- **📦 청크 단위**: 블록/페이지 병렬 처리
- **⚙️ 워커 큐**: Celery 기반 백그라운드 작업

### 캐싱 전략
- **💾 Redis 캐시**: 검색 결과, 임베딩 캐시
- **📊 인덱스 최적화**: FAISS IVF+PQ, FTS 튜닝
- **🔄 증분 업데이트**: 변경분만 재처리

## 🚀 배포 및 배포

### 실행 파일 빌드
```bash
# Windows (.exe)
npm run dist:win
# Output: dist/YBIGTA-Meeting-Analyzer-Setup-1.0.0.exe

# macOS (.dmg)
npm run dist:mac
# Output: dist/YBIGTA-Meeting-Analyzer-1.0.0.dmg

# Linux (.AppImage/.deb)
npm run dist:linux
# Output: dist/ybigta-meeting-analyzer-1.0.0.AppImage
```

### 자동 업데이트 설정
```javascript
// electron-builder.yml
publish:
  - provider: github
    owner: YBIGTA
    repo: meeting-analyzer
    releaseType: release
```

### 로컬 모니터링
- **📊 리소스 사용량**: CPU/메모리 실시간 모니터링
- **🔍 로그**: 앱 내 로그 뷰어 (개발자 도구)
- **🚨 에러 추적**: Sentry 통합 (opt-in)
- **💰 API 사용량**: 일별/월별 토큰 사용량 대시보드

## 🧪 테스트 및 평가

### 자동화된 테스트
```bash
# 단위 테스트
pytest backend/tests/

# 통합 테스트  
pytest backend/tests/integration/

# 성능 테스트
pytest backend/tests/performance/
```

### 품질 지표
- **📊 STT 정확도**: WER (Word Error Rate) 측정
- **👥 화자 분리**: DER (Diarization Error Rate) 추적
- **🎯 검색 품질**: Precision@K, Recall@K 평가
- **💬 에이전트 성능**: 근거 일치율, 논리 일관성

## 🛣️ 개발 로드맵

### Phase 1 (완료) ✅
- 기본 STT 파이프라인
- Notion/GitHub/Drive 연동
- FAISS 벡터 검색
- 병렬 처리 최적화

### Phase 2 (진행 중) 🚧
- 화자 분리 시스템
- 멀티에이전트 프레임워크
- 하이브리드 검색
- Slack 스타일 데스크톱 UI

### Phase 3 (예정) 📅
- 보고서 생성 엔진
- 권한 관리 시스템
- 성능 모니터링
- 배포 자동화

### Phase 4 (예정) 🔮
- 실시간 스트리밍 STT
- 고급 분석 기능
- 모바일 앱
- 엔터프라이즈 기능

---

## 📞 지원 및 기여

### 문의사항
- **📧 이메일**: support@ybigta-meeting.com
- **💬 Slack**: #meeting-platform
- **📚 문서**: https://docs.ybigta-meeting.com

### 기여 가이드
1. Issue 생성 및 논의
2. Fork & 브랜치 생성
3. 코드 작성 및 테스트
4. Pull Request 제출
5. 코드 리뷰 및 머지

### 라이센스
MIT License - 자유로운 사용 및 수정 가능

### 시스템 요구사항
- **OS**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **RAM**: 최소 8GB (권장 16GB)
- **저장공간**: 최소 2GB
- **인터넷**: API 키 인증 및 외부 서비스 연동 시 필요