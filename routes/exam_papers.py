"""
Exam Papers API Routes
Handles exam paper uploads, processing, collections, and sharing.
"""

import os
import shutil
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from middleware.auth import get_current_user
from services.exam_paper_processor import get_exam_paper_processor
from services.user_collections import (
    get_legal_protection,
    get_sharing_service,
    get_user_collections_service,
)

router = APIRouter(prefix="/api/exam-papers", tags=["exam-papers"])


@router.post("/upload")
async def upload_exam_paper(
    file: UploadFile = File(...), current_user: dict = Depends(get_current_user)
):
    """Upload and process an exam paper"""
    try:
        # Validate file type
        allowed_extensions = [".pdf", ".jpg", ".jpeg", ".png", ".tiff"]
        file_extension = os.path.splitext(file.filename)[1].lower()

        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}",
            )

        # Validate file size (10MB limit)
        if file.size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400, detail="File size too large. Maximum 10MB allowed."
            )

        # Check upload permissions
        legal_protection = get_legal_protection()
        can_upload = await legal_protection.validate_upload_permissions(
            current_user["id"]
        )

        if not can_upload:
            raise HTTPException(
                status_code=429,
                detail="Upload limit reached. Please upgrade to Pro for unlimited uploads.",
            )

        # Create upload directory
        upload_dir = f"uploads/{current_user['id']}"
        os.makedirs(upload_dir, exist_ok=True)

        # Save file
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Log user agreement
        await legal_protection.log_upload_agreement(current_user["id"], file.filename)

        # Process the paper
        processor = get_exam_paper_processor()
        result = await processor.process_uploaded_paper(
            file_path=file_path,
            user_id=current_user["id"],
            file_name=file.filename,
            file_size=file.size,
        )

        if result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "message": "Exam paper processed successfully",
                    "paper_id": result["paper_id"],
                    "questions_count": result["questions_count"],
                    "preview_questions": result["questions"],
                },
            )
        else:
            raise HTTPException(
                status_code=500, detail=f"Processing failed: {result['error']}"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/papers")
async def get_user_papers(
    current_user: dict = Depends(get_current_user), limit: int = 20, offset: int = 0
):
    """Get user's uploaded papers"""
    try:
        from services.supabase import supabase_client

        result = (
            await supabase_client.table("uploaded_papers")
            .select("*")
            .eq("user_id", current_user["id"])
            .order("upload_date", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )

        return {
            "papers": result.data if result.data else [],
            "total": len(result.data) if result.data else 0,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch papers: {str(e)}")


@router.get("/papers/{paper_id}/questions")
async def get_paper_questions(
    paper_id: str,
    current_user: dict = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0,
):
    """Get questions from a specific paper"""
    try:
        from services.supabase import supabase_client

        # Verify ownership
        paper_result = (
            await supabase_client.table("uploaded_papers")
            .select("user_id")
            .eq("id", paper_id)
            .single()
            .execute()
        )

        if not paper_result.data or paper_result.data["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get questions
        result = (
            await supabase_client.table("extracted_questions")
            .select("*")
            .eq("paper_id", paper_id)
            .order("question_number", asc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )

        return {
            "questions": result.data if result.data else [],
            "total": len(result.data) if result.data else 0,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch questions: {str(e)}"
        )


@router.delete("/papers/{paper_id}")
async def delete_paper(paper_id: str, current_user: dict = Depends(get_current_user)):
    """Delete an uploaded paper and all its questions"""
    try:
        from services.supabase import supabase_client

        # Verify ownership
        paper_result = (
            await supabase_client.table("uploaded_papers")
            .select("user_id, file_path")
            .eq("id", paper_id)
            .single()
            .execute()
        )

        if not paper_result.data or paper_result.data["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Delete file from storage
        file_path = paper_result.data["file_path"]
        if os.path.exists(file_path):
            os.remove(file_path)

        # Delete questions
        await supabase_client.table("extracted_questions").delete().eq(
            "paper_id", paper_id
        ).execute()

        # Delete paper record
        await supabase_client.table("uploaded_papers").delete().eq(
            "id", paper_id
        ).execute()

        return {"message": "Paper deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete paper: {str(e)}")


# Collections endpoints
@router.post("/collections")
async def create_collection(
    name: str = Form(...),
    description: str = Form(""),
    is_public: bool = Form(False),
    current_user: dict = Depends(get_current_user),
):
    """Create a new question collection"""
    try:
        collections_service = get_user_collections_service()

        collection = await collections_service.create_collection(
            user_id=current_user["id"],
            name=name,
            description=description,
            is_public=is_public,
        )

        return {"message": "Collection created successfully", "collection": collection}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create collection: {str(e)}"
        )


@router.get("/collections")
async def get_user_collections(current_user: dict = Depends(get_current_user)):
    """Get user's collections"""
    try:
        collections_service = get_user_collections_service()
        collections = await collections_service.get_user_collections(current_user["id"])

        return {"collections": collections}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch collections: {str(e)}"
        )


@router.get("/collections/{collection_id}")
async def get_collection_details(
    collection_id: str, current_user: dict = Depends(get_current_user)
):
    """Get collection details and questions"""
    try:
        collections_service = get_user_collections_service()

        # Get collection details
        collection = await collections_service.get_collection_details(collection_id)

        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")

        # Check access permissions
        if not collection["is_public"] and collection["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get questions in collection
        questions = await collections_service.get_collection_questions(collection_id)

        return {"collection": collection, "questions": questions}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch collection: {str(e)}"
        )


@router.post("/collections/{collection_id}/questions")
async def add_questions_to_collection(
    collection_id: str,
    question_ids: list[str],
    current_user: dict = Depends(get_current_user),
):
    """Add questions to a collection"""
    try:
        collections_service = get_user_collections_service()

        # Verify ownership
        collection = await collections_service.get_collection_details(collection_id)
        if not collection or collection["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Add questions
        success = await collections_service.add_questions_to_collection(
            collection_id, question_ids
        )

        if success:
            return {"message": "Questions added to collection successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to add questions")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to add questions: {str(e)}"
        )


@router.delete("/collections/{collection_id}/questions")
async def remove_questions_from_collection(
    collection_id: str,
    question_ids: list[str],
    current_user: dict = Depends(get_current_user),
):
    """Remove questions from a collection"""
    try:
        collections_service = get_user_collections_service()

        # Verify ownership
        collection = await collections_service.get_collection_details(collection_id)
        if not collection or collection["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Remove questions
        success = await collections_service.remove_questions_from_collection(
            collection_id, question_ids
        )

        if success:
            return {"message": "Questions removed from collection successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to remove questions")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to remove questions: {str(e)}"
        )


@router.put("/collections/{collection_id}")
async def update_collection(
    collection_id: str,
    name: str | None = Form(None),
    description: str | None = Form(None),
    is_public: bool | None = Form(None),
    current_user: dict = Depends(get_current_user),
):
    """Update collection details"""
    try:
        collections_service = get_user_collections_service()

        # Verify ownership
        collection = await collections_service.get_collection_details(collection_id)
        if not collection or collection["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Prepare updates
        updates = {}
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description
        if is_public is not None:
            updates["is_public"] = is_public

        # Update collection
        success = await collections_service.update_collection(collection_id, updates)

        if success:
            return {"message": "Collection updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update collection")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update collection: {str(e)}"
        )


@router.delete("/collections/{collection_id}")
async def delete_collection(
    collection_id: str, current_user: dict = Depends(get_current_user)
):
    """Delete a collection"""
    try:
        collections_service = get_user_collections_service()

        # Verify ownership
        collection = await collections_service.get_collection_details(collection_id)
        if not collection or collection["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Delete collection
        success = await collections_service.delete_collection(collection_id)

        if success:
            return {"message": "Collection deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete collection")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete collection: {str(e)}"
        )


# Sharing endpoints
@router.post("/collections/{collection_id}/share")
async def create_share_link(
    collection_id: str,
    expires_at: str | None = Form(None),
    current_user: dict = Depends(get_current_user),
):
    """Create a shareable link for a collection"""
    try:
        sharing_service = get_sharing_service()
        collections_service = get_user_collections_service()

        # Verify ownership
        collection = await collections_service.get_collection_details(collection_id)
        if not collection or collection["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Create share link
        share_data = await sharing_service.create_share_link(
            collection_id, current_user["id"], expires_at
        )

        return {"message": "Share link created successfully", "share_data": share_data}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create share link: {str(e)}"
        )


@router.get("/shared/{share_id}")
async def get_shared_collection(share_id: str):
    """Get a shared collection by share ID"""
    try:
        sharing_service = get_sharing_service()
        collections_service = get_user_collections_service()

        # Get shared collection
        collection = await sharing_service.get_shared_collection(share_id)

        if not collection:
            raise HTTPException(
                status_code=404, detail="Shared collection not found or expired"
            )

        # Get questions in collection
        questions = await collections_service.get_collection_questions(collection["id"])

        return {"collection": collection, "questions": questions}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch shared collection: {str(e)}"
        )


@router.delete("/shares/{share_id}")
async def deactivate_share_link(
    share_id: str, current_user: dict = Depends(get_current_user)
):
    """Deactivate a share link"""
    try:
        sharing_service = get_sharing_service()

        success = await sharing_service.deactivate_share_link(
            share_id, current_user["id"]
        )

        if success:
            return {"message": "Share link deactivated successfully"}
        else:
            raise HTTPException(
                status_code=500, detail="Failed to deactivate share link"
            )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to deactivate share link: {str(e)}"
        )


@router.get("/shares")
async def get_user_share_links(current_user: dict = Depends(get_current_user)):
    """Get user's active share links"""
    try:
        sharing_service = get_sharing_service()
        share_links = await sharing_service.get_user_share_links(current_user["id"])

        return {"share_links": share_links}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch share links: {str(e)}"
        )


# Public collections
@router.get("/public/collections")
async def get_public_collections(limit: int = 20):
    """Get public collections from all users"""
    try:
        collections_service = get_user_collections_service()
        collections = await collections_service.get_public_collections(limit)

        return {"collections": collections}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch public collections: {str(e)}"
        )


