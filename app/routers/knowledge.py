"""Knowledge base CRUD endpoints with search."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.knowledge import KnowledgeArticle

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


class ArticleCreate(BaseModel):
    title: str
    content: str
    category: str | None = None
    tags: str | None = None


class ArticleUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    category: str | None = None
    tags: str | None = None


@router.get("")
async def list_articles(
    search: str | None = None,
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(KnowledgeArticle)

    if category:
        query = query.where(KnowledgeArticle.category == category)

    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(
                KnowledgeArticle.title.ilike(pattern),
                KnowledgeArticle.content.ilike(pattern),
                KnowledgeArticle.tags.ilike(pattern),
            )
        )

    query = query.order_by(desc(KnowledgeArticle.updated_at))
    result = await db.execute(query)
    articles = result.scalars().all()
    return [a.to_dict() for a in articles]


@router.post("", status_code=201)
async def create_article(data: ArticleCreate, db: AsyncSession = Depends(get_db)):
    article = KnowledgeArticle(**data.model_dump())
    db.add(article)
    await db.commit()
    await db.refresh(article)
    return article.to_dict()


@router.get("/{article_id}")
async def get_article(article_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(KnowledgeArticle).where(KnowledgeArticle.id == article_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article.to_dict()


@router.put("/{article_id}")
async def update_article(article_id: int, data: ArticleUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(KnowledgeArticle).where(KnowledgeArticle.id == article_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(article, key, value)

    article.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(article)
    return article.to_dict()


@router.delete("/{article_id}")
async def delete_article(article_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(KnowledgeArticle).where(KnowledgeArticle.id == article_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    await db.delete(article)
    await db.commit()
    return {"message": "Article deleted"}
