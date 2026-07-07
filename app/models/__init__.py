from sqlalchemy import Column, Integer, String, VARCHAR, DECIMAL, DateTime, Text, ForeignKey, func, JSON, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.config import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nickname = Column(VARCHAR(50), nullable=False)
    avatar = Column(VARCHAR(255), nullable=True)
    phone = Column(VARCHAR(20), nullable=True, unique=True)
    password_hash = Column(VARCHAR(255), nullable=False)
    wechat_openid = Column(VARCHAR(128), nullable=True, unique=True)
    wechat_unionid = Column(VARCHAR(128), nullable=True, unique=True)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_disabled = Column(Boolean, default=False, nullable=False)
    can_post = Column(Boolean, default=True, nullable=False)
    xp = Column(Integer, default=0, nullable=False)
    level = Column(Integer, default=1, nullable=False)
    title = Column(VARCHAR(50), default="初学钓手", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    catch_logs = relationship("CatchLog", back_populates="user", cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    fishing_spots = relationship("FishingSpot", back_populates="user", cascade="all, delete-orphan")
    xp_logs = relationship("XPLog", back_populates="user", cascade="all, delete-orphan")


class XPLog(Base):
    __tablename__ = "xp_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    xp_delta = Column(Integer, nullable=False)
    reason = Column(VARCHAR(100), nullable=False)
    target_type = Column(VARCHAR(50), nullable=True, index=True)
    target_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="xp_logs")

class FishingSpot(Base):
    __tablename__ = "fishing_spots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(VARCHAR(100), nullable=False)
    province = Column(VARCHAR(50), nullable=True)
    city = Column(VARCHAR(50), nullable=True)
    latitude = Column(DECIMAL(10, 6), nullable=False)
    longitude = Column(DECIMAL(10, 6), nullable=False)
    water_type = Column(VARCHAR(20), nullable=True)  # sea, river, lake, reservoir
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="fishing_spots")
    catch_logs = relationship("CatchLog", back_populates="spot", cascade="all, delete-orphan")

class CatchLog(Base):
    __tablename__ = "catch_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    spot_id = Column(Integer, ForeignKey("fishing_spots.id"), nullable=False)
    fishing_at = Column(DateTime, nullable=False)
    duration = Column(Integer, nullable=False)  # minutes
    bait = Column(VARCHAR(100), nullable=True)
    species = Column(VARCHAR(100), nullable=True)
    quantity = Column(Integer, nullable=True)
    note = Column(Text, nullable=True)
    temperature = Column(DECIMAL(5, 2), nullable=True)
    pressure = Column(DECIMAL(6, 2), nullable=True)
    wind_speed = Column(DECIMAL(5, 2), nullable=True)
    weather_snapshot = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="catch_logs")
    spot = relationship("FishingSpot", back_populates="catch_logs")

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(VARCHAR(255), nullable=False)
    tag = Column(VARCHAR(20), nullable=False, default="野钓")
    content = Column(Text, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("PostLike", back_populates="post", cascade="all, delete-orphan")

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    post = relationship("Post", back_populates="comments")
    user = relationship("User", back_populates="comments")
    likes = relationship("CommentLike", back_populates="comment", cascade="all, delete-orphan")


class PostLike(Base):
    __tablename__ = "post_likes"
    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_post_likes_post_user"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    post = relationship("Post", back_populates="likes")
    user = relationship("User")


class CommentLike(Base):
    __tablename__ = "comment_likes"
    __table_args__ = (UniqueConstraint("comment_id", "user_id", name="uq_comment_likes_comment_user"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    comment_id = Column(Integer, ForeignKey("comments.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    comment = relationship("Comment", back_populates="likes")
    user = relationship("User")


class Badge(Base):
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(VARCHAR(50), nullable=False, unique=True)
    name = Column(VARCHAR(50), nullable=False)
    icon = Column(VARCHAR(20), nullable=False)
    description = Column(VARCHAR(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class UserBadge(Base):
    __tablename__ = "user_badges"
    __table_args__ = (UniqueConstraint("user_id", "badge_code", name="uq_user_badges_user_code"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    badge_code = Column(VARCHAR(50), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User")
