from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

# User Schemas
class UserRegister(BaseModel):
    nickname: str
    phone: str
    password: str

class UserLogin(BaseModel):
    phone: str
    password: str

class UserResponse(BaseModel):
    id: int
    nickname: str
    avatar: Optional[str] = None
    phone: str
    created_at: datetime

    class Config:
        from_attributes = True

# FishingSpot Schemas
class FishingSpotCreate(BaseModel):
    name: str
    province: Optional[str] = None
    city: Optional[str] = None
    latitude: float
    longitude: float
    water_type: Optional[str] = None
    description: Optional[str] = None

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
    spot_id: int
    fishing_at: datetime
    duration: int
    bait: Optional[str] = None
    species: Optional[str] = None
    quantity: Optional[int] = None
    note: Optional[str] = None

class CatchLogUpdate(BaseModel):
    fishing_at: Optional[datetime] = None
    duration: Optional[int] = None
    bait: Optional[str] = None
    species: Optional[str] = None
    quantity: Optional[int] = None
    note: Optional[str] = None

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
    title: str
    content: str

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class PostResponse(BaseModel):
    id: int
    user_id: int
    title: str
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
    content: str
    created_at: datetime
    updated_at: datetime
    user_nickname: Optional[str] = None
    comments: List[CommentResponse] = []

    class Config:
        from_attributes = True

class CommentCreate(BaseModel):
    content: str

