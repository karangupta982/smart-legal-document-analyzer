from sentence_transformers import SentenceTransformer
from astrapy import DataAPIClient
import uuid
import os
from typing import List, Dict, Any

class AstraService:
    def __init__(self):
        # Load environment variables
        self.astra_token = os.getenv("ASTRA_DB_TOKEN")
        self.astra_endpoint = os.getenv("ASTRA_DB_API_ENDPOINT")
        self.astra_keyspace = os.getenv("ASTRA_DB_KEYSPACE")

        if not all([self.astra_token, self.astra_endpoint, self.astra_keyspace]):
            raise ValueError("Missing Astra DB environment variables")

        # Initialize Astra client
        self.client = DataAPIClient(self.astra_token)
        self.database = self.client.get_database(self.astra_endpoint, keyspace=self.astra_keyspace)

        # Get collections
        self.documents_collection = self.database.get_collection("documents")
        self.chunks_collection = self.database.get_collection("document_chunks")

        # Load embedding model
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    def save_document(self, filename: str, size: int, full_text: str, chunks: List[str]) -> str:
        """
        Save document metadata and chunks with embeddings.
        Returns the document_id.
        """
        document_id = str(uuid.uuid4())

        # Save document metadata
        document_data = {
            "_id": document_id,
            "filename": filename,
            "size": size,
            "full_text": full_text,
            "chunk_count": len(chunks)
        }
        self.documents_collection.insert_one(document_data)

        # Generate embeddings and save chunks
        for i, chunk in enumerate(chunks):
            embedding = self.embedding_model.encode(chunk).tolist()
            chunk_data = {
                "_id": str(uuid.uuid4()),
                "document_id": document_id,
                "chunk_text": chunk,
                "chunk_index": i,
                "$vector": embedding
            }
            self.chunks_collection.insert_one(chunk_data)

        return document_id

    def semantic_search(self, document_id: str, query: str, top_k: int = 5) -> List[str]:
        """
        Perform vector search for relevant chunks.
        Returns list of chunk_text.
        """
        query_embedding = self.embedding_model.encode(query).tolist()

        # Perform vector search with filter
        results = self.chunks_collection.find(
            {"document_id": document_id},
            vector=query_embedding,
            limit=top_k,
            include_similarity=True
        )

        return [doc["chunk_text"] for doc in results]

    def get_document(self, document_id: str) -> Dict[str, Any]:
        """Get document metadata by ID."""
        return self.documents_collection.find_one({"_id": document_id})

    def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents."""
        return list(self.documents_collection.find({}))

    def delete_document(self, document_id: str) -> bool:
        """Delete document and its chunks."""
        # Delete chunks first
        self.chunks_collection.delete_many({"document_id": document_id})
        # Delete document metadata
        result = self.documents_collection.delete_one({"_id": document_id})
        return result.deleted_count > 0