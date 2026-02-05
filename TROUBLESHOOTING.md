# Troubleshooting Guide

## Dependency Installation Issues

### Issue: `unstructured==0.12.1` Not Found
**Error**: `ERROR: No matching distribution found for unstructured==0.12.1`

**Cause**: The `unstructured` package version 0.12.1 doesn't exist. Latest available is 0.18.3, which requires Python 3.10+.

**Solution**: 
- Uses `pypdf==3.17.1` instead for PDF parsing (lighter dependency)
- Python 3.9 users: Already resolved in current `requirements.txt`

### Issue: Python Version Too Old
**Error**: Various packages require `Requires-Python >=3.10.0`

**Cause**: Project venv using Python 3.9

**Solution**: 
- Updated requirements to use versions compatible with Python 3.9
- If upgrading to Python 3.11+, can use newer LangChain versions

### Installation Succeeded
✅ All packages now install on Python 3.9 with current `requirements.txt`:
- langchain 0.0.352
- chromadb 0.3.21  
- streamlit 1.28.0
- transformers, torch, sentence-transformers (for embeddings)

## Runtime Issues

### Issue: Ollama Connection Refused
```
ConnectionError: Failed to connect to http://localhost:11434
```

**Solution**:
```bash
# Start Ollama (if not running)
ollama serve &

# Or open the Ollama app
open -a Ollama
```

### Issue: Module Import Errors
```
ModuleNotFoundError: No module named 'langchain_ollama'
```

**Cause**: Using newer langchain imports with older API

**Solution**: Already fixed - imports use `langchain.chat_models.ChatOllama` pattern

### Issue: Vector Store Not Found
```
ValueError: Could not load existing vector store
```

**Solution**: 
- First run requires `ingest_documents()` to create `./chroma_db`
- To reset: `rm -rf chroma_db/` and re-ingest through UI

## Performance Issues

### Slow Installation (Long Dependency Resolution)
- First install may take 10-15 minutes due to large packages (torch, transformers)
- Subsequent installs are faster (caching)

### Large Download Sizes
- torch + transformers: ~100MB
- Total with deps: ~400MB
- Run `pip cache purge` to free space after install

## Verification

### Confirm Installation
```bash
source venv/bin/activate
python -c "import langchain, chromadb, streamlit, torch; print('✅ All core packages installed')"
```

### Check Ollama Models
```bash
ollama list
# Should show:
# llama3.2
# mxbai-embed-large
```

### Test Chain Locally
```python
from rag import load_existing_vectorstore, create_rag_chain
retriever = load_existing_vectorstore()
if retriever:
    chain = create_rag_chain(retriever)
    result = chain({"query": "Test query"})
    print(result["result"])
```

## Version Compatibility

| Component | Version | Reason |
|-----------|---------|--------|
| Python | 3.9+ | Current venv; upgrade to 3.11+ for newer LangChain |
| langchain | 0.0.352 | Last version before major API redesign; Python 3.9 compatible |
| chromadb | 0.3.21 | Stable, lightweight vector store |
| torch | 2.8.0 | Latest with Python 3.9 support |
| transformers | 4.57.6 | Matches torch version |

## Upgrading Python

To use newer LangChain (0.1.x, 1.x), upgrade to Python 3.11+:

```bash
# Create new environment with Python 3.11
python3.11 -m venv venv_new
source venv_new/bin/activate

# Update requirements for newer versions
pip install --upgrade langchain langchain-community langchain-ollama
```

Then update imports in `rag.py` and `app.py` to use new API patterns.

## Common Warnings (Safe to Ignore)

### LibreSSL Warning
```
urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'
```
**Status**: ✅ Safe - Only affects some SSL functionality, not needed for local Ollama usage

### Deprecated Warnings
Various deprecation warnings from transformers/torch are normal and won't affect functionality.

## Need Help?

1. Check `.github/copilot-instructions.md` for architecture overview
2. Review `SETUP.md` for dev workflows
3. Look at `test_rag.py` for usage examples
4. Test manually: `streamlit run app.py --logger.level=debug`
