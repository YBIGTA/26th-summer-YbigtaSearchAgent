# main.py
from fastapi import FastAPI, Request
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Histogram, Counter
import time

app = FastAPI()

# === 1) Instrumentator는 전역에서 'instrument'만 먼저 호출(미들웨어 추가는 앱 시작 전) ===
instrumentator = Instrumentator(
    should_instrument_requests_inprogress=True  # 요청 진행 중 gauge 노출
)
instrumentator.instrument(app)

# === 2) /metrics 엔드포인트 노출은 startup에서 한 번만 ===
@app.on_event("startup")
async def _startup():
    instrumentator.expose(app, endpoint="/metrics", include_in_schema=False)

# === 3) 사용자 정의 메트릭(기존 유지) ===
REQ_LAT = Histogram(
    "app_request_latency_seconds",
    "Latency",
    ["path", "method", "status_code"],
    buckets=(0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5)  # 필요 시 조정
)
REQ_CNT = Counter(
    "app_requests_total",
    "Requests",
    ["path", "method", "status_code"]
)

# === 4) 공통 미들웨어: 라벨과 관측치 기록 ===
@app.middleware("http")
async def _metrics(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    dur = time.perf_counter() - start

    path = request.url.path  # 라벨 폭발 방지를 원하면 '/items/{id}' 같은 경로는 정규화 필요
    method = request.method
    status = str(response.status_code)

    REQ_LAT.labels(path, method, status).observe(dur)
    REQ_CNT.labels(path, method, status).inc()
    return response

# === 5) 엔드포인트 예시 ===
@app.get("/")
def root():
    return {"ok": True}


# pip install prometheus_fastapi_instrumentator
# uvicorn prometheus_test:app --reload
