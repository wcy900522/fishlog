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

WaterType = Literal["river", "lake", "reservoir", "sea", "pond", "pay_pond", "other"]
PostTag = Literal["海钓", "路亚", "台钓", "飞钓", "黑坑", "野钓", "技术分享", "装备评测", "钓点攻略", "秀出鱼获"]
BaitType = Literal["植物饵", "商品饵", "软饵", "硬饵", "活饵"]
EquipmentType = Literal["鱼竿", "鱼轮", "鱼线", "鱼钩", "路亚饵", "其他"]

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


class UserProfileUpdate(BaseModel):
    nickname: str = Field(min_length=1, max_length=50)

    @field_validator("nickname")
    @classmethod
    def trim_nickname(cls, nickname: str) -> str:
        return nickname.strip()


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
    xp: int = 0
    level: int = 1
    title: str = "初学钓手"
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


class BadgeResponse(BaseModel):
    code: str
    name: str
    icon: str
    description: str


class UserLevelResponse(BaseModel):
    level: int
    title: str
    xp: int
    current_level_xp: int
    next_level_xp: Optional[int] = None
    xp_to_next: int
    progress_percent: int
    badges: List[BadgeResponse] = []
    benefits: List[str] = []


class XPLogResponse(BaseModel):
    id: int
    xp_delta: int
    reason: str
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LeaderboardUserResponse(BaseModel):
    user_id: int
    nickname: str
    level: int
    title: str
    xp: int
    score: int


class DashboardTopItem(BaseModel):
    name: str
    count: int


class DashboardLatestLog(BaseModel):
    id: int
    spot_id: int
    fishing_at: datetime
    duration: int
    bait: Optional[str] = None
    species: Optional[str] = None
    quantity: Optional[int] = None
    note: Optional[str] = None
    temperature: Optional[float] = None
    wind_speed: Optional[float] = None
    pressure: Optional[float] = None

    class Config:
        from_attributes = True


class UserDashboardResponse(BaseModel):
    trip_count: int
    total_quantity: int
    common_spots: List[DashboardTopItem] = []
    common_species: List[DashboardTopItem] = []
    common_baits: List[DashboardTopItem] = []
    latest_log: Optional[DashboardLatestLog] = None


class FishSpeciesCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    category: Optional[str] = Field(default=None, max_length=50)
    image_url: Optional[str] = Field(default=None, max_length=1000)
    description: Optional[str] = None
    common_methods: Optional[str] = None
    common_baits: Optional[str] = None


class FishSpeciesUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    category: Optional[str] = Field(default=None, max_length=50)
    image_url: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    common_methods: Optional[str] = None
    common_baits: Optional[str] = None


