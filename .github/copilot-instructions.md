# Career Intelligence Assistant - AI Agent Instructions

## Project Overview

A fully-local RAG (Retrieval-Augmented Generation) application that analyzes resumes against job descriptions using Ollama for LLMs and LangChain for orchestration. Everything runs offline on the user's MacBook.

**Core Purpose**: Help career seekers get intelligent, AI-powered insights on fit, skill gaps, and interview prep without sending data to the cloud.

## Architecture Overview

### Data Flow
```
User Resume (PDF/TXT) + Job Descriptions (PDF/TXT)
         ↓
    rag.py: Load → Chunk (1000 chars, 200 overlap) → Embed
         ↓
  Chroma Vector DB (persistent in ./chroma_db)
         ↓
  RAG Chain: User Query → Retrieve Top-6 Chunks → LLM → Answer
         ↓
  app.py: Streamlit Chat UI displays response + context
```

### Key Components

- **rag.py**: RAG engine
  - `load_document()`: PDF/TXT loading via LangChain loaders
  - `ingest_documents()`: Resume + jobs → Chroma with Ollama embeddings
  - `create_rag_chain()`: LLM chain with retrieval + prompt template
  - `load_existing_vectorstore()`: Restore previous sessions

- **app.py**: Streamlit frontend
  - Sidebar: Resume upload, jobs folder path, config (k_results, temperature)
  - Main chat interface with session state management
  - Retrieved document display in expanders

- **Dependencies**:
  - `langchain` + `langchain-community` + `langchain-ollama`: Core RAG
  - `chromadb`: Local vector store (persisted to disk)
  - `streamlit`: Web UI
  - `ollama`: Local LLM inference (llama3.2 + mxbai-embed-large)
  - `pypdf` + `unstructured`: Document parsing

## Critical Patterns & Conventions

### 1. Document Metadata
All chunks carry metadata for traceability:
```python
# In load_document() + ingest_documents()
doc.metadata['source_type'] = 'resume' or 'job_description'
doc.metadata['job_id'] = idx  # For jobs: 1, 2, 3...
doc.metadata['filename'] = file.name
```
Use these for filtering or contextual prompts.

### 2. Ollama Models
- **LLM**: `llama3.2` (3B, balanced speed/quality; ~1-2s inference on M1+)
- **Embeddings**: `mxbai-embed-large` (384-dim; faster alternatives: `nomic-embed-text`)
- Both pulled manually: `ollama pull <model>`
- Temperature: 0.1 (deterministic for career advice; increase for creative)

### 3. Prompt Engineering
Career-specific template in `create_rag_chain()`:
```
- Include explicit score format: "Fit score: X%"
- Ask for skill lists: "Matching skills: [...], Gaps: [...]"
- Ground in provided context
```
Customize by editing `ChatPromptTemplate.from_template()` for new use cases.

### 4. Vector Store Persistence
- Chroma stored in `./chroma_db` (on disk)
- Load existing: `load_existing_vectorstore()` — skip re-ingestion for faster startup
- Reset: `rm -rf chroma_db && re-ingest`

### 5. Session State (Streamlit)
- `st.session_state.chain`: Current RAG chain instance
- `st.session_state.chat_history`: Conversation list
- `st.session_state.retrieved_docs`: For context display
Clearing resets the entire analysis.

### 6. Error Handling
```python
# File loading: ValueError for unsupported types
# Document ingestion: ValueError if no docs found
# Chain invocation: Wrapped in try/except with st.error() UI feedback
```

## Developer Workflows

