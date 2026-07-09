from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from pathlib import Path
from uuid import uuid4
from app.core.config import get_db
from app.core.deps import can_manage_user_content, get_current_user, is_root_admin_user, require_admin_user, require_can_post_user
from app.schemas import PostResponse, PostCreate, PostUpdate, CommentResponse, CommentCreate, CommentUpdate, PostDetailResponse, PostTag
from app.repositories import LikeRepository, PostRepository, CommentRepository
from app.services import BadgeService, ExperienceService
from app.models import CommentLike, Post, PostLike, Comment, User

router = APIRouter(prefix="/api/forum", tags=["forum"])
PUBLISHER_DISPLAY_NAME = "管理员发布"
ALLOWED_POST_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_POST_IMAGE_SIZE = 5 * 1024 * 1024


def public_user_nickname(user: User | None) -> str:
    if not user:
        return "未知用户"
    if is_root_admin_user(user):
        return PUBLISHER_DISPLAY_NAME
    return user.nickname


def build_post_response(post: Post, user: User, comment_count: int, like_count: int = 0) -> dict:
    return {
        "id": post.id,
        "user_id": post.user_id,
        "title": post.title,
        "tag": post.tag or "野钓",
        "content": post.content,
        "image_urls": post.image_urls,
        "view_count": post.view_count or 0,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
        "user_nickname": public_user_nickname(user),
        "user_level": user.level,
        "user_title": user.title,
        "comment_count": comment_count,
        "like_count": like_count,
        "is_featured": post.is_featured,
    }

@router.get("/posts", response_model=List[PostResponse])
async def get_posts(skip: int = 0, limit: int = 10, tag: Optional[PostTag] = None, sort: Optional[str] = None, session: AsyncSession = Depends(get_db)):
    comment_count_expr = func.count(func.distinct(Comment.id))
    like_count_expr = func.count(func.distinct(PostLike.id))
    query = (
        select(Post, User, comment_count_expr.label("comment_count"), like_count_expr.label("like_count"))
        .join(User, User.id == Post.user_id)
        .outerjoin(Comment, Comment.post_id == Post.id)
        .outerjoin(PostLike, PostLike.post_id == Post.id)
        .group_by(Post.id, User.id)
    )
    if tag:
        query = query.where(Post.tag == tag)
    if sort == "hot":
        query = query.order_by(comment_count_expr.desc(), Post.created_at.desc())
    else:
        query = query.order_by(Post.created_at.desc())
    result = await session.execute(
        query
        .offset(skip)
        .limit(limit)
    )
    return [
        build_post_response(post, user, comment_count or 0, like_count or 0)
        for post, user, comment_count, like_count in result.all()
    ]

