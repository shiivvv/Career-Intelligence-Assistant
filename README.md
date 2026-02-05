# Career Intelligence Assistant 🚀

Matches your CV against job descriptions using local AI. Everything runs offline on your Mac with Ollama and LangChain, so your data stays private.

## Features

✨ **Local & Private**: Processing happens on your machine, no cloud uploads
🤖 **Powered by Ollama**: Local LLMs (Llama 3.2) for instant analysis
🧠 **RAG Pipeline**: Retrieval-augmented generation for context-aware insights
💬 **Chat Interface**: Interactive Streamlit UI
📊 **Career Intelligence**: Fit scores, skill gap analysis, interview prep
🌐 **URL Scraping**: Paste job URLs directly, no file downloads needed

## Quick Start

### Prerequisites

- macOS (M1/M2/M3 recommended for Ollama)
- [Homebrew](https://brew.sh/) (required for Ollama)
- Python 3.9+
- Git

If Homebrew is not installed, run:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Then add it to your PATH (Apple Silicon):

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

### 1. Install Ollama

```bash
/opt/homebrew/bin/brew install ollama
```

Pull the required models:

```bash
ollama pull llama3.2        # Chat model (3B params, fast on M1+)
ollama pull mxbai-embed-large  # Embeddings model
```

Test Ollama:

```bash
ollama run llama3.2 "Hello, what can you do?"
```

### 2. Clone & Setup Project

```bash
git clone <your-repo-url> career-assistant
cd career-assistant

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Prepare Your Data

**Option A: Local Files**

Create folders for your documents:

```bash
mkdir sample_jobs
# Add job description PDFs/TXTs/CSVs to sample_jobs/
# For example: sample_jobs/job1.pdf, sample_jobs/job2.txt, postings.csv
# CSV files are read row-by-row, treating each row as a job description.
```

**Option B: URLs**

No folder needed! You can paste job posting URLs directly in the app (see Usage below).

### 4. Run the Application

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`

## Usage

1. **Upload CV**: Choose your CV (PDF or TXT) from the sidebar
2. **Choose Input Method**:
   - **Folder**: Point to a directory with job files (PDF/TXT/CSV)
   - **URLs**: Paste job posting URLs (one per line) for automatic scraping
3. **Ingest Documents**: Click "Ingest Documents" to process
4. **Ask Questions**:
   - "What's my fit score for Job 1?"
   - "Which skills am I missing?"
   - "How should I prep for interviews?"
   - "Which job suits me best?"

### URL Scraping

Works well with company career pages, Greenhouse, and Lever. LinkedIn and Indeed can be tricky due to login walls. Just paste URLs one per line:

```
https://jobs.example.com/posting-1
https://careers.company.com/role-123
```

## Project Structure

```
├── app.py                 # Streamlit chat UI
├── rag.py                 # RAG pipeline (loading, embedding, retrieval)
├── test_rag.py            # Unit tests
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker containerization
├── .env.example           # Environment variables template
├── README.md              # This file
├── chroma_db/             # Vector store (persistent)
└── sample_jobs/           # Your job descriptions (add files here)
```

## Architecture / High Level Flow

![Diagram](<Architecture Diagram - Rough.png>)

## Key Files Explained

### `rag.py`
Core RAG pipeline:
- `load_document()`: Loads PDF/TXT files
- `load_csv_jobs()`: Parses CSV files (one job per row)
- `scrape_job_url()`: Scrapes job postings from URLs
- `load_job_urls()`: Batch processes multiple URLs
- `ingest_documents()`: Processes CV + jobs into embeddings (files or URLs)
- `create_rag_chain()`: Builds the LLM chain with prompt engineering
- `load_existing_vectorstore()`: Reuses previous ingestions

### `app.py`
Streamlit interface:
- Sidebar for CV upload and config
- Chat interface for questions
- Chat interface for asking questions
- Document retrieval display
- Session state management

## Development Workflow

### Activate Virtual Environment

```bash
source venv/bin/activate
```

### Regenerate Dependencies

```bash
pip freeze > requirements.txt
```

## Customization

### Change LLM Model

Edit `rag.py`:
```python
LLM_MODEL = "neural-chat"  # or "mistral", "dolphin-mixtral", etc.
EMBEDDINGS_MODEL = "nomic-embed-text"  # lighter alternative
```

Pull new models:
```bash
ollama pull neural-chat
```

### Modify Prompt

In `rag.py`, `create_rag_chain()`:
```python
prompt = ChatPromptTemplate.from_template("""
Your custom prompt here...
Question: {input}
Context: {context}
""")
```

### Adjust Chunking

In `rag.py`:
```python
CHUNK_SIZE = 1500        # Larger chunks = more context
CHUNK_OVERLAP = 300      # More overlap = better continuity
```

## Troubleshooting

### Ollama Not Running
```bash
# Start Ollama in background
ollama serve &

# Or in a separate terminal
open -a Ollama
```

### Vector Store Issues
```bash
# Remove and regenerate
rm -rf chroma_db/
# Re-ingest documents through the UI
```

### Model Not Found
```bash
ollama list          # Check available models
ollama pull llama3.2 # Install missing model
```

### Slow Inference
- Use smaller model: `ollama pull phi` (2.7B, faster)
- Reduce `CHUNK_SIZE` in `rag.py`

## Docker Deployment

Build:
```bash
docker build -t career-assistant .
```

Run (requires Ollama running on host):
```bash
docker run -p 8501:8501 \
  -e OLLAMA_HOST=http://host.docker.internal:11434 \
  career-assistant
```

## Performance Notes

- **M1/M2 MacBook**: Llama 3.2 inference ~1-2 seconds ( It's the only machine I had available. However, ofcourse this is not the ideal setup for production. For production, I would recommend using GPU instances on AWS/GCP/Azure or running Ollama on a local server with a powerful GPU.)
- **First ingestion**: 30-60 seconds (depends on document size)
- **Subsequent queries**: <2 seconds (vector search + LLM)
- **Memory usage**: ~3-4 GB (Ollama + Streamlit + Chroma)

## Future Enhancements

- [ ] Fit score visualization (pie charts of skill matches)
- [ ] Interview question generation
- [ ] Resume improvement suggestions with editing
- [ ] Multi-document comparison (best fit ranking)
- [ ] Export analysis report (PDF/Markdown)

## Contributing

Contributions welcome! Please:
1. Create a feature branch
2. Write tests for new functionality
3. Follow existing code style
4. Submit a pull request

## Acknowledgments

- [Ollama](https://ollama.ai) - Local LLM runtime
- [LangChain](https://python.langchain.com) - RAG orchestration
- [Streamlit](https://streamlit.io) - Web UI framework
- [ChromaDB](https://chroma.dev) - Vector database
