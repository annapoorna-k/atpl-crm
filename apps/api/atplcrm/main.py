from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from .api import router
from .admin import router as admin_router
from .data_tools import router as data_router
from .database import engine

app = FastAPI(title="ATPLCRM API", version="0.4.1", docs_url="/api/docs", openapi_url="/api/openapi.json", redoc_url=None)
app.include_router(router)
app.include_router(admin_router)
app.include_router(data_router)


@app.exception_handler(RequestValidationError)
async def validation_error(_request: Request, exc: RequestValidationError):
    fields: dict[str, str] = {}
    for error in exc.errors():
        name = ".".join(str(part) for part in error["loc"] if part != "body") or "request"
        fields[name] = error["msg"]
    return JSONResponse(status_code=422, content=fields)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Cache-Control"] = "no-store" if request.url.path.startswith("/api/") else response.headers.get("Cache-Control", "")
    return response


@app.get("/api/health/", include_in_schema=False)
def health():
    with Session(engine) as db:
        db.execute(text("SELECT 1"))
    return {"status": "ok", "application": "ATPLCRM", "framework": "FastAPI"}