@router.get("/posts/search", response_model=List[PostResponse])
async def search_posts(keyword: str, skip: int = 0, limit: int = 10, tag: Optional[PostTag] = None, session: AsyncSession = Depends(get_db)):
    query = (
        select(Post, User, func.count(func.distinct(Comment.id)).label("comment_count"), func.count(func.distinct(PostLike.id)).label("like_count"))
        .join(User, User.id == Post.user_id)
        .outerjoin(Comment, Comment.post_id == Post.id)
        .outerjoin(PostLike, PostLike.post_id == Post.id)
        .where((Post.title.ilike(f"%{keyword}%")) | (Post.content.ilike(f"%{keyword}%")))
        .group_by(Post.id, User.id)
    )
    if tag:
        query = query.where(Post.tag == tag)
    result = await session.execute(
        query
        .order_by(Post.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return [
        build_post_response(post, user, comment_count or 0, like_count or 0)
        for post, user, comment_count, like_count in result.all()
    ]

@router.get("/posts/{post_id}", response_model=PostDetailResponse)
async def get_post_detail(post_id: int, session: AsyncSession = Depends(get_db)):
    from sqlalchemy.orm import selectinload
    result = await session.execute(
        select(Post)
        .where(Post.id == post_id)
        .options(
            selectinload(Post.user),
            selectinload(Post.likes),
            selectinload(Post.comments).selectinload(Comment.user),
            selectinload(Post.comments).selectinload(Comment.likes),
        )
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    post.view_count = int(post.view_count or 0) + 1
    await session.commit()
    await session.refresh(post)

    comments_data = []
    if post.comments:
        for comment in sorted(post.comments, key=lambda item: item.created_at):
            comments_data.append({
                "id": comment.id,
                "post_id": comment.post_id,
                "user_id": comment.user_id,
                "content": comment.content,
                "created_at": comment.created_at,
                "user_nickname": public_user_nickname(comment.user),
                "user_level": comment.user.level if comment.user else 1,
                "user_title": comment.user.title if comment.user else "初学钓手",
                "like_count": len(comment.likes or []),
            })

    return {
        "id": post.id,
        "user_id": post.user_id,
        "title": post.title,
        "tag": post.tag or "野钓",
        "content": post.content,
        "image_urls": post.image_urls,
        "view_count": post.view_count or 0,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
        "user_nickname": public_user_nickname(post.user),
        "user_level": post.user.level if post.user else 1,
        "user_title": post.user.title if post.user else "初学钓手",
        "like_count": len(post.likes or []),
        "is_featured": post.is_featured,
        "comments": comments_data
    }

@router.post("/posts", response_model=PostResponse)
async def create_post(post_data: PostCreate, user = Depends(require_can_post_user), session: AsyncSession = Depends(get_db)):
    post = await PostRepository.create_post(session, user.id, post_data)
    await ExperienceService.award_post(session, user, post)
    await BadgeService.unlock_eligible_badges(session, user.id)
    return PostResponse(
        id=post.id,
        user_id=post.user_id,
        title=post.title,
        tag=post.tag or "野钓",
        content=post.content,
        image_urls=post.image_urls,
        view_count=post.view_count or 0,
        created_at=post.created_at,
        updated_at=post.updated_at,
        user_nickname=public_user_nickname(user),
        user_level=user.level,
        user_title=user.title,
        comment_count=0,
        like_count=0,
        is_featured=post.is_featured,
    )


@router.post("/images")
async def upload_forum_image(
    image: UploadFile = File(...),
    user = Depends(require_can_post_user),
):
    suffix = ALLOWED_POST_IMAGE_TYPES.get(image.content_type or "")
    if not suffix:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG, PNG, and WebP images are supported",
        )

    content = await image.read()
    if len(content) > MAX_POST_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image must be 5MB or smaller",
        )

    upload_dir = Path(__file__).resolve().parents[1] / "static" / "uploads" / "forum"
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{user.id}_{uuid4().hex}{suffix}"
    file_path = upload_dir / filename
    file_path.write_bytes(content)

    return {"url": f"/static/uploads/forum/{filename}"}

@router.put("/posts/{post_id}", response_model=PostResponse)
async def update_post(post_id: int, post_data: PostUpdate, user = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    post = await PostRepository.get_post_by_id(session, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if not can_manage_user_content(user, post.user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this post")

    updated_post = await PostRepository.update_post(session, post, post_data)
    comment_result = await session.execute(
        select(func.count(Comment.id)).where(Comment.post_id == updated_post.id)
    )
    comment_count = comment_result.scalar() or 0
    return PostResponse(
        id=updated_post.id,
        user_id=updated_post.user_id,
        title=updated_post.title,
        tag=updated_post.tag or "野钓",
        content=updated_post.content,
        image_urls=updated_post.image_urls,
        view_count=updated_post.view_count or 0,
        created_at=updated_post.created_at,
        updated_at=updated_post.updated_at,
        user_nickname=public_user_nickname(user),
        user_level=user.level,
        user_title=user.title,
        comment_count=comment_count,
        like_count=0,
        is_featured=updated_post.is_featured,
    )

@router.delete("/posts/{post_id}")
async def delete_post(post_id: int, user = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    post = await PostRepository.get_post_by_id(session, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if not can_manage_user_content(user, post.user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this post")

    await PostRepository.delete_post(session, post)
    return {"message": "Post deleted successfully"}

@router.post("/posts/{post_id}/comments", response_model=CommentResponse)
async def create_comment(post_id: int, comment_data: CommentCreate, user = Depends(require_can_post_user), session: AsyncSession = Depends(get_db)):
    post = await PostRepository.get_post_by_id(session, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    comment = await CommentRepository.create_comment(session, post_id, user.id, comment_data)
    await ExperienceService.award_comment(session, user, comment)
    return CommentResponse(
        id=comment.id,
        post_id=comment.post_id,
        user_id=comment.user_id,
        content=comment.content,
        created_at=comment.created_at,
        user_nickname=public_user_nickname(user),
        user_level=user.level,
        user_title=user.title,
        like_count=0,
    )

@router.put("/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(comment_id: int, comment_data: CommentUpdate, user = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    comment = await CommentRepository.get_comment_by_id(session, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if not can_manage_user_content(user, comment.user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this comment")

    updated_comment = await CommentRepository.update_comment(session, comment, comment_data)
    return CommentResponse(
        id=updated_comment.id,
        post_id=updated_comment.post_id,
        user_id=updated_comment.user_id,
        content=updated_comment.content,
        created_at=updated_comment.created_at,
        user_nickname=public_user_nickname(user),
        user_level=user.level,
        user_title=user.title,
        like_count=0,
    )

@router.delete("/comments/{comment_id}")
async def delete_comment(comment_id: int, user = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    comment = await CommentRepository.get_comment_by_id(session, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if not can_manage_user_content(user, comment.user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this comment")

    await CommentRepository.delete_comment(session, comment)
    return {"message": "Comment deleted successfully"}


@router.post("/posts/{post_id}/likes")
async def like_post(post_id: int, user = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    post = await PostRepository.get_post_by_id(session, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if post.user_id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot like your own post")

    like = await LikeRepository.create_post_like(session, post_id, user.id)
    if not like:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already liked")

    owner = await session.get(User, post.user_id)
    if owner:
        await ExperienceService.award_post_like(session, owner, post.id)
    else:
        await session.commit()
    return {"message": "Liked successfully"}


@router.post("/comments/{comment_id}/likes")
async def like_comment(comment_id: int, user = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    comment = await CommentRepository.get_comment_by_id(session, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if comment.user_id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot like your own comment")

    like = await LikeRepository.create_comment_like(session, comment_id, user.id)
    if not like:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already liked")

    owner = await session.get(User, comment.user_id)
    if owner:
        await ExperienceService.award_comment_like(session, owner, comment.id)
    else:
        await session.commit()
    return {"message": "Liked successfully"}


@router.post("/posts/{post_id}/feature", response_model=PostResponse)
async def feature_post(post_id: int, admin = Depends(require_admin_user), session: AsyncSession = Depends(get_db)):
    post = await PostRepository.get_post_by_id(session, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    owner = await session.get(User, post.user_id)
    was_featured = post.is_featured
    post.is_featured = True
    if owner and not was_featured:
        await ExperienceService.award_featured_post(session, owner, post.id)
    else:
        await session.commit()
    await session.refresh(post)

    comment_result = await session.execute(select(func.count(Comment.id)).where(Comment.post_id == post.id))
    like_result = await session.execute(select(func.count(PostLike.id)).where(PostLike.post_id == post.id))
    return PostResponse(
        id=post.id,
        user_id=post.user_id,
        title=post.title,
        tag=post.tag or "野钓",
        content=post.content,
        image_urls=post.image_urls,
        view_count=post.view_count or 0,
        created_at=post.created_at,
        updated_at=post.updated_at,
        user_nickname=public_user_nickname(owner) if owner else PUBLISHER_DISPLAY_NAME,
        user_level=owner.level if owner else 1,
        user_title=owner.title if owner else "初学钓手",
        comment_count=comment_result.scalar() or 0,
        like_count=like_result.scalar() or 0,
        is_featured=post.is_featured,
    )