class FishSpeciesResponse(FishSpeciesCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class BaitCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    bait_type: BaitType
    brand: Optional[str] = Field(default=None, max_length=100)
    target_species: Optional[str] = None
    water_type: Optional[str] = Field(default=None, max_length=50)
    note: Optional[str] = None


class BaitUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    bait_type: Optional[BaitType] = None
    brand: Optional[str] = Field(default=None, max_length=100)
    target_species: Optional[str] = None
    water_type: Optional[str] = Field(default=None, max_length=50)
    note: Optional[str] = None


class BaitResponse(BaitCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class EquipmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    equipment_type: EquipmentType
    brand: Optional[str] = Field(default=None, max_length=100)
    model: Optional[str] = Field(default=None, max_length=100)
    parameters: Optional[str] = None
    purchased_at: Optional[datetime] = None
    note: Optional[str] = None


class EquipmentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    equipment_type: Optional[EquipmentType] = None
    brand: Optional[str] = Field(default=None, max_length=100)
    model: Optional[str] = Field(default=None, max_length=100)
    parameters: Optional[str] = None
    purchased_at: Optional[datetime] = None
    note: Optional[str] = None


class EquipmentResponse(EquipmentCreate):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# FishingSpot Schemas
class FishingSpotCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    province: Optional[str] = Field(default=None, max_length=50)
    city: Optional[str] = Field(default=None, max_length=50)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    water_type: Optional[WaterType] = None
    target_species: Optional[str] = Field(default=None, max_length=255)
    best_season: Optional[str] = Field(default=None, max_length=100)
    image_url: Optional[str] = Field(default=None, max_length=1000)
    tags: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("image_url")
    @classmethod
    def validate_spot_image_count(cls, image_url: Optional[str]) -> Optional[str]:
        if not image_url:
            return image_url
        urls = [url.strip() for url in image_url.split(",") if url.strip()]
        if len(urls) > 3:
            raise ValueError("钓点照片最多上传3张")
        return ",".join(urls)

    @field_validator("tags")
    @classmethod
    def validate_spot_tag_count(cls, tags: Optional[str]) -> Optional[str]:
        if not tags:
            return tags
        values = [tag.strip() for tag in tags.split(",") if tag.strip()]
        if len(values) > 2:
            raise ValueError("标签最多选择2个")
        return ",".join(values)

class FishingSpotResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    name: str
    province: Optional[str] = None
    city: Optional[str] = None
    latitude: float
    longitude: float
    water_type: Optional[str] = None
    target_species: Optional[str] = None
    best_season: Optional[str] = None
    image_url: Optional[str] = None
    tags: Optional[str] = None
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
    weight: Optional[float] = Field(default=None, ge=0, le=100000)
    tide: Optional[str] = Field(default=None, max_length=100)
    equipment: Optional[str] = Field(default=None, max_length=255)
    rod: Optional[str] = Field(default=None, max_length=100)
    line_group: Optional[str] = Field(default=None, max_length=100)
    photo_urls: Optional[List[str]] = Field(default=None, max_length=3)
    note: Optional[str] = Field(default=None, max_length=5000)

class CatchLogUpdate(BaseModel):
    spot_id: Optional[int] = Field(default=None, gt=0)
    fishing_at: Optional[datetime] = None
    duration: Optional[int] = Field(default=None, gt=0, le=1440)
    bait: Optional[str] = Field(default=None, max_length=100)
    species: Optional[str] = Field(default=None, max_length=100)
    quantity: Optional[int] = Field(default=None, ge=0, le=10000)
    weight: Optional[float] = Field(default=None, ge=0, le=100000)
    tide: Optional[str] = Field(default=None, max_length=100)
    equipment: Optional[str] = Field(default=None, max_length=255)
    rod: Optional[str] = Field(default=None, max_length=100)
    line_group: Optional[str] = Field(default=None, max_length=100)
    photo_urls: Optional[List[str]] = Field(default=None, max_length=3)
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
    weight: Optional[float] = None
    tide: Optional[str] = None
    equipment: Optional[str] = None
    rod: Optional[str] = None
    line_group: Optional[str] = None
    photo_urls: Optional[List[str]] = None
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
    user_level: int = 1
    user_title: str = "初学钓手"
    like_count: int = 0

    class Config:
        from_attributes = True

class PostCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    tag: PostTag = "野钓"
    content: str = Field(min_length=2, max_length=20000)
    image_urls: Optional[List[str]] = Field(default=None, max_length=5)

    @field_validator("image_urls")
    @classmethod
    def validate_image_count(cls, image_urls: Optional[List[str]]) -> Optional[List[str]]:
        if image_urls and len(image_urls) > 5:
            raise ValueError("帖子照片最多上传5张")
        return image_urls

    @field_validator("image_urls")
    @classmethod
    def validate_catch_showcase_image_count(cls, image_urls: Optional[List[str]], info) -> Optional[List[str]]:
        if info.data.get("tag") == "秀出鱼获" and image_urls and len(image_urls) > 3:
            raise ValueError("秀出鱼获最多上传3张鱼获照片")
        return image_urls

class PostUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=255)
    tag: Optional[PostTag] = None
    content: Optional[str] = Field(default=None, min_length=2, max_length=20000)
    image_urls: Optional[List[str]] = Field(default=None, max_length=5)

    @field_validator("image_urls")
    @classmethod
    def validate_image_count(cls, image_urls: Optional[List[str]]) -> Optional[List[str]]:
        if image_urls and len(image_urls) > 5:
            raise ValueError("帖子照片最多上传5张")
        return image_urls

    @field_validator("image_urls")
    @classmethod
    def validate_catch_showcase_image_count(cls, image_urls: Optional[List[str]], info) -> Optional[List[str]]:
        if info.data.get("tag") == "秀出鱼获" and image_urls and len(image_urls) > 3:
            raise ValueError("秀出鱼获最多上传3张鱼获照片")
        return image_urls

class PostResponse(BaseModel):
    id: int
    user_id: int
    title: str
    tag: str = "野钓"
    content: str
    image_urls: Optional[List[str]] = None
    view_count: int = 0
    created_at: datetime
    updated_at: datetime
    user_nickname: Optional[str] = None
    user_level: int = 1
    user_title: str = "初学钓手"
    comment_count: int = 0
    like_count: int = 0
    is_featured: bool = False

    class Config:
        from_attributes = True

class PostDetailResponse(BaseModel):
    id: int
    user_id: int
    title: str
    tag: str = "野钓"
    content: str
    image_urls: Optional[List[str]] = None
    view_count: int = 0
    created_at: datetime
    updated_at: datetime
    user_nickname: Optional[str] = None
    user_level: int = 1
    user_title: str = "初学钓手"
    like_count: int = 0
    is_featured: bool = False
    comments: List[CommentResponse] = []

    class Config:
        from_attributes = True

class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)

class CommentUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
