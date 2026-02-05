# Career Intelligence Assistant: Submission Notes

## a. Quick setup

**Prerequisites**
- macOS (Apple Silicon recommended) (Only machine I had available)
- Homebrew
- Python 3.9+
- Git

**Install Homebrew (if needed)**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**Install Ollama and models**
```bash
/opt/homebrew/bin/brew install ollama
/opt/homebrew/bin/brew services start ollama
/opt/homebrew/opt/ollama/bin/ollama pull llama3.2
/opt/homebrew/opt/ollama/bin/ollama pull mxbai-embed-large
```

**Project setup**
```bash
git clone https://github.com/shiivvv/Career-Intelligence-Assistant.git
cd Career-Intelligence-Assistant
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

or
```
run the quickstart.sh
```
---

## b. Architecture overview

**High level flow**

![Rought Diagram](<Architecture Diagram - Rough.png>)

Key components:
- **rag.py**: ingestion, chunking, embedding, vector store, retrieval, prompt assembly, URL scraping.
- **app.py**: Streamlit UI, file upload, URL input, session state, chat output and context display.

---

## c. What’s required to productionise & scale

If I were moving this to AWS, GCP, or Azure:

1. **Containerise** the app and run it on a managed platform (ECS/Fargate, GKE, AKS).
2. **Replace local Chroma** with a managed vector DB (Pinecone, Vertex AI Vector Search, Azure AI Search) for durability and scale.
3. **Externalise model hosting** (Bedrock, Vertex, Azure OpenAI) or run Ollama on GPU instances with autoscaling.
4. **Introduce async ingestion** with a task queue (SQS + Lambda, Cloud Tasks, Azure Queue Storage) so uploads don't block.
5. **Secure storage** (S3/GCS/Blob) for documents with encryption and retention policies.
6. **Observability**: centralised logging, tracing, latency/quality metrics, and alerting.
7. **Auth & tenancy**: user accounts, access control, and per-tenant vector indexes.
8. **Infrastructure as code** (Terraform or Pulumi) for repeatable deployments.

---

## d. RAG/LLM approach & decisions

**LLM**: Ollama with `llama3.2`
- Chosen for local inference speed and decent quality for career-focused queries.

**Embeddings**: `mxbai-embed-large` via Ollama
- Good balance between embedding quality and latency on Apple Silicon.

**Vector database**: Chroma (local, persistent)
- Lightweight and easy to run locally without extra services.

**Orchestration**: LangChain 0.0.352
- Stable with Python 3.9, straightforward retrieval QA flow.
- Could've used newer versions but would require Python upgrade and refactoring. 3.9 worked on my machine without issues.

**Prompt & context management**
- Structured prompt requesting fit score, matching skills, and gaps.
- Retrieval limits clamped to available chunks to avoid errors.
- Source metadata retained for traceability.

**Guardrails & quality**
- Minimal guardrails: prompt directs to ground responses in context.
- Could add confidence scoring and refusal logic for out-of-scope questions. SFW

**Observability**
- Currently lightweight (console output). Production would need structured logs, latency tracking, and retrieval hit-rate metrics.

---

## e. Key technical decisions (and why)

- **Local-first design**: keeps data private and avoids cloud dependencies.
- **Chroma over heavier vector stores**: fast setup, no extra infrastructure.
- **Chunking at 1000/200**: balances recall vs token cost.
- **Retriever k=6**: good coverage for short CVs and job descriptions.
- **Streamlit**: fastest path to a usable UI for iteration and demos.
- **URL scraping with BeautifulSoup**: simple web scraping without requiring file downloads.

---

## f. Engineering standards followed (and skipped)

**Followed**
- Modular structure (rag.py vs app.py) to separate concerns.
- Basic tests in `test_rag.py` with temp data.
- Consistent config in one place (rag.py constants).

**Skipped (time constraints)**
- Full CI pipeline and linting.
- Formal type checking (mypy).
- Security review and model safety testing.

---

## g. Use of AI tools

I used GitHub Copilot for boilerplate generation with Claude Sonnet 4.5 and Haiku 4.5, quick iteration on prompts, and to speed up repetitive code refactors. All logic decisions, architecture choices, and final edits were reviewed and refined manually with testing and debugging to ensure correctness and quality.

---

## h. What I’d do differently with more time

- Add a hybrid retriever (BM25 (Best Match 25) + semantic understanding).
- Introduce user accounts and per-user vector stores.
- Provide explainability: highlight which chunks drove each claim.
- Add proper evaluation with a labelled dataset for quality tracking.

---

## i. Notes for reviewers

This solution prioritises privacy and speed on a local machine. The design keeps things simple while allowing clear upgrade paths to managed services on AWS/GCP/Azure.

---

## j. My path to production readiness

If I were taking this into production:

**Phase 1: Containerise & scale horizontally**
I'd wrap the app in Docker and deploy to Azure Container Apps, AWS ECS, or GKE. Multiple replicas behind a load balancer means one slow query doesn't block everyone else. A health check endpoint would let the orchestrator know when the service is up.

**Phase 2: Move to managed infrastructure**
Instead of running Ollama locally, I'd use Azure OpenAI Service, AWS Bedrock, or Vertex AI. This removes GPU management headaches and gives automatic scaling. Local Chroma would become Azure AI Search or Pinecone for durability and backups.

**Phase 3: Decouple document ingestion**
Currently, uploads block until ingestion finishes. I'd add a task queue (Azure Queue Storage + Functions, AWS SQS + Lambda, or Cloud Tasks) so uploads return immediately. Background workers handle chunking and embedding, preventing timeouts on large batches.

**Phase 4: Secure and isolate per user**
User authentication (Azure AD B2C, AWS Cognito, or OAuth2) plus separate vector collections per tenant. Alice's CV never mixes with Bob's queries. Encrypt documents at rest and in transit, with audit logs for compliance.

**Phase 5: Observe and optimise**
Structured logging (Azure Monitor, CloudWatch, or Stackdriver) to track query latency, embedding costs, and retrieval quality. This data helps identify slow queries, optimise chunk sizes, or flag when fit-score logic drifts. Alerts trigger before users complain.

**My cloud provider choice: Azure**
I'd go with Azure. Azure OpenAI Service gives direct access to GPT-4 with enterprise SLAs, which beats managing open-source models. Azure AI Search integrates with OpenAI embeddings and offers hybrid search out of the box (no custom BM25 needed). Authentication is cleaner with Azure AD B2C, especially for enterprise customers already using Microsoft 365. Pricing for Container Apps and Blob storage is competitive, and regional availability lets me deploy closer to users in EMEA or APAC without vendor lock-in pain.

**Quick wins I'd implement first:**
- `/health` endpoint for orchestrators to monitor the app.
- Move Chroma to cloud storage (no data loss if container restarts).
- Request timeouts and retry logic for Ollama calls.
- Simple metrics endpoint (JSON with response times, query count) for dashboards.

Each phase is independent. I could ship Phase 1 (containerisation) within a week and defer Phase 5 (observability) until user volume justifies it.
