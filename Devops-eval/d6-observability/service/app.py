import time

import structlog
from fastapi import FastAPI, Response
from metrics import REQUEST_COUNT, REQUEST_LATENCY, metrics_response
from starlette.middleware.base import BaseHTTPMiddleware

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)
log = structlog.get_logger()

app = FastAPI(title="DevOps Eval Observability Service")


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        path = request.url.path
        REQUEST_COUNT.labels(request.method, path, response.status_code).inc()
        REQUEST_LATENCY.labels(path).observe(duration)
        log.info(
            "request",
            method=request.method,
            path=path,
            status=response.status_code,
            duration_ms=round(duration * 1000, 2),
        )
        return response


app.add_middleware(MetricsMiddleware)


@app.get("/")
def root():
    return {"message": "devops-eval observability service"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    body, content_type = metrics_response()
    return Response(content=body, media_type=content_type)
