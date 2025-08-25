# YBIGTA Meeting AI 시작 가이드

## 🚀 빠른 시작

### Windows
```bash
start.bat
```

### Mac/Linux
```bash
./start.sh
```

---

## 📋 사전 준비사항

### 1. Python 환경 설정
- Python 3.8 이상 필요
- 가상환경 생성 (아직 없는 경우):
  ```bash
  python -m venv myenv
  ```

### 2. Node.js 설치
- Node.js 16.x 이상 필요
- https://nodejs.org 에서 다운로드

### 3. 의존성 설치
```bash
# Python 패키지
pip install -r requirements.txt

# Node 패키지
npm install
```

### 4. 환경 변수 설정
1. `.env.example` 파일을 `.env`로 복사
2. 필요한 API 키 입력:
   - **OpenAI API Key**: GPT 모델 사용
   - **Upstage API Keys**: 임베딩 (최대 8개)
   - **Notion API Key**: Notion 페이지 연동
   - **GitHub Token**: GitHub 리포 접근
   - **ReturnZero Keys**: STT 서비스

### 5. Google Drive 설정 (선택사항)
1. Google Cloud Console에서 서비스 계정 생성
2. Drive API 활성화
3. 인증 JSON 파일을 `gdrive-credentials.json`으로 저장

---

## 🔧 수동 실행 방법

### 1. 백엔드 서버 실행
```bash
# 가상환경 활성화
# Windows
myenv\Scripts\activate

# Mac/Linux
source myenv/bin/activate

# 백엔드 실행
cd src/backend
python main.py
```

### 2. 프론트엔드 실행 (새 터미널)
```bash
npm start
```

### 3. Electron 앱 실행 (새 터미널)
```bash
npm run electron
```

---

## 🌐 접속 정보

- **백엔드 API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **프론트엔드**: http://localhost:3000
- **데스크톱 앱**: Electron 창

---

## ⚙️ 설정 페이지에서 할 일

1. **API 키 입력**
   - OpenAI API 키 (필수)
   - Upstage API 키 (최소 1개)
   - 기타 서비스 API 키

2. **STT 엔진 선택**
   - Whisper (OpenAI)
   - ReturnZero (한국어 특화)

3. **동기화 설정**
   - Notion 페이지 ID 입력
   - 동기화 주기 확인

---

## 🔍 문제 해결

### "모듈을 찾을 수 없습니다" 에러
```bash
pip install -r requirements.txt
npm install
```

### 포트 충돌 (8000 또는 3000)
- 다른 프로그램이 포트를 사용 중인지 확인
- `netstat -an | findstr :8000` (Windows)
- `lsof -i :8000` (Mac/Linux)

### API 키 오류
- `.env` 파일의 API 키가 올바른지 확인
- 설정 페이지에서 API 키 테스트 실행

### ChromaDB 초기화 오류
- `data/indexes/chroma_db` 폴더 삭제 후 재시작

---

## 📁 폴더 구조

```
26th-summer-YbigtaSearchAgent/
├── src/
│   ├── backend/        # FastAPI 백엔드
│   └── (React 소스)    # React 프론트엔드
├── electron/           # Electron 메인 프로세스
├── data/              # 데이터 저장소
│   ├── indexes/       # ChromaDB 인덱스
│   └── audio/         # 업로드된 오디오 파일
├── .env               # 환경 변수 (생성 필요)
├── requirements.txt   # Python 의존성
└── package.json       # Node.js 의존성
```

---

## 🆘 추가 도움말

문제가 지속되면:
1. 모든 터미널 창 종료
2. 가상환경 재활성화
3. `start.bat` 또는 `./start.sh` 다시 실행

개발 모드에서 실행하려면:
```bash
# 백엔드 (자동 리로드)
cd src/backend
uvicorn main:app --reload

# 프론트엔드 (핫 리로드)
npm start

# Electron (개발 모드)
npm run electron-dev
```