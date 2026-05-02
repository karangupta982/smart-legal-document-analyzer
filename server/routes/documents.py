from fastapi import APIRouter, UploadFile, File, HTTPException
from services.astra_service import AstraService
from services.document_processor import extract_text, chunk_text
import os

router = APIRouter()
astra_service = AstraService()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a document.
    """
    # Validate file type
    file_extension = file.filename.lower().split('.')[-1]
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type. Only PDF, DOCX, and TXT are allowed.")

    # Validate file size
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit.")

    try:
        # Extract text
        text = extract_text(file_content, file.filename)
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text could be extracted from the document.")

        # Chunk text
        chunks = chunk_text(text, chunk_size=250, overlap=50)
        if not chunks:
            raise HTTPException(status_code=400, detail="Failed to create text chunks.")

        # Save to Astra DB
        document_id = astra_service.save_document(
            filename=file.filename,
            size=len(file_content),
            full_text=text,
            chunks=chunks
        )

        return {
            "document_id": document_id,
            "filename": file.filename,
            "size": len(file_content),
            "chunk_count": len(chunks)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@router.get("/")
async def list_documents():
    """List all documents."""
    try:
        documents = astra_service.list_documents()
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching documents: {str(e)}")

@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and its chunks."""
    try:
        success = astra_service.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found.")
        return {"message": "Document deleted successfully."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")