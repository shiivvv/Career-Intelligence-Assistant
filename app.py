"""
Career Intelligence Assistant - Streamlit UI
Chat interface for career analysis powered by local LLMs.
"""

import os
import tempfile
import warnings
from pathlib import Path

# Suppress warnings before importing streamlit
warnings.filterwarnings('ignore', category=UserWarning)
os.environ['PYTHONWARNINGS'] = 'ignore'

import streamlit as st
from rag import ingest_documents, create_rag_chain, load_existing_vectorstore


# Page configuration
st.set_page_config(
    page_title="Career Intelligence Assistant",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Career Intelligence Assistant 🚀")
st.markdown(
    "Analyze your resume against job descriptions using local AI. "
    "Offline, private, powered by Ollama + LangChain."
)


# Initialize session state
if "chain" not in st.session_state:
    st.session_state.chain = None
if "retrieved_docs" not in st.session_state:
    st.session_state.retrieved_docs = []


# Sidebar: Document Upload & Configuration
with st.sidebar:
    st.header("📋 Setup & Configuration")
    
    st.subheader("1. Upload Resume")
    resume_file = st.file_uploader(
        "Choose a resume (PDF or TXT)",
        type=["pdf", "txt"],
        help="Your resume will be analyzed against job descriptions"
    )
    
    st.subheader("2. Upload Job Descriptions")
    
    # Tab for different input methods
    job_input_tab = st.radio(
        "Choose input method:",
        ["Folder", "URLs"],
        horizontal=True
    )
    
    if job_input_tab == "Folder":
        st.write("Add job PDFs/TXTs to a folder on your local machine.")
        jobs_dir = st.text_input(
            "Path to jobs folder",
            value="./sample_jobs",
            help="Folder containing job description files (PDF/TXT)"
        )
        job_urls_input = None
    else:
        st.write("Paste job posting URLs (one per line):")
        job_urls_input = st.text_area(
            "Job URLs",
            height=150,
            placeholder="https://example.com/job1\nhttps://example.com/job2",
            help="Paste job posting URLs, one per line"
        )
        jobs_dir = "./sample_jobs"  # Default fallback
    
    st.subheader("3. Configuration")
    k_results = st.slider(
        "Number of relevant chunks to retrieve",
        min_value=3,
        max_value=15,
        value=6,
        help="Higher values = more context, slower inference"
    )
    temperature = st.slider(
        "LLM Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.1,
        step=0.1,
        help="Lower = more deterministic, Higher = more creative"
    )
    
    # Ingest button
    if st.button("📥 Ingest Documents", key="ingest_btn", use_container_width=True):
        if not resume_file:
            st.error("❌ Please upload a resume first.")
        elif job_input_tab == "Folder" and not Path(jobs_dir).exists():
            st.error(f"❌ Jobs folder not found: {jobs_dir}")
        elif job_input_tab == "URLs" and not job_urls_input:
            st.error("❌ Please provide at least one job URL.")
        else:
            with st.spinner("Ingesting documents... This may take a moment."):
                try:
                    # Save resume temporarily
                    with tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=".pdf" if resume_file.name.endswith(".pdf") else ".txt"
                    ) as tmp_file:
                        tmp_file.write(resume_file.read())
                        resume_path = tmp_file.name
                    
                    # Parse URLs if provided
                    job_urls = None
                    if job_input_tab == "URLs" and job_urls_input:
                        job_urls = [url.strip() for url in job_urls_input.split('\n') if url.strip()]
                    
                    # Ingest documents
                    retriever = ingest_documents(resume_path, jobs_dir, job_urls=job_urls)
                    st.session_state.chain = create_rag_chain(retriever)
                    
                    # Clean up
                    os.unlink(resume_path)
                    
                    st.success("✅ Documents ingested successfully!")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Error during ingestion: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
    
    # Load existing vectorstore
    if st.button("📂 Load Existing Vector Store", use_container_width=True):
        with st.spinner("Loading vector store..."):
            retriever = load_existing_vectorstore()
            if retriever:
                st.session_state.chain = create_rag_chain(retriever)
                st.success("✅ Vector store loaded!")
            else:
                st.warning("⚠️ No existing vector store found. Please ingest documents first.")


# Main content area
if st.session_state.chain is None:
    st.info(
        "👈 **Get Started:**\n\n"
        "1. Upload your resume in the sidebar\n"
        "2. Provide a path to a folder with job descriptions\n"
        "3. Click 'Ingest Documents'\n"
        "4. Start asking career questions!"
    )
    
    st.subheader("📚 Example Questions")
    st.write("""
    - "What is my fit score for Job 1?"
    - "What skills am I missing for this role?"
    - "How should I prepare for interviews based on my background?"
    - "Which job is the best fit for my profile?"
    - "What are the common requirements across all jobs?"
    """)

else:
    st.success("✅ Ready to analyze! Ask a question below.")
    
    # Chat interface
    st.subheader("💬 Career Analysis Chat")
    
    # Display chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if query := st.chat_input("Ask a career question (e.g., 'What's my fit score for Job 1?')"):
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": query
        })
        
        with st.chat_message("user"):
            st.markdown(query)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing... (running locally on Ollama)"):
                try:
                    response = st.session_state.chain(
                        {"query": query},
                        return_only_outputs=True
                    )
                    answer = response.get("result", "No response generated.")
                    st.markdown(answer)
                    
                    # Add assistant response to history
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": answer
                    })
                    
                    # Show retrieved documents in expander
                    with st.expander("📖 Retrieved Context"):
                        docs = response.get("source_documents", [])
                        if docs:
                            for i, doc in enumerate(docs, 1):
                                source = doc.metadata.get("filename", "Unknown")
                                st.write(f"**Document {i}: {source}**")
                                st.write(doc.page_content[:300] + "...")
                        else:
                            st.write("No documents retrieved.")
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # Sidebar: Chat controls
    with st.sidebar:
        st.divider()
        st.subheader("💬 Chat Controls")
        
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.chat_history = []
            st.success("Chat history cleared!")
        
        if st.button("🔄 Start New Analysis", use_container_width=True):
            st.session_state.chain = None
            st.session_state.chat_history = []
            st.rerun()


# Footer
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.9em;'>
    <p>Career Intelligence Assistant | Powered by Ollama + LangChain | All processing is local</p>
    </div>
    """,
    unsafe_allow_html=True
)
