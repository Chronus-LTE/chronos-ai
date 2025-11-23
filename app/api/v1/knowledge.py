"""
Knowledge Base API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.database import get_db
from app.models.conversation import KnowledgeBase
from app.models.user import User
from app.services.vector_db import VectorDBService

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])


# ============================================================================
# MODELS
# ============================================================================


class CreateKnowledgeRequest(BaseModel):
    """Request model for creating knowledge."""

    title: str
    content: str
    source: str | None = None
    category: str | None = None
    is_global: bool = False  # If True, available to all users


class UpdateKnowledgeRequest(BaseModel):
    """Request model for updating knowledge."""

    title: str | None = None
    content: str | None = None
    source: str | None = None
    category: str | None = None
    is_active: bool | None = None


class KnowledgeResponse(BaseModel):
    """Response model for knowledge."""

    id: int
    title: str
    content: str
    source: str | None = None
    category: str | None = None
    is_active: int
    created_at: str
    updated_at: str

    class Config:
        """Pydantic config."""

        from_attributes = True


class SearchKnowledgeResponse(BaseModel):
    """Response model for knowledge search."""

    id: int
    title: str
    content: str
    category: str | None = None
    score: float  # Similarity score


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_knowledge(
    request: CreateKnowledgeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new knowledge base entry."""
    try:
        # Create knowledge in DB
        knowledge = KnowledgeBase(
            user_id=None if request.is_global else current_user.id,
            title=request.title,
            content=request.content,
            source=request.source,
            category=request.category,
        )
        db.add(knowledge)
        await db.commit()
        await db.refresh(knowledge)

        # Add to vector DB
        vector_db = VectorDBService()
        vector_id = await vector_db.add_knowledge(
            knowledge_id=knowledge.id,
            title=request.title,
            content=request.content,
            user_id=knowledge.user_id,
            category=request.category,
        )

        knowledge.vector_id = vector_id
        await db.commit()

        return {
            "message": "Knowledge created successfully",
            "id": knowledge.id,
            "vector_id": vector_id,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create knowledge: {e!s}",
        ) from e


@router.get("/")
async def list_knowledge(
    category: str | None = None,
    include_global: bool = True,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List knowledge base entries."""
    try:
        # Build query
        conditions = []

        if include_global:
            # Include both user's and global knowledge
            conditions.append(
                (KnowledgeBase.user_id == current_user.id) | (KnowledgeBase.user_id.is_(None))
            )
        else:
            conditions.append(KnowledgeBase.user_id == current_user.id)

        if category:
            conditions.append(KnowledgeBase.category == category)

        conditions.append(KnowledgeBase.is_active == 1)

        # Execute query
        result = await db.execute(
            select(KnowledgeBase)
            .where(*conditions)
            .order_by(KnowledgeBase.updated_at.desc())
            .limit(limit)
        )
        knowledge_list = result.scalars().all()

        return {
            "knowledge": [KnowledgeResponse.from_orm(k) for k in knowledge_list],
            "count": len(knowledge_list),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list knowledge: {e!s}",
        ) from e


@router.get("/search")
async def search_knowledge(
    query: str,
    category: str | None = None,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
):
    """Search knowledge base using semantic search."""
    try:
        vector_db = VectorDBService()
        results = await vector_db.search_knowledge(
            query=query,
            user_id=current_user.id,
            category=category,
            limit=limit,
        )

        return {
            "results": [
                SearchKnowledgeResponse(
                    id=r["knowledge_id"],
                    title=r["title"],
                    content=r["content"],
                    category=r["category"],
                    score=r["score"],
                )
                for r in results
            ],
            "count": len(results),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search knowledge: {e!s}",
        ) from e


@router.get("/{knowledge_id}")
async def get_knowledge(
    knowledge_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific knowledge entry."""
    try:
        result = await db.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == knowledge_id,
                (KnowledgeBase.user_id == current_user.id) | (KnowledgeBase.user_id.is_(None)),
            )
        )
        knowledge = result.scalar_one_or_none()

        if not knowledge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge not found",
            )

        return KnowledgeResponse.from_orm(knowledge)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get knowledge: {e!s}",
        ) from e


@router.put("/{knowledge_id}")
async def update_knowledge(
    knowledge_id: int,
    request: UpdateKnowledgeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a knowledge entry."""
    try:
        result = await db.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == knowledge_id,
                KnowledgeBase.user_id == current_user.id,
            )
        )
        knowledge = result.scalar_one_or_none()

        if not knowledge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge not found or you don't have permission",
            )

        # Update fields
        if request.title is not None:
            knowledge.title = request.title
        if request.content is not None:
            knowledge.content = request.content
        if request.source is not None:
            knowledge.source = request.source
        if request.category is not None:
            knowledge.category = request.category
        if request.is_active is not None:
            knowledge.is_active = 1 if request.is_active else 0

        # Update vector DB if content changed
        if request.title is not None or request.content is not None:
            vector_db = VectorDBService()

            # Delete old vector
            if knowledge.vector_id:
                vector_db.delete_vector(
                    collection_name=vector_db.KNOWLEDGE_COLLECTION,
                    vector_id=knowledge.vector_id,
                )

            # Add new vector
            vector_id = await vector_db.add_knowledge(
                knowledge_id=knowledge.id,
                title=knowledge.title,
                content=knowledge.content,
                user_id=knowledge.user_id,
                category=knowledge.category,
            )
            knowledge.vector_id = vector_id

        await db.commit()

        return {"message": "Knowledge updated successfully", "id": knowledge_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update knowledge: {e!s}",
        ) from e


@router.delete("/{knowledge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge(
    knowledge_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a knowledge entry."""
    try:
        result = await db.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == knowledge_id,
                KnowledgeBase.user_id == current_user.id,
            )
        )
        knowledge = result.scalar_one_or_none()

        if not knowledge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge not found or you don't have permission",
            )

        # Delete from vector DB
        if knowledge.vector_id:
            vector_db = VectorDBService()
            vector_db.delete_vector(
                collection_name=vector_db.KNOWLEDGE_COLLECTION,
                vector_id=knowledge.vector_id,
            )

        # Delete from DB
        await db.delete(knowledge)
        await db.commit()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete knowledge: {e!s}",
        ) from e


@router.get("/categories/list")
async def list_categories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get list of all categories."""
    try:
        result = await db.execute(
            select(KnowledgeBase.category)
            .where(
                (KnowledgeBase.user_id == current_user.id) | (KnowledgeBase.user_id.is_(None)),
                KnowledgeBase.category.isnot(None),
            )
            .distinct()
        )
        categories = [row[0] for row in result.all()]

        return {"categories": categories, "count": len(categories)}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list categories: {e!s}",
        ) from e
