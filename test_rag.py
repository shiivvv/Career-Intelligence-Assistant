"""
Unit tests for Career Intelligence Assistant RAG pipeline.
Run with: pytest test_rag.py -v
"""

import os
import tempfile
from pathlib import Path
import pytest
from langchain_core.documents import Document
from rag import (
    load_document,
    ingest_documents,
    create_rag_chain,
)


@pytest.fixture
def temp_resume():
    """Create a temporary resume file for testing."""
    content = """
    John Doe
    Senior Software Engineer
    
    Skills: Python, JavaScript, Machine Learning, Cloud Architecture
    Experience: 8 years in tech
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        f.flush()
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def temp_jobs_dir():
    """Create a temporary jobs directory with sample job descriptions."""
    jobs_dir = tempfile.mkdtemp()
    
    job1_content = """
    Senior ML Engineer
    Requirements: Python, PyTorch, TensorFlow, 5+ years ML experience
    Responsibilities: Build ML pipelines, lead research, mentor junior engineers
    """
    
    job2_content = """
    Full Stack Developer
    Requirements: JavaScript, React, Node.js, AWS, Docker
    Responsibilities: Develop web applications, optimize performance, code reviews
    """
    
    with open(os.path.join(jobs_dir, "job1.txt"), 'w') as f:
        f.write(job1_content)
    
    with open(os.path.join(jobs_dir, "job2.txt"), 'w') as f:
        f.write(job2_content)
    
    yield jobs_dir
    
    # Cleanup
    for file in Path(jobs_dir).glob('*'):
        file.unlink()
    os.rmdir(jobs_dir)


class TestDocumentLoading:
    """Test document loading functionality."""
    
    def test_load_text_document(self, temp_resume):
        """Test loading a text document."""
        docs = load_document(temp_resume)
        assert len(docs) > 0
        assert isinstance(docs[0], Document)
        assert "John Doe" in docs[0].page_content
    
    def test_load_unsupported_format(self):
        """Test loading an unsupported file format."""
        with pytest.raises(ValueError):
            load_document("file.xyz")


class TestDocumentIngestion:
    """Test document ingestion pipeline."""
    
    def test_ingest_documents_missing_files(self, temp_resume):
        """Test ingestion with non-existent jobs directory."""
        with pytest.raises(ValueError):
            ingest_documents(temp_resume, "./nonexistent_dir")
    
    def test_ingest_documents_success(self, temp_resume, temp_jobs_dir):
        """Test successful document ingestion."""
        retriever = ingest_documents(temp_resume, temp_jobs_dir)
        assert retriever is not None
        
        # Test retrieval
        results = retriever.invoke("Python skills")
        assert len(results) > 0


class TestRAGChain:
    """Test RAG chain creation and invocation."""
    
    def test_create_rag_chain(self, temp_resume, temp_jobs_dir):
        """Test creating a RAG chain."""
        retriever = ingest_documents(temp_resume, temp_jobs_dir)
        chain = create_rag_chain(retriever)
        assert chain is not None
    
    def test_rag_chain_invocation(self, temp_resume, temp_jobs_dir):
        """Test invoking the RAG chain with a query."""
        retriever = ingest_documents(temp_resume, temp_jobs_dir)
        chain = create_rag_chain(retriever)
        
        # Test with a simple query
        response = chain.invoke({"input": "What are my Python skills?"})
        assert "answer" in response
        assert isinstance(response["answer"], str)
        assert len(response["answer"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