### Setup (First Time)
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
ollama pull llama3.2 && ollama pull mxbai-embed-large
```

### Development Cycle
1. **Edit code**: `rag.py` (pipeline) or `app.py` (UI)
2. **Test locally**: `streamlit run app.py` → upload test resume + jobs
3. **Debug**: VS Code F5, set breakpoints in `rag.py`
4. **Commit**: Test via pytest first (`pytest test_rag.py -v`)

### Testing Strategy
- **Unit tests**: `test_rag.py` uses temporary files (no fixtures to Ollama)
- **Integration tests**: Manual (requires Ollama running + test documents)
- Example: `test_ingest_documents_success()` verifies retrieval works end-to-end

### Performance Tuning
- **Slow inference**: Reduce `CHUNK_SIZE` (fewer tokens to embed), use lighter model (`phi`)
- **Memory pressure**: Lower `k_results` (fewer chunks to prompt), reduce chunk overlap
- **Sluggish ingestion**: Split large PDFs, parallelize with multiprocessing (future)

## Key Integration Points

### Ollama Integration
- Connection: `OllamaEmbeddings(model="mxbai-embed-large")` and `ChatOllama(model="llama3.2")`
- Assumption: Ollama running on localhost:11434 (default)
- Failure: Graceful error message in Streamlit; test via `ollama run llama3.2`

### Chroma Integration
- Type: `PersistentClient` (local file-based, not in-memory)
- Collections: One named `career_docs` for all documents
- Querying: `.as_retriever(search_kwargs={"k": 6})` returns LangChain Retriever interface

### LangChain Chains
- `create_stuff_documents_chain()`: Puts retrieved docs inline in prompt
- `create_retrieval_chain()`: Wraps retriever + doc chain; outputs `{"answer": "...", "context": [...]}` 
- Invoke: `chain.invoke({"input": "..."})` — synchronous

## Configuration & Customization

### Environment Variables (Optional)
See `.env.example`:
```
OLLAMA_HOST=http://localhost:11434
LLM_MODEL=llama3.2
EMBEDDINGS_MODEL=mxbai-embed-large
CHUNK_SIZE=1000
NUM_RETRIEVED_DOCS=6
LLM_TEMPERATURE=0.1
```
Not currently loaded in code—hardcoded in `rag.py`. To use: `load_dotenv()` + `os.getenv()`

### Extending RAG
- **Hybrid search**: Add BM25 retriever, merge results before prompting
- **Interview prep**: New prompt template in `create_rag_chain()`
- **Multi-resume**: Track `source_type` in metadata, filter by candidate

## Common Pitfalls & Solutions

| Issue | Cause | Fix |
|-------|-------|-----|
| Slow first load | Ollama not running / model not pulled | Check `ollama list`, restart Ollama |
| Chunking misses nuance | CHUNK_SIZE too large | Reduce to 800, increase overlap to 250 |
| Duplicate embeddings | Re-ingesting without clearing chroma_db | `rm -rf chroma_db` before re-ingest |
| UI hangs during ingestion | Blocking operations in main thread | Already wrapped in `st.spinner()` |
| Low fit accuracy | Prompt too generic | Customize template with specific criteria |

## File References for Key Patterns

- **Document loading**: [rag.py#L25-L35](rag.py#L25-L35) — `load_document()`
- **Ingestion logic**: [rag.py#L38-L87](rag.py#L38-L87) — `ingest_documents()`
- **RAG prompt**: [rag.py#L100-L115](rag.py#L100-L115) — `create_rag_chain()`
- **Streamlit upload**: [app.py#L47-L75](app.py#L47-L75) — Resume/jobs file handling
- **Session state**: [app.py#L28-L31](app.py#L28-L31) — Chat history + chain persistence
- **Metadata usage**: [rag.py#L54-L62](rag.py#L54-L62) — Source type tracking

## Debugging Tips for AI Agents

1. **Verify Ollama**: Before touching code, confirm `ollama run llama3.2` works locally
2. **Test retrieval**: Call `retriever.invoke("test query")` directly to debug embedding/search
3. **Check prompt template**: Print raw prompt before invoking chain to catch template errors
4. **Inspect metadata**: Log document metadata during ingestion to ensure correct tagging
5. **Profile inference**: Time each step (load → chunk → embed → retrieve → generate)

## Performance Baseline

- **M1 MacBook (8GB)**: Llama 3.2 ~1.5s per query after retrieval
- **Embedding**: ~100 chunks in 5-10s
- **Vector search**: <100ms for k=6 retrieval
- **Streamlit startup**: ~2s

## Next Steps for Agents

When assigned new features:
1. Identify which component owns it (rag.py vs. app.py)
2. Check existing patterns in that file
3. Add to `test_rag.py` if modifying `rag.py`
4. Test manually with sample data before committing
5. Update this document if introducing new conventions

---

**Last Updated**: February 2026 | **Owner**: Career Intelligence Assistant Team
