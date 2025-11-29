"""
Embedding Service for generating vector embeddings from text.
Uses OpenAI's text-embedding models to create semantic representations
that enable similarity search across reports and findings.
"""
import os
from typing import Optional, List
from openai import OpenAI


class EmbeddingService:
    """Service for generating text embeddings using OpenAI API"""
    
    def __init__(self):
        """Initialize the OpenAI client with API key from environment"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable not set. "
                "Please add it to your .env file."
            )
        
        self.client = OpenAI(api_key=api_key)
        # Using text-embedding-3-small: fast, cost-effective, 1536 dimensions
        # Alternative: text-embedding-3-large for higher quality (3072 dims)
        self.model = "text-embedding-3-small"
        self.dimensions = 1536
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate an embedding vector for the given text.
        
        Args:
            text: Input text to embed (will be truncated if too long)
        
        Returns:
            List of floats representing the embedding vector (1536 dimensions)
        
        Raises:
            Exception: If the OpenAI API call fails
        """
        if not text or not text.strip():
            raise ValueError("Cannot generate embedding for empty text")
        
        try:
            # OpenAI API handles tokenization and truncation automatically
            response = self.client.embeddings.create(
                input=[text],
                model=self.model
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"[ERROR] Failed to generate embedding: {e}")
            raise
    
    def embed_report(self, report) -> List[float]:
        """
        Generate embedding from report content.
        Combines title, description, and cluster_id into searchable text.
        
        Args:
            report: Report object with title, description, cluster_id attributes
        
        Returns:
            Embedding vector as list of floats
        """
        # Combine relevant fields into a single text representation
        # Weight title more heavily by putting it first
        parts = [report.title]
        
        if report.description:
            parts.append(report.description)
        
        # Include cluster context for better similarity matching
        parts.append(f"Cluster: {report.cluster_id}")
        
        # Optional: include metadata if available
        if hasattr(report, 'crdb_version') and report.crdb_version:
            parts.append(f"Version: {report.crdb_version}")
        
        text = "\n".join(parts)
        return self.embed_text(text)
    
    def embed_finding(self, finding) -> List[float]:
        """
        Generate embedding from finding content.
        Combines title, description, category, and severity.
        
        Args:
            finding: Finding object with title, description, category, severity
        
        Returns:
            Embedding vector as list of floats
        """
        parts = [
            finding.title,
            finding.description,
            f"Category: {finding.category}",
            f"Severity: {finding.severity}"
        ]
        
        # Include tags if available
        if hasattr(finding, 'tags') and finding.tags:
            parts.append(f"Tags: {', '.join(finding.tags)}")
        
        text = "\n".join(parts)
        return self.embed_text(text)
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in a single API call.
        More efficient for bulk operations.
        
        Args:
            texts: List of text strings to embed
        
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Filter out empty texts
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            raise ValueError("No valid texts to embed")
        
        try:
            response = self.client.embeddings.create(
                input=valid_texts,
                model=self.model
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            print(f"[ERROR] Failed to generate batch embeddings: {e}")
            raise


# Singleton instance for reuse across the application
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """
    Get or create the singleton embedding service instance.
    This avoids creating multiple OpenAI clients.
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
