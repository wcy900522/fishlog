from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from app.core.config import get_db
from app.core.security import SecurityService
from app.schemas import PostResponse, PostCreate, PostUpdate, CommentResponse, CommentCreate, PostDetailResponse
from app.repositories import PostRepository, CommentRepository, UserRepository
from app.models import Post, Comment

router = APIRouter(prefix="/api/forum", tags=["forum"])

async def get_current_user(authorization: Optional[str] = Header(None), session: AsyncSession = Depends(get_db)):
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format")

    token = parts[1]
    payload = SecurityService.decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    phone = payload.get("sub")
    user = await UserRepository.get_user_by_phone(session, phone)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user

@router.get("/posts", response_model=List[PostResponse])
async def get_posts(skip: int = 0, limit: int = 10, session: AsyncSession = Depends(get_db)):
    from sqlalchemy.orm import selectinload
    result = await session.execute(
        select(Post)
        .options(selectinload(Post.user))
        .order_by(Post.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    posts = result.scalars().all()

    posts_data = []
    for post in posts:
        # 计算评论数
        comment_result = await session.execute(
            select(func.count(Comment.id)).where(Comment.post_id == post.id)
        )
        comment_count = comment_result.scalar() or 0

        posts_data.append({
            "id": post.id,
            "user_id": post.user_id,
            "title": post.title,
            "content": post.content,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "user_nickname": post.user.nickname if post.user else "未知用户",
            "comment_count": comment_count
        })
    return posts_data

@router.get("/posts/search", response_model=List[PostResponse])
async def search_posts(keyword: str, skip: int = 0, limit: int = 10, session: AsyncSession = Depends(get_db)):
    from sqlalchemy.orm import selectinload
    result = await session.execute(
        select(Post)
        .where((Post.title.ilike(f"%{keyword}%")) | (Post.content.ilike(f"%{keyword}%")))
        .options(selectinload(Post.user))
        .order_by(Post.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    posts = result.scalars().all()

    posts_data = []
    for post in posts:
        comment_result = await session.execute(
            select(func.count(Comment.id)).where(Comment.post_id == post.id)
        )
        comment_count = comment_result.scalar() or 0

        posts_data.append({
            "id": post.id,
            "user_id": post.user_id,
            "title": post.title,
            "content": post.content,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "user_nickname": post.user.nickname if post.user else "未知用户",
            "comment_count": comment_count
        })
    return posts_data

@router.get("/posts/{post_id}", response_model=PostDetailResponse)
async def get_post_detail(post_id: int, session: AsyncSession = Depends(get_db)):
    from sqlalchemy.orm import selectinload
    result = await session.execute(
        select(Post)
        .where(Post.id == post_id)
        .options(selectinload(Post.user), selectinload(Post.comments).selectinload(Comment.user))
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    comments_data = []
    if post.comments:
        for comment in post.comments:
            comments_data.append({
                "id": comment.id,
                "post_id": comment.post_id,
                "user_id": comment.user_id,
                "content": comment.content,
                "created_at": comment.created_at,
                "user_nickname": comment.user.nickname if comment.user else "未知用户"
            })

    return {
        "id": post.id,
        "user_id": post.user_id,
        "title": post.title,
        "content": post.content,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
        "user_nickname": post.user.nickname if post.user else "未知用户",
        "comments": comments_data
    }

@router.post("/posts", response_model=PostResponse)
async def create_post(post_data: PostCreate, user = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    post = await PostRepository.create_post(session, user.id, post_data)
    return PostResponse(
        id=post.id,
        user_id=post.user_id,
        title=post.title,
        content=post.content,
        created_at=post.created_at,
        updated_at=post.updated_at,
        user_nickname=user.nickname,
        comment_count=0
    )

@router.put("/posts/{post_id}", response_model=PostResponse)
async def update_post(post_id: int, post_data: PostUpdate, user = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    post = await PostRepository.get_post_by_id(session, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if post.user_id != user.id:
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
        content=updated_post.content,
        created_at=updated_post.created_at,
        updated_at=updated_post.updated_at,
        user_nickname=user.nickname,
        comment_count=comment_count
    )

@router.delete("/posts/{post_id}")
async def delete_post(post_id: int, user = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    post = await PostRepository.get_post_by_id(session, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if post.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this post")

    await PostRepository.delete_post(session, post)
    return {"message": "Post deleted successfully"}

@router.post("/posts/{post_id}/comments", response_model=CommentResponse)
async def create_comment(post_id: int, comment_data: CommentCreate, user = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    post = await PostRepository.get_post_by_id(session, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    comment = await CommentRepository.create_comment(session, post_id, user.id, comment_data)
    return CommentResponse(
        id=comment.id,
        post_id=comment.post_id,
        user_id=comment.user_id,
        content=comment.content,
        created_at=comment.created_at,
        user_nickname=user.nickname
    )

@router.delete("/comments/{comment_id}")
async def delete_comment(comment_id: int, user = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    comment = await CommentRepository.get_comment_by_id(session, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if comment.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this comment")

    await CommentRepository.delete_comment(session, comment)
    return {"message": "Comment deleted successfully"}

