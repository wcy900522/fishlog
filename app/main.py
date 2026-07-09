from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, HTMLResponse
from app.api import admin, auth, baits, dashboard, equipment, species, spots, logs, records, forum, users, weather
from app.core.config import Base, async_session, engine
from app.core.security import SecurityService
from app.core.deps import DAILY_SUPER_ADMIN_NICKNAMES, ROOT_ADMIN_NICKNAMES, ROOT_ADMIN_PHONES
from app.models import Post, User
from app.core.nickname_validator import (
    NICKNAME_INVALID_MESSAGE,
    NicknameValidationError,
    NicknameValidator,
)
from app.services import BadgeService, LevelService
from pathlib import Path
from sqlalchemy import inspect, select, text, update
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
app.include_router(species.router)
app.include_router(baits.router)
app.include_router(equipment.router)
app.include_router(dashboard.router)
app.include_router(spots.router)
app.include_router(logs.router)
app.include_router(records.router)
app.include_router(forum.router)
app.include_router(admin.router)
app.include_router(users.router)
app.include_router(weather.router)


@app.exception_handler(NicknameValidationError)
async def nickname_validation_exception_handler(request: Request, exc: NicknameValidationError):
    return JSONResponse(
        status_code=400,
        content={"code": 400, "message": NICKNAME_INVALID_MESSAGE},
    )

templates_dir = Path(__file__).parent / "templates"
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
templates = Jinja2Templates(directory=str(templates_dir))


def _users_table_columns(sync_connection) -> set[str]:
    inspector = inspect(sync_connection)
    if "users" not in inspector.get_table_names():
        return set()

    return {column["name"] for column in inspector.get_columns("users")}


def _table_columns(sync_connection, table_name: str) -> set[str]:
    inspector = inspect(sync_connection)
    if table_name not in inspector.get_table_names():
        return set()

    return {column["name"] for column in inspector.get_columns(table_name)}


async def _sanitize_existing_user_nicknames() -> None:
    async with async_session() as session:
        result = await session.execute(select(User))
        updated_count = 0
        for user in result.scalars():
            if NicknameValidator.is_valid(user.nickname):
                continue
            user.nickname = NicknameValidator.fallback_nickname(user.id)
            updated_count += 1

        if updated_count:
            await session.commit()


async def _sync_existing_user_levels() -> None:
    async with async_session() as session:
        result = await session.execute(select(User))
        changed = False
        for user in result.scalars():
            before = (user.level, user.title)
            LevelService.apply_level_to_user(user)
            if (user.level, user.title) != before:
                changed = True

        if changed:
            await session.commit()


async def _sync_protected_admin_accounts() -> None:
    async with async_session() as session:
        changed = False
        for phone in ROOT_ADMIN_PHONES:
            result = await session.execute(select(User).where(User.phone == phone))
            admin_user = result.scalar_one_or_none()
            if not admin_user:
                session.add(User(
                    nickname="Demo用户",
                    phone=phone,
                    password_hash=SecurityService.get_password_hash("admin123"),
                    is_admin=True,
                    is_disabled=False,
                    can_post=True,
                ))
                changed = True
            else:
                if not admin_user.is_admin:
                    admin_user.is_admin = True
                    changed = True
                if admin_user.is_disabled:
                    admin_user.is_disabled = False
                    changed = True
                if not admin_user.can_post:
                    admin_user.can_post = True
                    changed = True

        result = await session.execute(
            select(User).where(User.nickname.in_(DAILY_SUPER_ADMIN_NICKNAMES))
        )
        daily_admin = result.scalar_one_or_none()
        if daily_admin:
            if not daily_admin.is_admin:
                daily_admin.is_admin = True
                changed = True
            if daily_admin.is_disabled:
                daily_admin.is_disabled = False
                changed = True
            if not daily_admin.can_post:
                daily_admin.can_post = True
                changed = True

            root_admin_ids = select(User.id).where(User.phone.in_(ROOT_ADMIN_PHONES))
            demo_result = await session.execute(
                select(User.id).where(
                    (User.nickname.in_(ROOT_ADMIN_NICKNAMES))
                    | (User.id.in_(root_admin_ids))
                )
            )
            demo_ids = [user_id for user_id in demo_result.scalars().all() if user_id != daily_admin.id]
            if demo_ids:
                await session.execute(
                    update(Post)
                    .where(Post.user_id.in_(demo_ids))
                    .values(user_id=daily_admin.id)
                )
                changed = True

        if changed:
            await session.commit()


@app.on_event("startup")
async def startup():
    NicknameValidator.load()

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
        if "xp" not in user_columns:
            await connection.execute(
                text("ALTER TABLE users ADD COLUMN xp INTEGER NOT NULL DEFAULT 0")
            )
        if "level" not in user_columns:
            await connection.execute(
                text("ALTER TABLE users ADD COLUMN level INTEGER NOT NULL DEFAULT 1")
            )
        if "title" not in user_columns:
            await connection.execute(
                text("ALTER TABLE users ADD COLUMN title VARCHAR(50) NOT NULL DEFAULT '初学钓手'")
            )
        post_columns = await connection.run_sync(_table_columns, "posts")
        if "is_featured" not in post_columns:
            await connection.execute(
                text("ALTER TABLE posts ADD COLUMN is_featured BOOLEAN NOT NULL DEFAULT FALSE")
            )

    await _sanitize_existing_user_nicknames()
    await _sync_existing_user_levels()
    await _sync_protected_admin_accounts()

    async with async_session() as session:
        await BadgeService.seed_badges(session)

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

@app.get("/records", response_class=HTMLResponse)
async def records_page(request: Request):
    return templates.TemplateResponse(
        "logs.html",
        {
            "request": request,
            "api_url": "/api/records",
            "create_url": "/logs/create",
            "edit_base_url": "/logs",
        },
    )

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

@app.get("/level", response_class=HTMLResponse)
async def level_page(request: Request):
    return templates.TemplateResponse("level.html", {"request": request})

@app.get("/leaderboards", response_class=HTMLResponse)
async def leaderboards_page(request: Request):
    return templates.TemplateResponse("leaderboards.html", {"request": request})

@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})

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

@app.get("/species", response_class=HTMLResponse)
async def species_page(request: Request):
    return templates.TemplateResponse("species.html", {"request": request})

@app.get("/baits", response_class=HTMLResponse)
async def baits_page(request: Request):
    return templates.TemplateResponse("baits.html", {"request": request})

@app.get("/equipment", response_class=HTMLResponse)
async def equipment_page(request: Request):
    return templates.TemplateResponse("equipment.html", {"request": request})

@app.get("/api/provinces")
async def get_provinces():
    """获取全国省份和城市列表"""
    try:
        with open(Path(__file__).parent / "data" / "provinces.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
