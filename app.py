from fastapi import FastAPI, Request, Depends, Form, HTTPException, Query
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse
from typing import List
from starlette.middleware.base import BaseHTTPMiddleware
import os
import logging
import time
from pydantic import BaseModel
from crud import get_university
from schemas import University
from database import SessionLocal, init_db

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

# Middleware для логирования всех запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Входящий запрос: {request.method} {request.url}")
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"Ответ отправлен: {response.status_code} за {process_time:.3f}с")
        return response
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {e}", exc_info=True)
        raise

# Инициализация базы данных при старте
@app.on_event("startup")
async def startup_event():
    try:
        init_db()
        logger.info("База данных инициализирована успешно")
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}", exc_info=True)

# Настройка статических файлов и шаблонов
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static")
templates_dir = os.path.join(BASE_DIR, "templates")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# Убрал глобальный обработчик - он может мешать нормальной работе FastAPI

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def search_universities(
    request: Request, 
    subject: List[str] = Query(None), 
    city: List[str] = Query(None), 
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Запрос получен: subject={subject}, city={city}")
        
        universities = get_university(db, subjects=subject, cities=city)
        logger.info(f"Найдено университетов: {len(universities)}")
        
        response = templates.TemplateResponse("search.html", {
            "request": request, 
            "universities": universities or []
        })
        return response
    except Exception as e:
        logger.error(f"Ошибка при получении университетов: {e}", exc_info=True)
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Полный traceback: {error_trace}")
        try:
            # Пытаемся вернуть страницу с ошибкой
            return templates.TemplateResponse("search.html", {
                "request": request, 
                "universities": [],
                "error": f"Ошибка при загрузке данных: {str(e)}"
            })
        except Exception as e2:
            # Если даже шаблон не может быть отрендерен, возвращаем простой текст
            logger.error(f"Критическая ошибка при рендеринге шаблона: {e2}", exc_info=True)
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse(f"Критическая ошибка: {str(e)}\n\nTraceback:\n{error_trace}", status_code=500)


