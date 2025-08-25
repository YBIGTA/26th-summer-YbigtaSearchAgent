# 🔧 문제 해결 가이드

## 현재 발생한 문제들

### 1. `'react-scripts'은(는) 내부 또는 외부 명령이 아닙니다`

**원인**: Node.js 의존성이 설치되지 않음

**해결방법**:
```powershell
npm install
```

### 2. `ModuleNotFoundError: No module named 'fastapi'`

**원인**: Python 의존성이 가상환경에 설치되지 않음

**해결방법**:
```powershell
# 가상환경 활성화 확인
myenv\Scripts\Activate.ps1

# Python 의존성 설치
pip install -r requirements.txt
```

---

## 🚀 완전 초기화 및 재설정

### **방법 1: 자동 설정 스크립트 사용**
```powershell
# PowerShell 실행 정책 설정 (한 번만)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 자동 설정 실행
.\setup.ps1
```

### **방법 2: 수동 설정**

#### Step 1: 기존 환경 정리
```powershell
# 기존 가상환경 삭제 (문제가 있는 경우)
Remove-Item -Recurse -Force myenv -ErrorAction SilentlyContinue

# Node modules 삭제 (문제가 있는 경우)
Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue
```

#### Step 2: 새로 설치
```powershell
# Python 가상환경 생성
python -m venv myenv

# 가상환경 활성화
myenv\Scripts\Activate.ps1

# Python 의존성 설치
pip install --upgrade pip
pip install -r requirements.txt

# Node.js 의존성 설치
npm install
```

#### Step 3: 환경변수 설정
```powershell
# .env 파일 생성
Copy-Item .env.example .env

# .env 파일 편집 (메모장으로 열기)
notepad .env
```

---

## 📋 필수 확인사항

### Python 설치 확인
```powershell
python --version  # Python 3.8+ 필요
where python       # 설치 경로 확인
```

### Node.js 설치 확인  
```powershell
node --version     # Node.js 16+ 필요
npm --version      # npm 버전 확인
```

### 가상환경 활성화 확인
```powershell
# 활성화 후 프롬프트 앞에 (myenv) 표시되어야 함
myenv\Scripts\Activate.ps1
```

---

## 🔍 일반적인 문제들

### 1. **PowerShell 실행 정책 오류**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 2. **포트 충돌 (8000, 3000 포트)**
```powershell
# 사용 중인 프로세스 확인
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# 프로세스 종료 (PID 확인 후)
taskkill /PID [PID번호] /F
```

### 3. **인터넷 연결 문제로 설치 실패**
```powershell
# 프록시 설정 (회사 네트워크인 경우)
npm config set proxy http://proxy-server:port
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### 4. **권한 문제**
```powershell
# PowerShell을 관리자 권한으로 실행
# 또는 사용자 디렉토리에서 실행
```

---

## 🎯 단계별 실행 순서

1. **PowerShell을 관리자 권한으로 실행**
2. **프로젝트 폴더로 이동**: `cd "C:\Users\jason\Desktop\코딩\26th-summer-YbigtaSearchAgent"`
3. **실행 정책 설정**: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
4. **자동 설정 실행**: `.\setup.ps1`
5. **.env 파일 편집**: API 키 추가
6. **프로그램 실행**: `.\start.ps1`

---

## ❌ 여전히 안 될 때

### 최후의 수단: 수동 실행
```powershell
# 터미널 1: 백엔드 실행
myenv\Scripts\Activate.ps1
cd src\backend
python main.py

# 터미널 2: 프론트엔드 실행 (새 PowerShell 창)
npm start

# 터미널 3: Electron 실행 (새 PowerShell 창)
npm run electron
```

이 방법으로도 안 되면 Python이나 Node.js 재설치가 필요할 수 있습니다.