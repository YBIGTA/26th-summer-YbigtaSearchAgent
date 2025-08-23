@echo off
echo ========================================
echo YBIGTA Meeting AI - Docker 실행
echo ========================================
echo.

REM .env 파일 확인
if not exist .env (
    echo [WARNING] .env 파일이 없습니다!
    if exist .env.example (
        copy .env.example .env
        echo .env 파일이 생성되었습니다.
        echo API 키를 입력한 후 다시 실행하세요.
        pause
        exit /b 1
    ) else (
        echo .env.example 파일을 찾을 수 없습니다.
        pause
        exit /b 1
    )
)

echo Docker 컨테이너 빌드 및 실행 중...
echo.
echo ========================================
echo 서비스 주소:
echo   Backend API: http://localhost:8000
echo   API 문서: http://localhost:8000/docs
echo   Frontend: http://localhost:3000
echo ========================================
echo.

REM Docker Compose로 실행
docker-compose up --build

pause