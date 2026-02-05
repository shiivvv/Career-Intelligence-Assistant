"""
Career Intelligence Assistant - RAG Pipeline
Handles document loading, chunking, embedding, and retrieval-augmented generation.
"""

import os
import sys
import warnings
import csv
import requests
from pathlib import Path
from typing import Optional, List
from bs4 import BeautifulSoup

# Suppress non-critical warnings
warnings.filterwarnings('ignore', category=UserWarning)
os.environ['PYTHONWARNINGS'] = 'ignore'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow warnings
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

from langchain.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OllamaEmbeddings
from langchain.chat_models import ChatOllama
import chromadb
from chromadb.config import Settings
from langchain.chains import RetrievalQA
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document, BaseRetriever


class SimpleChromaRetriever(BaseRetriever):
    collection: object
    embeddings: object
    k: int = 6

    class Config:
        arbitrary_types_allowed = True

    def get_relevant_documents(self, query: str):
        query_embedding = self.embeddings.embed_query(query)
        try:
            total = self.collection.count()
        except Exception:
            total = self.k
        k = min(self.k, total) if total else 0
        if k == 0:
            return []
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas"]
        )
        docs = []
        for doc_text, metadata in zip(results["documents"][0], results["metadatas"][0]):
            docs.append(Document(page_content=doc_text, metadata=metadata or {}))
        return docs


# Configuration
PERSIST_DIR = "./chroma_db"
EMBEDDINGS_MODEL = "mxbai-embed-large"
LLM_MODEL = "llama3.2"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

os.makedirs(PERSIST_DIR, exist_ok=True)


def load_document(file_path: str) -> List[Document]:
    """Load a PDF or text file into documents."""
    file_path = Path(file_path)
    
    if file_path.suffix.lower() == '.pdf':
        loader = PyPDFLoader(str(file_path))
    elif file_path.suffix.lower() in ['.txt', '.md']:
        loader = TextLoader(str(file_path))
    else:
        raise ValueError(f"Unsupported file type: {file_path.suffix}")
    
    return loader.load()


def load_csv_jobs(file_path: str) -> List[Document]:
    """Load a CSV file where each row is a job description."""
    file_path = Path(file_path)
    if file_path.suffix.lower() != ".csv":
        raise ValueError(f"Unsupported file type: {file_path.suffix}")

    docs: List[Document] = []
    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, 1):
            # Combine all columns into a single job description
            parts = [f"{k}: {v}" for k, v in row.items() if v is not None and str(v).strip()]
            content = "\n".join(parts).strip()
            if not content:
                continue
            doc = Document(page_content=content, metadata={
                "source_type": "job_description",
                "job_id": idx,
                "filename": file_path.name,
                "row": idx
            })
            docs.append(doc)

    return docs


