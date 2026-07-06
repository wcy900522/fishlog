from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Literal, Optional, List

COMMON_WEAK_PASSWORDS = {
    "123456",
    "12345678",
    "123456789",
    "11111111",
    "00000000",
    "password",
    "password123",
    "admin123",
    "qwerty123",
}


def is_sequential_password(password: str) -> bool:
    lowered = password.lower()
    sequences = ("0123456789", "9876543210", "abcdefghijklmnopqrstuvwxyz", "zyxwvutsrqponmlkjihgfedcba")
    return any(lowered in sequence for sequence in sequences)

WaterType = Literal["river", "lake", "reservoir", "sea", "pond", "other"]
PostTag = Literal["海钓", "路亚", "台钓", "飞钓", "黑坑", "野钓"]

# User Schemas
class UserRegister(BaseModel):
    nickname: str = Field(min_length=1, max_length=50)
    phone: str = Field(pattern=r"^1[3-9]\d{9}$")
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, password: str) -> str:
        lowered = password.lower()
        if lowered in COMMON_WEAK_PASSWORDS:
            raise ValueError("密码过于简单，请使用至少8位且包含字母和数字的密码")
        if password.isdigit() or password.isalpha():
            raise ValueError("密码必须同时包含字母和数字")
        if not any(char.isalpha() for char in password) or not any(char.isdigit() for char in password):
            raise ValueError("密码必须同时包含字母和数字")
        if len(set(password)) == 1 or is_sequential_password(password):
            raise ValueError("密码不能使用连续或重复字符")
        return password

class UserLogin(BaseModel):
    phone: str = Field(pattern=r"^1[3-9]\d{9}$")
    password: str = Field(min_length=1, max_length=128)

class UserResponse(BaseModel):
    id: int
    nickname: str
    avatar: Optional[str] = None
    phone: Optional[str] = None
    wechat_openid: Optional[str] = None
    wechat_unionid: Optional[str] = None
    is_admin: bool = False
    is_disabled: bool = False
    can_post: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class AdminUserResponse(UserResponse):
    post_count: int = 0
    comment_count: int = 0
    spot_count: int = 0
    log_count: int = 0


class AdminUserListResponse(BaseModel):
    total: int
    users: List[AdminUserResponse]


class AdminUserUpdate(BaseModel):
    is_admin: Optional[bool] = None
    is_disabled: Optional[bool] = None
    can_post: Optional[bool] = None


class AdminPasswordReset(BaseModel):
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, password: str) -> str:
        return UserRegister.validate_password_complexity(password)

# FishingSpot Schemas
class FishingSpotCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    province: Optional[str] = Field(default=None, max_length=50)
    city: Optional[str] = Field(default=None, max_length=50)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    water_type: Optional[WaterType] = None
    description: Optional[str] = Field(default=None, max_length=2000)

class FishingSpotResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    name: str
    province: Optional[str] = None
    city: Optional[str] = None
    latitude: float
    longitude: float
    water_type: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    user_nickname: Optional[str] = None

    class Config:
        from_attributes = True

# CatchLog Schemas
class CatchLogCreate(BaseModel):
    spot_id: int = Field(gt=0)
    fishing_at: datetime
    duration: int = Field(gt=0, le=1440)
    bait: Optional[str] = Field(default=None, max_length=100)
    species: Optional[str] = Field(default=None, max_length=100)
    quantity: Optional[int] = Field(default=None, ge=0, le=10000)
    note: Optional[str] = Field(default=None, max_length=5000)

class CatchLogUpdate(BaseModel):
    fishing_at: Optional[datetime] = None
    duration: Optional[int] = Field(default=None, gt=0, le=1440)
    bait: Optional[str] = Field(default=None, max_length=100)
    species: Optional[str] = Field(default=None, max_length=100)
    quantity: Optional[int] = Field(default=None, ge=0, le=10000)
    note: Optional[str] = Field(default=None, max_length=5000)

class CatchLogResponse(BaseModel):
    id: int
    user_id: int
    spot_id: int
    fishing_at: datetime
    duration: int
    bait: Optional[str] = None
    species: Optional[str] = None
    quantity: Optional[int] = None
    note: Optional[str] = None
    temperature: Optional[float] = None
    pressure: Optional[float] = None
    wind_speed: Optional[float] = None
    weather_snapshot: Optional[dict] = None
    created_at: datetime
    user_nickname: Optional[str] = None

    class Config:
        from_attributes = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    phone: Optional[str] = None

# Post Schemas
class CommentResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    content: str
    created_at: datetime
    user_nickname: Optional[str] = None

    class Config:
        from_attributes = True

class PostCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    tag: PostTag = "野钓"
    content: str = Field(min_length=2, max_length=20000)

class PostUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=255)
    tag: Optional[PostTag] = None
    content: Optional[str] = Field(default=None, min_length=2, max_length=20000)

class PostResponse(BaseModel):
    id: int
    user_id: int
    title: str
    tag: str = "野钓"
    content: str
    created_at: datetime
    updated_at: datetime
    user_nickname: Optional[str] = None
    comment_count: int = 0

    class Config:
        from_attributes = True

class PostDetailResponse(BaseModel):
    id: int
    user_id: int
    title: str
    tag: str = "野钓"
    content: str
    created_at: datetime
    updated_at: datetime
    user_nickname: Optional[str] = None
    comments: List[CommentResponse] = []

    class Config:
        from_attributes = True

class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)

class CommentUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