# Search endpoints
@router.get("/collections/search")
async def search_collections(
    query: str, current_user: dict = Depends(get_current_user)
):
    """Search user's collections"""
    try:
        collections_service = get_user_collections_service()
        collections = await collections_service.search_collections(
            current_user["id"], query
        )

        return {"collections": collections}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to search collections: {str(e)}"
        )


# Legal and compliance
@router.get("/legal/terms")
async def get_terms_of_service():
    """Get terms of service for uploads"""
    try:
        legal_protection = get_legal_protection()
        return {"terms": legal_protection.terms_of_service}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch terms: {str(e)}")


@router.get("/legal/upload-limits")
async def get_upload_limits(current_user: dict = Depends(get_current_user)):
    """Get user's upload limits and usage"""
    try:
        from services.supabase import supabase_client

        # Get today's uploads
        today = datetime.now().date().isoformat()

        upload_count = (
            await supabase_client.table("uploaded_papers")
            .select("id", count="exact")
            .eq("user_id", current_user["id"])
            .gte("upload_date", today)
            .execute()
        )

        current_count = upload_count.count if upload_count.count else 0
        daily_limit = 5  # Free tier limit

        return {
            "daily_limit": daily_limit,
            "current_uploads": current_count,
            "remaining_uploads": max(0, daily_limit - current_count),
            "can_upload": current_count < daily_limit,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch upload limits: {str(e)}"
        )
