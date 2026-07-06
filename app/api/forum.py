from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from app.core.config import get_db
from app.core.deps import can_manage_user_content, get_current_user, require_can_post_user
from app.schemas import PostResponse, PostCreate, PostUpdate, CommentResponse, CommentCreate, CommentUpdate, PostDetailResponse, PostTag
from app.repositories import PostRepository, CommentRepository
from app.models import Post, Comment, User

router = APIRouter(prefix="/api/forum", tags=["forum"])
PUBLISHER_DISPLAY_NAME = "管理员发布"

def build_post_response(post: Post, user_nickname: str, comment_count: int) -> dict:
    return {
        "id": post.id,
        "user_id": post.user_id,
        "title": post.title,
        "tag": post.tag or "野钓",
        "content": post.content,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
        "user_nickname": user_nickname,
        "comment_count": comment_count,
    }

@router.get("/posts", response_model=List[PostResponse])
async def get_posts(skip: int = 0, limit: int = 10, tag: Optional[PostTag] = None, sort: Optional[str] = None, session: AsyncSession = Depends(get_db)):
    comment_count_expr = func.count(Comment.id)
    query = (
        select(Post, User.nickname, comment_count_expr.label("comment_count"))
        .join(User, User.id == Post.user_id)
        .outerjoin(Comment, Comment.post_id == Post.id)
        .group_by(Post.id, User.nickname)
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
        build_post_response(post, PUBLISHER_DISPLAY_NAME, comment_count or 0)
        for post, nickname, comment_count in result.all()
    ]

@router.get("/posts/search", response_model=List[PostResponse])
async def search_posts(keyword: str, skip: int = 0, limit: int = 10, tag: Optional[PostTag] = None, session: AsyncSession = Depends(get_db)):
    query = (
        select(Post, User.nickname, func.count(Comment.id).label("comment_count"))
        .join(User, User.id == Post.user_id)
        .outerjoin(Comment, Comment.post_id == Post.id)
        .where((Post.title.ilike(f"%{keyword}%")) | (Post.content.ilike(f"%{keyword}%")))
        .group_by(Post.id, User.nickname)
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
        build_post_response(post, PUBLISHER_DISPLAY_NAME, comment_count or 0)
        for post, nickname, comment_count in result.all()
    ]

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
        for comment in sorted(post.comments, key=lambda item: item.created_at):
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
        "tag": post.tag or "野钓",
        "content": post.content,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
        "user_nickname": PUBLISHER_DISPLAY_NAME,
        "comments": comments_data
    }

@router.post("/posts", response_model=PostResponse)
async def create_post(post_data: PostCreate, user = Depends(require_can_post_user), session: AsyncSession = Depends(get_db)):
    post = await PostRepository.create_post(session, user.id, post_data)
    return PostResponse(
        id=post.id,
        user_id=post.user_id,
        title=post.title,
        tag=post.tag or "野钓",
        content=post.content,
        created_at=post.created_at,
        updated_at=post.updated_at,
        user_nickname=PUBLISHER_DISPLAY_NAME,
        comment_count=0
    )

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
        created_at=updated_post.created_at,
        updated_at=updated_post.updated_at,
        user_nickname=PUBLISHER_DISPLAY_NAME,
        comment_count=comment_count
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
    return CommentResponse(
        id=comment.id,
        post_id=comment.post_id,
        user_id=comment.user_id,
        content=comment.content,
        created_at=comment.created_at,
        user_nickname=user.nickname
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
        user_nickname=user.nickname
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
