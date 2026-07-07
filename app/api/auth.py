from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from urllib.parse import urlencode
import json
import secrets
import httpx
from app.core.config import get_db, settings
from app.core.deps import get_current_user
from app.core.security import SecurityService
from app.schemas import UserRegister, UserLogin, UserResponse, Token
from app.repositories import UserRepository
from app.models import User
from app.core.nickname_validator import NicknameValidationError, NicknameValidator

router = APIRouter(prefix="/api/auth", tags=["auth"])

WECHAT_AUTH_URL = "https://open.weixin.qq.com/connect/qrconnect"
WECHAT_TOKEN_URL = "https://api.weixin.qq.com/sns/oauth2/access_token"
WECHAT_USERINFO_URL = "https://api.weixin.qq.com/sns/userinfo"


def create_user_token(user: User) -> str:
    subject = user.phone or f"wechat:{user.wechat_openid}"
    return SecurityService.create_access_token(
        data={"sub": subject, "uid": user.id},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )


def is_wechat_enabled() -> bool:
    return bool(settings.WECHAT_APP_ID and settings.WECHAT_APP_SECRET)


def get_valid_wechat_nickname(raw_nickname: str | None, fallback: str = "微信用户") -> str | None:
    nickname = raw_nickname or fallback
    try:
        NicknameValidator.validate(nickname)
        return nickname
    except NicknameValidationError:
        return None


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister, session: AsyncSession = Depends(get_db)):
    NicknameValidator.validate(user_data.nickname)

    existing_user = await UserRepository.get_user_by_phone(session, user_data.phone)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone already registered")

    user = await UserRepository.create_user(session, user_data)
    return user

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, session: AsyncSession = Depends(get_db)):
    user = await UserRepository.get_user_by_phone(session, user_data.phone)
    if not user or not SecurityService.verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if user.is_disabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="该账号已被禁用，请等待管理员审核")

    access_token = create_user_token(user)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_me(user = Depends(get_current_user)):
    return user


@router.get("/wechat/status")
async def wechat_status():
    return {"enabled": is_wechat_enabled()}


@router.get("/wechat/login")
async def wechat_login(request: Request):
    if not is_wechat_enabled():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="WeChat login is not configured")

    state = secrets.token_urlsafe(24)
    redirect_uri = settings.WECHAT_REDIRECT_URI or str(request.url_for("wechat_callback"))
    params = {
        "appid": settings.WECHAT_APP_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "snsapi_login",
        "state": state,
    }
    response = RedirectResponse(f"{WECHAT_AUTH_URL}?{urlencode(params)}#wechat_redirect")
    response.set_cookie("wechat_oauth_state", state, max_age=600, httponly=True, samesite="lax")
    return response


@router.get("/wechat/callback", name="wechat_callback")
async def wechat_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    session: AsyncSession = Depends(get_db),
):
    if error:
        return RedirectResponse(f"/login?wechat_error={error}")
    if not code or not state:
        return RedirectResponse("/login?wechat_error=missing_code")
    if state != request.cookies.get("wechat_oauth_state"):
        return RedirectResponse("/login?wechat_error=invalid_state")
    if not is_wechat_enabled():
        return RedirectResponse("/login?wechat_error=not_configured")

    async with httpx.AsyncClient(timeout=10.0) as client:
        token_response = await client.get(WECHAT_TOKEN_URL, params={
            "appid": settings.WECHAT_APP_ID,
            "secret": settings.WECHAT_APP_SECRET,
            "code": code,
            "grant_type": "authorization_code",
        })
        token_data = token_response.json()
        if token_data.get("errcode"):
            return RedirectResponse(f"/login?wechat_error={token_data.get('errcode')}")

        openid = token_data.get("openid")
        access_token = token_data.get("access_token")
        if not openid or not access_token:
            return RedirectResponse("/login?wechat_error=invalid_token")

        userinfo_response = await client.get(WECHAT_USERINFO_URL, params={
            "access_token": access_token,
            "openid": openid,
            "lang": "zh_CN",
        })
        userinfo = userinfo_response.json()
        if userinfo.get("errcode"):
            return RedirectResponse(f"/login?wechat_error={userinfo.get('errcode')}")

    user = await UserRepository.get_user_by_wechat_openid(session, openid)
    nickname = get_valid_wechat_nickname(userinfo.get("nickname"))
    if not user:
        user = User(
            nickname=nickname or "微信用户",
            avatar=userinfo.get("headimgurl"),
            phone=None,
            password_hash=SecurityService.get_password_hash(secrets.token_urlsafe(32)),
            wechat_openid=openid,
            wechat_unionid=userinfo.get("unionid") or token_data.get("unionid"),
        )
        session.add(user)
    else:
        if nickname:
            user.nickname = nickname
        user.avatar = userinfo.get("headimgurl") or user.avatar
        user.wechat_unionid = user.wechat_unionid or userinfo.get("unionid") or token_data.get("unionid")

    await session.commit()
    await session.refresh(user)

    access_token = create_user_token(user)
    html = f"""
    <!doctype html>
    <html lang="zh-CN">
    <head><meta charset="utf-8"><title>微信登录成功</title></head>
    <body>
        <script>
            localStorage.setItem('token', {json.dumps(access_token)});
            window.location.replace('/');
        </script>
    </body>
    </html>
    """
    response = HTMLResponse(html)
    response.delete_cookie("wechat_oauth_state")
    return response
