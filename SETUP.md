# Career Intelligence Assistant - Setup & Contribution Guide

## 🚀 Quick Setup for Developers

### Prerequisites Check
```bash
# Verify Python 3.9+
python3 --version

# Install Homebrew if missing
command -v brew >/dev/null 2>&1 || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Add Homebrew to PATH (Apple Silicon)
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"

# Verify Ollama is installed
/opt/homebrew/bin/brew list ollama || /opt/homebrew/bin/brew install ollama

# Verify models are pulled
ollama list | grep -E "llama3.2|mxbai-embed-large"
```

### First-Time Setup
```bash
# 1. Clone repository
git clone <repo-url> && cd <repo-dir>

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Pull Ollama models (if not already done)
ollama pull llama3.2
ollama pull mxbai-embed-large

# 5. Create sample data directory
mkdir -p sample_jobs
# Add your job description files here

# 6. Run the app
streamlit run app.py
```

The app opens at **http://localhost:8501**

## 📝 Code Structure

### `rag.py` - RAG Pipeline
- **`load_document(file_path)`**: Load PDF/TXT files
- **`ingest_documents(resume_path, jobs_dir)`**: Process documents into embeddings
- **`create_rag_chain(retriever)`**: Build retrieval chain with LLM
- **`load_existing_vectorstore()`**: Load cached embeddings for faster startup

### `app.py` - Streamlit UI
- **Sidebar**: File upload, folder path input, model configuration
- **Chat Interface**: Query-response with session history
- **Context Display**: Retrieved documents in expandable panels

### `test_rag.py` - Unit Tests
Run tests:
```bash
pytest test_rag.py -v
pytest test_rag.py::TestDocumentLoading::test_load_text_document -v
```

## 🔧 Common Development Tasks

### Test a Query Locally
```python
from rag import ingest_documents, create_rag_chain

retriever = ingest_documents("path/to/resume.pdf", "./sample_jobs")
chain = create_rag_chain(retriever)
result = chain.invoke({"input": "What's my fit score?"})
print(result["answer"])
```

### Debug in VS Code
1. Press **Cmd+Shift+D** to open Run & Debug
2. Click "Run" (should auto-detect Python environment)
3. Set breakpoints (red dots on line numbers)
4. Run: `streamlit run app.py --logger.level=debug`

### Change LLM Models
Edit `rag.py`:
```python
EMBEDDINGS_MODEL = "nomic-embed-text"  # Faster, smaller
LLM_MODEL = "neural-chat"  # More creative responses
```

Then:
```bash
ollama pull neural-chat
# Restart app
```

### Clear Vector Store
```bash
rm -rf chroma_db/
# Re-ingest documents through UI
```

### Update Dependencies
```bash
pip install --upgrade -r requirements.txt
pip freeze > requirements.txt
git add requirements.txt && git commit -m "Update dependencies"
```

## 🧪 Testing Guidelines

### Adding New Tests
Edit `test_rag.py`:
```python
def test_new_feature(self, temp_resume, temp_jobs_dir):
    """Test new feature with sample data."""
    retriever = ingest_documents(temp_resume, temp_jobs_dir)
    # Your test logic here
    assert retriever is not None
```

Run:
```bash
pytest test_rag.py::TestRAGChain::test_new_feature -v
```

### Test Coverage
```bash
pytest test_rag.py --cov=rag --cov-report=html
open htmlcov/index.html
```

## 📊 Performance Profiling

### Timing Chain Invocation
```python
import time
from rag import create_rag_chain, load_existing_vectorstore

retriever = load_existing_vectorstore()
chain = create_rag_chain(retriever)

start = time.time()
result = chain.invoke({"input": "Test query"})
print(f"Time: {time.time() - start:.2f}s")
```

### Check Model Performance
```bash
# Test LLM inference time
time ollama run llama3.2 "What is machine learning?"

# Test embeddings
time ollama run mxbai-embed-large "Sample text to embed"
```

## 🐛 Troubleshooting

### "Connection refused" Error
```bash
# Ollama not running
open -a Ollama
# Or in terminal:
ollama serve
```

### "Module not found" Errors
```bash
# Verify venv is activated
which python  # Should show /path/to/venv/bin/python

# Reinstall packages
pip install -r requirements.txt
```

### Slow Ingestion
- **Too many large PDFs?** Split them or reduce `CHUNK_SIZE`
- **Out of memory?** Reduce `CHUNK_OVERLAP` from 200 to 100

### Duplicate Entries in Vector Store
```bash
rm -rf chroma_db/
# Re-ingest from scratch
```

## 📦 Docker Development

### Build Locally
```bash
docker build -t career-assistant:dev .
```

### Run with Local Ollama
```bash
docker run -p 8501:8501 \
  -e OLLAMA_HOST=http://host.docker.internal:11434 \
  career-assistant:dev
```

### Mount Source for Hot Reload
```bash
docker run -p 8501:8501 \
  -v $(pwd):/app \
  -e OLLAMA_HOST=http://host.docker.internal:11434 \
  career-assistant:dev
```

## 🤖 VS Code + Copilot Tips

### Use Copilot for Code Generation
- Press **Cmd+I** in any file for inline suggestions
- Type comments like `# Load and chunk PDFs from jobs folder` → Copilot generates code
- Accept suggestions with **Tab**

### Chain Snippets
```python
# Copilot can auto-complete:
from langchain_core.prompts import ChatPromptTemplate
prompt = ChatPromptTemplate.from_template("""
# Type here, Copilot suggests the structure
""")
```

### Test Generation
Comment: `# Test that embeddings are created`
Copilot generates test scaffolding.

## 🚢 Git Workflow

### Commit Template
```bash
git add <files>
git commit -m "feat(rag): Add hybrid search support"
# Types: feat, fix, refactor, test, docs, chore
```

### Before Pushing
```bash
# Run tests
pytest test_rag.py -v

# Check linting (optional)
pylint rag.py app.py

# Verify requirements.txt is up-to-date
pip freeze | diff - requirements.txt
```

## 📚 Key References

- [LangChain Docs](https://python.langchain.com/docs/)
- [Ollama Models](https://ollama.ai/library)
- [Streamlit API](https://docs.streamlit.io)
- [ChromaDB Guide](https://docs.trychroma.dev)

## 💡 Enhancement Ideas

- [ ] Add PDF export of analysis report
- [ ] Support multiple resume formats (DOCX, RTF)
- [ ] Skill matching heatmap visualization
- [ ] BM25 hybrid search for better retrieval
- [ ] Interview question generator
- [ ] Resume improvement suggestions

---

**Happy coding! 🎉** If you get stuck, check the troubleshooting section or open an issue.
