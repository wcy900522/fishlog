from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse
from app.api import admin, auth, spots, logs, forum
from app.core.config import Base, async_session, engine
from app.core.security import SecurityService
from app.models import User
from pathlib import Path
from sqlalchemy import inspect, select, text
import json

app = FastAPI(
    title="渔迹录 - 钓鱼记录工具",
    description="专业的钓鱼数据记录和管理平台",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(spots.router)
app.include_router(logs.router)
app.include_router(forum.router)
app.include_router(admin.router)

templates_dir = Path(__file__).parent / "templates"
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
templates = Jinja2Templates(directory=str(templates_dir))


def _users_table_columns(sync_connection) -> set[str]:
    inspector = inspect(sync_connection)
    if "users" not in inspector.get_table_names():
        return set()

    return {column["name"] for column in inspector.get_columns("users")}


@app.on_event("startup")
async def startup():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        user_columns = await connection.run_sync(_users_table_columns)
        if "is_admin" not in user_columns:
            await connection.execute(
                text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE")
            )
        if "is_disabled" not in user_columns:
            await connection.execute(
                text("ALTER TABLE users ADD COLUMN is_disabled BOOLEAN NOT NULL DEFAULT FALSE")
            )
        if "can_post" not in user_columns:
            await connection.execute(
                text("ALTER TABLE users ADD COLUMN can_post BOOLEAN NOT NULL DEFAULT TRUE")
            )

    async with async_session() as session:
        result = await session.execute(select(User).where(User.phone == "18610137321"))
        admin_user = result.scalar_one_or_none()
        if not admin_user:
            session.add(User(
                nickname="管理员",
                phone="18610137321",
                password_hash=SecurityService.get_password_hash("admin123"),
                is_admin=True
            ))
            await session.commit()
        elif not admin_user.is_admin:
            admin_user.is_admin = True
            await session.commit()

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    return templates.TemplateResponse("logs.html", {"request": request})

@app.get("/logs/create", response_class=HTMLResponse)
async def create_log_page(request: Request):
    return templates.TemplateResponse("create_log.html", {"request": request})

@app.get("/spots/{spot_id}", response_class=HTMLResponse)
async def spot_detail_page(request: Request, spot_id: int):
    return templates.TemplateResponse("spot_detail.html", {"request": request, "spot_id": spot_id})

@app.get("/logs/{log_id}/edit", response_class=HTMLResponse)
async def edit_log_page(request: Request, log_id: int):
    return templates.TemplateResponse("edit_log.html", {"request": request, "log_id": log_id})

@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/forum", response_class=HTMLResponse)
async def forum_page(request: Request):
    return templates.TemplateResponse("forum.html", {"request": request})

@app.get("/forum/create", response_class=HTMLResponse)
async def create_post_page(request: Request):
    return templates.TemplateResponse("create_post.html", {"request": request})

@app.get("/forum/posts/{post_id}", response_class=HTMLResponse)
async def post_detail_page(request: Request, post_id: int):
    return templates.TemplateResponse("post_detail.html", {"request": request, "post_id": post_id})

@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users_page(request: Request):
    return templates.TemplateResponse("admin_users.html", {"request": request})

@app.get("/spots", response_class=HTMLResponse)
async def spots_page(request: Request):
    return templates.TemplateResponse("spots.html", {"request": request})

@app.get("/api/provinces")
async def get_provinces():
    """获取全国省份和城市列表"""
    try:
        with open(Path(__file__).parent / "data" / "provinces.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