def scrape_job_url(url: str, job_id: int = 1) -> Optional[Document]:
    """
    Scrape a job posting from a URL.
    Simple implementation that extracts visible text from the page.
    
    Args:
        url: Job posting URL
        job_id: Unique identifier for this job
    
    Returns:
        Document with job description or None if scraping fails
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()
        
        # Get text and clean it up
        text = soup.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        content = '\n'.join(lines)
        
        if not content or len(content) < 100:
            print(f"  Warning: Very little content extracted from {url}")
            return None
        
        doc = Document(
            page_content=content,
            metadata={
                'source_type': 'job_description',
                'job_id': job_id,
                'url': url,
                'source': 'url_scrape'
            }
        )
        
        return doc
        
    except requests.exceptions.RequestException as e:
        print(f"  Error scraping {url}: {e}")
        return None
    except Exception as e:
        print(f"  Unexpected error scraping {url}: {e}")
        return None


def load_job_urls(urls: List[str]) -> List[Document]:
    """
    Load job descriptions from a list of URLs.
    
    Args:
        urls: List of job posting URLs
    
    Returns:
        List of Document objects
    """
    docs = []
    for idx, url in enumerate(urls, 1):
        url = url.strip()
        if not url or not url.startswith(('http://', 'https://')):
            continue
        print(f"  Scraping URL {idx}: {url}")
        doc = scrape_job_url(url, job_id=idx)
        if doc:
            docs.append(doc)
    
    return docs


def ingest_documents(resume_path: str, jobs_dir: str, job_urls: Optional[List[str]] = None) -> object:
    """
    Ingest resume and job descriptions into vector store.
    
    Args:
        resume_path: Path to resume (PDF or TXT)
        jobs_dir: Directory containing job descriptions
        job_urls: Optional list of URLs to scrape for job descriptions
    
    Returns:
        Retriever object for RAG chain
    """
    all_docs = []
    
    # Load resume
    print(f"Loading resume from {resume_path}...")
    resume_docs = load_document(resume_path)
    for doc in resume_docs:
        doc.metadata['source_type'] = 'resume'
    all_docs.extend(resume_docs)
    
    # Load job URLs if provided
    if job_urls:
        print(f"Scraping {len(job_urls)} job URL(s)...")
        url_docs = load_job_urls(job_urls)
        all_docs.extend(url_docs)
        print(f"  Successfully scraped: {len(url_docs)} job(s)")
    
    # Load job descriptions
    print(f"Loading resume from {resume_path}...")
    resume_docs = load_document(resume_path)
    for doc in resume_docs:
        doc.metadata['source_type'] = 'resume'
    all_docs.extend(resume_docs)
    
    # Load job descriptions
    jobs_path = Path(jobs_dir)
    if jobs_path.exists():
        print(f"Loading job descriptions from {jobs_dir}...")
        if jobs_path.is_file() and jobs_path.suffix.lower() == ".csv":
            try:
                job_docs = load_csv_jobs(str(jobs_path))
                all_docs.extend(job_docs)
                print(f"  Loaded: {jobs_path.name} ({len(job_docs)} rows)")
            except Exception as e:
                print(f"  Error loading {jobs_path.name}: {e}")
        else:
            for idx, file_path in enumerate(jobs_path.glob('*'), 1):
                if file_path.is_file() and file_path.suffix.lower() in ['.pdf', '.txt', '.md', '.csv']:
                    try:
                        if file_path.suffix.lower() == ".csv":
                            job_docs = load_csv_jobs(str(file_path))
                        else:
                            job_docs = load_document(str(file_path))
                            for doc in job_docs:
                                doc.metadata['source_type'] = 'job_description'
                                doc.metadata['job_id'] = idx
                                doc.metadata['filename'] = file_path.name
                        all_docs.extend(job_docs)
                        print(f"  Loaded: {file_path.name}")
                    except Exception as e:
                        print(f"  Error loading {file_path.name}: {e}")
    
    if not all_docs:
        raise ValueError("No documents loaded. Check resume and jobs directory paths.")
    
    print(f"Total documents loaded: {len(all_docs)}")
    
    # Chunk documents
    print("Chunking documents...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    splits = splitter.split_documents(all_docs)
    print(f"Total chunks created: {len(splits)}")
    
    # Embed and store in Chroma
    print("Embedding documents and storing in vector DB...")
    try:
        embeddings = OllamaEmbeddings(model=EMBEDDINGS_MODEL)
        # Test the embeddings by embedding a single document
        test_embed = embeddings.embed_query("test")
        print(f"✅ Using Ollama embeddings ({EMBEDDINGS_MODEL})")
    except Exception as e:
        print(f"⚠️  Warning: Could not connect to Ollama embeddings: {e}")
        print("    Using default SentenceTransformer embeddings instead")
        from langchain.embeddings import HuggingFaceEmbeddings
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Reset existing collection to ensure embedding function is applied
    client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=PERSIST_DIR))
    try:
        client.delete_collection(name="career_docs")
        print("Cleared existing vector store collection.")
    except Exception:
        pass

    collection = client.get_or_create_collection(name="career_docs")

    texts = [doc.page_content for doc in splits]
    metadatas = [doc.metadata for doc in splits]
    ids = [f"doc_{i}" for i in range(len(splits))]
    embeddings_list = embeddings.embed_documents(texts)

    collection.add(
        documents=texts,
        metadatas=metadatas,
        ids=ids,
        embeddings=embeddings_list
    )
    
    print("Documents ingested successfully!")
    return SimpleChromaRetriever(collection=collection, embeddings=embeddings, k=6)


def create_rag_chain(retriever: object):
    """
    Create the RAG chain for career intelligence queries.
    
    Args:
        retriever: Document retriever from vector store
    
    Returns:
        RAG chain for invoking with queries
    """
    # Initialize LLM
    llm = ChatOllama(model=LLM_MODEL, temperature=0.1)
    
    # Create retrieval QA chain
    rag_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={
            "prompt": ChatPromptTemplate.from_template("""
You are a Career Intelligence Assistant. Analyze the provided resume and job descriptions to answer career-related questions.

For fit/gap analysis: Provide a fit score (0-100%), list matching skills, highlight gaps, and suggest preparation areas.
For skill matching: Show which skills from the resume align with job requirements.
For interview prep: Suggest relevant questions and talking points based on the resume and job description.

Be specific and actionable in your responses.

Context:
{context}

Question: {question}

Answer based on the provided context:""")
        }
    )
    
    return rag_chain


def load_existing_vectorstore() -> Optional[object]:
    """Load existing vector store if available."""
    try:
        embeddings = OllamaEmbeddings(model=EMBEDDINGS_MODEL)
        client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=PERSIST_DIR))
        collection = client.get_or_create_collection(name="career_docs")
        return SimpleChromaRetriever(collection=collection, embeddings=embeddings, k=6)
    except Exception as e:
        print(f"Could not load existing vector store: {e}")
        return None


if __name__ == "__main__":
    # Example usage
    resume_path = "sample_resume.pdf"
    jobs_dir = "sample_jobs"
    
    if os.path.exists(resume_path) and os.path.isdir(jobs_dir):
        retriever = ingest_documents(resume_path, jobs_dir)
        chain = create_rag_chain(retriever)
        
        # Test query
        response = chain.invoke({"input": "What is my fit score for the first job?"})
        print("\nAnswer:", response["answer"])
