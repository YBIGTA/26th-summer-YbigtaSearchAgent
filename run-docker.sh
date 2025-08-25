#!/bin/bash
# YBIGTA Meeting AI - Docker 실행 스크립트

echo "🚀 YBIGTA Meeting AI - Docker로 실행"
echo "=================================="

# .env 파일 확인
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ .env 파일 생성됨"
        echo "📝 .env 파일을 편집하고 API 키를 입력한 후 다시 실행하세요."
        exit 1
    else
        echo "❌ .env.example 파일을 찾을 수 없습니다."
        exit 1
    fi
fi

echo "🔧 Docker 컨테이너 빌드 및 실행 중..."
echo ""
echo "📍 서비스 주소:"
echo "   Backend API: http://localhost:8000"
echo "   API 문서: http://localhost:8000/docs" 
echo "   Frontend: http://localhost:3000"
echo ""
echo "⏹️  중지하려면: Ctrl+C 또는 docker-compose down"
echo ""

# Docker Compose로 실행
docker-compose up --build
#!/bin/bash
# YBIGTA Meeting AI - Docker 실행 스크립트

echo "🚀 YBIGTA Meeting AI - Docker로 실행"
echo "=================================="

# .env 파일 확인
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ .env 파일 생성됨"
        echo "📝 .env 파일을 편집하고 API 키를 입력한 후 다시 실행하세요."
        exit 1
    else
        echo "❌ .env.example 파일을 찾을 수 없습니다."
        exit 1
    fi
fi

echo "🔧 Docker 컨테이너 빌드 및 실행 중..."
echo ""
echo "📍 서비스 주소:"
echo "   Backend API: http://localhost:8000"
echo "   API 문서: http://localhost:8000/docs" 
echo "   Frontend: http://localhost:3000"
echo ""
echo "⏹️  중지하려면: Ctrl+C 또는 docker-compose down"
echo ""

# Docker Compose로 실행
docker-compose up --build