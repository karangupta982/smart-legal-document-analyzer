from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.astra_service import AstraService
from services.groq_service import GroqService

router = APIRouter()
astra_service = AstraService()
groq_service = GroqService()

class QueryRequest(BaseModel):
    document_id: str
    question: str

@router.post("/")
async def query_document(request: QueryRequest):
    """
    Query a document using semantic search and LLM.
    """
    try:
        # Validate document exists
        document = astra_service.get_document(request.document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found.")

        # Perform semantic search
        relevant_chunks = astra_service.semantic_search(
            document_id=request.document_id,
            query=request.question,
            top_k=5
        )

        if not relevant_chunks:
            return {
                "answer": "Not found in document",
                "explanation": "No relevant information found in the document.",
                "source": ""
            }

        # Combine chunks into context
        context = "\n\n".join(relevant_chunks)

        # Ask LLM
        response = groq_service.ask_question(context, request.question)

        return {"response": response}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")